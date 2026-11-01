# Task 003: Bounded NAV change-feed metadata collector

## Goal and scope

Implement `harness/nav_collect.py` as a separate, standard-library command for a bounded preview of changes in NAV's job-advertisement feed. Select current `ACTIVE` advertisements only when at least one `workLocations[].county` is `INNLANDET` and at least one `occupationCategories[].level1` is `IT`, after trimming whitespace and ignoring case. Multiple locations may qualify; remote work by itself does not. Either definitely false selection condition makes a nonmatch, even if the other condition is unknown; otherwise an unknown condition makes relevance unknown. The saved-input extraction command remains separate and unchanged.

This task does not implement full ingestion, an all-active-ad scan, a persistent database, a change-feed checkpoint, model extraction, statistics, or a web dashboard. It does not establish coverage or completeness.

## Interface and bounds

```powershell
python harness/nav_collect.py --mode dry-run
python harness/nav_collect.py --mode collect --since 2026-10-24T00:00:00Z
```

Collection requires an explicit ISO-8601 UTC date or timestamp. `--max-pages` and `--max-details` default to 2 and 50; zero or negative values are rejected. The request timeout is 30 seconds. No automatic retries are made. Dry-run prints stages and limits without reading credentials, making requests, or creating files.

## Collection and output

Retrieve the rotating public experimental token, extract one JWT in memory, and use Bearer authentication for the documented NAV feed and detail endpoints. Send `If-Modified-Since` in RFC 1123 UTC format. Follow only returned `next_url` links after checking HTTPS, the NAV API host, and the expected feed-page path. Validate detail links similarly. Within each fetched page, group entries by UUID and choose the newest using the documented ISO `date_modified` change timestamp, independent of array order. Request details only when that newest entry is ACTIVE. Skip a UUID if any of its inspected entries lacks a valid change timestamp or equally recent entries conflict. This does not determine the latest state across unread pages. Count each attempted page and detail request. Request a given advertisement UUID at most once per run, and always check the current detail status, even if its feed event says ACTIVE.

Keep raw responses, credentials, descriptions, contacts, employer details, and street addresses in memory only. A completed run writes a unique directory under `out/nav_collection/` with `matches.json` and `summary.json`. Matching records contain only UUID, current status, county/municipality values, occupation level1/level2 values, publication and update dates, and an original link if supplied by NAV. The summary records the chosen date, execution time, request counts, distinct UUID count, outcomes, sanitized failures, pagination/limit stop reason, and whether fetched-page candidates were left without a detail request. It records one exclusive reason per unknown or nonmatching detail, including false-plus-unknown combinations; reason counts do not overlap. Each page summary records earliest and latest valid feed-entry change timestamps in UTC, counts of missing and invalid timestamps, and skipped UUIDs whose recency is unusable or ambiguous. A failed run saves only a failure summary, not a success-shaped matches file. Zero matches is valid.

The run is labelled a bounded preview of changes since the chosen date. Old or inactive advertisements may appear in the feed; missing or masked detail content is a data condition. Neither a bounded preview nor a recent-date window establishes all currently active advertisements.

## Acceptance checks

- The reviewed saved fixture meets the stated county and occupation criteria; its saved ACTIVE status is historical.
- Synthetic multiple-location, wrong-county, non-IT, missing-field, and inactive cases follow the three-way selection rules.
- Synthetic repeated UUIDs produce one detail candidate; page and detail limits are enforced; unsafe pagination and detail URLs are rejected before credentials are sent.
- Dry-run has no network or file effects. Syntax and the focused model-free checks pass before at most one live preview using a seven-day cutoff, two pages, and 50 details.
- Any live preview reports actual counts and paths. No matching ad is required for acceptance.

No `eval/` files, existing fixtures, or saved-input extraction files are changed. This task adds requested functionality; it is not a correction to a prior agent output.

## Verification on 2026-10-31

