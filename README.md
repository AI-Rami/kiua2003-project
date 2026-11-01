# kiua2003-project

A two-person KIUA2003 project exploring an agentic workflow.

This project includes an implemented NAV saved-input extraction skeleton, a bounded metadata preview, and a resumable NAV discovery and edited-text capture command. See [SPEC.md](SPEC.md) for the product plan and [AGENTS.md](AGENTS.md) for working instructions.

- `tasks/`: task briefs with owner, reviewer, acceptance criteria, and status. The two people can alternate roles.
- `harness/`: workflow stages, prompts, tools, and execution code.
- `eval/`: evaluation cases, expected outcomes, and scoring criteria; changes require permission.
- `fixtures/`: saved real public inputs without personal data for reproducible offline runs. Record source, retrieval date, and permission/license alongside future inputs.
- `docs/meetings/`: decisions and next actions using Person A and Person B.
- [docs/prompt-log.md](docs/prompt-log.md): corrected or rejected agent output and lessons.

The earlier MET Norway exercise is in `harness/probe.py`; its checker is `eval/check_probe.py`. The NAV walking skeleton is separate.

## NAV saved-input walking skeleton

Requires Python 3 and internet access with OpenAI API credits. Set the process environment variable `KIUA2003_API` to your API key before the saved-input run; do not put a real key in project files. The program never writes the key or Authorization header. In PowerShell, set it privately for the current process, then run:

```powershell
python harness/nav_skeleton.py --mode dry-run
python harness/nav_skeleton.py --mode saved-input
```

Use `--input path/to/ad.json` with either command for another compatible saved advertisement. The default is the edited fixture `fixtures/nav_ad_01.json`. Dry run only prints the plan and limits; it does not read or validate the input, require a key, make a network call, or change files. Saved-input mode automatically (1) reads the saved advertisement and prepares its entire HTML description as readable text, (2) calls `gpt-6-luna` through OpenAI's Responses API to extract technical skills, and (3) validates the response before creating the JSON result and Markdown report.

Each extracted item is `required` for an applicant qualification, `preferred` for an explicitly optional advantage, or `unclear` when the advertisement mentions a skill without establishing either. A `single` item contains exactly one skill. An `any_of` item preserves at least two explicit alternatives, such as “A or B”, without choosing between them. Validation checks JSON structure and that each supporting quotation occurs exactly in the prepared text. It does not establish extraction accuracy or completeness.

Each run has its own `out/nav_runs/<run-id>/` directory. New run IDs use the UTC date, time, and validated advertisement UUID, for example `2026-10-31_08-23-49_UTC_ad-8119dbb1-530f-4307-9ee0-e030c2b8e581`; the run ID matches the folder name. A run fails without overwriting anything if that folder already exists. Read `report.md` alongside the saved advertisement and its notes; `result.json` holds structured items. `prepared_ad.txt`, `request.json` without credentials, `response.json`, and `validation.json` aid inspection. A failed run has no successful result or report. The fixture's saved `ACTIVE` status is not a live status check.

Extraction accuracy and completeness remain to be evaluated against a human-reviewed reference. The NAV collectors below are separate from extraction. Connecting saved captures to extraction, calculating skill statistics across advertisements, and building the dashboard remain planned, with explicit rules for skill naming, alternative groups, and duplicates.

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

The whole available HTML description is converted to plain text with headings, paragraphs, and list boundaries. Cleaner version `nav-contact-clean-v2` removes the smallest recognizable contact passage it can separate. It uses `contactList` hints in memory, preserves useful wording in mixed paragraphs, and recognizes contact headings in heading tags or bold paragraphs. If separation is uncertain, the text is blocked for review rather than silently discarding a requirement. Cleaning action counts and the cleaning version are stored without removed values. This deterministic screening does **not** guarantee that all personal data has been removed; saved captures have `pending_human_review` state. Previously saved captures are retained if the source later becomes inactive or unavailable. A content hash prevents another capture version when the cleaned text is unchanged.

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
