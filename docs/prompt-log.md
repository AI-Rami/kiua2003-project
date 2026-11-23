# Prompt correction log

Record corrected or rejected agent output using: date, task reference, sanitized prompt/output excerpt, reason, correction, and lesson. Never include personal data or secrets.

## 2026-10-10 — Scaffold planning: data policy

- Task: Initial scaffold planning.
- Rejected output: "Use only synthetic data."
- Reason: The project should support permitted public data and reproducible offline runs with saved real public inputs.
- Correction: "Use permitted public data without personal data; synthetic data may supplement tests."
- Lesson: Do not impose a synthetic-only data restriction. Record source, retrieval date, and permission/license for future public fixtures.

## 2026-10-10 — Scaffold planning: environment variables

- Task: Initial scaffold planning.
- Rejected output: Assume `OPENAI_API_KEY` and `OPENAI_MODEL` belong in `.env.example`.
- Reason: The workflow's provider and configuration requirements have not been selected.
- Correction: Keep `.env.example` comment-only: "Variable names will be added when needed; never put real secrets here."
- Lesson: Add variable names only when a concrete requirement exists; never add real secrets.

## Permission-test status

Project secret-file protection remains unverified. The 2026-10-11 tests below covered temporary-file creation, not secret-file reads. Use only harmless dummy data for future secret-file testing and record the effective profile, tool paths tested, denied-read results, readable-file results, and Git ignore results here when that test is performed.

## 2026-10-11 - Permission tests: desktop and CLI

- Task: Test the current `kiua2003` permission profile using harmless temporary files, without changing configuration or the checker.
- Test conclusion: Desktop eval/ protection failed. CLI temporary-file creation protection passed in the tested session. Secret-file protection remains unverified.
- Reason: In the desktop app, temporary-file creation in `eval/` succeeded; protection failed. Secret-file reads were not tested.
- Correction: Limit verification to the tested CLI behavior described below; keep secret-file protection marked unverified.
- CLI version: 0.162.1. Launch command for this test and future CLI work:

  ```powershell
  codex.cmd -c windows.sandbox=mxc -c default_permissions=kiua2003
  ```

- CLI results: Normal sandboxed exclusive creation (`FileMode.CreateNew`) of root `__permission_test__.tmp` succeeded and cleanup succeeded. Creation of `eval/__permission_test__.tmp` failed with error ID `UnauthorizedAccessException`; the reported error was `Exception calling "Open" with "4" argument(s): "Access to the path '...\eval\__permission_test__.tmp' is denied."` Cleanup for that path was skipped because the test did not create the file.
- Checker integrity: The SHA-256 hash of `eval/check_probe.py` was identical before and after: `34C98C2F6289BE236EE5EEEF325BF42EFC21A78BD7337235E64A6AF9C197383F`.
- Cleanup: No temporary files remained after the tests.
- Lesson: The observed CLI behavior supports root creation and denied `eval/` creation in that tested session only. It does not establish protection in the desktop app, for secret-file reads, or through other tools and sessions.

## 2026-10-12 - MET probe implementation and verification limits

- Task: `tasks/001-probe.md`; implement the standard-library forecast downloader and verify online and offline behavior.
- Correction: An implementation and passing synthetic tests do not establish live acceptance. Do not describe the live checker as passing when the real output is unavailable.
- Online result: Both the normal sandboxed run and an approved elevated retry failed with `urlopen error [Errno 11001] getaddrinfo failed`. DNS diagnosis using `Resolve-DnsName api.met.no` also reported access denied, including the approved retry. No real forecast response or output was produced.
- Offline result: The real-cache invocation failed clearly because `fixtures/met_hamar.json` was unavailable. The existing checker reported `FAIL: out/probe.json is missing.`
- Synthetic tests: Initial temporary-directory creation/cleanup failed with sandbox `PermissionError`. An approved retry passed the five initial tests. After adding offline CLI verification against every saved source timestamp and temperature, the final approved run passed all six tests. Synthetic data stays in isolated temporary directories and is not presented as downloaded MET data.
- Checker integrity: No files in `eval/` were changed; the checker SHA-256 remains `34C98C2F6289BE236EE5EEEF325BF42EFC21A78BD7337235E64A6AF9C197383F`.
- Lesson: Repeat the online probe and checker, then the offline probe and checker, once DNS/network access to MET is available. No commit, tag, or push was performed.

## 2026-10-12 - MET probe verified outside Codex

- Task: `tasks/001-probe.md`; record successful online and offline acceptance testing.
- Verification source: User-reported results from Windows PowerShell outside Codex.
- Online result: `Wrote out/probe.json: 87 forecasts (downloaded)`.
- Offline result: `Wrote out/probe.json: 87 forecasts (offline)`.
- Acceptance checker result: `PASS`.
- Follow-up verification in Codex: The unchanged checker also printed `PASS`; a read-only comparison confirmed all 87 output timestamps and temperatures match the saved source response.
- Correction: The earlier Codex DNS failures remain an accurate record of that session; subsequent external testing confirms successful download and offline execution.
- Lesson: Distinguish environment-specific network failures from verified application behavior, and identify where verification was performed.

## 2026-10-27 - NAV project specification review and revision

- Task: Review and revise the NAV project specification in `SPEC.md`.
- Initial output: `SPEC.md` included skills, education and experience, and listed some already agreed decisions as open questions.
- Review: The project scope was narrowed to skills only to keep implementation and evaluation manageable. Education and experience were explicitly requested in the original prompt; their removal was a user scope change, not an invented requirement or agent error. Clarification was also requested of the chosen NAV API source, advertisement selection, required/preferred/unclear classification, supporting quotations, validation, model selection, and the distinction between the earlier MET exercise and the NAV project.
- Correction: A follow-up prompt requested changes only to `SPEC.md`.
- Outcome: The revised text was reviewed against these requests and found consistent with them. Repository inspection claims were reported by Codex, not independently verified in the external review. Codex reported that `git diff --check` found no whitespace errors. No runtime tests were performed.
- Lesson: Review the specification before implementation. Distinguish user scope changes from agent mistakes, and code inspection from successful execution.

## 2026-10-30 - NAV advertisement fixture download

- Task: Download one NAV advertisement as a JSON fixture.
- Failure: The public-token endpoint returned explanatory text and a JWT. Codex incorrectly used the entire multiline response as the Bearer value. PowerShell rejected the header before sending the advertisement request. Error output exposed the public token, contrary to the instruction not to display it.
- Correction: Extract and validate only the JWT, keep it in memory, and handle errors without displaying the token or Authorization header.
- Outcome: Codex reported that the retry returned HTTP 200 inside the sandbox and saved `fixtures/nav_ad_01.json` as UTF-8. It reported reading the file back and successfully parsing JSON. External review confirmed valid JSON, found named employees and biographies in the description's “Om oss” section, and compared the revised JSON with the original. The review confirmed that only the agreed “Om oss” section was removed and all other values and job requirements were unchanged. The revised file parsed as UTF-8 JSON without a BOM.
- Lesson: Inspect response formats before constructing authentication headers, and ensure error reporting does not expose tokens.

## 2026-10-31 - NAV saved-input extraction output format

- Task: `tasks/002-nav-skeleton.md`; run the saved advertisement through `gpt-6-luna`.
- Rejected output: The first run returned two items with multiple skills but `relationship: "single"`.
- Reason: The agreed schema requires exactly one skill for `single`; validation failed for items 4 and 5. No result or report was produced for that run.
- Correction: The general extraction prompt now states the `single` and `any_of` rules, separates skills joined by “and” into single items, and permits separate items to share exact evidence. The validator and failed run artifacts were left unchanged.
- Outcome: Focused model-free checks passed. One new saved-input API request returned a completed response; structural and exact-quotation validation passed, and a result and report were produced. Extraction accuracy and completeness have not been evaluated.
- Lesson: A strict JSON shape does not ensure that relationship labels match the number and meaning of skills; make grouping rules explicit and validate them independently.

## 2026-10-31 - NAV skeleton diagnostics and run naming cleanup

- Task: Clean up `harness/nav_skeleton.py` and the README for saved-input runs.
- Corrected output: The main error handler could overwrite detailed `validation.json` diagnostics after validation failed; new run folders used a compact timestamp.
- Correction: Preserve an existing validation file, write fallback diagnostics only when absent, and format new UTC run IDs as `YYYY-MM-DD_HH-MM-SS_UTC-xxxxxxxx`. Clarify the implemented stages, classifications, grouping rules, validation limits, and dry-run behavior in the README.
- Checks: Syntax passed. Temporary model-free checks confirmed detailed diagnostics survive validation failure, earlier failures receive fallback diagnostics, and new folder names follow the specified pattern. No API request was made.
- Lesson: Keep detailed failure evidence when reporting an error, and make run artifact names readable without changing earlier runs.

## 2026-10-31 - NAV run folder identification

