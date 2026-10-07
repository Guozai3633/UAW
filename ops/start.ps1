param([switch]$WithPostgres)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run uv sync before startup' }
Push-Location $taskRoot
try {
    $taskConfig = 'ops/development.toml'
    if ($WithPostgres) {
        & $taskPython ops/provision_dev_auth.py
        if ($LASTEXITCODE -ne 0) { throw 'Secure development authentication setup failed' }
        & (Join-Path $PSScriptRoot 'start-dev-db.ps1')
        & $taskPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Database migration failed' }
        $taskConfig = 'ops/database-development.toml'
    }
    & $taskPython -m uaw.application serve --config $taskConfig
    if ($LASTEXITCODE -ne 0) { throw 'UAW startup failed' }
} finally {
    Pop-Location
}

