# Task 005: Repeatable NAV skill-extraction evaluation

## Status and goal

**Offline baseline and qualitative review complete; fresh model mode locally tested only.** Fixed-case offline replay, a single-command offline suite with named synthetic boundary and rejection checks, deterministic approved-reference scoring and a bounded fresh-model command are implemented. The model command has only been tested with mocked responses; no paid evaluation run has been made. Five complete reference answers were selected and scored in an offline replay on 22 November 2026. The [reviewed baseline report](../docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md) explains all five saved model/reference comparisons. The fifth case is retained as a baseline improvement example because the saved extraction missed its required three-way OR group. This is a repeatable evaluation of development cases and may report poor extraction accuracy; it does not establish accuracy on unseen advertisements.

## Existing work and dependencies

- Commit `22da659` added `eval/gold/gold.csv`, `eval/labeling-rules.md`, `eval/score.py` and saved scores. Preserve that first attempt and its factual results. Its scorer reads the changing `out/current/` selection, flattens alternative groups and uses word-overlap matching. Its saved scores are provisional, not approved accuracy measurements.
- The six original first-attempt files were later moved without content changes to `eval/history/first-attempt/`; the original paths above describe commit `22da659`.
- The CSV has 175 rows for 13 advertisements: five advertisements have `checked=yes` throughout and eight have `checked=no`. `checked=yes` records earlier review; it is not new approval by Rami and Yehya. Do not score drafts as approved references.
- Reuse the existing v2 extraction prompt, strict schema, response validator, quotation checker, contact cleaner and update input gate where applicable. Keep the earlier MET weather checker separate.
- `shared/baseline/` supplies a fresh checkout with selected runs and a NAV checkpoint. The baseline manifest's review hash matches this Windows CRLF checkout but not the LF bytes stored by Git for `reviews/current-v2.json`. Fix cross-platform restoration without weakening content verification. Any change to the shared package requires the audit and fresh-checkout checks in `AGENTS.md`.
- Keep `docs/meetings/meeting-06.md` and all unrelated work unchanged. No new NAV collection is required for this task.

## Work sequence

### 1. Preserve the first attempt

Keep commit `22da659` and preserve the first scorer, reference draft, labeling rules and reports as clearly labeled historical evidence, with their original results and limitations. Use one clearly named current evaluator under `eval/`; do not leave two competing active commands. Put new run artifacts in unique directories so replay and model runs never overwrite previous results or the first attempt. Do not archive or publish any unscreened personal data or credentials.

### 2. Fix fresh-checkout startup

Make review and baseline integrity checks independent of platform line endings while still detecting a substantive content change. Test a fresh Git checkout with LF and a Windows checkout with CRLF. On each, `python harness/start.py --check-only` must restore and validate the same 13-advertisement snapshot without network or model calls. Confirm that an already updated local `out/` is not overwritten. Report the actual checkout environments tested; do not claim an untested platform.

### 3. Approve reference answers (human decision gate)

Rami and Yehya recheck all five previously checked advertisements against their complete **prepared, cleaned text**, confirming both included and omitted technical mentions. Resolve classifications, mention types, example technologies, supporting passages, and alternatives. In particular, decide how broad Azure competence and named services are labelled; whether a combined name such as `C# .NET` is one skill or two; and how `Unity or another game engine` is represented. Record reviewer decisions, unresolved items and approval status without inventing approval. **Exclude an entire advertisement from the approved accuracy score if its reference answer is incomplete or any relevant decision remains unresolved.** Excluding only the disputed item could wrongly penalize a model for extracting it. State which advertisements are approved and the resulting denominator. The eight draft advertisements remain draft until separately reviewed.

Use a versioned reference format with full advertisement UUID, frozen input hash, item relationship (`single` or `any_of`), skill names, classification, mention type, supporting quotation and optional separate classification-context quotation. A quotation must be a continuous passage in the prepared input. Reference answers must never be supplied to the extraction model.

### 4. Freeze cases and add synthetic tests