- Task: Use UTC time and the saved advertisement UUID in future run folder names.
- Requested improvement: The earlier folder format used an eight-character random suffix and did not identify the advertisement.
- Correction: Validate and normalize the advertisement UUID before creating a folder; use `YYYY-MM-DD_HH-MM-SS_UTC_ad-<uuid>` for both folder name and run ID. Refuse to overwrite an existing folder.
- Checks: Syntax passed. Temporary model-free checks accepted a valid UUID, rejected an invalid UUID before folder creation, verified the new name and matching run ID, and verified that a folder collision left existing contents unchanged. No API request was made and existing run folders were not changed.
- Lesson: Identify the saved source in the run path and fail safely when the same source and UTC second collide.

## 2026-10-31 - NAV collector syntax correction

- Task: Implement the requested bounded NAV metadata collector in `harness/nav_collect.py`.
- Requested feature: Collect a limited change-feed preview and save only qualifying advertisement metadata and a run summary. This request was new functionality, not a correction to the earlier saved-input skeleton.
- Corrected output: The initial version of the new collector had an unmatched closing parenthesis; its first syntax check failed. Post-preview review also found that a mid-page failure could undercount unprocessed detail candidates. An initial new-file whitespace check falsely flagged lines because its trim expression included a literal `t` character.
- Correction: Remove the extra parenthesis before running any live preview. Count remaining candidates in a failure summary if a later detail request fails mid-page. Replace the whitespace check with an explicit space-or-tab suffix check.
- Checks: The subsequent syntax check passed. Focused synthetic selection, UUID deduplication, limit, URL, pagination, failure-handling, and dry-run checks passed. The actual dry-run exited successfully without creating the output directory. `git diff --check` passed before the live preview. After the live preview, a further synthetic mid-page HTTP failure check passed; the corrected new-file whitespace check passed; no second live run was made.
- Live outcome: One bounded preview fetched one page and made 50 detail requests. It recorded zero matches, two nonmatches, 48 inactive details, zero unknown relevance, and no failures; the detail limit stopped the run with 94 active candidates on the fetched page uninspected.
- Lesson: Run syntax and model-free checks before live requests, and report a bounded zero-match result without implying complete coverage.

## 2026-10-31 - NAV feed duplicate selection correction

- Task: Improve candidate selection in the bounded NAV metadata collector.
- Corrected output: The collector could request a detail for an older ACTIVE feed entry even when a newer entry for the same UUID on that page was INACTIVE.
- Correction: Group entries by UUID within each fetched page and compare the documented `date_modified` timestamps before selecting ACTIVE details. Skip UUIDs when recency cannot be determined safely; report valid time bounds and missing or invalid timestamps per page. Keep the current detail-status check and one-detail-request-per-UUID rule.
- Checks: Syntax passed. Synthetic model-free cases passed for both status transitions in both array orders, duplicate UUIDs, timestamp diagnostics, timezone comparison, and a collection run with a one-detail limit. No live request was made or existing output changed.
- Lesson: Use the feed's change timestamp to resolve duplicates on a fetched page; this does not establish the latest state across unread pages.

## 2026-10-31 - NAV relevance reason correction

- Task: Add aggregate reasons for unknown and nonmatching details in the bounded collector.
- Corrected output: The previous relevance logic returned unknown whenever either selection condition was unknown, even if the other was definitely false. The saved summary counted outcomes but did not identify their reasons.
- Correction: Treat either definitely false condition as a nonmatch, both true as a match, and all remaining active cases as unknown. Keep inactive and invalid status explicit. Record one exclusive reason for each unknown or nonmatching detail, including false-plus-unknown combinations.
- Checks: Synthetic model-free checks passed for all nine true/false/unknown condition pairs, inactive and invalid status, missing content, and aggregate reason counts in a mocked collection run. No network or model request was made; existing run outputs were not changed.
- Lesson: Report both condition states so a false-plus-unknown case is not mistaken for a single known exclusion reason.

## 2026-11-01 - Resumable NAV availability investigation

- Task: Add a separate resumable feed scan and metadata-only detail discovery command.
- Requested change: The bounded preview did not retain a cursor or reconcile changes across pages. The new investigation saves feed progress in SQLite and waits for the current feed end before detail discovery.
- Checks: Temporary mocked cases passed for page and detail resume, overlapping pages, status changes with regressing or equal timestamps, final-page polling, phase separation, overlapping occupation counts, unsafe URLs, rate-limit progress, unavailable content, and the existing preview relevance function. No advertisement body was saved by these checks.
- Correction: A review of the new summary found that a detail saved before a later feed change could still contribute to counts. The summary now counts a detail only when its saved feed order matches the UUID's latest reconciled order; a synthetic stale-detail check passed.
- Limitation: The scan and any later detail availability describe observed API data, not complete market coverage or historical text recovery.
- Live outcome: One session from `2026-08-01T00:00:00Z` reached the current feed end after 181 pages and stopped at the 2,000-detail limit. It left 7,133 detail candidates pending; the saved partial summary counted 69 IT ads with usable text, including 3 explicitly listing Innlandet.

## 2026-11-01 - NAV edited text capture and queue completion

- Task: Continue the existing discovery database, backfill previously processed IT text, and save edited text captures for later extraction.
- Requested change: Add a SQLite-backed capture state, conservative contact cleaning, separate confirmed Innlandet and remote-review sets, and an offline JSON export. This was new work rather than a correction to the saved-input skeleton.
- Correction: A temporary whitespace-check command used an incorrect trim expression and failed; the corrected space-or-tab check passed. A synthetic review-flag assertion initially compared a SQLite row object directly with a tuple; comparing its values passed.
- Checks: Synthetic migration, backup, cursor, cleaning, review blocking, deduplication, resume, inactive preservation, backfill, export, and credential/body exclusion checks passed. Syntax, the prior collector dry-run, and `git diff --check` passed before live execution.
- Live outcome: Four bounded resume batches made 7,202 detail requests, including 69 IT backfills, without rescanning feed pages. The queue completed with zero pending work and zero request failures. It saved 167 distinct cleaned IT captures: 10 confirmed Innlandet and 157 remote-review candidates. Another 114 IT records were review blocked without saved text.
- Limitation: The latest feed end checked remains the earlier observed `2026-11-01T10:47:55.775278Z`; these captures do not reconstruct removed historical descriptions or establish complete market coverage. All saved text still needs human review for personal information.

## 2026-11-01 - Targeted Innlandet contact-cleaning correction

- Task: Correct contact cleaning and reprocess only the 11 previously detailed IT ads explicitly listing Innlandet.
- Corrected output: The earlier cleaner could leave a named contact sentence, discard a qualification sharing a paragraph with contact text, and miss contact headings marked as bold paragraphs.
- Correction: Version 2 separates recognizable contact passages, uses `contactList` hints only in memory, recognizes bold headings, and blocks ambiguous separation. Earlier captures remain unchanged; revised outcomes are stored separately.
- Checks: Twelve synthetic cleaner cases passed, including Norwegian and English contact wording, mixed paragraphs, headings, company wording, and ambiguity. A mocked 11-target run verified backup, remote exclusion, one request per UUID, review blocking, prior-capture retention, and offline export. Syntax and `git diff --check` passed before live requests.
- Live outcome: A SQLite backup preceded 11 sequential detail requests. Ten revised captures were saved with `pending_human_review` status; one was review blocked for an uncertain section boundary. The separate export contains 11 JSON files and an index. Earlier 167 captures and discovery progress remained intact.
- Limitation: Automated cleaning does not guarantee removal of all personal information; revised captures still need human review.

## 2026-11-01 - NAV collection review before commit

- Task: Review the remaining NAV collection and cleaning code after the one-off reprocessing script and earlier output folders were removed.
- Corrected output: The README still gave commands for the removed script, and the specification still said live NAV collection and persistent storage were only planned. The discovery command's module description also said it never stored advertisement text, although it saves edited IT text captures.
- Correction: Remove the obsolete commands, distinguish implemented collection and cleaning from saved-fixture extraction and planned integration, statistics, and dashboard work, and identify the reprocessing task as historical. Preserve earlier prompt-log entries.
- Checks: Syntax and imports passed for the three collection and cleaning modules and the saved-input skeleton. Four synthetic relevance cases and four synthetic cleaner cases passed. Both dry-run commands, discovery command help, and `git diff --check` passed without network or model requests. An initial cleaner assertion incorrectly expected a non-contact heading to be removed; the corrected assertion passed.
- Limitation: The cleaner's edited captures remain pending human review, and the current collector does not feed them to the extraction skeleton.

## 2026-11-01 - One cleaned NAV capture through the extraction skeleton

