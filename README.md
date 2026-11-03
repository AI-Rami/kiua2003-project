# kiua2003-project

A two-person KIUA2003 project exploring an agentic workflow.

This project includes a NAV saved-input extraction skeleton, resumable NAV discovery and edited-text capture, and a bounded incremental update command that connects discovery, extraction and offline statistics. See [SPEC.md](SPEC.md) for the product plan and [AGENTS.md](AGENTS.md) for working instructions.

- `tasks/`: task briefs with owner, reviewer, acceptance criteria, and status. The two people can alternate roles.
- `harness/`: workflow stages, prompts, tools, and execution code.
- `eval/`: evaluation cases, expected outcomes, and scoring criteria; changes require permission.
- `fixtures/`: saved real public inputs without personal data for reproducible offline runs. Record source, retrieval date, and permission/license alongside future inputs.
- `docs/meetings/`: decisions and next actions using Person A and Person B.
- [docs/prompt-log.md](docs/prompt-log.md): corrected or rejected agent output and lessons.

The earlier MET Norway exercise is in `harness/probe.py`; its checker is `eval/check_probe.py`. The NAV walking skeleton is separate.

## Compulsory 2 output layout and incremental update

The current deliverables include a project plan, saved-input walking skeleton, automatic discovery-to-statistics command, and a local web dashboard. Extensive prompt optimization and extraction evaluation are paused until after Compulsory 2. The update command passed isolated local checks. One bounded live NAV run on 2026-11-02 exercised feed continuation and queue persistence, then stopped at its two-page limit before detail discovery or model extraction. The dashboard has been checked locally with saved results and a mocked update; its button has not been used for a live end-to-end run.

| Path | Purpose |
| --- | --- |
| `out/nav_discovery/` | Active SQLite NAV feed checkpoint, version metadata, edited captures and backups. |
| `out/current/index.json` | **Sole application statistics selection:** at most one validated v2 model extraction per eligible UUID, plus pending, stale, failed and blocked statuses. Existing selected runs are under `out/current/<uuid>/`; newly published versions are under `out/current/<uuid>/versions/<content-hash>/`. Selection does not imply human approval or semantic accuracy. |
| `out/statistics/` | Current prototype tables generated only from `out/current/index.json`. All skill rows are present in `summary.md` and `summary.json`. |
| `out/ui/` | Ignored local dashboard status from the latest button-triggered update, when one has run. The page itself is in `ui/`. |
| `archive/comp2-generated-2026-11-02/` | Historical extraction runs, batch indexes, evaluation, review records and old summaries, outside active application output. The archived MET probe has a compatibility copy at `out/probe.json` because `eval/check_probe.py` expects that path. |

Selection and archive decisions are in [the Comp2 migration manifest](docs/comp2-output-migration.md); the [earlier cleanup manifest](docs/output-cleanup-manifest.md) records the previous stage and is historical. The active collection checkpoint is `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3`; its companion `summary.json` records the last observed feed end. The standalone discovery command can still poll that end with:

```powershell
python harness/nav_discover.py --mode poll --db out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3 --max-pages 1000 --max-details 2000 --max-seconds 1200
```

The incremental command below resumes the saved cursor; it does not restart from August. Its first bounded live run advanced the cursor by two pages and left processing queued because the feed scan had not reached its current end. The latest frozen-prompt evaluation reviewed nine ads; one known problematic capture was blocked rather than processed. A second targeted review record has no usable cleaned capture. Both remain blocked and excluded from current statistics. The older ten-ad summaries and the frozen evaluation remain archived for the postponed table investigation.

### One-command catch-up update

From the repository root, with `KIUA2003_API` available to the Python process, run the normal catch-up command:

```powershell
python harness/nav_update.py --db out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3
```