An initial syntax check found an unmatched parenthesis in the new collector; that was corrected before the live run. The subsequent syntax check, focused synthetic selection and request-bound checks, dry-run isolation check, and `git diff --check` passed. The actual dry-run exited successfully without creating `out/nav_collection/`.

After the live preview, a model-free check of a synthetic mid-page HTTP failure confirmed that the failure summary records the attempted request and any remaining unprocessed candidates without saving a success-shaped matches file. The live preview was not repeated.

One live bounded preview started at `2026-10-24T20:11:48Z` with limits of two pages and 50 details. It fetched one 1,000-entry page and made 50 detail requests. It recorded 902 distinct UUIDs, zero matches, two nonmatches, 48 inactive details, zero unknown relevance, and no failures. The detail limit stopped the run; pagination had not ended, and 94 active candidates on the fetched page were left without a detail request. Outputs are in `out/nav_collection/2026-10-31_20-11-48_UTC-7d872239/`. This result does not establish the absence of relevant advertisements.

## Resumable availability investigation

The requested follow-on investigation uses the separate `harness/nav_discover.py` command described in README. Its first phase stores feed-entry ID, UUID, change timestamp, status, validated detail URL, page position, and cursor in SQLite under ignored `out/`. It traverses NAV's `next_url` to the current end without requesting details. The second phase requests distinct latest-`ACTIVE` UUIDs and stores only permitted metadata and a readable-description boolean. It records unavailable content and failures separately. Each page and its cursor are saved in one transaction; each detail result is saved before proceeding. `resume` continues saved work, and `poll` rechecks the final page after reaching the end.

NAV source orders pages by an internal sequence number; timestamps alone do not establish feed order. Adjacent pages overlap by one entry. The command verifies that boundary, reconciles repeated UUIDs in traversal order, reports timestamp regressions and equal-timestamp status conflicts, and stops if the page boundary is ambiguous. The feed's public entry ID is the advertisement UUID, so page ID and item position distinguish repeated change events. An old publication date does not make the currently retrieved description a historical snapshot.

Ordering and cursor behavior were checked against NAV's official [feed repository](https://github.com/navikt/pam-stilling-feed/blob/main/src/main/kotlin/no/nav/pam/stilling/feed/FeedRepository.kt), [feed service](https://github.com/navikt/pam-stilling-feed/blob/main/src/main/kotlin/no/nav/pam/stilling/feed/FeedService.kt), [feed entry DTO](https://github.com/navikt/pam-stilling-feed/blob/main/src/main/kotlin/no/nav/pam/stilling/feed/dto/FeedAd.kt), and [API documentation](https://navikt.github.io/pam-stilling-feed/).

The hard per-session limits are 1,000 pages, 2,000 details, and 20 minutes, with sequential 30-second requests and no automatic retry. HTTP 401, 403, or 429 stops with saved progress. Unavailable text and failed details are coverage gaps. Counts are per UUID within each occupation level1, but one UUID may count in more than one occupation. An explicit Innlandet location is required for the Innlandet subset; remote eligibility is not inferred. The investigation does not change the project's IT scope or establish representative market coverage.

### Verification and first session on 2026-11-01

Syntax, new-file whitespace, and `git diff --check` passed. Temporary mocked checks passed for scan and detail resume, page overlap, final-page polling, duplicate UUIDs, timestamp disagreements, phase separation, overlapping occupation counts, unsafe URLs, rate-limit preservation, unavailable content, and exclusion of stale details from counts. The earlier collector's dry-run and relevance function still passed model-free checks.

One session started at `2026-08-01T00:00:00Z`. It saved 181 feed pages (178,893 feed entries; 49,914 distinct UUIDs), reached the current feed end, and made 2,000 detail requests. The detail limit stopped the session with 7,133 candidates pending. Among the 2,000 saved detail records, 69 had IT level1 and usable text, including 3 explicitly listing Innlandet. There were 5 records without a location, no missing categories, inactive detail responses, unavailable content, or request failures. These are partial detail counts. State and summary are in `out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/`.