- Task: Accept one explicitly selected, edited Innlandet IT review capture as plain-text input to the existing skill-extraction skeleton.
- Requested change: Add a cleaned-capture input path while preserving the saved-fixture path, existing prompt, schema, validator, model settings and one-request limit. Retain the capture UUID, source link and provenance; the selected export has no title field.
- Checks: Syntax, actual-capture hash and exact-input checks, five synthetic invalid-capture checks, a synthetic validation/report check, the saved-fixture request-format check, and the capture dry run passed. The dry run created no run folder. A first temporary test location was denied by the sandbox; the checks passed when run in ignored `out/`.
- Run outcome: One `gpt-6-luna` request for UUID `2ed29047-97e4-4168-adb9-8da83e968c94` returned HTTP 429. No retry was made. The new run folder contains the exact prepared text, credential-free request and sanitized failure diagnostics; no API response, result or report was produced.
- Limitation: No model output or skill extraction was validated in this run. The edited capture remains pending human review.

## 2026-11-01 - Remaining cleaned Innlandet IT extraction batch

- Task: Process the nine remaining successfully saved review captures once each using the unchanged `gpt-6-luna` extraction workflow. Exclude the blocked record and the UUID already extracted successfully.
- Rejected output: Six of nine new responses failed the existing validator. Five responses were incomplete or truncated under the configured output cap; one contained an evidence value that was not an exact quotation from the saved cleaned text.
- Checks: Before requests, the export had 11 JSON records, with one blocked, one previously successful, and exactly nine eligible inputs. Each selected input passed capture preparation and the request-size limit. Afterward, the batch index links were checked, three success reports and six failure diagnostics were verified, and no failed run had a result or report.
- Outcome: Nine separate new run folders were created with one model request per UUID and no retries. Three new runs passed validation, six failed validation, and none remained unprocessed. New responses reported 14,756 input tokens, 16,318 output tokens and 31,074 total tokens. The earlier success was indexed without another request.
- Limitation: Structural and exact-quotation validation does not establish extraction accuracy or completeness; edited captures remain pending human review.

## 2026-11-01 - NAV extraction output cap and whitespace quotation correction

- Task: Correct the two failure types observed in the six rejected saved-capture extraction runs and retry only those six.
- Corrected output: Five responses ended with `incomplete_details.reason: max_output_tokens` at the previous 2,048-token cap. The sixth completed response had evidence differing from the saved text only in whitespace, including a newline and nonbreaking space.
- Correction: Raise the output allowance to 8,192 tokens. Estimate pre-request cost with the existing dated rates, request-byte input proxy and full output allowance while retaining the 20,000-byte request bound. Accept quotations after whitespace-only normalization and record `exact` or `whitespace_normalized` without changing the model's evidence. Keep the model, reasoning effort, prompt, schema and other checks unchanged.
- Checks: Model-free cases passed for exact and whitespace-normalized quotations, changed words, capitalization, punctuation, empty evidence, the 8,192-token request cap, and planning and actual-usage cost calculations. The earlier whitespace-only failure passed the new validator in memory. A dry run showed the new cap and cost estimate; `git diff --check` passed before requests. An initial read-only post-run audit incorrectly expected match-mode metadata in four older results; the corrected audit passed.
- Retry outcome: Six sequential requests, one per previously failed UUID and no retries, produced six new validated reports. Their reported usage was 10,447 input, 13,665 output and 24,112 total tokens. All six new evidence matches were exact. The latest batch index links ten successful reports: the six new results and four preserved earlier successes.
- Limitation: Structural and quotation validation does not establish extraction accuracy or completeness; edited captures remain pending human review.

## 2026-11-01 - Offline skill summary for ten saved advertisements

- Task: Summarize only the ten successful extraction results linked by the saved correction-batch index, without network or model requests.
- Requested change: Add a reusable standard-library command that validates ten distinct UUIDs and saved successful results, counts exact saved skill names by advertisement and classification, separates `single` mentions from `any_of` alternatives, and writes a readable summary, structured counts and an advertisement link index.
- Checks: Three synthetic tests passed for repeated skills, overlapping classifications, OR alternatives and groups, reversed saved group order, and duplicate or unsuccessful index rows. Syntax and whitespace checks passed. The generated JSON parsed; an independent recount from the ten linked results matched every count and supporting-UUID union in all four sections. All ten report links and ten saved source links were verified.
- Outcome: The new offline output contains ten advertisements, 211 distinct saved skill strings, 179 single-skill strings, 39 alternative-skill strings and 14 saved OR groups. A new unique output folder was created under ignored `out/nav_skill_summaries/`; earlier results and indexes were preserved.
- Limitation: This describes the ten collected advertisements only. Extraction accuracy and completeness have not been fully evaluated; the cleaned captures remain pending human review. No publication-date views or dashboard were added.

## 2026-11-01 - Source-text audit of ten saved skill results

- Task: Review the ten linked extraction results against their saved prepared advertisement texts, then correct confirmed summary errors without altering original runs.
- Corrected output: The first summary faithfully recounted model results but included unsupported required classifications, generic non-skills, fragmented equivalent names and incorrectly separated OR alternatives. A recount matching saved results had not established extraction accuracy.
- Correction: Review each of the ten UUIDs in index order and record findings in a separate progress file. Apply 46 explicit item decisions and two reviewed name aliases through a hash-checked correction manifest. Preserve saved evidence and original result files. Regenerate the summary in a new output folder.
- Checks: Ten distinct linked UUIDs and matching prepared-text captures were confirmed. Four model-free summary tests, Python syntax, and `git diff --check` passed. The regenerated JSON parsed, and UUID union/count invariants passed for all rows in all four summary sections. No NAV or model request was made.
- Outcome: The corrected small-sample summary has 10 advertisements, 187 distinct counted skill names and 15 OR groups. The initial mechanical summary had 211 saved skill strings and 14 OR groups. `Project work` and the falsely required `Data structures` item no longer appear in counts.
- Limitation: The audit used saved cleaned text; raw pre-cleaning bodies are unavailable for most records. Some interpretations remain uncertain, and cleaned captures have not been human-approved for personal data. This is not complete Innlandet market coverage or an approved extraction reference.

## 2026-11-01 - SSB extraction with revised prompt

- Task: Make one fresh extraction request for SSB advertisement `dc0bdd91-ddb4-4e5f-8eb7-bf51f57e31aa` using the already updated prompt and exactly the previous prepared advertisement text.
- Checks: The selected capture, prior `prepared_ad.txt`, prior request input and new request input matched. The new credential-free `request.json` contained the current prompt, which differed from the previous run's prompt. The request body was 10,998 bytes, below the existing 20,000-byte limit.
- Rejected output: The API returned a completed response with 17 items. Local quotation validation rejected items 4–8 because their evidence joined the optional-qualification heading to later bullets while omitting intervening bullets. This was not a whitespace-only difference. The run therefore produced no `result.json` or `report.md`; the response and diagnostics remain saved in its new folder.
- Comparison: The new output classified `Data structures` as unclear rather than the previous run's required, consistent with the source wording “interesse for datastrukturer”. It also omitted several generic labels from the previous result. Possible overinterpretations in remaining labels were identified for review, not manually corrected.
- Usage: The response reported 2,386 input tokens, 2,193 output tokens including 1,409 reasoning tokens, and 4,579 total tokens. No other advertisement was requested, and no retry or manual correction was made.

## 2026-11-01 - Separate-quotation NAV extraction format

- Task: Revise the saved-input extractor to distinguish candidate qualifications, duties, work context and interest-only mentions, and to save separate exact skill and optional classification-context quotations. Preserve the previous run outputs and the ten-ad summary.
- Corrected output: The earlier SSB retry was rejected because five evidence values stitched a preferred-qualification heading to later bullets while omitting intervening text. The new format uses two independently checked quotations rather than one stitched passage.
- Changes: Add strict v2 schema fields `mention_type`, `skill_evidence`, and nullable `classification_context`; require exact continuous source passages; show both in the report and identify format v2. Keep the model, reasoning setting, output allowance, timeout and one-request behavior. Classification-context governance remains a semantic review task.
- Checks: Four synthetic model-free tests passed for separate quotes, OR groups, nullable context, invalid labels, stitched or altered quotes, and v2 reporting. Python syntax and `git diff --check` passed before the live request. The SSB capture and new request input matched the previous prepared text; the saved request contained the current prompt and v2 schema. Dry run passed.
- Run outcome: One fresh SSB request returned a completed response with 16 items. Local v2 validation passed; each supplied quotation matched the prepared text exactly. The new result and report were saved in a separate run folder. Reported usage was 2,638 input tokens, 2,282 output tokens including 1,552 reasoning tokens, and 4,920 total tokens; estimated token cost was $0.00140480 using the configured dated rates. No other advertisement was requested or retried.
- Semantic review: The preferred heading governs the quoted optional bullets, and the saved OR groups preserve their alternatives. The output omits the preferred user-support/advising/dissemination group. Some duty items name objects or support tasks as broader skills, and the preferred metadata/classification labels may overstate the quoted wording. These observations were not manually corrected in the saved result. Passing quotation checks does not establish extraction accuracy or completeness.

## 2026-11-01 - General prompt refinement and one SSB extraction

