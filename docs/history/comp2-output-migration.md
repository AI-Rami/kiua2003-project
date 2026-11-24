# Comp2 generated-output migration

This manifest describes the migration from development output folders to an explicit selected-result set. Paths are relative to the repository root. It records decisions without reproducing advertisement text, contact details or credentials.

## Selection and status

The source population is the 11 Innlandet IT UUIDs in the targeted review export and the ten-ad extraction batch. Nine eligible captures have a matching saved v2 extraction using frozen prompt SHA-256 `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`. The request input equals the saved prepared text and current cleaned capture; the database's targeted content hash matches that input. Each selected result has successful validation. These are validated **model outputs**, not human-approved answers; semantic warnings remain in the frozen evaluation review.

| UUID | Decision | Original run / reason |
| --- | --- | --- |
| `2ed29047-97e4-4168-adb9-8da83e968c94` | Current | `2026-11-01_22-18-19_UTC_ad-2ed29047-97e4-4168-adb9-8da83e968c94` |
| `2f62e300-c698-4f53-8510-db90b1692cb9` | Current | `2026-11-01_22-13-46_UTC_ad-2f62e300-c698-4f53-8510-db90b1692cb9`; reused frozen-prompt run |
| `4135497b-cb65-4bed-890d-f9dcaf478711` | Current | `2026-11-01_22-19-56_UTC_ad-4135497b-cb65-4bed-890d-f9dcaf478711` |
| `8119dbb1-530f-4307-9ee0-e030c2b8e581` | Blocked | Known unresolved cleaning/personal-data issue. No older run is substituted. Its review-export capture remains in place and is not copied. |
| `8d77969c-ab60-4da0-9a1e-427bf1eee30e` | Current | `2026-11-01_22-21-21_UTC_ad-8d77969c-ab60-4da0-9a1e-427bf1eee30e` |
| `a1613f9c-1757-4351-81ea-1d0e5246fbd3` | Current | `2026-11-01_22-22-13_UTC_ad-a1613f9c-1757-4351-81ea-1d0e5246fbd3` |
| `a5dabb26-7b1f-4538-aabe-cd78cac5f2cb` | Current | `2026-11-01_22-23-08_UTC_ad-a5dabb26-7b1f-4538-aabe-cd78cac5f2cb` |
| `b35c3ca3-5e17-4e62-b048-c37317096e61` | Current | `2026-11-02_05-59-01_UTC_ad-b35c3ca3-5e17-4e62-b048-c37317096e61` |
| `b69f0bbd-082e-4d36-baae-456fb23ca32a` | Current | `2026-11-02_06-00-34_UTC_ad-b69f0bbd-082e-4d36-baae-456fb23ca32a` |
| `dc0bdd91-ddb4-4e5f-8eb7-bf51f57e31aa` | Current | `2026-11-02_06-02-37_UTC_ad-dc0bdd91-ddb4-4e5f-8eb7-bf51f57e31aa` |
| `1f614033-73b3-4c26-bda5-3d9abe281a12` | Blocked | Targeted review export records blocked cleaning and no usable revised capture. No extraction is selected. |

`out/current/index.json` is the sole application statistics selection. `out/current/<uuid>/` holds verified copies of six files from each selected run: `prepared_ad.txt`, `request.json`, `response.json`, `validation.json`, `result.json` and `report.md`. The original run ID remains inside those files and in the index. The index also records the prepared-content hash, prompt and schema hashes, model ID, reasoning effort and output cap. One UUID contributes at most once. A new attempt does not replace the selected result until it is explicitly checked and indexed. The index has statuses for current, blocked, failed, stale and pending records; only current entries enter prototype statistics. The blocked records have no selected result path.

## Location mapping

| Before | After | Reason |
| --- | --- | --- |
| `out/nav_discovery/` | Unchanged | Active SQLite feed checkpoint, version metadata, edited capture inputs, backups and review export. The problematic capture stays in its existing location. |
| Nine selected `out/nav_runs/<run-id>/` folders | Verified copies under `out/current/<uuid>/`; original folders under `archive/comp2-generated-2026-11-02/nav_runs/<run-id>/` | The active selection has one validated v2 version per eligible UUID; complete original attempts remain historical evidence. |
| Other `out/nav_runs/` folders and `batches/` | `archive/comp2-generated-2026-11-02/nav_runs/` | Earlier prompt versions, failures and historical indexes remain available for Comp2 and later evaluation. No folder is treated as an application input by recency. |
| `out/nav_evaluations/`, `out/nav_skill_reviews/` | Matching folders under `archive/comp2-generated-2026-11-02/` | Preserve the frozen evaluation and earlier correction evidence. Their relative links to archived runs retain the same folder relationships. |
| `out/nav_skill_summaries/` and the prior `out/archive/comp2-cleanup-2026-11-02/nav_skill_summaries/` | `archive/comp2-generated-2026-11-02/nav_skill_summaries/` | Preserve all earlier mechanical and corrected tables, including the intermediate copy, outside current statistics. |
| `out/probe.json` | `archive/comp2-generated-2026-11-02/probe.json` plus retained compatibility file at `out/probe.json` | The MET course output is archived. `eval/check_probe.py` still requires the original path; `eval/` is not changed without separate permission. The compatibility copy is not an application statistics input. |
| `out/statistics/`, `out/ui/` | New active locations | Statistics contain only explicit indexed current results. No UI is implemented; `out/ui/` is empty. |

The archive is outside `out/` and ignored by Git. Historical prompt logs, meeting reports, source fixtures, code, tests and dependency/configuration files remain in place. No API or model requests are part of this migration.

## Post-migration verification

- Nine selected run directories were copied with six required files each. All 54 copies matched their archived originals by SHA-256 after relocation. The two blocked UUIDs have no `out/current/<uuid>/` directory; the problematic review-export capture remains at its original path.
- The four moved historical folders contained 168 run files, four evaluation files, two review files and six summary files; each moved file matched its pre-move SHA-256 hash. Three previously archived summary files were moved into the same archive summary tree and matched their hashes. The archived MET `probe.json` copy matches the compatibility file byte-for-byte.
- `out/current/index.json` has 11 distinct UUIDs: nine current and two blocked. Each current entry matched its saved capture input, database content hash, v2 result identity, frozen prompt, strict v2 request schema, `gpt-6-luna`/medium/8,192-token settings and successful validation at selection time. The current loader checked the copied files and indexed identities again.
- The current summary includes nine UUIDs and excludes two blocked UUIDs. It has 192 distinct skill-name rows, 176 single-skill rows, 18 alternative-skill rows and seven OR-group rows. An independent recount of every indexed item matched all row counts and supporting UUID sets; the full tables are saved in `out/statistics/`.
- Eight model-free summary tests passed. They cover UUID-set counts and OR groups, duplicate UUID rejection, blocked/failed/stale exclusion, archived-path rejection, an invalid replacement leaving existing statistics unchanged, and a failed newer attempt leaving the selected result intact. Syntax checks passed. `eval/check_probe.py` passed using the retained compatibility output.
- SQLite `quick_check` returned `ok`. All 102 local Markdown links across retained and archived documents/indexes resolved after relocation. The archive is outside `out/` and excluded by `.gitignore`. No API/model request, prompt optimization, manual result correction, UI implementation, commit, push or merge occurred.

The summary command still has no automatic integration with the NAV poller or extractor. A later workflow must decide when a changed UUID is eligible, promote a checked version into `out/current/`, update the index atomically, and keep a prior selected result if a replacement fails. The two blocked records need separate resolution before they can be selected.
