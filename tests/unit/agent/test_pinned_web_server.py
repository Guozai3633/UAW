"""Actual TCP proxy boundaries for independently pinned human experience services."""

import http.client
import socket
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ops.serve_existing_web import create_server


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def running(server):
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        assert not worker.is_alive()


@pytest.mark.parametrize(
    "ports", [(1023, 8000), (5173, 65536), (65536, 8000), (5173, 1023), (8000, 8000)]
)
def test_invalid_or_shared_ports_refused(tmp_path, ports):
    with pytest.raises(ValueError):
        create_server(tmp_path, port=ports[0], backend_port=ports[1])


def test_missing_dist_does_not_listen(tmp_path):
    with pytest.raises(ValueError):
        create_server(tmp_path, port=free_port(), backend_port=8000)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "localhost", "example.com"])
def test_unpinned_or_public_host_refused(tmp_path, host):
    with pytest.raises(ValueError):
        create_server(tmp_path, host=host)


def test_actual_independent_loopback_is_separate_cookie_host(tmp_path):
    class Backend(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            assert self.headers["Host"] == f"127.0.0.2:{self.server.server_port}"
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

    (tmp_path / "index.html").write_bytes(b"<h1>H01</h1>")
    backend = ThreadingHTTPServer(("127.0.0.2", 0), Backend)
    with socket.socket() as sock:
        sock.bind(("127.0.0.2", 0))
        port = sock.getsockname()[1]
    with (
        running(backend),
        running(
            create_server(tmp_path, host="127.0.0.2", port=port, backend_port=backend.server_port)
        ),
    ):
        client = http.client.HTTPConnection("127.0.0.2", port, timeout=3)
        try:
            client.request(
                "GET", "/v1/web/session", headers={"Referer": f"http://127.0.0.2:{port}/"}
            )
            response = client.getresponse()
            assert response.status == 200 and response.read() == b"{}"
        finally:
            client.close()


def test_actual_nondefault_tcp_preserves_session_and_exact_origin(tmp_path):
    seen = []

    class Backend(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            seen.append(
                (
                    self.path,
                    dict(self.headers),
                    self.rfile.read(int(self.headers["Content-Length"])),
                )
            )
            data = b'{"actual_backend":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "fixture=session; HttpOnly; SameSite=strict; Path=/v1")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    backend = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
    port = free_port()
    origin = f"http://127.0.0.1:{port}"
    (tmp_path / "index.html").write_bytes(b"<h1>pinned</h1>")
    with (
        running(backend),
        running(create_server(tmp_path, port=port, backend_port=backend.server_port)),
    ):
        client = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            for headers in (
                {"Origin": "http://127.0.0.1:5173"},
                {"Origin": origin, "Host": "evil.invalid"},
            ):
                client.request("POST", "/v1/web/session", body=b"{}", headers=headers)
                response = client.getresponse()
                assert response.status == 403
                response.read()
            assert seen == []
            client.request(
                "POST",
                "/v1/web/session",
                body=b"{}",
                headers={
                    "Origin": origin,
                    "Cookie": "original=fixture",
                    "X-UAW-CSRF": "fixture-csrf",
                    "Content-Type": "application/json",
                },
            )
            response = client.getresponse()
            assert response.status == 200 and response.read() == b'{"actual_backend":true}'
            assert "HttpOnly" in response.getheader("Set-Cookie")
            assert len(seen) == 1
            assert seen[0][1]["Host"] == f"127.0.0.1:{backend.server_port}"
            assert seen[0][1]["Origin"] == origin
            assert seen[0][1]["Cookie"] == "original=fixture"
            assert seen[0][1]["X-UAW-CSRF"] == "fixture-csrf"
            client.request("GET", "/conversation/example")
            response = client.getresponse()
            assert response.status == 200 and response.read() == b"<h1>pinned</h1>"
            client.request("GET", "/%2e%2e/private.txt")
            response = client.getresponse()
            assert response.status == 403
            response.read()
        finally:
            client.close()


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_proxy_preserves_explicit_protocol_and_rejects_duplicate_headers(tmp_path, version):
    seen = []

    class Backend(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            seen.append(self.headers.get_all("X-UAW-Schema-Version"))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"{}")

    (tmp_path / "index.html").write_bytes(b"<h1>pinned</h1>")
    backend = ThreadingHTTPServer(("127.0.0.1", 0), Backend)
    port = free_port()
    with (
        running(backend),
        running(create_server(tmp_path, port=port, backend_port=backend.server_port)),
    ):
        client = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            client.request(
                "GET", "/v1/runs/original/conversation", headers={"X-UAW-Schema-Version": version}
            )
            response = client.getresponse()
            assert response.status == 200 and response.read() == b"{}"
            assert seen == [[version]]
            client.putrequest("GET", "/v1/runs/original/conversation")
            client.putheader("X-UAW-Schema-Version", version)
            client.putheader("X-UAW-Schema-Version", version)
            client.endheaders()
            response = client.getresponse()
            assert response.status == 400
            response.read()
            assert seen == [[version]]
        finally:
            client.close()