- Task: Add general rules against unsupported ability words, object-only evidence for duties, conflating technical support with performing an activity, skipped technical qualification bullets, and nontechnical support/advice/UX mentions. Do not change the v2 schema or manually correct model output.
- Checks: Four model-free v2 tests and `git diff --check` passed before the request. The new request used exactly the prior 5,602-character SSB prepared text, unchanged v2 schema/model/reasoning settings, and the revised prompt; its body was 13,520 bytes under the 20,000-byte limit. The prompt contained no SSB-specific expected labels.
- Run outcome: One fresh SSB request completed and passed v2 structure and exact-quotation validation with 18 items, compared with 16 in the previous v2 result. The new run was saved separately. Reported usage was 2,826 input tokens and 2,618 output tokens including 1,716 reasoning tokens, 5,444 total tokens; the configured dated rates estimate $0.00159160. No other ad was requested or retried.
- Review: The preferred metadata/classifications group no longer adds unsupported `management`; the model now calls assistance with data extraction technical support rather than data extraction itself. It still quotes only the objects for three creation-and-maintenance duty items, leaving the claimed action absent from their individual evidence. The preferred support/advice/dissemination bullet remains unextracted; whether it meets the technical-only scope needs review. The new UX interest-only mention is unclear rather than a competence claim. These findings were not manually corrected in the saved output.
- Unresolved review cases: Three SSB duty labels include creation and maintenance, but their individual quotations are only “tabellmatriser”, “klassifikasjoner”, and “kodelister i Statistikkbanken”; the shared verb occurs earlier in the same source bullet. The omitted “erfaring med brukerstøtte, rådgivning eller formidling” bullet is an uncertain inclusion under the agreed technical-only scope, not a confirmed extraction error. No saved result was changed.
- Limitation: Exact quotation and structure checks passed, but they do not establish semantic support, completeness or heading governance. Previous runs and combined statistics were unchanged.

## 2026-11-01 - Shared-verb evidence rule tested on two saved ads

- Task: Strengthen the general evidence instruction for action-labelled skills and shared verbs, without changing the v2 schema. Test one saved ad with OR alternatives and one with qualification headings and example technologies.
- Requested change: Require `skill_evidence` to include wording for any action in a skill label. When one verb governs several objects, quote the continuous clause or bullet through the target object, including intervening objects; a bare noun is insufficient. No SSB-specific expected answer was added.
- Checks: Four local model-free v2 tests and `git diff --check` passed before the requests. The two selected captures matched their respective earlier prepared texts. Their request bodies were 13,092 and 9,226 bytes, both under the 20,000-byte limit. The schema, model and reasoning setting remained unchanged.
- Run outcomes: Exactly one request each for `4135497b-cb65-4bed-890d-f9dcaf478711` and `2f62e300-c698-4f53-8510-db90b1692cb9`; both completed and passed v2 structural and exact-quotation checks. Their new run folders contain 20 and 29 items respectively. Earlier runs were preserved; no result was manually corrected and no statistics were regenerated.
- Meaning review, OR ad: Linux/Windows, scripting/Infrastructure as Code, and VMware/Omnissa remained preferred `any_of` groups. Duty items quoting action-labelled skills included their source verbs. The optional-qualification heading governs the preferred items. Automation/orchestration and its scripting/IaC alternatives may be redundant, requiring review.
- Meaning review, headings/examples ad: The desired-qualification heading governs preferred items, and the key-qualification heading governs required items, though the required items saved null context quotations. General Azure competence is stated; the model again labelled every parenthesized Azure service independently required, which the source does not establish. Individual preferred labels for parenthesized container/orchestration tools are also uncertain. Exact quotation checks did not detect these interpretation problems.
- Usage: The OR ad reported 2,694 input and 3,639 output tokens, including 2,299 reasoning tokens; estimated cost $0.00208890. The headings/examples ad reported 1,644 input and 2,525 output tokens, including 988 reasoning tokens; estimated cost $0.00142690. These are estimates from the configured dated rates, not billing statements.

## 2026-11-01 - Broad technology examples and heading evidence

- Task: Add a general rule distinguishing broad technology requirements from individually named examples or components, and require a separate heading quotation when classification depends on that heading. Keep the v2 schema and model settings unchanged; test only the saved advertisement `2f62e300-c698-4f53-8510-db90b1692cb9` once.
- Corrected output: The previous v2 result labelled each parenthesized service in a general Azure requirement independently required and omitted the key-qualification heading from required-item context quotations. This was an interpretation error despite passing exact-quotation validation.
- Checks: Four model-free v2 tests and `git diff --check` passed before the request. The selected capture matched the previous 1,167-character prepared text, and the new request kept the schema, model and settings unchanged. The request body was 10,012 bytes under the 20,000-byte limit; `request.json` contains the revised prompt and excludes credentials.
- Run outcome: One new run completed and passed v2 validation with 28 items and exact quotation matches. General Azure competence was required; seven individually named services were unclear. Preferred containerization and orchestration remained preferred while five parenthesized named tools were unclear. All required and preferred items carried a heading context quotation. No explicit OR group occurs in this advertisement; none was invented.
- Review boundary: The short advertisement's technical qualification bullets were represented, and no confirmed new omission or classification error was found. Naming choices such as the combined `C# .NET` label and individual normalized product names remain review judgments. One passing advertisement does not establish general extraction accuracy. The prompt is a candidate for the next evaluation batch, not approved ground truth.
- Usage: The response reported 1,767 input and 3,303 output tokens including 1,781 reasoning tokens, 5,070 total tokens; estimated cost $0.00182820 using the configured dated rates. No retry, manual correction, other-ad request or statistics update occurred.
- Prompt identity: SHA-256 of the UTF-8 prompt file and saved request instructions was `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`.

## 2026-11-02 - Frozen-prompt development-set evaluation

- Task: Evaluate the ten advertisements in the original extraction batch with prompt SHA-256 `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`, saving sequential meaning reviews separately from automatic validation.
- Reuse and safety: The existing Azure run matched the frozen prompt, schema, settings and saved input and was reused. One capture with an unresolved cleaning/personal-data issue was blocked without a model request. Eight other advertisements received one fresh request each, with no retries or manual changes to model outputs.
- Checks: The prompt hash matched before each new request and in a final audit. All nine evaluated runs had matching request instructions and settings, request input equal to their saved prepared text, and passing structural and quotation validation. All ten distinct UUIDs have saved progress and review entries, including the blocked case.
- Review outcome: The separate meaning review found confirmed interpretation errors in some passing runs, including lost OR alternatives, independently classified example technologies, an omitted broad preferred mention, and generic non-skills. Other classification and technical-scope judgments remain unresolved. The detailed per-ad findings and source quotations are in the ignored evaluation review record; original runs were preserved and statistics were not regenerated.
- Usage: The eight new responses reported 22,152 input tokens and 28,601 output tokens, 50,753 total; the configured dated rates estimate $0.0165157. One earlier matching run was reused without a new request. These development-set findings do not establish accuracy on unseen advertisements.

## 2026-11-02 - Bounded incremental NAV update command

- Task: Connect saved NAV feed continuation, edited-text capture, existing v2 extraction and selected-result statistics in one reusable command for the Compulsory 2 walking skeleton.
- Requested change: Add a processing queue committed with each feed page and cursor, resume pending work, reuse unchanged cleaned-text hashes, publish only validated replacements, keep blocked inputs blocked, and bound page, detail, extraction and runtime work. Keep the extraction prompt, schema, model and settings unchanged.
- Checks: Seventeen isolated, model-free workflow tests passed for no updates, changed and unchanged UUIDs, blocked inputs, inactive historical results, request limits, discovery and model rate-limit failures, page/queue transaction rollback, saved final-page continuation and restart from a saved model response. The full NAV test suite, syntax check and `git diff --check` passed. No NAV or model request was made.
- Outcome: `harness/nav_update.py` now provides a single command and reusable `run_update()` function. The existing current index was annotated with last-known activity from saved discovery metadata; the offline statistics were regenerated from it, retaining nine selected results and two blocked entries. Newly published versions will be placed under the corresponding UUID in `out/current/`. The command has not yet been run live.
- Limitation: The command does not perform human meaning review, build the UI or establish complete market coverage. Unreviewed semantic accuracy and uncertain contact cleaning remain separate concerns.

## 2026-11-02 - First bounded live incremental update verification

