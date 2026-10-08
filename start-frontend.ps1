# Start only the Vite frontend and capture its output in the project logs folder.
param(
    [ValidateRange(1024, 65535)][int]$Port = 5173,
    [ValidateRange(1024, 65535)][int]$BackendPort = 8000
)

$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$frontendDirectory = Join-Path $projectRoot 'frontend'
$logDirectory = Join-Path $projectRoot 'logs'
$child = $null
$environmentNames = @('NO_COLOR', 'VITE_API_BASE_URL', 'VITE_API_PREFIX')
$previousEnvironment = @{}

try {
    $nodeExecutable = (Get-Command node -ErrorAction Stop).Source
    if (-not (Test-Path (Join-Path $frontendDirectory 'node_modules/vite/bin/vite.js'))) {
        throw 'Frontend dependencies are missing. Run npm ci from frontend first.'
    }
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() }
    catch { throw "Port $Port is already in use. Stop the existing frontend before starting this script." }
    finally { $listener.Stop() }

    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    foreach ($name in $environmentNames) {
        $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    $env:NO_COLOR = '1'
    $env:VITE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
    $env:VITE_API_PREFIX = '/api/v1'
    $child = Start-Process -FilePath $nodeExecutable `
        -ArgumentList @('node_modules/vite/bin/vite.js', '--host', '127.0.0.1', '--port', $Port, '--strictPort') `
        -WorkingDirectory $frontendDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logDirectory 'frontend.stdout.log') `
        -RedirectStandardError (Join-Path $logDirectory 'frontend.stderr.log')

    $ready = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        if ($child.HasExited) { throw "The frontend exited during startup. Check frontend.stderr.log." }
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw "Timed out waiting for the frontend. Check frontend.stderr.log." }
    Write-Host "Frontend running at http://127.0.0.1:$Port"
    Write-Host "Backend expected at http://127.0.0.1:$BackendPort"
    Write-Host "Logs: $logDirectory\frontend.stdout.log and frontend.stderr.log"
    Write-Host 'Keep this terminal open; press Ctrl+C to stop the frontend.'
    while (-not $child.HasExited) { Start-Sleep -Seconds 1 }
    throw "The frontend stopped with exit code $($child.ExitCode). Check frontend.stderr.log."
} finally {
    if ($child -and -not $child.HasExited) {
        try { & taskkill.exe /PID $child.Id /T /F 2>&1 | Out-Null }
        catch { Write-Warning "Could not stop frontend process $($child.Id)." }
    }
    foreach ($name in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previousEnvironment[$name], 'Process')
    }
}
