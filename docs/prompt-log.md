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
