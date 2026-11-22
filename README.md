#KIUA2003 NAV Skills Dashboard

This project helps students, jobseekers and career advisers explore
technical skills mentioned in selected NAV IT advertisements listing
Innlandet. The dashboard shows how many advertisements mention each
skill and links the counts to saved quotations and source advertisements.

## How it works

When **Run update** starts, Python resumes the saved NAV feed position
and checks new or changed advertisements. It processes new details that
are active, list Innlandet as a work location and have an IT occupation
category. It converts their descriptions to text and screens contact
details before sending eligible text to the extraction model. Python
checks the model's JSON and supporting quotations before publishing a
result. Unchanged advertisements reuse their saved results. Python
counts distinct advertisements per skill, and the dashboard displays
the counts, classifications and evidence. Previously saved results
remain available when an advertisement later becomes inactive.

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

## Evaluate the saved workflow

Run from the project root without an API key:

```powershell
python eval/run.py --mode offline-suite --suite eval/cases/manifest.json
```

The offline suite replays five fixed development advertisements against approved answers and checks five synthetic boundaries, including a contact-uncertain input that must be blocked before a model call. Each run creates one dated, readable `out/evaluation/<run>/report.md` covering all five ads and the separate synthetic results. Open `out/evaluation/index.md` to find current reports by run date; `record.json` holds the detailed numbers. It needs no API key or network access and does not change dashboard statistics. The five ads do not measure accuracy on unseen advertisements. See [eval/README.md](eval/README.md) for the case catalog, replay-only command and local regression tests, [task 005](tasks/005-nav-evaluation.md) for the evaluation scope and [task 006](tasks/006-evaluation-reporting.md) for reporting. The earlier scorer and saved scores are retained as provisional history.

The [reviewed five-ad baseline report](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md), its [original generated report](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/report.md), and its [run record](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/record.json) are shared under `docs/`. Later generated runs remain local under ignored `out/` until a checked report is deliberately shared.

For a bounded fresh-model evaluation, see the exact command, pricing preflight and prompt-hash requirement in [eval/README.md](eval/README.md). This mode needs your own `KIUA2003_API` key and has only been tested locally with mocked responses; it does not update the dashboard dataset.

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
- `eval/`: MET weather checker, historical NAV evaluation attempt, and fixed-case NAV replay/model evaluator.

See [SPEC.md](SPEC.md) for scope and [AGENTS.md](AGENTS.md)
for coding-agent instructions.

## Limitations

Results cover a small selected dataset, including historical
advertisements. Counts do not represent current vacancies or the
complete regional IT market. Extraction accuracy remains under
evaluation, and automatic contact cleaning cannot guarantee
removal of all personal information.
