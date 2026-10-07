param([switch]$WithPostgres)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run uv sync before checks' }
Push-Location $taskRoot
try {
    & $taskPython ops/sync_runtime_contracts.py
    if ($LASTEXITCODE -ne 0) { throw 'Contract synchronization failed' }
    & $taskPython -m ruff check src tests/unit tests/integration tests/conftest.py
    if ($LASTEXITCODE -ne 0) { throw 'Static checks failed' }
    & $taskPython -m ruff format --check src tests/unit tests/integration tests/conftest.py
    if ($LASTEXITCODE -ne 0) { throw 'Formatting checks failed' }
    & $taskPython -m mypy src/uaw
    if ($LASTEXITCODE -ne 0) { throw 'Type checks failed' }
    if ($WithPostgres) {
        & (Join-Path $PSScriptRoot 'start-dev-db.ps1')
        & $taskPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Database migration failed' }
        & $taskPython -m pytest -q --require-postgres --junitxml=docs/implementation/evidence/p0-tests.xml
    } else {
        & $taskPython -m pytest -q
    }
    if ($LASTEXITCODE -ne 0) { throw 'Runtime checks failed' }
} finally {
    Pop-Location
}

