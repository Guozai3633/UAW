"""Real Windows temporary path/junction checks; no real user project is touched."""

import subprocess
import sys
from pathlib import Path

import pytest

from tests.unit.runner.conftest import EXPIRES, NOW, SelectionDouble
from uaw.shared.contracts import Ref
from uaw.shared.errors import DomainError
from uaw.workspace.binding import RootBindings
from uaw.workspace.contracts import RootSelection
from uaw.workspace.repository import MemoryRootRepository


def test_real_native_junctions_inside_and_outside_root(tmp_path: Path):
    root = tmp_path / "root"
    inside = root / "inside"
    outside = tmp_path / "outside"
    inside.mkdir(parents=True)
    outside.mkdir()
    (inside / "ok.txt").write_text("原文", encoding="utf-8")
    (outside / "secret.txt").write_text("outside fixture", encoding="utf-8")
    bindings = RootBindings(MemoryRootRepository(), SelectionDouble(root))
    workspace = Ref(kind="workspace", id="fixture", version="v1")
    bindings.bind(
        RootSelection(
            selection_token="native-test-token",
            display_name="fixture",
            expires_at=EXPIRES,
            root_handle="native1",
        ),
        principal_id="u1",
        device_id="d1",
        workspace_ref=workspace,
        capabilities=frozenset({"read"}),
        now=NOW,
    )
    links = []
    try:
        for name, target in (("local", inside), ("escape", outside)):
            link = root / name
            if sys.platform == "win32":
                result = subprocess.run(
                    ["cmd.exe", "/c", "mklink", "/J", str(link), str(target)],
                    capture_output=True,
                    check=False,
                )
                assert result.returncode == 0, "Native junction fixture could not be created"
            else:
                link.symlink_to(target, target_is_directory=True)
            links.append(link)
        options = dict(
            root_handle="native1",
            principal_id="u1",
            device_id="d1",
            workspace_ref=workspace,
            expected_revision=0,
        )
        assert bindings.check_scope(**options, relative_path="local/ok.txt") == inside / "ok.txt"
        with pytest.raises(DomainError):
            bindings.check_scope(**options, relative_path="escape/secret.txt")
        bindings.revoke("native1", expected_revision=0)
        with pytest.raises(DomainError):
            bindings.check_scope(**options, relative_path="inside/ok.txt")
        assert (outside / "secret.txt").read_text(encoding="utf-8") == "outside fixture"
    finally:
        for link in reversed(links):
            if sys.platform == "win32":
                link.rmdir()  # Removes only the junction, never its target.
            else:
                link.unlink()


def test_real_root_replacement_invalidates_binding(tmp_path: Path):
    root = tmp_path / "selected"
    root.mkdir()
    (root / "file.txt").write_text("original", encoding="utf-8")
    bindings = RootBindings(MemoryRootRepository(), SelectionDouble(root))
    workspace = Ref(kind="workspace", id="fixture", version="v1")
    bindings.bind(
        RootSelection(
            selection_token="native-test-token",
            display_name="fixture",
            expires_at=EXPIRES,
            root_handle="r1",
        ),
        principal_id="u1",
        device_id="d1",
        workspace_ref=workspace,
        capabilities=frozenset({"read"}),
        now=NOW,
    )
    root.rename(tmp_path / "old-selected")
    root.mkdir()
    (root / "file.txt").write_text("replacement", encoding="utf-8")
    with pytest.raises(DomainError):
        bindings.check_scope(
            root_handle="r1",
            principal_id="u1",
            device_id="d1",
            workspace_ref=workspace,
            expected_revision=0,
            relative_path="file.txt",
        )
