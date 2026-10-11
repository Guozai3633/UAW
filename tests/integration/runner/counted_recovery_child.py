"""D actual helper with labelled registration/UI fixture, counted OS opens only."""

import os
from pathlib import Path

from uaw_runner.handle_read import WindowsReadHandle

from tests.integration.runner.helper_fixture import assembly as assembly

original = WindowsReadHandle.__init__


def counted_open(self, *args, **kwargs):
    directory = Path(os.environ["UAW_D_TEST_HELPER_INPUT"]).resolve().parent
    counter = directory / "os-open-count.txt"
    count = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(count + 1), encoding="ascii")
    return original(self, *args, **kwargs)


WindowsReadHandle.__init__ = counted_open
