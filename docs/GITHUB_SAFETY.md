# Publishing this repository safely

## What belongs in Git

Commit application source (`frontend/src/`, `Backend/`, and `Backend/scripts/`), tests,
synthetic test fixtures, documentation, `.gitignore`, `.env.example`,
`frontend/.env.example`, `pyproject.toml`, `uv.lock`, and frontend package/lock files.

Real credentials belong only in local `.env` files or your deployment's secret
configuration. Frontend `VITE_*` values are browser-visible: never put database
passwords, private API keys, or other secrets there.

The ignore rules exclude real environment files, Python environments, dependencies,
build output, test artifacts, logs, runtime storage, CSV/spreadsheet/SQL dumps,
database files, and common private-key files. The CSV exception is intentionally
limited to the two reviewed files `frontend/e2e/fixtures/dump.csv` and
`frontend/e2e/fixtures/school.csv`; other CSV files remain ignored.

Temporary directories, nested storage/log directories, archives, local tool
settings, binary snapshots, Word/PDF exports and additional data-export formats
are also ignored. Keep Markdown documentation in Git; the generated DOCX remains
available locally to send separately. Review any new images or JSON files before
adding them, since source assets and configuration can legitimately use those formats.

Database configuration already reads `DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD` and `DB_NAME` from the backend environment or the root `.env`.
Keep actual values there and placeholders in `.env.example`. Database URL creation
uses SQLAlchemy `URL.create`, so special characters in passwords are preserved
without embedding them in a manually constructed URL string.

The publication preparation checked ignore behavior for 14 representative private
and public paths using an isolated Git index, since this workspace has no root
`.git` directory. Three startup tests passed. A scan of the 172 publishable files
found no checked credential-token patterns. The local `DB_PASSWORD` value was
empty, so there was no current nonempty password to compare against those files.
Configure a nonempty database password through the database administrator and
store it in the ignored `.env`; merely editing `.env` does not change the database
account's password. This is a limited working-tree check, not a complete secret
or history audit.

## Previous repository history

The old local `.git` directory has been removed at your request. A newly initialized
repository here will not inherit that history. The earlier audit report records
`.env` in commit `31aab2c` and storage/log content in commit `6b313f8`. Those commits
are not available in this workspace for reinspection. A committed `.env` alone
does not establish which nonempty credentials it contained or whether they remain
active. Removing these paths from the current Git index and
adding ignore rules does **not** remove previous committed copies. Pushing a branch
also sends its reachable history.

Before making this repository public:

1. Identify the database account and any other active credentials present in the
   previously committed `.env`, using a private copy of that history or the account
   owner's records. Rotate any exposed credentials at their issuing service, then
   update each dependent application's private environment. Do not paste the old
   or new values into documentation, chat, shell command arguments or Git.
2. Have the repository owner remove private configuration, student records, and
   logs from all affected history, or publish a reviewed clean source snapshot in
   a new repository with no inherited history.
3. Coordinate any history rewrite with collaborators. It changes commit IDs and
   can require a force push; it is not performed by this working-tree cleanup.
4. If those commits were already shared, history cleanup cannot revoke existing
   copies. Any exposed active credentials still need rotation.

### Current rotation status

Rotation has not been performed. The current root `.env` targets a local database
and has an empty `DB_PASSWORD`; it does not identify a previously exposed remote
account or password. Before changing a database account, identify the affected
server/account and dependent applications. Changing an unrelated local password
does not revoke an old remote credential. After the correct account is changed,
update the private environment, verify that the application connects with the new
credential, and verify that the old credential no longer authenticates.

## Check the next commit

After you initialize the new repository, run from its root:

```powershell
git status --short
git diff --cached --name-status
git ls-files -ci --exclude-standard
git check-ignore .env frontend/.env storage/example.csv mapping.log
```

`git ls-files -ci --exclude-standard` should print nothing: otherwise some ignored
files are still tracked. Staged deletions of old private files are expected after
untracking them. Their local working copies can remain on disk.

Inspect the staged diff locally before committing. Do not paste credentials or
student records into public issues or logs. Do not use `git add -f` to bypass these
rules for private files.

These checks reduce accidental publication risk; they are not a guarantee that
arbitrary new files or historical commits contain no sensitive information.