`run_update()` in `harness/nav_update.py` is the same reusable workflow entry point a future “Run update” button can call. The saved database is currently in `scan` phase after the two-page verification, with an advanced cursor and 1,440 queued UUIDs. This command resumes that position; it does **not** restart from August or discard the queue. When a prior scan has finished, it polls the saved final page using conditional headers. [NAV documents](https://navikt.github.io/pam-stilling-feed/) that the current feed end has both `next_url` and `next_id` set to `null`; it is a polling point, not a permanent historical snapshot. The collector validates each returned next URL, the overlapping page boundary, and forward cursor movement. A repeated or non-advancing cursor stops with saved progress rather than looping.

Normal mode has no two-page test default. Its operational ceilings are **1,000 feed pages, 2,000 detail requests, 20 model requests and 1,200 seconds per invocation**. These are safeguards, not claims that one invocation will always catch up. `--max-pages` is optional and can impose a smaller test limit; `--max-details`, `--max-extractions` and `--max-seconds` can also be reduced for a test. For example, the earlier bounded verification used `--max-pages 2 --max-details 50 --max-extractions 5 --max-seconds 600`. A ceiling or interruption yields partial progress; run the **same normal command** again to continue. Feed-page and detail progress is printed during a long run. The command distinguishes a reached feed end from remaining detail or extraction work, and reports `caught_up` only after the saved phase is done and the processing queue has no unfinished entries. `no_updates_found` means a completed poll found no work.

The workflow collects changed feed events, requests current details and applies the existing active IT + explicit Innlandet selection and contact cleaner. Feed events, pending processing work and the page cursor are committed in one SQLite transaction. Processing also checks previously pending work. Requests are sequential with existing per-request timeouts and no automatic network retries. A detail HTTP 404 is recorded as unavailable content for that feed version and does not repeatedly block the next candidate; a later change to that UUID can be checked again. Other NAV HTTP or network failures stop the invocation with its checkpoint retained. Model failures have at most two attempts per cleaned-text version across separate invocations by default (`--max-attempts 2`).

Intentional UUID blocks remain in place until explicitly resolved. Both original intentional blocks passed targeted cleaner-version-3 checks and extraction on 2026-11-02; neither remains blocked in the current index. Other blocks record the feed version (its order) and a sanitized reason in `out/current/index.json` and SQLite `processing_blocks`: the same version is skipped, while a newer feed event is assessed again, including its cleaning outcome. New captures whose cleaning is uncertain or whose required fields are unavailable are blocked before any model request. The automatic input gate requires a capture produced by cleaner version 3 with `auto_contact_checked` state, a matching text hash, and no remaining email, phone or recognized contact wording. Older captures marked `pending_human_review` are not automatically accepted for new extraction. A checked state is not human approval and cannot prove that every possible contact detail was detected. An unchanged cleaned-text hash reuses the current extraction. A changed eligible ad uses the existing `gpt-6-luna` prompt, v2 schema, medium reasoning, 8,192 output-token allowance and local validator. An attempt keeps its credential-free request, original API response and diagnostics in `out/nav_discovery/<run-id>/processing/<uuid>/<content-hash>/attempt-N/`. A validated version is published under `out/current/<uuid>/versions/<content-hash>/`, then atomically selected in `out/current/index.json`. Only selected `current` entries feed `out/statistics/`; archived and failed runs are not scanned. Existing selected results are retained when an update fails.

If a known UUID has changed but its replacement is still pending, failed or blocked, its previous result stays available as `previous_result_path` while the index marks the entry `stale`. Stale entries are **excluded** from statistics until a validated replacement is published; the command does not silently count an older version as current. An inactive feed event or detail changes the last-known activity status without deleting a previously selected historical extraction. The current tables include historical selected results, report last-known activity counts, and do not claim active-only statistics. Activity observations are not live status checks. `summary.json` includes a hash of the source index; a later update repairs statistics if interruption occurs after an index change but before regeneration. A future UI should verify that hash before displaying the tables.

The command reports discovery progress, each extraction/publish/failure, and a final `caught_up`, `partial_pending`, `processing_failed`, `discovery_failed` or `no_updates_found` status. A no-update run makes no model request and retains the existing results. A nonzero exit status signals a request or processing failure; bounded pending work remains in SQLite for the next invocation. Authentication, rate-limit or network failures stop further model requests in that run. A saved model response is validated and published after a restart without repeating its request. Review `out/nav_discovery/<run-id>/summary.json`, the SQLite `processing_queue`, `out/current/index.json` and `out/statistics/` for state and outputs. Reaching the feed end covers the feed events available through that endpoint at that moment; it does not establish relevant-ad coverage while details or extractions remain unfinished. No human meaning review is automated, and structural validation does not establish extraction accuracy. Remote eligibility, historical publication-period aggregates and complete market coverage remain outside this command.

### Local dashboard

From the repository root, start the server with one command, then open the printed local address:

```powershell
python harness/nav_dashboard.py --port 8765
```

The dashboard binds only to `127.0.0.1`. Reading saved results needs no API key. **Run update** calls the same `run_update()` workflow as the command above, so that button needs NAV access and `KIUA2003_API` available to the server process. It uses the command's normal operational limits, saved checkpoint and pending queue. It prevents a second button-triggered run in that server process. The page keeps the prior selected results visible while an update runs and displays a plain-language final status; interrupted work remains in SQLite. The latest dashboard update status, when present, is saved under ignored `out/ui/last_update.json`. Stop the server with Ctrl+C.

Tables read only the selected validated v2 results from `out/current/index.json` and their linked artifacts; they do not scan `out/nav_runs/` or the archive. Publication-period, last-saved-status and skill-search filters recalculate the counts from those saved records without NAV or model calls. Custom dates are inclusive; records without a saved publication date are excluded from period filters and reported. “Active” and “Inactive” mean status at the last saved NAV check. Every count uses distinct advertisement UUIDs; applicant `OR` groups remain separate, and other technical mentions have their own table. Clicking a row shows saved supporting quotations, available titles (otherwise a short UUID), publication date, status, classification and NAV source link. The page withholds a quotation if the local contact screen detects a contact pattern in that quotation.

The dataset currently includes nine earlier-cleaner captures accepted for this project and two newer automatically contact-checked captures. Neither state proves that all contact data was removed. The current index also records blocked, stale, failed and pending results; only `current` validated results appear in the tables. Structural validation does not establish skill-extraction accuracy or completeness. The page's date filters describe selected ads only and are not weekly, monthly or yearly market-coverage statistics. The local dashboard was not tested with a live button-triggered update in this build.

## NAV saved-input walking skeleton

Requires Python 3 and internet access with OpenAI API credits. Set the process environment variable `KIUA2003_API` to your API key before the saved-input run; do not put a real key in project files. The program never writes the key or Authorization header. In PowerShell, set it privately for the current process, then run:

```powershell
python harness/nav_skeleton.py --mode dry-run
python harness/nav_skeleton.py --mode saved-input
```

Use `--input path/to/ad.json` with either command for another compatible saved advertisement. The default is the edited fixture `fixtures/nav_ad_01.json`. Dry run only prints the plan and limits; it does not read or validate the input, require a key, make a network call, or change files. Saved-input mode automatically (1) reads the saved advertisement and prepares its entire HTML description as readable text, (2) calls `gpt-6-luna` through OpenAI's Responses API to extract technical skills, and (3) validates the response before creating the JSON result and Markdown report.

For an edited review export with `cleaned_description`, supply `--capture` explicitly. This mode sends the entire saved plain text to the same extractor and validator without another HTML conversion or cleaning step. For the selected Innlandet IT capture:

```powershell
python harness/nav_skeleton.py --mode dry-run --capture out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/review_exports/2026-11-01_14-02-32_UTC-e1de2335/2ed29047-97e4-4168-adb9-8da83e968c94-nav-contact-clean-v2.json
python harness/nav_skeleton.py --mode cleaned-capture --capture out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/review_exports/2026-11-01_14-02-32_UTC-e1de2335/2ed29047-97e4-4168-adb9-8da83e968c94-nav-contact-clean-v2.json
```

The export is edited data pending human review. It has no title field, so the result records the title as unavailable. The report and result retain its UUID, source link, cleaner version, retrieval provenance and review state. No NAV request is made. A successful structure and quotation check does not establish extraction accuracy or personal-data clearance.

New extraction runs use **format v2**. Each item has `skills`, `relationship`, `classification`, `mention_type`, `skill_evidence` and nullable `classification_context`. `mention_type` distinguishes `candidate_qualification`, `work_duty`, `work_context` and `interest_only`. A qualification may be `required`, `preferred` or `unclear`; duty, context and interest-only mentions are `unclear` unless a separate applicant qualification establishes competence, in which case that qualification supplies the item's evidence and mention type. Interest alone is never existing competence. A `single` item contains exactly one skill; `any_of` preserves explicit alternatives without making each mandatory.

The two quotations are separate, exact continuous passages from the prepared text. The context quotation may be null. Local validation checks both quotations literally and checks structure, relationship cardinality and allowed mention/classification combinations. It cannot prove that a matching heading governs a particular skill, nor establish extraction accuracy or completeness; review those meanings separately. Earlier v1 runs retain their original `evidence` field and are not rewritten. New `result.json`, `validation.json` and `report.md` identify format v2.

Requests retain the 20,000-byte serialized input bound, one-call limit and 60-second timeout. The output allowance is 8,192 tokens, including reasoning tokens. Before a request, the command prints a planning cost estimate using request bytes as a proxy for input tokens and the full output allowance. At the input byte bound, the dated rates in the task brief give about **$0.006096**; this is not a guaranteed billing cap because request bytes are not an exact count of billed input tokens. Successful runs calculate a separate cost estimate from actual reported token usage.

Each new extraction attempt still writes a unique staging folder at `out/nav_runs/<run-id>/`; creating a run does **not** select it for statistics. Historical attempts from this migration are under `archive/comp2-generated-2026-11-02/nav_runs/`. New run IDs use the UTC date, time, and validated advertisement UUID, for example `2026-10-31_08-23-49_UTC_ad-8119dbb1-530f-4307-9ee0-e030c2b8e581`; the run ID matches the folder name. A run fails without overwriting anything if that folder already exists. `result.json` and `report.md` show a successful output; `prepared_ad.txt`, credential-free `request.json`, original `response.json`, and `validation.json` support review. A failed run has no successful result or report. Saved source status is not a live status check.

Extraction accuracy and completeness remain to be evaluated against a human-reviewed reference. The standalone saved-input command accepts one explicit capture. The incremental command above automatically selects newly captured eligible inputs and refreshes small-sample statistics; the local dashboard displays them. Full market statistics remain planned.

## Offline statistics from selected current results

Run this model-free command from the repository root:

```powershell
python harness/nav_skill_summary.py
```

The command reads the explicit selection in `out/current/index.json` and the provisional, version-checked source review in `reviews/current-v2.json`. It rejects duplicate UUIDs, unsafe selected paths, mismatched input hashes, prompt identities, run identities, failed validation and malformed v2 items before writing `out/statistics/summary.json`, `summary.md` and `advertisements.md`. It never scans archived run folders or selects by modification time. A failed validation leaves the existing statistics files in place. The index currently has eleven selected model extractions and one blocked record; blocked, failed, stale and pending entries never enter the count. The generated tables are a small-sample prototype rather than approved skill statistics. The review changes derived counts only; original model results remain unchanged. A decision is skipped if its advertisement version changes. Unresolved interpretation and skill-name aliases require human review.

The readable report now leads with **single applicant qualifications**, counted by distinct advertisement UUID and required/preferred/unclear classification. Its next table keeps applicant `OR` choices as whole groups, without counting every alternative as independently mandatory. Separate tables show technical mentions in duties, work context and interest-only wording; these are mentions, not applicant requirements. A UUID counts once per row and classification, and each row's total is the union of UUIDs across its columns. The structured JSON retains the earlier broad count arrays for traceability, but the new qualification and other-mention arrays are the intended table sources. Skill names remain as saved except for explicit provisional review decisions. No fuzzy aliases are merged.

The advertisement index now displays publication dates taken from each selected result's saved capture provenance and job titles when available. On 2026-11-03 a bounded title-only NAV detail lookup added display titles for four older selected ads without changing their extraction results; six of eleven selected ads now have titles and five remain "Title unavailable." Future detail discovery stores title metadata, and the incremental updater carries a saved title into new results without adding it to the skill-extraction prompt. The summary shows how many selected ads have a valid publication date and their date range. This range is **not** NAV collection-period coverage; it cannot establish that all ads published between those dates were collected. Weekly, monthly and yearly views remain planned. The older v1 mechanical and corrected summaries, review decisions and frozen-prompt evaluation remain under `archive/comp2-generated-2026-11-02/` as development evidence.

## Bounded NAV metadata collection

Requires Python 3 and access to NAV's public experimental token and change-feed API. No OpenAI key or model call is used. The collector is separate from `harness/nav_skeleton.py`.

```powershell
python harness/nav_collect.py --mode dry-run
python harness/nav_collect.py --mode collect --since 2026-10-24T00:00:00Z --max-pages 2 --max-details 50
```

Supply `--since` explicitly for collection as an ISO-8601 UTC date (`YYYY-MM-DD`, interpreted as midnight UTC) or timestamp ending in `Z` or using `+00:00`. The example date is illustrative; choose the date for the intended run. The limits default to two feed pages and 50 distinct advertisement detail requests and must be positive. Each request has a 30-second timeout and no automatic retry. Dry-run prints the planned stages and limits; it makes no network request, reads no credentials, and creates no files.

The collector follows NAV's returned feed-page links. Within each fetched page, it groups feed entries by advertisement UUID and uses the documented `date_modified` change timestamp to select the newest entry. It requests a detail only when that entry is ACTIVE, and requests each UUID at most once per run. If an entry for a UUID lacks a valid timestamp, or equally recent entries conflict, the collector skips that UUID rather than guessing its state. This resolves duplicates within an inspected page; unread pages may contain later changes. A detail qualifies only if it is still ACTIVE, a work location lists county `INNLANDET`, and an occupation category lists level1 `IT` (trimmed, case-insensitive comparisons). Any Innlandet location suffices for a multi-location ad. A definite false condition makes the detail a nonmatch even if the other condition is unknown; otherwise an unknown condition makes relevance unknown. Inactive details have a separate count. No title keywords, remote-only assumption, or extra occupation mappings are used.

Each run creates a unique `out/nav_collection/<run-id>/` directory. `matches.json` contains only selected advertisement metadata: UUID, status, county and municipality, occupation levels, publication and update dates, and a source link when NAV supplies one. `summary.json` records date, request limits and actual counts, selection outcomes, failures, and why the run stopped. Its `nonmatch_reasons` distinguish outside Innlandet only, non-IT only, both false, and either false condition paired with an unknown condition. Its `unknown_reasons` distinguish invalid status or content from one or both unknown selection conditions. Each detail contributes to exactly one reason count, so reason counts do not overlap and each group sums to its outcome total. Each page summary also gives its earliest and latest valid `date_modified` timestamps in UTC, counts of missing and invalid timestamps, and counts of UUIDs skipped because recency was unusable or ambiguous. Raw responses, tokens, descriptions, contacts, employer details, and street addresses are not saved. A failed run writes a failure summary without a matches file. Zero matches is a valid result.

This is a **bounded preview of changes since the chosen date**. It is not a scan of all active advertisements, a complete historical dataset, or an incremental synchronization checkpoint. It does not extract skills, store a persistent database, calculate statistics, or update a dashboard. See [tasks/003-nav-collection.md](tasks/003-nav-collection.md) for scope and checks.

## Resumable NAV availability discovery

`harness/nav_discover.py` is a separate, standard-library investigation command. It starts at an explicit UTC date, saves feed-entry metadata in SQLite, and continues until NAV's current feed end or a session limit. Only after reaching the current end does it request details for distinct UUIDs whose latest scanned feed status is `ACTIVE`. It checks each detail's current status and stores location, occupation, dates, source metadata, and whether the description contains readable text. For selected IT ads it can also save edited, cleaned text captures. Raw descriptions and contact details are not saved.

```powershell
python harness/nav_discover.py --mode start --since 2026-08-01T00:00:00Z --max-pages 1000 --max-details 2000 --max-seconds 1200
python harness/nav_discover.py --mode resume --db out/nav_discovery/<run-id>/state.sqlite3 --max-pages 1000 --max-details 2000 --max-seconds 1200
python harness/nav_discover.py --mode poll --db out/nav_discovery/<run-id>/state.sqlite3 --max-pages 1000 --max-details 2000 --max-seconds 1200
```

The hard session caps are 1,000 feed pages, 2,000 detail requests, and 1,200 seconds; smaller positive limits are allowed. Requests are sequential, have a maximum 30-second timeout, and are never retried automatically. `resume` continues an unfinished scan or detail batch. After a scan has reached the current end, `poll` rechecks the saved final page using NAV's conditional response headers; a later feed update can add or change candidates. Polling the end is necessary because reaching it is not a permanent snapshot.

State and a readable `summary.json` are in a unique ignored `out/nav_discovery/<run-id>/` directory. Feed events and cursor are committed together after each page; each detail result is committed separately. NAV's feed source orders entries by its internal sequence, while `date_modified` may regress. The command therefore reconciles UUIDs by traversed feed order, verifies the documented overlap between pages, and records timestamp regressions and conflicting equal timestamps. A boundary conflict stops the run. Feed entry `id` and `_feed_entry.uuid` both identify the advertisement; the database also records page ID and item position to distinguish change events.

The summary counts distinct ads with usable current text by occupation level1, including a separate count for ads explicitly listing `INNLANDET`. It also reports IT counts, inactive responses, missing location/category data, unavailable content, failures, and pending detail work. One ad can appear in multiple occupation categories, so category totals overlap. These counts do not infer remote eligibility, historical text recovery, or representative market coverage. The earlier `nav_collect.py` preview and saved-input extraction remain separate.

### Edited IT text captures

Resume an existing discovery database to process pending details and backfill text for IT ads that were detailed before text capture was added. The first resume makes a SQLite backup before a versioned migration; it keeps the existing feed cursor and detail records. It does not restart the feed scan. Each session is limited to 1,000 feed pages, 2,000 detail requests **including backfill**, and 1,200 seconds. A request error stops the session with its unfinished work saved. Run the same resume command again only when ready to make another bounded batch.

```powershell
python harness/nav_discover.py --mode resume --db out/nav_discovery/<run-id>/state.sqlite3 --max-pages 1000 --max-details 2000 --max-seconds 1200
python harness/nav_discover.py --mode export --db out/nav_discovery/<run-id>/state.sqlite3
```

Text capture requires `occupationCategories[].level1` equal to `IT`, after trimming and case folding. Any `workLocations[].county` equal to `INNLANDET` makes it a confirmed Innlandet capture. IT ads with an explicit location elsewhere are saved as **remote-review candidates**; this does not establish remote eligibility or count them as confirmed Innlandet ads. Missing location is flagged for review rather than assigned to either set. No municipality or title prefilter is used.

The whole available HTML description is converted to plain text with headings, paragraphs, and list boundaries. Cleaner version `nav-contact-clean-v3` recognizes email, phone and clear Norwegian or English contact wording anywhere in the description, including the end. It removes the smallest separable contact passage, preserves useful wording in mixed paragraphs, and recognizes contact headings in heading tags or bold paragraphs, including `Kontaktperson for stillingen`. It recognizes `Slik søker du` as a following application section rather than extending the preceding contact section into it. Names alone are not treated as contact details; `contactList` name hints are used only alongside contact wording. If separation is uncertain, the capture is held for review rather than silently discarding a requirement. A second contact screen checks the edited text before saving it with `auto_contact_checked` state. Cleaning action counts and the cleaning version are stored without removed values. This deterministic screen does **not** guarantee detection of every contact detail or establish human approval. Previously saved captures are retained if the source later becomes inactive or unavailable. A content hash prevents another capture version when the cleaned text is unchanged.

`--mode export` is offline: it reads saved captures and creates a unique directory of UTF-8 JSON files under `out/nav_discovery/<run-id>/exports/`. Each file is labelled an **edited capture**, not an unchanged NAV response. Backups, databases, captures, and exports remain under Git-ignored `out/`. These captures are for project analysis, not an expired-ad public listing. Feed changes since August do not reconstruct removed historical descriptions, and NAV's public feed may exclude sources such as Finn.

An earlier one-off review reprocessed 11 Innlandet IT records with cleaner version 2 and saved separate review outcomes. Its script has been removed; the current commands above do not reproduce or export those separate review records. The historical results remain recorded in the task brief and prompt log.

## Secret-file protection

`.codex/config.toml` proposes project-scoped denied reads for root `.env` and `.env.local`, while leaving `.env.example` readable. `.gitignore` prevents accidental tracking; it does not prevent reads.

Secret-file protection remains unverified: the permission tests below did not attempt secret-file reads. Before adding real secrets, use only harmless dummy markers such as `DUMMY_SECRET=NOT_A_REAL_SECRET` in `.env` and `.env.local`.

## Permission tests and CLI launch (2026-10-11)

- Desktop app: temporary-file creation in `eval/` succeeded; protection failed.
- CLI 0.162.1 was launched with the following command. Use this command for future CLI work:

  ```powershell
  codex.cmd -c windows.sandbox=mxc -c default_permissions=kiua2003
  ```

- In that CLI session, normal sandboxed exclusive creation of `__permission_test__.tmp` in the project root succeeded. Creation of `eval/__permission_test__.tmp` was denied with `UnauthorizedAccessException`.
- The SHA-256 hash of `eval/check_probe.py` remained unchanged: `34C98C2F6289BE236EE5EEEF325BF42EFC21A78BD7337235E64A6AF9C197383F`.
- No temporary files remained after the tests.

Verification is limited to the tested CLI temporary-file creation behavior. It does not verify desktop protection, secret-file protection, or other tools and sessions. See [docs/prompt-log.md](docs/prompt-log.md) for the recorded results.

## Future secret-file verification

In a fresh desktop session for this trusted project:

1. Confirm the effective permission profile is `kiua2003` and that legacy sandbox settings or managed requirements have not overridden it.
2. Attempt sandboxed direct reads of both dummy secret files; both must fail with permission denied.
3. Confirm `.env.example` and `README.md` remain readable, and test other available file-reading tools separately.
4. Do not approve elevated retries or use full access during the test.
5. Check Git ignore behavior and record the results in `docs/prompt-log.md`.

If protection fails, keep only dummy data while resolving compatibility. Add explicit protection before introducing secrets at other paths. Keep real secrets outside Codex's accessible environment until verification passes.
