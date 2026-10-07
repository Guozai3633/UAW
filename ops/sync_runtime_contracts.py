"""Copy the single authoritative schema into the distributable Python package."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "contracts/uaw.schema.json"
target = ROOT / "src/uaw/resources/uaw.schema.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(source.read_bytes())
print("Runtime schema synchronized from contracts/uaw.schema.json")

