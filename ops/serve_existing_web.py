"""Development only: serve an already built, pinned UI without installing packages."""

import argparse
import http.client
import mimetypes
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


def create_server(
    artifact: Path, *, port: int = 5173, backend_port: int = 8000, host: str = "127.0.0.1"
) -> ThreadingHTTPServer:
    if host not in ("127.0.0.1", "127.0.0.2", "::1"):
        raise ValueError("An explicit loopback host is required")
    if not 1024 <= port <= 65535 or not 1024 <= backend_port <= 65535 or port == backend_port:
        raise ValueError("Distinct loopback frontend/backend ports in 1024..65535 required")
    root = artifact.resolve(strict=True)
    if not (root / "index.html").is_file():
        raise ValueError("An existing built index.html is required")
    authority = f"[{host}]" if ":" in host else host
    expected_host = f"{authority}:{port}"
    expected_origin = f"http://{expected_host}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            # Do not record query strings, cookies, CSRF or one-use launch fragments.
            pass

        def handle_request(self) -> None:
            if self.headers.get("Host") != expected_host:
                self.send_error(403)
                return
            path = urlsplit(self.path).path
            if path.startswith("/v1/"):
                if len(self.headers.get_all("X-UAW-Schema-Version", [])) > 1:
                    self.send_error(400)
                    return
                if (
                    self.headers.get_all("Content-Length")
                    and len(self.headers.get_all("Content-Length")) != 1
                ):
                    self.send_error(400)
                    return
                if self.headers.get("Transfer-Encoding"):
                    self.send_error(400)
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self.send_error(400)
                    return
                if not 0 <= size <= 1048576:
                    self.send_error(413)
                    return
                if self.command != "GET" and self.headers.get("Origin") != expected_origin:
                    self.send_error(403)
                    return
                body = self.rfile.read(size) if size else None
                headers = {
                    key: self.headers[key]
                    for key in (
                        "Cookie",
                        "Origin",
                        "Referer",
                        "X-UAW-CSRF",
                        "X-UAW-Schema-Version",
                        "Content-Type",
                        "Accept",
                    )
                    if self.headers.get(key)
                }
                connection = http.client.HTTPConnection(host, backend_port, timeout=30)
                try:
                    connection.request(self.command, self.path, body=body, headers=headers)
                    response = connection.getresponse()
                    data = response.read(2097153)
                    if len(data) > 2097152:
                        self.send_error(502)
                        return
                    self.send_response(response.status)
                    for key, value in response.getheaders():
                        if key.lower() in ("content-type", "set-cookie", "cache-control"):
                            self.send_header(key, value)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except OSError, http.client.HTTPException:
                    self.send_error(502)
                finally:
                    connection.close()
                return
            if self.command != "GET":
                self.send_error(405)
                return
            target = (root / unquote(path).lstrip("/")).resolve()
            if not target.is_relative_to(root):
                self.send_error(403)
                return
            if not target.is_file():
                target = root / "index.html"
            data = target.read_bytes()
            self.send_response(200)
            self.send_header(
                "Content-Type", mimetypes.guess_type(target)[0] or "application/octet-stream"
            )
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_DELETE = handle_request

    class Server(ThreadingHTTPServer):
        address_family = socket.AF_INET6 if ":" in host else socket.AF_INET

    return Server((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--host", choices=("127.0.0.1", "127.0.0.2", "::1"), default="127.0.0.1")
    args = parser.parse_args()
    try:
        server = create_server(
            args.artifact, port=args.port, backend_port=args.backend_port, host=args.host
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
