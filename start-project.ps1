# Local development only. Stop with Ctrl+C to shut down both process trees.
param(
    [ValidateRange(1024, 65535)][int]$BackendPort = 8000,
    [ValidateRange(1024, 65535)][int]$FrontendPort = 5173
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$backendDirectory = Join-Path $projectRoot 'backend'
$frontendDirectory = Join-Path $projectRoot 'frontend'
$logDirectory = Join-Path $projectRoot 'logs'
$children = @()
$environmentNames = @('SESSION_COOKIE_SECURE', 'SESSION_COOKIE_SAMESITE', 'CORS_ORIGINS', 'API_V1_PREFIX', 'VITE_API_BASE_URL', 'VITE_API_PREFIX')
$previousEnvironment = @{}

try {
    if ($BackendPort -eq $FrontendPort) { throw 'BackendPort and FrontendPort must be different.' }
    $uvExecutable = (Get-Command uv -ErrorAction Stop).Source
    $nodeExecutable = (Get-Command node -ErrorAction Stop).Source
    if (-not (Test-Path (Join-Path $backendDirectory '.env'))) {
        throw 'Missing backend/.env. Copy backend/.env.example to backend/.env and configure it first.'
    }
    if (-not (Test-Path (Join-Path $frontendDirectory 'node_modules/vite/bin/vite.js'))) {
        throw 'Frontend dependencies are missing. Run npm ci from frontend first.'
    }
    foreach ($port in @($BackendPort, $FrontendPort)) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start() }
        catch { throw "Port $port is already in use. Stop its existing server before starting this script." }
        finally { $listener.Stop() }
    }
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    foreach ($name in $environmentNames) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    # These overrides apply only to the local child processes, not .env files.
    $env:SESSION_COOKIE_SECURE = 'false'
    $env:SESSION_COOKIE_SAMESITE = 'lax'
    $env:CORS_ORIGINS = "http://127.0.0.1:$FrontendPort"
    $env:VITE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
    $env:VITE_API_PREFIX = '/api/v1'
    $env:API_V1_PREFIX = '/api/v1'
    $children += Start-Process -FilePath $uvExecutable -ArgumentList @('run', 'python', '-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', $BackendPort) -WorkingDirectory $backendDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'backend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'backend.stderr.log')
    $children += Start-Process -FilePath $nodeExecutable -ArgumentList @('node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', $FrontendPort, '--strictPort') -WorkingDirectory $frontendDirectory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'frontend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'frontend.stderr.log')
    foreach ($url in @("http://127.0.0.1:$BackendPort/", "http://127.0.0.1:$FrontendPort/")) {
        $ready = $false
        for ($attempt = 0; $attempt -lt 45; $attempt++) {
            foreach ($child in $children) {
                if ($child.HasExited) { throw "A service exited during startup. Check logs in $logDirectory." }
            }
            try {
                $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200) { $ready = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if (-not $ready) { throw "Timed out waiting for $url. Check logs in $logDirectory." }
    }
    Write-Host 'Project running. Keep this terminal open; press Ctrl+C to stop both services.'
    Write-Host "Mapping:  http://127.0.0.1:$FrontendPort"
    Write-Host "Bulk reg: http://127.0.0.1:$FrontendPort/bulk-reg"
    Write-Host "API docs: http://127.0.0.1:$BackendPort/docs"
    Write-Host "Logs: $logDirectory"
    while ($true) {
        foreach ($child in $children) {
            if ($child.HasExited) { throw "A service stopped. Check logs in $logDirectory." }
        }
        Start-Sleep -Seconds 1
    }
} finally {
    foreach ($child in $children) {
        if (-not $child.HasExited) {
            try { & taskkill.exe /PID $child.Id /T /F 2>&1 | Out-Null }
            catch { Write-Warning "Could not stop service process $($child.Id)." }
        }
    }
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
