$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskData = Join-Path $taskRoot '.data'
New-Item -ItemType Directory -Path $taskData -Force | Out-Null
$taskEnvFile = Join-Path $taskData 'dev-db.env'
if (-not (Test-Path -LiteralPath $taskEnvFile)) {
    $taskPassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
    Set-Content -LiteralPath $taskEnvFile -Value "UAW_DEV_DB_PASSWORD=$taskPassword" -Encoding utf8NoBOM
}
$taskPasswordLine = Get-Content -LiteralPath $taskEnvFile | Where-Object { $_ -match '^UAW_DEV_DB_PASSWORD=[A-Fa-f0-9]{48}$' }
if (@($taskPasswordLine).Count -ne 1) { throw 'Invalid development database credential file' }
$taskPassword = $taskPasswordLine.Split('=', 2)[1]
$env:UAW_TEST_DATABASE_URL = "postgresql+psycopg://uaw_dev:${taskPassword}@127.0.0.1:55432/uaw_dev"
$env:UAW_DATABASE_URL = $env:UAW_TEST_DATABASE_URL
docker compose --progress quiet --env-file $taskEnvFile -f (Join-Path $PSScriptRoot 'compose.yaml') up -d --wait --wait-timeout 60
if ($LASTEXITCODE -ne 0) { throw 'Development PostgreSQL did not become ready' }
Write-Output 'Development PostgreSQL ready on loopback port 55432; URL set in this process environment.'
