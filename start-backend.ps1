# Start only the FastAPI backend and capture its output in the project logs folder.
param(
    [ValidateRange(1024, 65535)][int]$Port = 8000,
    [ValidateRange(1024, 65535)][int]$FrontendPort = 5173
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$backendDirectory = Join-Path $projectRoot 'backend'
$logDirectory = Join-Path $projectRoot 'logs'
$child = $null
$environmentNames = @('NO_COLOR', 'SESSION_COOKIE_SECURE', 'SESSION_COOKIE_SAMESITE', 'CORS_ORIGINS', 'API_V1_PREFIX')
$previousEnvironment = @{}

try {
    if (-not (Test-Path (Join-Path $backendDirectory '.env'))) {
        throw 'Missing backend/.env. Copy backend/.env.example to backend/.env and configure it first.'
    }
    $uvExecutable = (Get-Command uv -ErrorAction Stop).Source
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() }
    catch { throw "Port $Port is already in use. Stop the existing backend before starting this script." }
    finally { $listener.Stop() }

    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    foreach ($name in $environmentNames) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    $env:NO_COLOR = '1'
    $env:SESSION_COOKIE_SECURE = 'false'
    $env:SESSION_COOKIE_SAMESITE = 'lax'
    $env:CORS_ORIGINS = "http://127.0.0.1:$FrontendPort"
    $env:API_V1_PREFIX = '/api/v1'
    $child = Start-Process -FilePath $uvExecutable `
        -ArgumentList @('run', 'python', '-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', $Port) `
        -WorkingDirectory $backendDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logDirectory 'backend.stdout.log') `
        -RedirectStandardError (Join-Path $logDirectory 'backend.stderr.log')

    $ready = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        if ($child.HasExited) { throw "The backend exited during startup. Check backend.stderr.log." }
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw "Timed out waiting for the backend. Check backend.stderr.log." }
    Write-Host "Backend running at http://127.0.0.1:$Port"
    Write-Host "API docs: http://127.0.0.1:$Port/docs"
    Write-Host "Logs: $logDirectory\backend.stdout.log and backend.stderr.log"
    Write-Host 'Keep this terminal open; press Ctrl+C to stop the backend.'
    while (-not $child.HasExited) { Start-Sleep -Seconds 1 }
    throw "The backend stopped with exit code $($child.ExitCode). Check backend.stderr.log."
} finally {
    if ($child -and -not $child.HasExited) {
        try { & taskkill.exe /PID $child.Id /T /F 2>&1 | Out-Null }
        catch { Write-Warning "Could not stop backend process $($child.Id)." }
    }
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}

