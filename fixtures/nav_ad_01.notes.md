# NAV advertisement fixture notes

- API source URL: https://pam-stilling-feed.nav.no/api/v1/feedentry/8119dbb1-530f-4307-9ee0-e030c2b8e581
- Advertisement UUID: `8119dbb1-530f-4307-9ee0-e030c2b8e581`
- Original retrieval time: `2026-10-30T06:36:14.9027845Z`
- Fixture provenance: This is an edited API fixture, not an unchanged response. The advertisement source link remains in the JSON.
- Removed content: The entire “Om oss” section of `ad_content.description`, from its heading up to but not including “Hva trenger vi deg til”. No other sections or fields were removed; `contactList` was empty.
- Status: `ACTIVE` is the status saved at retrieval, not a live status check.
- Intended use: This fixture tests extraction. Its geographical inclusion remains undecided; the advertisement lists several counties including Innlandet, and describes an Oslo office with flexible home working.
- Review: External review compared the revised JSON with the original and confirmed that only the agreed “Om oss” section was removed; all other values and job requirements were unchanged. The revised file parsed as UTF-8 JSON without a BOM.
- Review boundary: Removing personal information here does not establish that future live ingestion meets the course’s input restrictions.