- Task: Run the documented incremental update command once with limits of two feed pages, 50 details, five extractions and 600 seconds, after backing up the saved discovery database.
- Starting state: The saved scan had reached a final page after 181 pages and 178,893 feed events. The current index selected nine validated v2 extractions and listed two blocked UUIDs; the statistics index hash matched.
- Checks: A SQLite backup passed `PRAGMA integrity_check` and retained the starting event count. After the command, the index still had nine distinct selected UUIDs and two blocked UUIDs. An offline recount of the selected results matched all saved skill and alternative-group counts; the statistics index hash still matched.
- Outcome: The single live command exited 0 with `partial_pending`. It read two feed pages from the saved continuation path, added 1,998 change events and left 1,440 distinct UUIDs queued. It stopped at `page_limit` with `phase=scan` and an advanced cursor. No advertisement details or model requests were made, so no relevance decisions, extraction validations or publications occurred. The nine current results and two blocked entries were unchanged.
- Limitation: This run verified feed continuation and queue persistence live. Detail discovery, cleaning, extraction, validation and replacement publication remain locally tested but were not exercised live. The queued entries have not yet been assessed for IT or Innlandet relevance.

## 2026-11-02 - Normal NAV catch-up defaults and pagination guards

- Task: Replace the incremental command's two-page test default with a normal resumable catch-up mode, while retaining explicit smaller limits for tests.
- Requested improvement: The first live verification stopped at its requested two-page limit with 1,440 UUIDs queued. The normal command now resumes that saved cursor and uses operational ceilings of 1,000 pages, 2,000 details, 20 model requests and 1,200 seconds per invocation. The same command can be repeated after a partial stop.
- Correction: Reject a non-advancing or repeated feed-page cursor. Treat detail HTTP 404 as a recorded unavailable-content condition for that feed version so it does not repeatedly block later candidates; a subsequent feed change to that UUID remains eligible for a new check. Preserve the existing prompt, schema, model, filtering and cleaning rules.
- Checks: Twenty-two isolated model-free workflow tests passed, including three-page pagination, saved-cursor resume, reaching the feed end, one synthetic detail-to-extraction path, pending processing, cursor guards and detail-404 handling. The full NAV suite passed 34 tests; syntax and `git diff --check` passed. An earlier local test attempt encountered a temporary Windows file-access error while replacing a synthetic statistics file; its immediate rerun passed. No NAV or model request was made.
- Outcome: The README now documents the normal command, optional test limits, progress, stop reasons and the distinction between reaching the feed end and finishing queued work. The real saved discovery database and its 1,440-item queue were inspected read-only and left unchanged.

## 2026-11-02 - Version-specific NAV processing blocks

- Task: Keep the two existing intentional UUID blocks while allowing a later feed version of another blocked advertisement to be assessed again.
- Correction: The updater previously treated every blocked index entry as a permanent UUID block. It now distinguishes intentional blocks from feed-version blocks, saves a sanitized reason and feed order for the latter, skips the same version, and reassesses a later event. SQLite retains the version-block history. An older selected result stays available as stale evidence and remains excluded from statistics until a validated replacement is published.
- Checks: Thirty-seven model-free NAV tests passed, including synthetic same-version skips, newer-version reassessment, distinct reasons across versions, intentional blocks and previous-result retention. Three changed Python files passed syntax parsing; `git diff --check` passed. The saved index has nine current entries and two intentional blocks, and its statistics hash matches. The real discovery database remained in scan phase with 1,440 pending UUIDs.
- Limitation: The proposed automatic input acceptance gate was not implemented. A saved capture marked `pending_human_review` currently passes structural input checks; this state does not mean human approval or guarantee removal of personal information. No NAV or model request was made.

## 2026-11-02 - Contact cleaning and automatic input screen

- Task: Recognize contact information throughout an advertisement, including at its end; allow names alone while removing clear contact passages, email addresses and phone numbers.
- Requested change: Cleaner version 3 no longer treats a `contactList` name by itself as a contact signal. It recognizes additional clear Norwegian and English contact wording, keeps separable job content in mixed paragraphs, and holds uncertain passages for review. The edited text passes a second email, phone and contact-wording screen before capture is saved as `auto_contact_checked`. The updater accepts that checked cleaner version and rejects older `pending_human_review` captures for new extraction.
- Checks: Fifty-two model-free NAV tests passed, including synthetic end-of-ad contacts, mixed qualification/contact text, names without contact wording, English and Norwegian wording, bold headings, residual contact screening, pending-review rejection, rechecking the same text hash under the newer cleaner, and continuing to a second ad after a held capture. Five changed Python files passed syntax parsing. No NAV or model request was made.
- Limitation: The screen recognizes defined patterns; it cannot establish that every possible contact detail is absent or that a person approved the edited text. Historical captures and selected extraction results were not reprocessed.

## 2026-11-02 - Targeted check of two intentional NAV blocks

- Task: Recheck the two intentionally blocked UUIDs with cleaner version 3 and extract only a current relevant advertisement whose edited text passes the contact screen.
- Outcome: Both live detail responses were ACTIVE and matched IT plus Innlandet. UUID `8119dbb1-530f-4307-9ee0-e030c2b8e581` passed cleaning and the second contact screen. One `gpt-6-luna` request completed and passed local structural and quotation validation; its result was selected in the current index and statistics were refreshed to ten selected advertisements. UUID `1f614033-73b3-4c26-bda5-3d9abe281a12` remained blocked with `uncertain_section_boundary`; no model request was made for it. A sanitized structural check did not resolve that boundary.
- Requests and saved state: Three public-token requests, four detail requests across the two UUIDs, and one model request were made; none was retried after failure. The index and previous statistics were backed up before publication. The second advertisement's raw response and description were not saved. Its intentional block remains in place. The discovery database and feed checkpoint were not changed.
- Validation boundary: Local validation checked output structure and source quotations, not extraction meaning or completeness. Pattern-based contact screening and this targeted pass are not human approval.

## 2026-11-02 - Resolve the second contact-section boundary

- Task: Reassess the remaining blocked advertisement after the user identified a separate contact-information passage and contact-person section.
- Correction: Cleaner version 3 now recognizes `Kontaktperson for stillingen` as a contact heading and `Slik søker du` as a following application heading, so the application text is retained while the contact section is removed. Contact wording `Kontaktinformasjon` is included in the residual contact screen. Three new synthetic cleaner checks passed; the full 55-test NAV suite passed.
- Live outcome: Four public-token and four detail requests were made for UUID `1f614033-73b3-4c26-bda5-3d9abe281a12` during targeted diagnosis, rechecking and extraction; no feed page was scanned. Its current detail was ACTIVE and met the IT and Innlandet criteria. The edited text passed the contact screen and one `gpt-6-luna` request passed local structural and quotation validation. After backing up the index and statistics, its validated result was selected and statistics refreshed to eleven advertisements. No intentional block remains in the current index.
- Limitation: Validation does not establish extraction meaning or completeness, and the automatic contact screen is not human approval. The saved discovery checkpoint and old run evidence were not changed.

## 2026-11-02 - Separate qualification statistics from other mentions

- Task: Improve the offline statistics table for the eleven selected advertisements without changing saved extraction results or making requests.
- Requested change: Make single applicant qualifications the main table, keep applicant `OR` groups separate, and show duties, work context and interest-only technical mentions separately. Preserve exact saved skill names without automatic alias merging. Display publication dates from selected capture provenance with an explicit selected-sample coverage note; do not create weekly, monthly or yearly counts.
- Checks: Fifty-seven model-free NAV tests and syntax parsing of the changed statistics files passed. `git diff --check` passed. An initial temporary report check omitted `status_counts` and failed with `KeyError`; the corrected check generated a temporary report and verified all eleven report links. The prior statistics files were backed up before the active report was regenerated.
- Outcome: The new report contains eleven distinct selected advertisements, 128 single-qualification skill rows, 12 qualification `OR` groups and 90 other single-mention rows. All eleven selected results have valid saved publication dates, ranging from 2025-11-27 to 2026-10-29. The regenerated statistics hash matches the current index, and all selected report links resolve.
- Limitation: The date range describes only selected advertisements, not feed collection coverage. No skill-name aliases were approved or merged, and structural validation does not establish extraction accuracy.

## 2026-11-03 - Retain and retrieve NAV job titles

- Task: Check whether the incremental pipeline retains job titles and try a bounded title-only NAV lookup for the nine selected advertisements whose saved results lacked titles.
- Correction: Discovery previously stored no title, and the incremental updater passed `title=None` to extraction. Future detail retrieval now stores title metadata by UUID and feed order; the updater includes an available title in new results and the selected index. The statistics advertisement index displays a title when saved, with a fallback when unavailable. Earlier extraction files were not rewritten.
- Checks: Sixty model-free NAV tests passed, including synthetic title storage, title propagation and later display metadata. Five changed Python files passed syntax parsing; `git diff --check` passed. The selected index still has eleven current UUIDs, the statistics hash matches, and all report links resolve.
- Live outcome: One public-token request and nine sequential detail requests returned four usable titles; five details did not supply a usable title. No retry or model request was made. Four titles were added as display metadata to the current index after backing up the old index and statistics; six of the eleven selected ads now have titles.
- Limitation: The lookup did not save raw NAV bodies or change the discovery database. A missing title was not inferred from other fields. The newly fetched titles describe the detail responses at lookup time, not necessarily the older extraction version.