### Edited text capture extension

Continue the existing SQLite database without rescanning its August feed history. Before its first migration, make a consistent SQLite backup in the same ignored run directory. A versioned transaction adds capture versions and per-UUID capture processing state, retaining the existing event, advertisement, detail, and cursor tables. Backfill previously detailed IT records once for available text, then continue pending detail discovery. Each successful detail and any cleaned text are committed together. A failed request stops the batch and remains pending for an explicitly started resume; blocked cleaning and unavailable content are recorded without unsafe text. Request limits include backfill.

Save a cleaned version only when current detail categories confirm level1 IT and a county either confirms Innlandet or explicitly locates the ad elsewhere. The latter is a remote-review candidate, not a confirmed Innlandet match or proof of remote eligibility. Missing locations are review blocked. The deterministic HTML and contact-cleaning method removes contact passages and records only action counts; its automated `pending_human_review` state is not a guarantee that all personal data is absent. Capture revisions are keyed by UUID and cleaned-text hash, preserving first capture dates and earlier content when the current source becomes inactive or unavailable. The offline `--mode export` command writes labelled edited JSON captures to a unique ignored directory. No skill model, historical-content reconstruction, advertisement statistics, or web UI is added.

### Verification and resumed discovery on 2026-11-01

Temporary databases and mocked responses verified the backup and migration, cursor preservation, separate Innlandet and remote-review selection, non-IT exclusion, HTML preparation, contact passage removal, review blocking without unsafe text, unchanged-content deduplication, interrupted resume, inactive-content preservation, prior IT backfill, offline export, and sanitized saved state. Syntax, the existing preview dry-run, and `git diff --check` passed before live execution. An initial temporary whitespace check used an incorrect trim expression; the corrected check passed.

The existing database was backed up to `state.v0-backup-b11f7e8d.sqlite3`, then migrated in place. Four sequential resume batches made 2,000, 2,000, 2,000, and 1,202 detail requests, including 69 prior-IT backfill requests in the first batch. No feed pages were requested in these batches. The queue finished with 9,133 details saved and zero pending details or backfills. The saved feed-change range remains `2026-08-01T00:00:04.836257Z` through `2026-11-01T10:47:55.775278Z`, the latest feed end observed by the earlier scan. This is feed-change coverage, not all ads published in that period.

Of 281 IT details with readable text, 167 distinct UUIDs have cleaned captures: 10 confirmed Innlandet and 157 remote-review candidates. Another 114 IT records were review blocked (110 uncertain personal passages and 4 unknown locations); their text was not saved. No missing readable detail text, unavailable content, inactive detail response, or request failure was recorded in this completed queue. An offline export created 167 UTF-8 JSON files under `exports/2026-11-01_13-06-52_UTC-c372f60d/`; all parsed, matched their stored hashes, and passed the same contact-pattern screen. Automated screening does not replace human review.

### Targeted contact-cleaning correction

The follow-on correction reprocessed only the 11 previously detailed IT UUIDs explicitly listing Innlandet. The one-off `harness/nav_reprocess.py` script used the saved metadata to select those UUIDs, backed up SQLite, and saved version-2 outcomes and edited text in a separate table. Earlier captures and exports were preserved. It did not scan feed pages or request remote-review candidates. A distinct offline review export contained 11 JSON records and a Markdown index with source links, outcome, cleaning version, action counts, previous-version metadata, and review state. The one-off script was later removed; this paragraph records a historical run, not a current command.

The cleaner now removes recognizable contact sentences instead of discarding an entire mixed paragraph. It uses `contactList` only as in-memory hints, recognizes actual and bold-paragraph headings, and blocks ambiguous cases rather than guessing where useful wording ends. It does not treat every capitalized phrase or company description as a person. The version increment and saved action counts provide provenance; automatic cleaning remains subject to human review.
