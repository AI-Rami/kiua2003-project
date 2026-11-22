# Task 006: Human-readable NAV evaluation reports

## Goal and status

**Markdown and JSON reporting implemented and locally verified on 22 November 2026.** Optional Word export remains unimplemented because it has not passed the required document-rendering review. Keep one readable report for each evaluation run, covering all real advertisements tested in that run. Give each advertisement its own short section. Report synthetic boundary and rejection checks separately. Make runs easy to find by date and test type. Preserve the machine-readable record and all earlier runs.

## Context and dependencies

- `eval/run.py` implements frozen replay, the offline suite and a bounded fresh-model mode. All three already create unique folders under ignored `out/evaluation/`.
- `eval/cases/manifest.json` pins five approved development cases. `eval/cases/offline-suite.json` names five synthetic checks. `eval/scoring.py` compares exact item or complete OR-group names; wording differences can cause unmatched items without proving semantic errors.
- The offline suite validates five saved responses and passes five synthetic checks. The generated report gives quantitative results and automatic differences; the [separate reviewed report](../docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md) explains their meaning against the source. Fresh-model mode has only been exercised with mocks.
- Keep Task 005's approved references, saved responses, prompt, schema, model settings and counting rules unchanged. Preserve unrelated work and existing run folders.

## Report design

For each new run, write one `report.md` and one `record.json` in its unique dated run folder. Put the generation date and time, with the time zone, at the top of the report. State the test type, prompt hash, model, selected/attempted/validated/failed/not-run counts and whether the run is complete or partial.

Lead with a plain-English explanation of the overall quantitative results. Show matched model items, total model items, total approved reference items, precision, recall and F1 with short definitions and explicit denominators. Explain that passing format and quotation checks does not mean the skill interpretation is correct. Identify development-set and exact-name matching limitations.

Give each real advertisement a short section in the same report. Show its UUID and available title without inventing one; structure/quotation outcome; matched, unmatched-model and unmatched-reference item counts; precision, recall and F1 where applicable; classification, mention-type and OR-group differences; and a short list of actual unmatched item names. Label those lists as automatic comparison differences, not confirmed semantic mistakes. For incomplete or failed cases, show what was attempted and why the result was not scored. Do not turn an automatically detected difference into a human-reviewed conclusion.

For an offline-suite report, add separate sections for the named synthetic boundary and rejection cases. State each case's expected outcome, observed outcome and pass/fail result in ordinary language. Synthetic outcomes never enter real-advertisement accuracy. For a fresh-model report, show actual request status, token usage and estimated cost; do not imply that synthetic checks ran when they did not. A later prompt comparison can link two dated reports and discuss improvements and regressions without altering either run's evidence.

Maintain `out/evaluation/index.md` as a readable directory of runs. List each run's local date/time, mode, prompt version, completion, real-ad score availability and link to its report. Update it after each run without rewriting older run artifacts. A failed or partial model run must still have a report and an index entry. Do not scan archived runs or application statistics.

A Word copy is desirable for sharing with the teacher. It must be generated from the same structured results as Markdown so the two formats cannot disagree, require no new project dependency, and pass visual review before it is offered as a deliverable. Markdown and JSON remain the required, reproducible formats if Word generation cannot meet that gate.

## Acceptance checks

- A new offline-suite run produces one dated report with all five real advertisements and all five synthetic checks, plus one `record.json` and an updated index. The report's overall and per-ad numbers match the record. Existing reports remain unchanged.
- A mocked fresh-model run produces one report covering all selected ads, including failed and not-run cases. It shows usage and estimated cost and does not claim synthetic checks were run.
- Repeated runs create distinct folders and separate index entries. An interrupted or failed run stays visible. Index links resolve.
- Model-free tests cover per-ad metrics, plain-English status for failed/partial runs, date/time formatting, index update, unchanged older reports and separation of synthetic checks from real-ad accuracy.
- Run syntax checks, the evaluation regression suite and `git diff --check`. Verify that the selected dashboard index and statistics are unchanged. Make no NAV or paid model requests for this task.

## Out of scope

Do not change extraction prompts, schema, approved references, scorer matching rules, dashboard statistics or collection. Do not regenerate old run responses, treat exact-name mismatches as confirmed semantic errors, commit or push.
