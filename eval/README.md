# NAV evaluation

The evaluator uses five fixed development cases from the shared baseline. To run the complete **offline exam test set** from the project root, use:

```powershell
python eval/run.py --mode offline-suite --suite eval/cases/manifest.json
```

This command needs no API key and makes no NAV or model requests. It replays the five saved real-advertisement responses against approved reference answers, then runs five named synthetic cases: OR grouping, heading context, duty versus qualification, quotation boundaries, and an input the cleaning/gate workflow must reject. The synthetic rejection passes only if it is held before a model call and no result is published. The case roles, fixed inputs and expected outcomes are in `cases/offline-suite.json`, whose hash is pinned by `cases/manifest.json`. Two real cases show common wording patterns; three exercise difficult boundaries. They are development examples, not a representative market sample.

The command writes one dated run folder under ignored `out/evaluation/` with `report.md` and `record.json`. The report begins with the run time, test type, prompt hash, completion and overall quantitative score; it then gives each tested advertisement its own readable section with per-ad numbers and automatic name/group differences. Synthetic pass/fail results are separate. `out/evaluation/index.md` links the reports for runs that still exist; deleting an old run removes it from the index on the next run. A low extraction score remains a reported finding; a failed mechanical or rejection check makes the command exit with a failure code. The saved dashboard selection and statistics remain unchanged. To run just the five-ad replay or the evaluator's local regression tests, use:

Markdown is the reproducible human-readable format. A Word copy is not generated yet; it would need to be built from the same record and visually checked before being offered as a report.

```powershell
python eval/run.py --mode replay --suite eval/cases/manifest.json
python eval/test_evaluation.py
```

Replay checks file hashes, saved request settings, output structure and literal supporting quotations. It needs no API key, makes no network requests, and does not alter application statistics. Each invocation writes a separate report and machine-readable record under ignored `out/evaluation/`.

All five fixed cases have complete v2 references in `references/development-v2-approved.json`. Rami agreed to their full answers and reported Yehya's concurrence. The other eight historical labels remain drafts. The case manifest pins the references, fixed UUIDs, baseline hash, original prompt, schema and model settings. Synthetic scorer checks are separate from real-advertisement accuracy.

## Bounded fresh model evaluation

When you choose to make five paid requests, set your own `KIUA2003_API` environment variable and verify [current Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna). The standard prices verified on 22 November 2026 were $0.10 per million input tokens and $0.50 per million output tokens. If prices change, update the cost constants and checks before running. With the current revised prompt (SHA-256 `efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1`), the command is:

```powershell
python eval/run.py --mode model --suite eval/cases/manifest.json --max-requests 5 --max-seconds 900 --max-cost-usd 0.05 --prompt-sha256 efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1
```

The explicit hash prevents an unnoticed prompt change. The frozen baseline remains pinned to the earlier prompt SHA-256 `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`; its saved results and score are unchanged. For a later prompt version, replace the hash argument with the verified SHA-256 of the new prompt file; the run records both that hash and the frozen baseline hash. The five inputs and references remain pinned, and references are never sent to the model. Schema, model (`gpt-6-luna`), medium reasoning and the 8,192-token output cap must still match the suite. The command checks all five cases and the full cost estimate before reading the key or sending a request. It uses a 60-second request timeout and no automatic retries. The estimate uses request bytes plus a 4,096-token framing allowance per case as an input-token proxy and the entire output cap, including reasoning tokens; it is a planning estimate, not a billing guarantee. The command stops after an API or network error, preserves completed records and marks remaining cases not run. A validation failure is saved and the next case is tested.

Each model run creates a unique ignored `out/evaluation/` folder with per-case request payloads (no credentials), raw JSON responses, validation and scoring records, token usage and time. Its single dated report covers all selected advertisements, including failures and cases not run, and it does not claim synthetic checks ran. The run appears in `out/evaluation/index.md`. The command does not change dashboard results or statistics. One bounded live model evaluation on 22 November 2026 attempted all five cases once, validated four and failed one. Its [reviewed comparison](../docs/evaluation/2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md) includes the failure and compares only the four cases scored in both runs.

Use `labeling-rules-v2.md` as the human review guide, `cases/review-index.md` to locate each frozen prepared input, and `reference-format.md` for the reference structure. The five approved answers use those exact input versions and are scored by the deterministic one-to-one matcher. Draft answers never enter the score. In a local offline replay on 22 November 2026, all five saved outputs passed structural and quotation validation; five approved cases were scored. Exact item-name/group matching found 47 matches among 83 model items and 90 reference items (precision 0.566, recall 0.522, F1 0.543). Five matched items had classification errors. The [reviewed baseline report](../docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md) explains all five comparisons and the [fifth-case baseline comparison](cases/ad5-baseline-comparison.md) records the OR-group error in more detail. These are development-set replay results, not accuracy on unseen ads; quotation validation and exact-name metrics do not establish semantic correctness of all results.

Yehya's original scorer, CSV labels, labeling rules and three saved result files are together in `history/first-attempt/`. Their contents were preserved during the move. The paths printed inside the historical files refer to their original locations; see `history/first-attempt/README.md`. The first labels were drafted with Claude and later checked by a group member. That earlier check does not establish complete, jointly approved reference answers.
