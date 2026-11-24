# KIUA2003 NAV Skills Dashboard

Which technical skills do employers mention in IT advertisements for Innlandet? This dashboard lets students, jobseekers and career advisers select a skill, see which advertisements mention it, and read the employer's wording. The shared starting dataset contains **13 advertisements**, including historical ones. Its counts describe this sample.

## 1. Open the dashboard

Use Python 3 (tested with Python 3.12). The dashboard and offline tests use Python's standard library. You can view the results and repeat the checks without an API key.

In PowerShell, download the project and start it:

```powershell
git clone --branch main https://github.com/AI-Rami/kiua2003-project.git
cd kiua2003-project
python harness/start.py
```

If you downloaded a ZIP from GitHub, extract it, open a terminal in the folder containing this README, and run just the last command. Open **http://127.0.0.1:8765/** in your browser. Select a skill to see its supporting advertisements and quotations. Press **Ctrl+C** in the terminal to stop the server.

On first startup the program copies the shared results and saved collection position from `shared/baseline/` into `out/`. Later starts keep your local updates. To check the saved data without opening the dashboard, run `python harness/start.py --check-only`. On a fresh download, expect **13 selected advertisements**.

## 2. Repeat the evaluation offline

Run the following commands from the same project folder. The evaluation uses **five fixed advertisements** with answers approved by the project team. It checks the saved model answers against those references. It also runs **five short synthetic cases** covering boundary conditions and an input the program should block.

```powershell
python eval/run.py --mode offline-suite --suite eval/cases/manifest.json
```

Open `out/evaluation/index.md` to find your new dated report. Each run has a readable `report.md` and a detailed `record.json`. In the recorded original run, all five real answers passed the format and quotation checks, and all five synthetic checks passed. The model still made interpretation mistakes, which are discussed in the reviewed reports below.

To reproduce the second prompt's results from its saved answers, run:

```powershell
python harness/check_revised_evaluation.py
```

Expect four answers to pass validation and one to be rejected. The check succeeds when it reproduces those recorded outcomes. For the case definitions, regression tests and optional paid evaluation with fresh model answers, see the [evaluation guide](eval/README.md).

## 3. Repeat the stress tests offline

```powershell
python harness/test_nav_stress.py
```

Expect **four tests** and **OK**. Two change the input (an empty description and an IT job outside Innlandet). Two simulate a service problem (a rate limit and an unusable reply). The tests check what the workflow skips, saves or publishes in each situation. Compare your result with the [stress-test report](docs/stress/2026-11-23/report.md), the [output before the repair](docs/stress/2026-11-23/before.txt) and the [output after the repair](docs/stress/2026-11-23/after.txt).

## 4. Read the reports

Start with the [evaluation report (Word)](docs/evaluation/NAV-evaluation-report.docx) for the method, scores and examples. The following records show exactly what was tested.

| Evaluation run | Extraction instructions | Results |
| --- | --- | --- |
| Original prompt, saved answers | [Prompt 1](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/prompt.txt) | [Generated report](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/report.md) · [Run record](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/record.json) · [Source review](docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md) |
| Revised prompt, fresh answers | [Prompt 2](docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/prompt.txt) | [Results and comparison](docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md) |
| Final prompt, fresh answers | [Prompt 3](docs/evaluation/2026-11-22_19-41-04_UTC-555f6602/prompt.txt) | [Results and comparison](docs/evaluation/2026-11-22_19-41-04_UTC-555f6602/reviewed-report.md) |

The five real advertisements also guided prompt revisions. Accuracy on unfamiliar advertisements remains an open question. The [safe-operation report](docs/safe-operation.md) explains permissions, costs, stop conditions and the tests behind those controls.

## Optional live update

Select **View cases** beside the update details to see saved failures and holds, their reasons and the affected advertisements. If a previous failure has used all allowed attempts, later updates identify it separately from new failures. Other eligible ads can still be processed.

Set your own OpenAI key in the `KIUA2003_API` environment variable **before starting the server**, then select **Run update**. This contacts NAV and may incur model charges. Keep credentials out of Git.

The program resumes the saved NAV feed position and checks new or changed advertisements for active IT jobs listing Innlandet. It screens contact details, sends eligible text to the model and checks the returned structure and quotations. It reuses unchanged results and refreshes statistics from selected results. A skill counts once per distinct advertisement in the total. Alternatives such as “Python or R” appear together. Automatic contact screening and quotation checks have limits, which the safe-operation and evaluation reports describe.

## Project map

| Location | What you will find |
| --- | --- |
| [harness/](harness/) and [ui/](ui/) | Python workflow, extraction prompt and dashboard interface |
| [shared/baseline/](shared/baseline/), [reviews/](reviews/) and [fixtures/](fixtures/) | Starting data and checkpoint, provisional review decisions and saved examples |
| [eval/](eval/) and [tasks/](tasks/) | Fixed evaluation cases, checker and development task briefs |
| [SPEC.md](SPEC.md) and [AGENTS.md](AGENTS.md) | Product scope and instructions for coding agents |
| [Meeting reports](docs/meetings/) and [prompt log](docs/prompt-log.md) | Project decisions and development history |
| [Archived weather exercise](history/met-weather/) and [earlier output-layout documents](docs/history/) | Earlier course work and records of how the local data was reorganized |