## 2026-11-03 - Local NAV skills dashboard

- Task: Add a local dashboard over the selected saved results, with publication-date and saved-status filters, skill search, advertisement drill-down, data-quality details and a button wired to the existing incremental updater.
- Requested improvement: Keep the earlier-cleaner captures accepted for this project dataset visibly distinguished from newer automatically contact-checked captures. Show saved activity status as the last NAV check, and use a short UUID when a title is unavailable.
- Correction during preview: The first page version referenced a table wrapper without its expected ID, causing a browser error after loading rows. The wrapper ID was added; the page then showed saved counts, filtered a Python row and opened its supporting-ad panel.
- Checks: Six dashboard model-free checks passed, including a local HTTP POST test with a fake updater. An initial full 65-test NAV run had one Windows access-denied error while replacing a temporary statistics file; the affected test passed on a focused rerun, and the next full 65-test run passed. After the button-route check was added, the full 66-test NAV run passed. Python syntax parsing, JavaScript syntax checking and `git diff --check` passed. The local HTTP preview returned 200 and displayed eleven selected advertisements. No live NAV or model request was made and the update button was not run live.
- Limitation: The UI has not been verified through a live end-to-end update. Saved quotation checks and contact screening do not establish extraction meaning or complete removal of personal data. The eleven selected advertisements do not establish complete market coverage.

## 2026-11-03 - Restore dashboard styling and clarify update result

- Rejected output: Screenshots of the local dashboard showed unstyled browser-default layout. Inspection found that `ui/app.css` contained only the update-details rule; the main styles were missing.
- Correction: Restore the dashboard layout, table and responsive styles. Show “no new skill results” when a completed update publishes none, and distinguish held advertisements in the status. Relabel the updater's broad `reused` count as “resolved without extraction” in the UI, because the counter also includes inactive and nonmatching records.
- Saved result inspected: The dashboard's existing status file reported a `caught_up` run with three feed pages, 980 detail requests, zero extraction requests, zero published results, one blocked candidate and no pending queue. The current index had eleven selected results and one blocked UUID with unknown occupation relevance. This was inspection of saved state, not another update run.
- Checks: Six dashboard model-free tests passed; JavaScript syntax and `git diff --check` passed. The local CSS endpoint returned HTTP 200 with the restored layout rules, and browser inspection showed the grid layout, a bounded table and the revised status text. No NAV or model request was made for this correction.
- Limitation: The selected eleven advertisements remain a small dataset. Their 128 single qualification names have not been fully evaluated for meaning or consistent naming.

## 2026-11-03 - Provisional skill-result corrections

- Rejected output: Source review found independently counted skills within explicit alternatives, individually preferred example technologies, an educational-background group and generic nontechnical labels in selected v2 results. One duty item combined several objects joined by “and.”
- Requested improvement: Apply only source-supported decisions to derived statistics and the dashboard. Keep the original model responses and selected run files unchanged; make every decision conditional on the advertisement version and original item hash.
- Correction: Added 23 provisional item decisions in `reviews/current-v2.json`. The review removes unsupported or out-of-scope rows, preserves explicit alternatives, reclassifies named examples as unclear and splits the combined duty. The summary and dashboard apply this review without fuzzy skill-name aliases.
- Checks: The targeted model-free tests passed (49 tests). A first full 67-test run had one Windows access-denied error replacing a temporary report; the affected test and a subsequent full 67-test run passed. Python and JavaScript syntax checks and `git diff --check` passed. The regenerated summary has eleven distinct selected UUIDs, 119 single applicant-qualification names, thirteen applicant OR groups and 91 other single-mention names. The dashboard calculation matched those report row counts, and all 23 review decisions applied to the current saved versions. A fresh local preview on port 8766 served the revised counts over HTTP 200. No NAV or model request was made.
- Limitation: This is provisional agent review, not approved ground truth or a complete extraction audit. Ambiguous alternative backgrounds, omitted broad competence and skill-name aliases remain unresolved. One selected saved input has a previously identified biographical section; it was not sent to a model in this correction. The prior statistics files were backed up before regeneration.

## 2026-11-03 - Correct provisional review item numbering and stale preview

- Rejected output: Screenshots from port 8765 still showed the earlier 128-name and 12-OR counts. A later inspection found that three provisional review decisions used item positions after earlier removals, so they removed different original items than intended.
- Correction: Kept the older server untouched and opened the corrected local preview on port 8766. Replaced the three wrongly targeted decisions with decisions against the original item numbers. Removed one regulatory-compliance duty that the cited wording did not establish as a technical skill. Added readable expected-skill labels to review decisions and checked them against the immutable original items before applying a correction.
- Checks: The affected synthetic checks passed; a first full 67-test run hit one Windows access-denied error replacing a temporary report, then the affected tests and a second full 67-test run passed. The regenerated report and port-8766 preview show eleven selected ads, 117 single applicant-skill names, thirteen applicant OR groups and 91 other single-mention names. All 24 provisional decisions match the selected saved versions. No NAV or model request was made.
- Limitation: The old port-8765 server still serves its earlier in-memory code until restarted. The corrected counts remain provisional source-review results, not approved ground truth.

## 2026-11-04 - Shared NAV dashboard snapshot and startup

- Requested improvement: Make the selected working results and NAV checkpoint available in a fresh checkout without sharing an OpenAI key or old attempts.
- Correction: The earlier documentation still described eleven selected results and an untested live button. The saved 2026-11-04 button update had thirteen selected results and completed after six feed pages, 1,479 detail requests and two published extractions; README and SPEC were updated to reflect that saved state.
- Outcome: Added a checked shared baseline, restore/start command and model-free restore tests. A database audit found two unused capture rows and one old targeted row that triggered the current contact screen; these were excluded only from the shared copy. The working database was left unchanged. Automatic checks cannot establish that all personal information has been removed.
- Checks: The 77 model-free tests passed with a workspace temporary directory; earlier attempts hit sandbox temporary-directory access errors and one intermittent Windows file-replacement error. Python syntax and `git diff --check` passed. A fresh copy exported from the committed Git contents restored thirteen ads; its local UI served HTTP 200 for the page and data, with thirteen ads, 132 applicant-skill names and fifteen OR groups. The copied checkpoint was in `done` phase with zero pending work. An offline injected discovery call returned `no_updates_found` with no model call. A direct `git clone` test failed while Git's helper process started in this desktop environment; the archive test used the committed Git contents instead. No NAV or model request was made for these checks.

## 2026-11-21 - Frozen NAV evaluation groundwork

- Requested improvement: Preserve the earlier evaluation attempt and create a repeatable fixed-case evaluator before prompt changes.
- Correction: Isolated startup checks exposed a cross-platform review-file line-ending hash mismatch and a SQLite read-only URL failure when a temporary path contained `#`. Review hashing now normalizes line endings without ignoring content changes, and SQLite uses an encoded file URL.
- Outcome: Added a pinned five-case offline replay, deterministic item-level scoring functions and synthetic checks. Replay validated all five saved responses structurally and checked their quotations. It did not calculate extraction accuracy because the complete references have not been jointly approved. No NAV or model request was made.
- Checks: Ten evaluation tests, five shared-data tests, twelve summary tests and four v2 extractor tests passed. A 32-test update run had one intermittent Windows access-denied error replacing a temporary report; a repeat of the same suite passed. Isolated copies of the shared baseline started and replayed the five fixed cases with both LF and CRLF text files, and retained existing data on a second start. The working checkout's `start.py --check-only` reported thirteen existing selected advertisements. Syntax parsing of eight changed Python files and `git diff --check` passed.

## 2026-11-21 - Move first evaluation attempt into history

- Corrected output: The earlier explanation implied Yehya's first-attempt files were in `eval/history/`, but that folder held only an explanatory note.
- Correction: Moved the original scorer, gold CSV, labeling rules and three saved result files into `eval/history/first-attempt/` without changing their contents. Moved the explanatory note into the same folder and updated active replay paths and documentation. Historical text inside the original files still names their old locations.
- Checks: SHA-256 hashes of all seven moved files matched before and after the move. Ten model-free evaluation tests passed; fixed-case replay still validated five of five saved responses. `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Tighten approved-reference checks

- Corrected output: An audit found that the new reference checker accepted extra item fields, non-qualification mentions labelled required or preferred, and duplicate reference items after an approved alias was applied. The replay command would also have said approved accuracy was unavailable after approved cases were scored.
- Correction: Require exactly the six v2 item fields, enforce unclear classification for non-qualification mentions, apply approved aliases before checking reference duplicates, and report whether approved cases were scored. Clarified the evaluation task status. The five real references remain unapproved.
- Checks: Thirteen model-free evaluation tests passed, including synthetic checks for the rejected reference cases and the approved-case CLI message. Offline replay validated five of five saved responses and reported no approved accuracy score. Syntax parsing of the three changed evaluation Python files and `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Simplify the reference labeling guide

