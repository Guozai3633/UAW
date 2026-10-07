"""Capture versions and reviewed source hashes; never capture config secrets/env values."""

import argparse
import hashlib
import json
import platform
import subprocess
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--allow-offline-engine", action="store_true",
                    help="Carry forward explicitly labelled engine version metadata; never test results")
args = parser.parse_args()
target = ROOT / "docs/implementation/evidence/environment.json"
test_path = ROOT / "docs/implementation/evidence/p0-tests.xml"
suites = ET.parse(test_path).getroot().iter("testsuite")
test_counts = {key: 0 for key in ("tests", "failures", "errors", "skipped")}
for suite in suites:
    for key in test_counts:
        test_counts[key] += int(suite.get(key, "0"))
if not test_counts["tests"] or any(test_counts[key] for key in ("failures", "errors", "skipped")):
    raise RuntimeError("Environment evidence requires passing real-database checks without skipped tests")
packages = {
    "fastapi": "fastapi", "uvicorn": "uvicorn", "pydantic": "pydantic",
    "jsonschema": "jsonschema", "sqlalchemy": "sqlalchemy", "psycopg": "psycopg",
    "alembic": "alembic", "structlog": "structlog", "httpx": "httpx",
    "keyring": "keyring",
    "langgraph": "langgraph", "graph_checkpoint": "langgraph-checkpoint-postgres",
    "langchain": "langchain-core", "pytest": "pytest", "ruff": "ruff", "mypy": "mypy",
}
components = {id: {"installed": True, "version": version(package)} for id, package in packages.items()}
components["python"] = {"installed": True, "version": platform.python_version()}
components["uv"] = {
    "installed": True,
    "version": subprocess.check_output(["uv", "--version"], text=True).strip().split()[1],
}
engine_metadata: dict[str, object] = {"observed_live": True}
try:
    postgres_version = subprocess.check_output(
        ["docker", "exec", "uaw-development-postgres-1", "psql", "-U", "uaw_dev", "-d", "uaw_dev",
         "-Atc", "SHOW server_version"], text=True, stderr=subprocess.DEVNULL,
    ).strip().split()[0]
    components["postgres"] = {
        "installed": True, "version": postgres_version, "scope": "isolated_dev_container"
    }
    components["docker"] = {
        "installed": True,
        "version": subprocess.check_output(
            ["docker", "info", "--format", "{{.ServerVersion}}"], text=True,
            stderr=subprocess.DEVNULL,
        ).strip(),
    }
except (OSError, subprocess.CalledProcessError):
    if not args.allow_offline_engine:
        raise RuntimeError("Engine unavailable; offline metadata requires explicit opt-in") from None
    previous_bytes = target.read_bytes()
    previous = json.loads(previous_bytes)
    for component in ("postgres", "docker"):
        if not previous["components"][component].get("version"):
            raise RuntimeError("Missing previously verified engine metadata")
        components[component] = {
            **previous["components"][component],
            "version_source": "previous_verified_environment",
            "currently_available": False,
        }
    engine_metadata = {
        "observed_live": False,
        "version_metadata_source": "previous_verified_environment",
        "previous_evidence_sha256": hashlib.sha256(previous_bytes).hexdigest(),
        "note": "Engine stopped after passing test receipt; versions are historical, not current availability",
    }
paths = [ROOT / p for p in ["pyproject.toml", "uv.lock", ".python-version", "alembic.ini"]]
for directory, pattern in [
    ("src/uaw", "*.py"), ("tests/unit", "*.py"), ("tests/integration", "*.py"),
    ("ops", "*.py"), ("ops", "*.ps1"), ("ops", "*.toml"),
]:
    paths.extend((ROOT / directory).rglob(pattern))
paths.extend([ROOT / "tests/conftest.py", ROOT / "ops/compose.yaml", ROOT / "contracts/uaw.schema.json"])
paths.extend(ROOT / "contracts" / name for name in (
    "interface_catalog.py", "implementation_catalog.py", "build_interfaces.py", "check_interfaces.py",
))
paths.extend((ROOT / "src/uaw/resources/prompts").glob("*.txt"))
paths = [p for p in paths if "__pycache__" not in p.parts and p.name != "local.toml"]
report = {
    "date": "2026-10-07", "platform": platform.system(), "machine": platform.machine(),
    "scope": "P0 foundation/control plane/model protocol and P1-01 source-bound understanding, using real PostgreSQL and controlled HTTP replies; no external LLM, Agent or Runner task",
    "components": components,
    "python_packages": {package: version(package) for package in packages.values()},
    "compatibility": {"core_checks": True, "langgraph_basic_api": True,
                      "postgres_development_checks": True, "model_protocol_checks": True,
                      "intent_protocol_checks": True,
                      "external_llm_verified": False, "model_agent_runner": False},
    "test_counts": test_counts,
    "engine_metadata": engine_metadata,
    "test_evidence_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
    "runtime_implementation": "development_control_plane_run_admission_model_and_intent_protocol",
    "source_hashes": {str(p.relative_to(ROOT)).replace('\\', '/'):
                      hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},
}
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"components": len(components), "source_files": len(report["source_hashes"]),
                  "report": str(target.relative_to(ROOT))}))
