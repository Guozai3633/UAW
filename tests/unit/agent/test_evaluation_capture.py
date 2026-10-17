"""Offline evidence publication must not execute or overwrite captured content."""

import io
import zipfile

import pytest

from uaw.run.evaluation_capture import CaptureError, verify_runtime, write_bundle


def test_review_page_escapes_content_keeps_empty_human_reviews_and_refuses_overwrite(tmp_path):
    target = tmp_path / "capture"
    text = '</pre><script>fetch("https://untrusted.invalid")</script>'
    bundle = {
        "suite": {"cases": [{"prompt": text, "rubric": {"critical": True}}]},
        "manifest": {},
        "audit": {},
        "observations": [{"phase": "answer", "attempt_id": "attempt-1", "output": text}],
        "reviews": [],
    }
    write_bundle(target, bundle)
    page = (target / "review.html").read_text(encoding="utf-8")
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "default-src 'none'" in page and (target / "reviews.jsonl").read_bytes() == b""
    original = (target / "suite.json").read_bytes()
    with pytest.raises(FileExistsError):
        write_bundle(target, bundle)
    assert (target / "suite.json").read_bytes() == original


@pytest.mark.parametrize("change", ["content", "extra_python", "escape"])
def test_attestation_rejects_runtime_drift_or_escape(tmp_path, monkeypatch, change):
    root = tmp_path / "runtime"
    package = root / "src/uaw"
    package.mkdir(parents=True)
    source = package / "__init__.py"
    source.write_bytes(b"# pinned\n")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("src/uaw/__init__.py", b"# pinned\n")
        if change == "escape":
            output.writestr("../outside.py", b"# outside\n")
    monkeypatch.setattr(
        "uaw.run.evaluation_capture.subprocess.check_output", lambda *a, **k: archive.getvalue()
    )
    if change == "content":
        source.write_bytes(b"# changed\n")
    elif change == "extra_python":
        (package / "surprise.py").write_bytes(b"# extra\n")
    else:
        (tmp_path / "outside.py").write_bytes(b"# outside\n")
    with pytest.raises(CaptureError):
        verify_runtime(tmp_path, root, "a" * 40)
