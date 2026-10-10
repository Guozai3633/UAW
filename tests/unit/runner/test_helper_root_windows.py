"""Constructor-only source doubles; no IPC, authority, root or native approval claim."""

from types import SimpleNamespace

import pytest
from uaw_runner.keys import Ed25519SignatureAdapter
from uaw_runner.runtime import ReadOnlyHelper


def construct(**limits):
    directory, mapping, bindings, reader = object(), object(), object(), object()
    protocol = SimpleNamespace(
        bindings=bindings,
        principal_mapping=mapping,
        device_id="d1",
        signatures=Ed25519SignatureAdapter(directory),
    )
    bootstrap = SimpleNamespace(
        directory=directory, mapping=mapping, device_key=SimpleNamespace(device_id="d1")
    )
    roots = SimpleNamespace(bindings=bindings, directory=directory, mapping=mapping)
    return ReadOnlyHelper(
        bootstrap=bootstrap,
        protocol=protocol,
        commands=reader,
        journal=SimpleNamespace(protocol=protocol, reader=reader),
        executions=None,
        roots=roots,
        registry=None,
        currency="USD",
        **limits,
    )


def test_default_root_windows_preserve_60():
    helper = construct()
    assert helper.session_lifetime_seconds == helper.native_timeout_seconds == 60


@pytest.mark.parametrize("session,native", [(120, 120), (120, 60), (60, 30), (0.1, 0.05)])
def test_valid_trusted_limits(session, native):
    helper = construct(session_lifetime_seconds=session, native_timeout_seconds=native)
    assert helper.session_lifetime_seconds == session and helper.native_timeout_seconds == native


@pytest.mark.parametrize(
    "session,native",
    [
        (True, 1),
        (60, True),
        (False, False),
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
        (60, 61),
        (120.01, 60),
        (121, 121),
        (float("nan"), 60),
        (60, float("nan")),
        (float("inf"), 60),
        (60, float("inf")),
        (float("-inf"), 60),
        ("120", 60),
        (120, "60"),
        (None, 60),
        (60, None),
        (10**500, 60),
    ],
)
def test_bad_limits_refused_before_sources(session, native):
    with pytest.raises(ValueError):
        construct(session_lifetime_seconds=session, native_timeout_seconds=native)
