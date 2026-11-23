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

Read the exact extraction instructions used in each test:

- [Version 1 — prompt used to produce the answers replayed in the first test](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/prompt.txt)
- [Version 2 — prompt sent in the second test](docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/prompt.txt)
- [Version 3 — final prompt, with education and single-skill checks](docs/evaluation/2026-11-22_19-41-04_UTC-555f6602/prompt.txt)

The [final test review](docs/evaluation/2026-11-22_19-41-04_UTC-555f6602/reviewed-report.md) covers all five outcomes and compares the three ads validated in both fresh runs.

The application reads its [current extraction prompt](harness/prompts/extract_skills.txt).

To reproduce the **second test** from the five saved revised-prompt answers, run

```powershell
python harness/check_revised_evaluation.py
```

This offline check needs only Python. It validates the original answer text, compares each outcome and score with the saved record, and exits successfully when it reproduces all five outcomes. Expect four validated ads, one rejected answer (item 8), and 50 matches among 84 model items and 80 reference items. The [reviewed comparison](docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md) explains these results. The screened answers are included beside the report in `answers.json`.

To reproduce the **first test** and its synthetic checks, run from the project root:

```powershell
python eval/run.py --mode offline-suite --suite eval/cases/manifest.json
```

The offline suite replays five fixed development advertisements against approved answers and checks five synthetic boundaries, including a contact-uncertain input that must be blocked before a model call. Each run creates one dated, readable `out/evaluation/<run>/report.md` covering all five ads and the separate synthetic results. Open `out/evaluation/index.md` to find current reports by run date; `record.json` holds the detailed numbers. It needs no API key or network access and does not change dashboard statistics. The five ads do not measure accuracy on unseen advertisements. See [eval/README.md](eval/README.md) for the case catalog, replay-only command and local regression tests, [task 005](tasks/005-nav-evaluation.md) for the evaluation scope and [task 006](tasks/006-evaluation-reporting.md) for reporting. The earlier scorer and saved scores are retained as provisional history.

The [reviewed five-ad baseline report](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md), its [original generated report](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/report.md), and its [run record](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/record.json) are shared under `docs/`. The [revised-prompt reviewed report and four-ad comparison](docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md) records a fresh five-request run with four validated responses and one validation failure; its generated report and run record are copied beside it. Raw responses remain local under ignored `out/`.

For a bounded fresh-model evaluation, see the exact command, pricing preflight and prompt-hash requirement in [eval/README.md](eval/README.md). This mode needs your own `KIUA2003_API` key. It was exercised with five live model requests on 22 November 2026 and does not update the dashboard dataset.

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