- Requested improvement: The draft v2 labeling guide was difficult to understand and too long for joint advertisement review.
- Correction: Rewrote it as a shorter five-step checklist covering technical scope, mention type, classification, alternatives, exact evidence and whole-advertisement approval. It remains a draft for Rami and Yehya and is not sent to the extraction model.
- Checks: The revised file is 497 words, UTF-8 without a BOM or trailing whitespace. Its three local links resolve. `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Keep reference labeling independent of model output

- Corrected output: The shortened guide told reviewers to compare their draft list with the model answer, which could bias the expected answer. The review index also left room to use the model response as a reference.
- Correction: Both instructions now say to build and approve a complete reference from the prepared advertisement without inspecting the model answer. The evaluation program performs the comparison afterward; no manual row-by-row comparison is required. Historical first-attempt files were left unchanged.
- Checks: The two links in the guide resolve, and `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Record human NAV reference-review decisions

- User clarification: Rami said Yehya agrees with his decisions and no separate wait for Yehya is needed. The earlier assistant replies had treated a separate Yehya reply as pending.
- Outcome: Recorded the five agreed draft items and exclusions for the first frozen advertisement, plus the C#/.NET and Azure decisions for the second advertisement, in `eval/cases/review-progress.md`. The Azure note records that individually named services are `candidate_qualification` items with `unclear` requirement status, not optional skills. The second advertisement remains partially reviewed; no approved reference JSON or model comparison was created.
- Checks: The recorded quotations were present in the respective frozen prepared texts, the note contained no email-like string or trailing whitespace, and `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Refine Azure-advertisement reference draft

- Corrected output: Rami replaced the assistant's proposed `Backend expertise` name with `Backend development` and chose one combined `Relational databases (SQL)` item rather than splitting that phrase.
- Outcome: Recorded these choices and the other agreed required qualifications for advertisement `2f62e300-c698-4f53-8510-db90b1692cb9` in the partial review note. The note also retains an evidence check for the action word in `Backend development`; the reference JSON has not been frozen or scored.
- Checks: All six newly recorded qualification quotations occurred in the frozen prepared text. No NAV or model request was made.

## 2026-11-21 - Review preferred technologies in Azure advertisement

- Corrected output: Rami changed the assistant's proposed `Orchestration` name to `Container orchestration` and changed the five parenthesized container tools from individually `unclear` to `preferred`.
- Outcome: Recorded the agreed preferred-qualification items and the governing-heading reasoning in the partial review note. Clarified the draft labeling guide: a preferred heading may support preferred named tools in a desired-knowledge bullet without requiring every tool; a broad required qualification does not automatically require each named component. The Azure service decisions remain unchanged. No reference JSON was approved or scored.
- Checks: The preferred heading and four quoted source passages were present in the frozen prepared text. The changed Markdown files had no trailing whitespace or UTF-8 BOM, and the review note had no email-like text. `git diff --check` passed. No NAV or model request was made.

## 2026-11-21 - Finish the second advertisement's draft review

- Corrected output: The assistant continued to describe the Azure advertisement review as incomplete after Rami had agreed to the qualification items. Rami then agreed to include XR as an unclear work-context mention and to use one continuous passage including the Backend Developer role and backend-experience qualification as evidence for `Backend development`.
- Outcome: Recorded both decisions and marked the second advertisement's item decisions complete in the review note. Clarified the draft labeling rule so a title may explain an already stated qualification without creating a skill from the title alone. No machine-readable reference JSON was frozen or scored.
- Checks: The continuous backend passage and XR quotation occurred exactly in the frozen prepared text. The review note had no email-like string or trailing whitespace, and `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Record third advertisement reference decisions

- Requested improvement: Complete the independent source review for the third frozen advertisement before comparing with a model answer.
- Outcome: Rami chose to exclude the education/background route, keep `Modbus RTU (RS485)` together, retain `Modbus TCP` separately, and include five distinct inverter, battery and sensor configuration/integration duties as unclear work duties. The agreed preferred VPN items, four-alternative OR group, other technical duties and exclusions were recorded in `eval/cases/review-progress.md`. The required Sensor integration qualification was not duplicated as an unclear duty. No reference JSON was frozen or scored.
- Checks: The frozen input byte hash matched the shared baseline manifest. All seven recorded evidence passages and the qualification heading occurred in the prepared text. The review note had no email-like text, trailing whitespace or UTF-8 BOM, and `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Record fourth advertisement reference draft

- Corrected output: Rami changed the assistant's proposed `Interest in ICT` label to `ICT`; `interest_only` records how it is mentioned. Rami also asked that the action–object splitting convention be made explicit.
- Outcome: Recorded ten draft items for advertisement `a1613f9c-1757-4351-81ea-1d0e5246fbd3`: nine unclear work duties and one unclear ICT interest. The draft records the exclusions and explains that the eight action–object splits are an annotation choice. It remains pending Yehya's review; no approved reference JSON was frozen or scored.
- Checks: The frozen input byte hash matched the shared baseline manifest. All four recorded evidence passages appeared in the prepared text, the draft table contained ten items, and the note had no email-like string. `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Refine fifth advertisement reference draft

- Corrected output: Rami rejected a two-member technical OR group that omitted the nontechnical collaboration alternative, changed the platform duty from ten action–platform labels to seven activity/target items, chose `Network code` over `Network programming`, and identified overlap in the proposed codebase labels.
- Outcome: Recorded the complete mixed three-way condition and its out-of-scope member in `eval/cases/review-progress.md`. The current reference format and scorer cannot mark one alternative out of scope, so the advertisement remains unapproved. Recorded the seven duty items and the unresolved codebase and technical-personality overlap decisions. Clarified the draft labeling rule against automatic action–target multiplication and reduced OR groups. No model output or reference JSON was changed.
- Checks: The frozen input byte hash matched the shared baseline manifest; four table quotations and the complete OR passage occurred in the prepared text. The new review note had no email-like text or trailing whitespace. No NAV or model request was made.

## 2026-11-22 - Select four approved NAV evaluation references

- User clarification: Rami accepted the recommendation to score the four complete cases first, leave the fifth mixed OR case outside the accuracy score, and said Yehya agrees with his decisions. Yehya's concurrence is recorded as reported by Rami, not as an independent review observed by the agent.
- Outcome: Created a versioned reference JSON with 61 items for the first four fixed cases, pinned its line-ending-stable hash in the case manifest, and kept the fifth case unapproved. The fifth-case note now keeps Codebase comprehension without separate overlapping development/improvement items and distinguishes the general UX and architecture statements from later specific technical abilities. Updated evaluation documentation. The saved model responses and application statistics were not changed.
- Correction: The first evaluation test run failed because two tests assumed the suite had no approved cases. Updated their synthetic statuses and assertions to reflect four approved cases; the second run passed all 13 tests.
- Checks: All four references passed the deterministic reference validator and matched their normalized frozen input hashes. Offline replay validated 5/5 saved outputs and scored 4/4 approved cases; 30 of 58 model items matched 61 reference items (item-name/group precision 0.517, recall 0.492, F1 0.504), with five classification errors among matches. `python harness/start.py --check-only` reported 13 existing selected advertisements. `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Keep all three required alternatives in fifth case

- Corrected output: The assistant treated development-team collaboration as outside scope and said the existing format could not represent the advertisement's mixed OR condition. Rami clarified that the employer accepts any one of the three named experiences and wants all three shown as sought alternatives, without claiming an applicant needs all three.
- Outcome: The draft guide now includes collaboration explicitly tied to technical development work while continuing to exclude generic teamwork. The fifth-case review note records one three-member `required` `any_of` qualification: VR optimization, Network code, or cross-disciplinary collaboration in development teams. The fifth advertisement remains unapproved because its full item list still needs review; the four-case replay score and model output were not changed. Updated the manifest note and documentation to remove the obsolete format-blocker claim.
- Checks: A synthetic three-member reference item passed the existing checker, and its full quotation matched the frozen input. All 13 evaluation tests and `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Prepare complete fifth-case reference draft

