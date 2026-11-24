# Compulsory 2 output cleanup manifest (2026-11-02)

**Historical snapshot:** A subsequent [Comp2 output migration](comp2-output-migration.md) moved development runs and summaries to `archive/comp2-generated-2026-11-02/` and made `out/current/index.json` the statistics selection. The paths below describe the earlier cleanup stage, not the present output layout.

This manifest records the cleanup decision for the current checkout. Paths are relative to the repository root. It describes the intended incremental workflow; it does not claim that the application pipeline or web UI exists. The source advertisement text and any contact details are excluded from this manifest.

## Intended next workflow

After Compulsory 2, poll the saved NAV feed end using the supported `nav_discover.py --mode poll --db ...` continuation. Reconcile events by NAV UUID and saved version before deciding which details or extractions need work. Reuse retained results for unchanged content. Process changed or new relevant ads, validate outputs, then update statistics and the UI from a single explicit set of accepted results. Persist collection and processing status after each stage. A no-change poll should succeed without removing the prior statistics or UI. Blocked and failed ads must remain separate from accepted results; changed versions of one UUID must not create a second advertisement count. These integration steps are planned, not implemented.

## Retain in active locations

| Path | Decision | Purpose and dependency |
| --- | --- | --- |
| `harness/`, `fixtures/`, `tasks/`, `eval/`, `docs/`, `SPEC.md`, `README.md`, configuration and dependency files | Keep | Source code, prompts, schema, tests, course and project history. The MET exercise and its evidence are course work. This cleanup does not edit `eval/` or historical logs. |
| `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3` and `summary.json` | Keep, active collection state | The SQLite database contains feed events, UUID reconciliation, detail metadata, capture versions, statuses and saved feed continuation. The summary reports the last observed feed end. The supported continuation is `--mode poll` with this database; `--mode resume` continues unfinished work. This is not yet a processing or statistics checkpoint. |
| `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.v0-backup-b11f7e8d.sqlite3` and `state.target-review-backup-51b26810.sqlite3` | Keep | Unique database backups from earlier migration and targeted review; neither is a substitute for current continuation state. |
| `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/exports/2026-11-01_13-06-52_UTC-c372f60d/` | Keep, uncertain | Earlier edited captures for 167 UUIDs, including remote-review candidates. The database holds capture data, but these export files are existing usable inputs and their later dependencies have not been fully established. Do not assume remote eligibility. |
| `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/review_exports/2026-11-01_14-02-32_UTC-e1de2335/` | Keep in place | The latest 11-record targeted review export supplies the saved cleaned inputs used by extraction. One record, UUID `8119dbb1-530f-4307-9ee0-e030c2b8e581`, remains blocked for an unresolved cleaning/personal-data issue. It was not copied or moved during cleanup. The other captures remain pending human personal-data review. |
| `out/nav_runs/batches/2026-11-01_16-23-41_UTC-721bdf71/index.md` and `out/nav_runs/batches/2026-11-01_16-02-57_UTC-de980ae1/index.md` | Keep, evidence | The original ten-ad index drives the current offline summary and the frozen evaluation; it is not an authoritative application dataset. The earlier index is linked from it and records the initial failures. The old blocked-ad extraction must not be treated as a current accepted result. |
| `out/nav_evaluations/2026-11-01_22-17-11_UTC-ec0042de/` and all nine linked `out/nav_runs/<run-id>/` directories | Keep, evaluation evidence | Frozen prompt index, per-ad meaning review, progress and linked runs. Eight runs were new; the Azure run was reused. All nine validated structurally, while some had meaning errors. Each retained run keeps prepared input, credential-free request, original response, validation, result and report. The blocked capture has no frozen-prompt run. |
| Other `out/nav_runs/<run-id>/` directories | Keep, uncertain or report evidence | Earlier requests include distinct prompt versions, failed responses and iterative improvements cited by the prompt log. None was verified as an exact disposable duplicate. Preserve their complete run artifacts for Compulsory 2 reporting and later evaluation. |
| `out/nav_skill_reviews/2026-11-01_20-50-23_UTC-41a167b3/` | Keep, review evidence | Correction manifest and source-based progress record used by the corrected small-sample summary. No saved model output is rewritten. |
| `out/nav_skill_summaries/2026-11-01_20-39-06_UTC-2e12a67b/` | Keep, baseline evidence | Initial mechanical ten-ad summary; needed to investigate the postponed table and interpretation issue. |
| `out/nav_skill_summaries/2026-11-01_20-58-59_UTC-6774e647/` | Keep, corrected baseline | Later corrected small-sample summary with working links. It is not the application's live statistics and still includes the ten-ad development set, including a now-blocked capture. |
| `out/probe.json` | Keep | Output of the earlier MET course exercise; its checker expects this path. |

## Archived redundant output

| Original path | Archive path | Reason |
| --- | --- | --- |
| `out/nav_skill_summaries/2026-11-01_20-58-06_UTC-a5e3f230/` | `out/archive/comp2-cleanup-2026-11-02/nav_skill_summaries/2026-11-01_20-58-06_UTC-a5e3f230/` | Intermediate corrected summary. Its advertisement list and all counted sections match the later `20-58-59` summary; only generation time and slash style in the review path differ. The later Markdown corrects that path style. No repository or retained-output Markdown link points to this intermediate folder. The archived files remain available as run evidence outside the summary output directory scanned by the summary workflow. |

No generated run or capture was archived on age alone. No unique prompt-log or meeting evidence was removed. There is no verified exact duplicate run folder to remove.

## Gaps and verification boundary

- There is no authoritative working extraction dataset or per-UUID accepted-version pointer. The offline summary selects the ten **v1** results in its explicit batch index; the frozen evaluation selects nine **v2** runs and blocks one capture. Do not combine these indexes or choose the newest folder by timestamp.
- The current discovery command can poll its saved feed end, but it does not automatically reuse old extraction results, process changed captures through the model, maintain an application processing checkpoint, or refresh statistics.
- No web UI source or UI data was found in the checkout. Weekly, monthly and yearly statistics and a no-update UI path remain planned.
- Earlier corrected and mechanical summaries remain investigation evidence, not publishable statistics. Human personal-data review and the blocked capture's handling remain unresolved.
- Before archival, the SQLite `quick_check` returned `ok`; the two corrected summaries had equal advertisement and counted-skill sections; 90 local Markdown links across then-active indexes, reviews, summaries and README resolved. After moving, the three archived files matched their original SHA-256 hashes, their former active folder was absent, and the archive was outside `out/nav_skill_summaries/`. All 81 local Markdown links across retained indexes, reviews, summaries, README and this manifest resolved. Each of the nine frozen-prompt linked runs retained its prepared input, request, response, validation, result and report. The current database again passed `quick_check`; the blocked review-export file remained in place.