Create a fixed manifest naming exact full UUIDs, reviewed reference version, sanitized prepared-input files, saved request and original response files, and their hashes. Record prompt, v2 schema, model/settings and preparation or cleaning versions. Verify all paths and hashes before scoring. Do not select whichever run or advertisement version happens to be current. Keep saved model responses for offline replay; a fresh model evaluation must create new responses.

Include representative real cases and clearly identified synthetic boundary cases for OR alternatives, broad requirements with examples, duties versus applicant qualifications, and quotation whitespace. Include at least one synthetic case the workflow is expected to reject. **Report synthetic scoring, validation and rejection checks separately from real-advertisement accuracy.** The manifest must explicitly list the approved real advertisement UUIDs selected for a fresh model run; do not select cases by directory order or silently stop before the listed set is attempted. Screen any shared case files for contacts and credentials; keep blocked or uncertain real captures out of model requests.

For the exam test-set requirement, add a small case catalog with stable case IDs, input or frozen-artifact references, expected outcomes, and a reason for each case's role. Inspect the five real inputs before identifying at least one as a typical example and at least one as a boundary example; do not claim the five advertisements represent the wider market. Keep synthetic boundary and rejection cases explicitly separate from the five real cases and their approved accuracy denominator. An expected rejection is a passing test when the workflow blocks it for the documented reason.

### 5. Make scoring deterministic and checkable

Define an **item** as the primary scoring unit: a `single` item has one skill; an `any_of` item is one unordered group containing at least two explicit alternatives. The group matches only when its complete alternative set and relationship match. Do not score its members as independent mandatory requirements. Compare item order independently.

Match reference and model items one-to-one using exact normalized names or explicitly approved, versioned aliases. Decide the combined-name cases during human review; do not use unrestricted word overlap, fuzzy matching or an LLM judge. An item may count once only. Report skill/group detection separately from classification and mention-type agreement. Check schema, allowed fields, the current validator's literal quotation matching, empty evidence, source/link safety and validation failure separately. Test whitespace changes as a boundary case without changing the extractor during baseline measurement. A quotation match does not establish correct meaning or heading scope.

Produce per-case true positives, unsupported model items, omissions, classification errors, mention-type errors, OR-group errors and validator failures. Calculate precision, recall and F1 with explicit denominators; use `not applicable` when a denominator is zero. Report both numbers and reviewed qualitative examples. Do not call every model item absent from an incomplete reference a confirmed false positive.

### 6. Exercise the input gate and rejection behavior

Run synthetic raw advertisement content through cleaning, capture preparation and the update input gate with mocked NAV and model clients. One safely cleaned case may continue. A case with residual contact data or unresolved cleaning must be blocked with a reason, **zero model calls and zero newly published results**. Extend the existing `harness/test_nav_update.py` cases rather than counting a direct validator rejection as the only workflow rejection. Also test fabricated or empty quotations as separate validator failures.

### 7. Provide replay and fresh-model commands

Proposed interfaces, to finalize in implementation and document in `eval/README.md` and root `README.md`:

```text
python eval/run.py --mode replay --suite eval/cases/manifest.json
python eval/run.py --mode offline-suite --suite eval/cases/manifest.json
python eval/run.py --mode model --suite eval/cases/manifest.json --max-requests 5 --max-seconds 900 --max-cost-usd 0.05 --prompt-sha256 789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b
```

Replay must make no NAV/model requests, need no API key and leave application `out/current/` and statistics unchanged. It rechecks frozen original responses with the current validation code and scores them against approved references. Model mode uses the **same explicitly selected real-advertisement inputs** with the recorded current prompt, schema, model and settings; makes at most one request per eligible case with no automatic retries; and never sends expected answers. Synthetic checks run separately without paid requests. Require `--max-requests` to cover every selected real advertisement before starting; otherwise fail preflight rather than silently leaving cases untested. Require the user's own `KIUA2003_API` key only for model mode. Before a paid run, verify current pricing and refuse a run whose conservative maximum estimate exceeds the configured budget, including reasoning output tokens. Bound input size, output tokens, request time and total requests. Stop safely on API/authentication/network failure and preserve completed case records without fabricating answers. No paid model call is part of preparing this brief; a later model-mode run follows reference approval and the agreed bounds.

