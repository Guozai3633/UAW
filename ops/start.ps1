param([switch]$WithPostgres, [switch]$Browser, [switch]$EnableAgent)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run uv sync before startup' }
Push-Location $taskRoot
try {
    if ($EnableAgent -and -not $Browser) { throw 'EnableAgent requires the explicit Browser startup mode' }
    $taskConfig = 'ops/development.toml'
    if ($WithPostgres -or $Browser) {
        & $taskPython ops/provision_dev_auth.py
        if ($LASTEXITCODE -ne 0) { throw 'Secure development authentication setup failed' }
        & (Join-Path $PSScriptRoot 'start-dev-db.ps1')
        & $taskPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Database migration failed' }
        $taskConfig = 'ops/database-development.toml'
    }
    if ($Browser) {
        $taskConfig = 'ops/browser-development.toml'
        if ($EnableAgent) {
            # Copy only the public template, never resolved secrets or environment values.
            $taskConfig = '.data/browser-agent-development.toml'
            $taskTemplate = Get-Content -LiteralPath 'ops/browser-development.toml' -Raw
            Set-Content -LiteralPath $taskConfig -Value ($taskTemplate + "`nagent_execution_enabled = true`n") -Encoding utf8NoBOM
        }
    }
    & $taskPython -m uaw.application serve --config $taskConfig
    if ($LASTEXITCODE -ne 0) { throw 'UAW startup failed' }
} finally {
    Pop-Location
}

