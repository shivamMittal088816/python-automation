# Project diagrams

Each diagram type has its own editable `specs/` and generated `output/` folders.
Folder names match Archify's diagram-type arguments.

```text
diagrams/
├── architecture/
│   ├── README.md
│   ├── specs/
│   │   └── architecture.json
│   └── output/
│       ├── architecture.html
│       └── architecture.visual-check.*
├── workflow/
│   ├── specs/
│   └── output/
├── sequence/
│   ├── specs/
│   └── output/
├── dataflow/
│   ├── specs/
│   └── output/
└── lifecycle/
    ├── specs/
    └── output/
```

Open the [current architecture diagram](architecture/output/architecture.html).
Its [source references and regeneration instructions](architecture/README.md)
are alongside it. Open the [current student mapping workflow](workflow/output/workflow.html)
and see its [regeneration instructions](workflow/README.md). The remaining type
folders are ready for future diagrams; their `.gitkeep` files preserve the empty
folders in Git. Open the [student mapping data-flow diagram](dataflow/output/dataflow.html)
and see its [evidence and regeneration instructions](dataflow/README.md).

Use descriptive matching filenames, such as `workflow/specs/student-mapping.json`
and `workflow/output/student-mapping.html`. Multiple diagrams can share a type
folder. Edit JSON sources, validate, then generate HTML with `deliver`; do not
manually edit generated HTML. Keep screenshots and validation receipts with the
corresponding output. Generation remains a development/build step.

For example, after creating a workflow specification, run from the project root:

```powershell
.\archify.ps1 validate workflow diagrams/workflow/specs/student-mapping.json --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Diagram validation failed' }
.\archify.ps1 deliver workflow diagrams/workflow/specs/student-mapping.json diagrams/workflow/output/student-mapping.html --quality showcase --json
if ($LASTEXITCODE -ne 0) { throw 'Diagram delivery failed' }
```

View the existing architecture diagram:

```powershell
Start-Process .\diagrams\architecture\output\architecture.html
```