- Requested improvement: Finish the source-based answer for advertisement `b69f0bbd-082e-4d36-baae-456fb23ca32a` while preserving the current model response as an evaluation baseline for later prompt improvements.
- Outcome: Added a 29-item proposal covering the complete prepared advertisement in `eval/cases/review-progress.md`, including the agreed three-member required OR group, the seven platform-duty items, precise technical abilities from the personality section, and stated exclusions. The proposal remains pending Rami's whole-answer review; no approved reference, dashboard selection, model output or extraction prompt was changed.
- Checks: The frozen input byte hash matched the shared baseline manifest. All 15 listed evidence passages and the complete three-way OR passage occurred exactly in the prepared text; the table contained 29 items and no email-like text. `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Approve fifth reference and replay frozen answers

- User decision: Rami approved the complete 29-item source-based answer for advertisement `b69f0bbd-082e-4d36-baae-456fb23ca32a` and had previously reported Yehya's agreement. This did not authorize a prompt change or model request.
- Outcome: Added the fifth case to the pinned approved reference and kept its saved model response unchanged. Offline replay scored all five fixed development cases. Recorded a separate fifth-case baseline comparison: the saved answer split the required three-way OR condition into two unclear singles and omitted the collaboration alternative. It also combined two software duties and changed a source-supported building action to design. Naming and granularity differences were separated from confirmed interpretation errors. The dashboard selection and statistics were not changed.
- Checks: All five references passed preflight; the fifth has 29 items and two OR groups. Replay validated 5/5 saved outputs and exact item-name/group scoring matched 47 of 83 model items to 90 reference items (precision 0.566, recall 0.522, F1 0.543). The fifth case matched 17 of 25 model items to 29 reference items. All 13 evaluation tests passed, the reference hash matched the manifest, the reference had no email-like string, and `git diff --check` passed. No NAV or model request was made.

## 2026-11-22 - Add bounded fresh-model evaluation command

- Requested improvement: Add a repeatable fresh-model evaluation path for the five approved, frozen development cases, to use later when comparing prompt versions.
- Outcome: Implemented `eval/run.py --mode model` with an explicit prompt hash, five-case request preflight, input/output/time/cost bounds, sequential requests without retries, per-case saved requests and responses, validation, deterministic scoring and partial-run records. Updated the evaluation guide, README and task status. The application result index and extraction prompt were not changed.
- Checks: OpenAI's official Luna model page listed standard text pricing of $0.10 per million input tokens and $0.50 per million output tokens on this date. Seventeen model-free evaluation tests passed, including mocked five-request and API-failure runs. A syntax parse of the two changed Python files passed. The CLI rejected a four-request limit for five selected cases with exit code 1. No NAV or model request was made.

## 2026-11-22 - Add one-command offline evaluation suite

- Requested improvement: Make the exam test set explicit and runnable in one offline command, with typical wording examples, boundary cases and an input the workflow must reject.
- Outcome: Added a pinned case catalog and `eval/run.py --mode offline-suite`. It replays five approved real-advertisement results and separately checks five synthetic cases for OR grouping, heading context, duty classification, quotation boundaries and rejection of a contact-uncertain raw input. The report records expected and actual synthetic outcomes without adding them to real-ad accuracy. Updated the README, evaluation guide and Task 005. No prompt, saved model response, selected dashboard result or statistics was changed.
- Correction: The first expanded test run found that the run record reported a raw-byte catalog hash while the manifest used the line-ending-stable text hash. Changed the record to use the pinned text-hash rule; the next run passed.
- Checks: The offline command exited 0 with 5/5 real responses validated and 5/5 synthetic checks passed. The real-ad item score remained 47 matches among 83 model items and 90 reference items. Twenty evaluation tests passed, including fresh-checkout LF and CRLF runs of the offline command; 32 update-workflow tests and four extractor-format tests passed. Syntax parsing passed. The selected index and statistics summary SHA-256 hashes were identical before and after the offline run. No NAV or model request was made.

## 2026-11-22 - Improve evaluation report readability

- Requested improvement: Create a new reporting task and make each evaluation run produce one dated, easy-to-read report covering all tested advertisements, with separate synthetic results and an index of runs. Rami approved the design and then clarified that the task brief should have been shown before implementation; he asked the agent to continue.
- Outcome: Created Task 006 and a shared report renderer for replay, offline-suite and fresh-model records. New reports explain overall and per-ad item counts, classification and mention-type differences, unmatched OR groups, failures and limits in plain English. Added `out/evaluation/index.md` linking only run folders still present. Existing extraction prompts, references, scorer rules, dashboard selection and statistics were not changed. Word export remains optional and was not generated.
- Correction: Three evaluation assertions initially failed because they expected wording from the previous report layout. Updated them to check the new wording; the next evaluation test run passed.
- Checks: After Rami removed older local reports, the offline suite ran once and exited 0, validating 5/5 saved real responses and passing 5/5 synthetic checks. Its report recorded 47 matches among 83 model items and 90 reference items, with per-ad sections and a UTC generation time. The index linked the one remaining run. Twenty-two evaluation tests, 32 update-workflow tests and four extractor-format tests passed; syntax parsing and `git diff --check` passed. The selected index and statistics summary hashes were unchanged before and after the run. No NAV or model request was made.

## 2026-11-22 - Complete five-case qualitative evaluation review

- Requested improvement: Explain the saved model-versus-reference differences for all five approved development advertisements without changing the original generated evaluation run.
- Outcome: Added `out/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md` and linked it from the evaluation run index. The review quotes the frozen prepared inputs, lists all 83 saved model items and 90 approved reference items, separates naming and grouping differences from interpretation errors, and explains the mixed technical/nontechnical three-way OR condition in the fifth advertisement. The original report, record, saved outputs, approved references, scorer and extraction prompt were not changed.
- Checks: All five prepared-input and result-file byte hashes matched the original run record. The reviewed report has five case sections, five model inventories and five reference inventories containing 173 items in total; its local links and the index links resolve. The original report, record, reference and scorer hashes remained unchanged. No NAV or model request was made.

## 2026-11-22 - Share the reviewed evaluation baseline

- Corrected output: The assistant left the completed reviewed report only under Git-ignored `out/`, so a partner cloning the repository would not receive it. Rami said it should not be ignored.
- Correction: Added a screened repository copy under `docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/`, including the reviewed report, the original generated report and its run record. Linked the reviewed copy from README. Kept runtime `out/` ignored and did not change the original run, scores, references, or scorer.
- Checks: The three shared files contained no email-like string or detected credential/contact marker. The copied generated report and record matched the original byte hashes. Local links in the tracked reviewed report resolved. No NAV or model request was made.

## 2026-11-22 - Revise the extraction prompt for a later fixed-case test

- Requested improvement: Rami approved the supplied general extraction-prompt draft with two edits: narrow the mixed OR exception to a specific practice tied to technical development, and require one continuous quotation covering the introductory condition and every alternative.
- Outcome: Updated `harness/prompts/extract_skills.txt` with those edits. Its new UTF-8 SHA-256 is `efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1`. Updated the current bounded model command in `eval/README.md` and identified the earlier command in Task 005 as the frozen baseline version. The baseline responses, references, schema, model settings and scores were not changed.
- Checks: The new prompt passed the model-free five-case preflight with an estimated maximum cost of $0.029749 under the configured $0.05 limit. All 22 evaluation tests and four extractor-format tests passed. `git diff --check` passed with a line-ending warning. No NAV or model request was made.

## 2026-11-22 - Review the revised-prompt five-case evaluation

- Observed run: The bounded fresh-model command attempted all five approved development advertisements once with prompt SHA-256 `efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1`. Four responses passed local validation; the ICT-support response failed because item 8 used `single` with two skill names. No request was retried. The four scored cases had 50 exact item/group matches among 84 model items and 80 reference items (precision 0.595, recall 0.625, F1 0.610). The run used 13,315 input and 16,494 output tokens, with a usage-based estimate of $0.0095785.
- Review outcome: Added a [reviewed report](evaluation/2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md) comparing the revised answers with the unchanged approved references and the first run. On the same four scored ads, exact F1 changed from 0.590 to 0.610; the fifth revised answer was not scored. The review records the corrected Azure-tool labels and preserved three-way OR condition, the excluded education/background group newly extracted in the energy ad, the invalid relationship in the ICT-support ad, and remaining naming, granularity and reference-scope questions. Updated README and Tasks 005–006 to reflect the actual live test; corrected the previous mocks-only claim in `eval/README.md`. It does not repair model output or change references or scorer rules.
- Sharing and checks: Copied only the generated report and run record into the new screened `docs/evaluation/` folder beside the review; their byte hashes match the original local files. The reviewed report's four relative links resolve. A targeted email/contact/credential-pattern scan found no matches in those three shared files. `git diff --check` passed with a line-ending warning. No additional NAV or model request was made during this review.

## 2026-11-22 - Make the revised evaluation replayable offline

- Packaged five screened original answer strings with the response metadata used by the validator. The first local check caught missing response ID and usage in the replay envelope. Added the original values and compared scorer index pairs in their JSON representation.
- The documented offline check reproduced four validated responses, the original item 8 rejection, and 50 matches among 84 model items and 80 reference items. No new model or NAV requests were made.

## 2026-11-22 - Final prompt test

- Clarified the exclusion of education and equivalent-background routes and added a final count of names in each single item. All 22 local evaluator tests passed.
- Five fresh requests produced four validated responses. ICT passed and the education list disappeared, but two energy-ad items quoted a passage with extra words. The Azure preferred labels and the complete game-ad OR condition were preserved. No case was retried.
- The [final review](evaluation/2026-11-22_19-41-04_UTC-555f6602/reviewed-report.md) links the tested instructions, answers and original scores. On the same three validated ads, exact F1 moved from 0.578 to 0.571.