The implemented model mode also requires the expected SHA-256 of the current prompt. A future prompt revision uses a new hash while the five case inputs, references and original baseline prompt stay pinned. The pricing rates and budget must be checked again before a paid run. Its cost calculation is a conservative planning estimate, not a provider billing cap.

Add one offline suite command under the existing evaluator, proposed as `python eval/run.py --mode offline-suite --suite eval/cases/manifest.json`. It should run the frozen real-advertisement replay and named synthetic boundary and input-rejection checks in one invocation, without NAV/model requests or an API key. Preserve `--mode replay` for the existing five-case comparison and `--mode model` for a later paid prompt comparison. The offline suite report must show real-ad accuracy and synthetic pass/fail results in separate sections; synthetic outcomes must not alter real-ad precision, recall or F1. A low real-ad accuracy score is an evaluation finding, not a test-run failure. A broken expected rejection or another failed mechanical check must make the offline suite fail visibly.

Each run gets a unique folder under ignored `out/evaluation/` with a manifest of case IDs and hashes, prompt/schema/model/settings, request payload without credentials, raw response or sanitized failure, validation result, scoring result, token usage, time and cost estimate. Save quantitative and qualitative reports with failure explanations. Every report must list cases **selected, attempted, successfully validated, failed and not run**. Label an interrupted or limited run as partial. Calculate extraction accuracy only for the approved cases with validated responses, identify those cases and their coverage, and separately report end-to-end completion as validated cases divided by selected cases. Never present an accuracy value from a partial subset as a full-suite result. Preserve one screened, reproducible full evaluation run as final-report evidence; do not silently overwrite tracked first-attempt reports.

### 8. Verify and report

Use focused model-free tests for one-to-one matching, aliases, combined names, OR groups, order independence, duplicate items, classification and mention-type errors, missing/extra skills, empty or changed quotations, invalid schema, missing paths/hashes, rejected input, and failed/partial runs. Test that an incomplete reference excludes the whole advertisement; synthetic outcomes never enter real-ad accuracy; an insufficient request limit fails before a model call; and a failed or unattempted case remains visible in the report. Verify replay twice against the same frozen cases with identical results. Verify a fresh checkout can run startup and replay using only the repository and Python standard library. Run syntax checks and `git diff --check`. Record exact commands and results; do not present saved first-attempt scores as newly reproduced.

Acceptance for the offline suite: one documented command produces a new JSON record and readable report listing all five fixed real case IDs and all named synthetic case IDs, their expected and actual outcomes, and pass/fail explanations. The real cases include a source-justified typical case and boundary case. The synthetic checks cover OR structure, heading or classification context, quotation matching, and a raw contact-uncertain input that the existing cleaning/input gate blocks with zero model calls and zero newly published results. A failed synthetic check yields a non-zero exit code and remains visible in the report. Confirm that replay scores stay unchanged, no reference answer reaches a model payload, and neither application statistics nor selected dashboard results change. No live NAV or model request is needed for this acceptance check.

The final evaluation report must state the reviewed sample size, draft exclusions, quantitative results, per-advertisement results, concrete qualitative errors, unresolved human judgments, and limitations. The existing advertisements have been used during prompt development, so they are a **development/regression set**, not evidence of accuracy on unseen ads. Later generalization claims need new, untouched and independently reviewed advertisements.

## Decisions required from Rami and Yehya

1. Approve or revise the five reference answers, including completeness, Azure examples, combined names and OR alternatives; identify any item that remains uncertain.
2. Approve the explicit alias list and the item-level scoring unit before accuracy numbers are reported.
3. Choose whether to run the bounded paid model mode after offline checks and reference approval. Its command must show the verified maximum estimated cost first.
4. Review the qualitative error examples and the final wording of claims in the report. Do not mark draft labels approved through automation.

## Out of scope

Do not optimize the extraction prompt during baseline measurement, change application statistics or the UI, collect more NAV advertisements for this task, rewrite existing extraction results, or treat first-attempt scores as final accuracy evidence. Later prompt improvements must use a new version, rerun the same regression suite, document both improvement and regression, and ultimately test on untouched cases. Do not commit, push or merge without a separate request.
