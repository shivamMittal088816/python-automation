# Student mapping workflow diagram

The editable Archify source is [`specs/workflow.json`](specs/workflow.json).
The generated, self-contained interactive diagram is
[`output/workflow.html`](output/workflow.html).

The workflow documents workspace restoration, input preparation, the three
independent mapping stages, validation/retry behavior, saved result groups,
optional forwarding of unmatched rows, previews, and downloads.

Regenerate and verify it from the repository root:

```powershell
.\archify.ps1 validate workflow diagrams/workflow/specs/workflow.json --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Workflow validation failed' }

.\archify.ps1 deliver workflow diagrams/workflow/specs/workflow.json diagrams/workflow/output/workflow.html --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Workflow delivery failed' }

.\archify.ps1 visual-check diagrams/workflow/output/workflow.html --json
if ($LASTEXITCODE -ne 0) { throw 'Workflow visual check failed' }
```

Edit the JSON source and regenerate the HTML; do not edit generated HTML or
visual-check artifacts manually.
