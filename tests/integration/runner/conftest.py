"""Use the source Runner package until A publishes its installation entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/local_runner"))
