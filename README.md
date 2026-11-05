# KIUA2003 NAV Skills Dashboard

Analyses technical skills in NAV IT advertisements for Innlandet.
For students, jobseekers and career advisers.

## Start

Requires Python 3. Run from the project root:

```powershell
git clone --branch work/nav-skeleton https://github.com/AI-Rami/kiua2003-project.git
cd kiua2003-project
python harness/start.py
```

Open http://127.0.0.1:8765/. Stop with Ctrl+C.

Startup restores the shared snapshot of 13 advertisements into
`out/`. Viewing saved results needs no API key or additional packages.

## Check saved data

```powershell
python harness/start.py --check-only
```

This checks the shared data and restoration, not extraction accuracy.

## Update

Provide your own OpenAI key through the `KIUA2003_API` environment
variable before starting the server, then click **Run update**.
Updates require internet access and may incur API costs.
Never commit credentials.

## Project files

- `harness/`: Python workflow and extraction prompts.
- `ui/`: dashboard interface.
- `shared/baseline/`: shared results and collection checkpoint.
- `out/`: generated local data; Git-ignored.
- `reviews/`: provisional corrections to displayed results.
- `fixtures/`: saved inputs.
- `tasks/`: development task briefs.
- `docs/`: documentation, meeting reports and prompt log.
- `eval/`: earlier MET weather checker; not a NAV evaluation harness.

See [SPEC.md](SPEC.md) for scope and [AGENTS.md](AGENTS.md)
for coding-agent instructions.

## Limitations

Results cover a small selected dataset, including historical
advertisements. Counts do not represent current vacancies or the
complete regional IT market. Extraction accuracy remains under
evaluation, and automatic contact cleaning cannot guarantee
removal of all personal information.