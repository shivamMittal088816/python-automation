# Forward arguments to the separately installed Archify CLI.
# Example: .\archify.ps1 guide "Show the student mapping workflow" --json
$ErrorActionPreference = 'Stop'

$skillRoots = @()
if ($env:ARCHIFY_HOME) {
    $skillRoots += $env:ARCHIFY_HOME
} else {
    if ($env:CODEX_HOME) {
        $skillRoots += Join-Path $env:CODEX_HOME 'skills/archify'
    }
    $skillRoots += Join-Path $env:USERPROFILE '.agents/skills/archify'
    $skillRoots += Join-Path $env:USERPROFILE '.codex/skills/archify'
    $skillRoots += Join-Path $env:USERPROFILE '.codex-account1/skills/archify'
}

$cli = $null
foreach ($root in $skillRoots) {
    $candidate = Join-Path $root 'bin/archify.mjs'
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $cli = $candidate
        break
    }
}
if (-not $cli) {
    throw 'Archify is not installed. See backend/docs/ARCHIFY.md, or set ARCHIFY_HOME to its installed skill directory.'
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw 'Node.js is required to run Archify.'
}

& node $cli @args
exit $LASTEXITCODE
