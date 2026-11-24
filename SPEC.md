# Project specification

## Purpose

The project includes a local web dashboard showing prototype skill statistics from collected NAV job advertisements, initially focused on IT roles in Innlandet. Its purpose is to make skill requirements across advertisements easier to compare by extracting skills and classifying them as required, preferred, or unclear.

Education and experience extraction are possible future extensions and are outside the current scope.

A saved-input walking skeleton, NAV collection and cleaning, a resumable incremental discovery-to-extraction-to-statistics command, and a local dashboard are implemented. A completed button-triggered live update on 2026-11-04 read six feed pages, made 1,479 detail requests and two model requests, and published two validated results. The selected index now has thirteen validated v2 model extractions and one blocked entry. The repository shares a dated, checked snapshot of those selected results, derived statistics, and the saved NAV checkpoint for a fresh checkout; each user's later updates remain local under ignored `out/`. Offline code produces small-sample prototype skill counts from the index and a provisional, version-checked source review, distinguishing applicant qualifications from duties, work context and interest-only mentions; the dashboard recalculates these counts over saved publication-date, status and skill-name filters. Original model results are retained. The review is not approved ground truth, and extraction accuracy remains unresolved. Historical period aggregates and complete market statistics remain planned.

## Users

The intended primary users are IT jobseekers in Innlandet, particularly recent graduates. Career advisers are potential secondary users.

The intended user need has not yet been demonstrated or validated. The project currently treats easier comparison of advertisement requirements as a working assumption to investigate.

## Intended workflow

The following product workflow combines the implemented command-line update path and local dashboard interaction with longer-term product plans:

1. The user clicks “Run update” in the web dashboard. Users do not paste advertisement links.
2. Collect relevant advertisements through NAV's job vacancy API, after verifying endpoints, access requirements, usage terms, and how the selected NAV search filters for IT roles in Innlandet can be implemented. Do not assume website filters are exposed through the API. Use deadline and source status where available to identify expiry or withdrawal; retain expired advertisements in historical statistics. Handling of remote jobs and multiple locations remains open.
3. Identify new or changed advertisements by NAV advertisement UUID. The same UUID updates an existing stored record without adding another advertisement. A new UUID counts as a new advertisement, including when a job is republished under a new UUID. Preserve the original source link and publication date with the record.
4. Extract skills from relevant new or changed advertisements. Each extracted skill must have a skill name, a classification of required, preferred, or unclear, and an exact supporting quotation from the advertisement. Preserve the source link so users can inspect the advertisement behind a statistic. Flag ambiguous wording as unclear without forcing a required or preferred classification.
5. Validate output structure and check with code that each quotation occurs in the source text. Use reviewed reference examples to evaluate skill extraction, classification, omissions, and invented skills. A matching quotation alone does not prove that the interpretation is correct. Flag uncertain results without numerical confidence scores. Store validated results.
6. Calculate statistics using ordinary code rather than the AI agent. Count advertisements by UUID, not unique jobs or vacancies. Plan weekly, monthly, and yearly views using advertisement publication dates. Show the period and coverage of collected data; do not imply historical completeness before collection began.
7. Update the web dashboard with skill statistics and links and quotations supporting the underlying advertisements. Produce structured JSON and a readable report as additional outputs.

The local dashboard, JSON, and a readable report with source links are implemented prototype outputs. Dashboard presentation may change after user review; the existing v2 extraction schema is implemented and retained.

The saved-input skeleton currently uses configurable `gpt-6-luna`. The model for the integrated product remains undecided until candidates have been evaluated for extraction accuracy, cost, speed, and access through the project's setup.

## Definition of success

Success means that the project:

- extracts skills accurately, distinguishes required from preferred skills, and marks ambiguous wording as unclear, with omissions and invented skills assessed against reviewed reference examples;
- makes each extracted skill traceable to an exact supporting quotation and a source link, while evaluating interpretation separately from quotation matching;
- supports reproducible execution from documented inputs and steps;
- reports failures and uncertain results clearly rather than presenting them as reliable output;
- counts advertisements consistently by UUID, retains expired advertisements in historical views, and shows publication-date periods with data coverage; and
- lets users inspect the source links and quotations behind displayed statistics.

Numerical success thresholds have not yet been defined. Appropriate evaluation cases, scoring methods, and acceptance thresholds must be established in later task briefs.

## Open questions

- Which endpoints, access requirements, and usage terms apply to NAV's job vacancy API?
- Which API fields and filters support NAV's IT categories, Innlandet locations, deadlines, and source status, and how should selection work when these are unavailable?
- How should remote jobs and advertisements with multiple locations be handled?
- Which source fields reliably indicate that an existing UUID has changed, and how should an updated record's extraction and publication date be handled?
- Which NAV publication-date field and time zone should define weekly, monthly, and yearly periods, and how should data coverage be displayed?
- How should alternative skill groups and repeated skills within one advertisement contribute to advertisement counts?
- Which candidate AI models should be tested, and which best meets the extraction accuracy, cost, speed, and access needs of the project?
- Which prompting approach and final JSON schema should be used for extraction?
- How should advertisement text be prepared so exact supporting quotations can be reliably checked against the source?
- Which reviewed reference examples and review process should evaluate extraction, classification, omissions, invented skills, and ambiguous wording?
- How should the dashboard show the last successful collection period? Its current local version shows progress, completion and partial or failed outcomes, but not a verified collection-period history.

## Current implementation status

The [archived MET Norway exercise](history/met-weather/README.md) retains the earlier Hamar weather task, its saved forecast, Python code, tests and checker.

The NAV saved-input walking skeleton is implemented in `harness/nav_skeleton.py` with an edited advertisement fixture. It prepares the saved description, calls `gpt-6-luna`, validates output structure and exact quotations, and writes JSON and Markdown run artifacts. One saved-input run passed those structural checks; this does not establish extraction accuracy or completeness.

`harness/nav_collect.py` implements a bounded metadata preview. `harness/nav_discover.py` implements a resumable NAV feed scan, SQLite metadata storage, detail discovery, and edited text capture for selected IT ads. New detail discovery retains available job titles as display metadata. `harness/nav_text.py` provides deterministic contact cleaning, which flags uncertain text and does not establish that saved captures are free of personal information. The discovery scan is a data-availability investigation, not complete NAV search-filter implementation or market coverage. Individual cleaned captures can be passed to the extraction skeleton. `harness/nav_update.py` connects saved feed continuation, pending work, extraction and statistics in one bounded command; the dashboard button exercised this path live on 2026-11-04. `out/current/index.json` selects at most one validated v2 model extraction per eligible UUID, with blocked, stale and failed entries excluded. `harness/nav_skill_summary.py` counts only these explicit selected results and separates single applicant qualifications, applicant `OR` groups, and other technical mentions. It displays available titles and publication dates without treating their date range as collection coverage. `harness/nav_dashboard.py` serves a local UI over the selected results, saved-data filters and the same update workflow. `harness/start.py` restores the shared baseline on a fresh checkout and opens that dashboard. The generated statistics remain a small-sample prototype with unresolved interpretation warnings, not established extraction accuracy or complete market coverage. Weekly, monthly and yearly historical aggregates remain planned.
