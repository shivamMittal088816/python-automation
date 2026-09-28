# Archify commands

This project uses [tt-a1i/archify](https://github.com/tt-a1i/archify), the
interactive diagram tool. Its skill and CLI are installed in your user profile;
the repository contains only a PowerShell command wrapper. There is no Archify
application dependency or copied upstream repository.

## Installation on another machine

Install Node.js, then install the skill outside the project:

```powershell
npx.cmd -y skills add tt-a1i/archify --skill archify --agent codex --global --copy --yes
```

The wrapper checks `CODEX_HOME/skills/archify`, then the user profile's
`.agents/skills/archify`, `.codex/skills/archify`, and
`.codex-account1/skills/archify`. For a custom install, set `ARCHIFY_HOME` to the
directory containing Archify's `bin/archify.mjs`.

## Run from the project root

```powershell
.\archify.ps1 doctor
.\archify.ps1 --help
.\archify.ps1 guide "Show the student mapping workflow" --json
.\archify.ps1 demo .\tmp\archify-demo
```

If PowerShell blocks scripts, use this invocation for any command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\archify.ps1 doctor
```

Archify renders authored diagram JSON; the CLI does not automatically analyze
the application. Ask the agent to read the source and create that JSON, for example:

> Use Archify to map this project's React frontend, FastAPI backend, MySQL
> lookup, and disk-backed mapping sessions. Read backend/docs/CODE_FLOW.md and
> backend/docs/MAPPING_WORKFLOW.md and verify them against the source. Save the
> diagram JSON and HTML under tmp/archify-output.

For an existing architecture JSON file:

```powershell
.\archify.ps1 validate architecture .\tmp\archify-output\architecture.json --json
.\archify.ps1 deliver architecture .\tmp\archify-output\architecture.json .\tmp\archify-output\architecture.html --open --json
.\archify.ps1 preview architecture .\tmp\archify-output\architecture.json .\tmp\archify-output\architecture.html
```

Stop preview with Ctrl+C. Other diagram types include `workflow`, `sequence`,
`dataflow`, and `lifecycle`; consult `--help` for their current commands.
Generated files under `tmp/` are already ignored by Git.

To disable Archify's optional update check for the current terminal:

```powershell
$env:ARCHIFY_UPDATE_CHECK_DISABLED = '1'
```
