"""Resumable NAV feed discovery with metadata and edited IT text captures."""

import argparse
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

import nav_collect as nav
from nav_text import CLEANING_VERSION, clean_description, content_hash


ROOT = nav.ROOT / "out" / "nav_discovery"
MAX_PAGES = 1000
MAX_DETAILS = 2000
MAX_SECONDS = 1200
SCHEMA_VERSION = 1

CAPTURE_SCHEMA = """
CREATE TABLE IF NOT EXISTS captures(
    uuid TEXT NOT NULL, content_hash TEXT NOT NULL, cleaned_text TEXT NOT NULL,
    captured_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, source_status TEXT NOT NULL,
    published TEXT, updated TEXT, source_link TEXT, source_id TEXT,
    locations_json TEXT NOT NULL, occupations_json TEXT NOT NULL,
    selection_basis TEXT NOT NULL, cleaning_version TEXT NOT NULL,
    cleaning_actions_json TEXT NOT NULL, review_state TEXT NOT NULL,
    PRIMARY KEY(uuid,content_hash));
CREATE TABLE IF NOT EXISTS capture_state(
    uuid TEXT PRIMARY KEY, feed_order INTEGER NOT NULL, checked_at TEXT NOT NULL,
    current_status TEXT NOT NULL, outcome TEXT NOT NULL, reason TEXT,
    content_hash TEXT);
"""


class DiscoveryError(Exception):
    """A diagnostic that contains no response or credential data."""


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def has_readable_text(value):
    if not isinstance(value, str):
        return False
    try:
        parser = VisibleText()
        parser.feed(value)
        return any(char.isalnum() for char in " ".join(parser.parts))
    except (ValueError, OverflowError):
        return False


def state(db, key, default=None):
    row = db.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def put(db, key, value):
    db.execute("INSERT INTO state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
               (key, json.dumps(value)))


def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(
            page_id TEXT NOT NULL, item_index INTEGER NOT NULL, entry_id TEXT NOT NULL,
            uuid TEXT NOT NULL, change_at TEXT, status TEXT NOT NULL, detail_url TEXT NOT NULL,
            feed_order INTEGER NOT NULL UNIQUE, PRIMARY KEY(page_id,item_index));
        CREATE TABLE IF NOT EXISTS ads(
            uuid TEXT PRIMARY KEY, last_order INTEGER NOT NULL, change_at TEXT,
            status TEXT NOT NULL, detail_url TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS details(
            uuid TEXT PRIMARY KEY, last_order INTEGER NOT NULL, status TEXT NOT NULL,
            locations_json TEXT NOT NULL, occupations_json TEXT NOT NULL,
            published TEXT, updated TEXT, source_link TEXT, source_id TEXT,
            content_available INTEGER NOT NULL, has_text INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS failures(
            uuid TEXT NOT NULL, feed_order INTEGER NOT NULL, kind TEXT NOT NULL,
            PRIMARY KEY(uuid,feed_order));
    """)
    return db


def migrate_schema(path, *, backup=True):
    """Upgrade legacy state only after a consistent SQLite backup exists."""
    path = Path(path)
    db = sqlite3.connect(path)
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == SCHEMA_VERSION:
            return None
        if version != 0:
            raise DiscoveryError("database: unsupported schema version")
        backup_path = None
        if backup:
            backup_path = path.with_name("state.v0-backup-" + uuid.uuid4().hex[:8] + ".sqlite3")
            destination = sqlite3.connect(backup_path)
            try:
                db.backup(destination)
            finally:
                destination.close()
        try:
            db.executescript("BEGIN IMMEDIATE;\n" + CAPTURE_SCHEMA +
                             f"\nPRAGMA user_version={SCHEMA_VERSION};\nCOMMIT;")
        except sqlite3.Error:
            db.rollback()
            raise DiscoveryError("database: migration failed; backup preserved") from None
        return backup_path
    finally:
        db.close()


def initialize(root, since):
    root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC-") + uuid.uuid4().hex[:8]
    folder = root / run_id
    folder.mkdir(exist_ok=False)
    db = connect(folder / "state.sqlite3")
    with db:
        for key, value in {
            "since": nav.iso_utc(since), "phase": "scan", "scan_complete": False,
            "cursor_url": nav.FEED_URL, "expected_next_id": None,
            "last_fingerprint": None, "end_url": None, "end_etag": None,
            "end_last_modified": None, "polling": False, "pages_done": 0,
            "next_order": 1, "timestamp_regressions": 0,
            "equal_timestamp_status_changes": 0, "last_stop": None,
        }.items():
            put(db, key, value)
    db.executescript("BEGIN IMMEDIATE;\n" + CAPTURE_SCHEMA +
                     f"\nPRAGMA user_version={SCHEMA_VERSION};\nCOMMIT;")
    return folder, db


def fetch(opener, url, headers, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return "time_limit", None, {}
    try:
        with opener.open(Request(url, headers=headers, method="GET"),
                         timeout=min(nav.TIMEOUT_SECONDS, remaining)) as response:
            code = response.status
            body = response.read(nav.MAX_RESPONSE_BYTES + 1)
            meta = {"etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified")}
    except HTTPError as exc:
        return exc.code, None, {}
    except (URLError, TimeoutError, OSError) as exc:
        return f"network_{type(exc).__name__}", None, {}
    if len(body) > nav.MAX_RESPONSE_BYTES:
        return "response_too_large", None, {}
    return code, body, meta


def get_token(opener, deadline):
    code, body, _ = fetch(opener, nav.TOKEN_URL, {"Accept": "text/plain"}, deadline)
    if code != 200:
        raise DiscoveryError(f"token: {code}")
    try:
        matches = nav.JWT_PATTERN.findall(body.decode("utf-8"))
    except UnicodeError:
        raise DiscoveryError("token: invalid UTF-8") from None
    if len(matches) != 1 or not matches[0] or re.search(r"\s", matches[0]):
        raise DiscoveryError("token: invalid JWT format")
    return matches[0]


def checked_page(page, expected_id):
    page_id = nav.usable_uuid(page.get("id"))
    items = page.get("items")
    if page_id is None or not isinstance(items, list) or not items:
        raise DiscoveryError("feed: invalid page ID or items")
    if expected_id is not None and page_id != expected_id:
        raise DiscoveryError("feed: page boundary ID mismatch")
    next_path, next_id = page.get("next_url"), page.get("next_id")
    if next_path is None and next_id is None:
        next_url = None
    elif next_path is not None and nav.usable_uuid(next_id):
        next_url = nav.validated_nav_url(next_path, "pagination")
        if next_url.rsplit("/", 1)[1] != nav.usable_uuid(next_id):
            raise DiscoveryError("feed: next URL and ID mismatch")
    else:
        raise DiscoveryError("feed: inconsistent next cursor")
    entries = []
    for item in items:
        if not isinstance(item, dict):
            raise DiscoveryError("feed: invalid entry")
        header = item.get("_feed_entry")
        if not isinstance(header, dict):
            raise DiscoveryError("feed: missing entry metadata")
        ad_id = nav.usable_uuid(header.get("uuid"))
        entry_id = nav.usable_uuid(item.get("id"))
        if ad_id is None or entry_id != ad_id:
            raise DiscoveryError("feed: missing or inconsistent advertisement UUID")
        status = header.get("status")
        if status not in ("ACTIVE", "INACTIVE"):
            raise DiscoveryError("feed: invalid status")
        detail_url = nav.validated_nav_url(item.get("url"), "detail")
        if detail_url.rsplit("/", 1)[1] != ad_id:
            raise DiscoveryError("feed: detail URL and UUID mismatch")
        changed = nav.change_timestamp(item.get("date_modified"))
        entries.append((entry_id, ad_id, changed[1] if changed else None, status, detail_url))
    return page_id, entries, next_url, nav.usable_uuid(next_id) if next_url else None


def fingerprint(entry):
    return list(entry)


def save_page(db, page, page_url, response_headers):
    expected = state(db, "expected_next_id")
    page_id, entries, next_url, next_id = checked_page(page, expected)
    if expected is not None and fingerprint(entries[0]) != state(db, "last_fingerprint"):
        raise DiscoveryError("feed: overlapping page boundary differs")
    start_index = 1 if expected is not None else 0
    order = state(db, "next_order")
    with db:
        for index in range(start_index, len(entries)):
            entry_id, ad_id, changed, status, detail_url = entries[index]
            prior = db.execute("SELECT entry_id,uuid,change_at,status,detail_url FROM events WHERE page_id=? AND item_index=?",
                               (page_id, index)).fetchone()
            if prior is not None:
                if tuple(prior) != entries[index]:
                    raise DiscoveryError("feed: existing page position changed")
                continue
            db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?)",
                       (page_id, index, entry_id, ad_id, changed, status, detail_url, order))
            old = db.execute("SELECT change_at,status FROM ads WHERE uuid=?", (ad_id,)).fetchone()
            if old is not None:
                old_time = nav.change_timestamp(old["change_at"])
                new_time = nav.change_timestamp(changed)
                if old_time and new_time and new_time[0] < old_time[0]:
                    put(db, "timestamp_regressions", state(db, "timestamp_regressions") + 1)
                if old_time and new_time and new_time[0] == old_time[0] and old["status"] != status:
                    put(db, "equal_timestamp_status_changes", state(db, "equal_timestamp_status_changes") + 1)
            db.execute("INSERT INTO ads VALUES(?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                       "last_order=excluded.last_order,change_at=excluded.change_at,"
                       "status=excluded.status,detail_url=excluded.detail_url",
                       (ad_id, order, changed, status, detail_url))
            order += 1
        put(db, "next_order", order)
        put(db, "pages_done", state(db, "pages_done") + 1)
        put(db, "last_fingerprint", fingerprint(entries[-1]))
        put(db, "expected_next_id", next_id)
        put(db, "cursor_url", next_url if next_url else page_url)
        put(db, "polling", False)
        if next_url is None:
            put(db, "scan_complete", True)
            put(db, "phase", "detail")
            put(db, "end_url", page_url)
            put(db, "end_etag", response_headers.get("etag"))
            put(db, "end_last_modified", response_headers.get("last_modified"))
    return next_url is None


PENDING_SQL = """SELECT a.uuid,a.last_order,a.detail_url FROM ads a
        LEFT JOIN details d ON d.uuid=a.uuid
        WHERE a.status='ACTIVE' AND (d.uuid IS NULL OR d.last_order<a.last_order)"""


def pending_count(db):
    return db.execute("SELECT count(*) FROM (" + PENDING_SQL + ")").fetchone()[0]


def next_detail(db):
    return db.execute(PENDING_SQL + " ORDER BY a.last_order LIMIT 1").fetchone()


def backfill_candidates(db):
    """Only previously detailed, currently reconciled IT ads need a text backfill."""
    rows = db.execute("SELECT a.uuid,a.last_order,a.detail_url,d.occupations_json,"
                      "c.feed_order AS captured_order,c.outcome FROM ads a "
                      "JOIN details d ON d.uuid=a.uuid AND d.last_order=a.last_order "
                      "LEFT JOIN capture_state c ON c.uuid=a.uuid "
                      "WHERE a.status='ACTIVE' ORDER BY a.last_order").fetchall()
    for row in rows:
        if row["captured_order"] == row["last_order"] and row["outcome"] != "failed":
            continue
        occupations = json.loads(row["occupations_json"])
        if any(nav.normalized_label(item.get("level1")) == "it" for item in occupations):
            yield row


def next_backfill(db):
    return next(backfill_candidates(db), None)


def backfill_count(db):
    return sum(1 for _ in backfill_candidates(db))


def capture_outcome(db, ad_id, order, status, outcome, reason=None, digest=None):
    db.execute("INSERT INTO capture_state VALUES(?,?,?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
               "feed_order=excluded.feed_order,checked_at=excluded.checked_at,"
               "current_status=excluded.current_status,outcome=excluded.outcome,"
               "reason=excluded.reason,content_hash=excluded.content_hash",
               (ad_id, order, nav.iso_utc(datetime.now(timezone.utc)), status,
                outcome, reason, digest))


def store_capture(db, detail, record, *, backfill=False):
    """Store safe text and processing state in the caller's detail transaction."""
    ad_id, order, status = record[:3]
    locations = json.loads(record[3])
    occupations = json.loads(record[4])
    is_it = any(nav.normalized_label(item.get("level1")) == "it" for item in occupations)
    if not is_it:
        had_capture = db.execute("SELECT 1 FROM captures WHERE uuid=? LIMIT 1", (ad_id,)).fetchone() is not None
        if backfill or had_capture:
            outcome = "not_it" if record[9] else "unavailable"
            reason = "current_category_changed" if record[9] else "missing_content"
            capture_outcome(db, ad_id, order, status, outcome, reason)
        return "not_it"
    ad = detail.get("ad_content")
    if not isinstance(ad, dict):
        capture_outcome(db, ad_id, order, status, "unavailable", "missing_content")
        return "unavailable"
    counties = {nav.normalized_label(item.get("county")) for item in locations}
    if "innlandet" in counties:
        basis = "confirmed_innlandet"
    elif any(counties):
        basis = "remote_review_candidate"
    else:
        capture_outcome(db, ad_id, order, status, "review_blocked", "unknown_location")
        return "review_blocked"
    cleaned, actions, reason = clean_description(ad.get("description"), ad.get("contactList"))
    if cleaned is None:
        outcome = "unavailable" if reason in ("missing_description", "no_safe_readable_text") else "review_blocked"
        capture_outcome(db, ad_id, order, status, outcome, reason)
        return outcome
    digest = content_hash(cleaned)
    now = nav.iso_utc(datetime.now(timezone.utc))
    db.execute("INSERT OR IGNORE INTO captures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
               (ad_id, digest, cleaned, now, now, status, record[5], record[6],
                record[7], record[8], record[3], record[4], basis, CLEANING_VERSION,
                json.dumps(actions), "pending_human_review"))
    db.execute("UPDATE captures SET last_seen_at=? WHERE uuid=? AND content_hash=?",
               (now, ad_id, digest))
    capture_outcome(db, ad_id, order, status, "saved", None, digest)
    return "saved"


def safe_text(value):
    return value if isinstance(value, str) and value.strip() else None


def safe_list(ad, field, keys):
    values = ad.get(field)
    if not isinstance(values, list):
        return []
    return [{key: safe_text(item.get(key)) for key in keys}
            for item in values if isinstance(item, dict)]


def detail_record(detail, ad_id, order):
    if nav.usable_uuid(detail.get("uuid")) != ad_id:
        raise DiscoveryError("detail: UUID mismatch")
    status = detail.get("status")
    if status not in ("ACTIVE", "INACTIVE"):
        raise DiscoveryError("detail: invalid status")
    ad = detail.get("ad_content")
    available = isinstance(ad, dict)
    if not available:
        ad = {}
    locations = safe_list(ad, "workLocations", ("county", "municipal"))
    occupations = safe_list(ad, "occupationCategories", ("level1", "level2"))
    source_link = next((value for key in ("sourceurl", "link")
                        if (value := safe_text(ad.get(key))) and value.startswith(("https://", "http://"))), None)
    return (ad_id, order, status, json.dumps(locations, ensure_ascii=False),
            json.dumps(occupations, ensure_ascii=False), safe_text(ad.get("published")),
            safe_text(ad.get("updated")), source_link, safe_text(ad.get("source")),
            int(available), int(has_readable_text(ad.get("description"))))


def summarize(db):
    rows = db.execute("SELECT d.* FROM details d JOIN ads a ON a.uuid=d.uuid "
                      "AND a.last_order=d.last_order WHERE a.status='ACTIVE'").fetchall()
    by_occupation = {}
    by_occupation_innlandet = {}
    missing_categories = missing_locations = inactive = no_text = no_content = 0
    it_all = it_innlandet = 0
    for row in rows:
        inactive += row["status"] == "INACTIVE"
        no_text += not row["has_text"]
        no_content += not row["content_available"]
        locations = json.loads(row["locations_json"])
        occupations = json.loads(row["occupations_json"])
        counties = {nav.normalized_label(item.get("county")) for item in locations}
        categories = {item["level1"].strip().upper() for item in occupations
                      if isinstance(item.get("level1"), str) and item["level1"].strip()}
        if not any(counties):
            missing_locations += 1
        if not categories:
            missing_categories += 1
        if not row["has_text"]:
            continue
        in_innlandet = "innlandet" in counties
        for category in categories:
            by_occupation[category] = by_occupation.get(category, 0) + 1
            if in_innlandet:
                by_occupation_innlandet[category] = by_occupation_innlandet.get(category, 0) + 1
        if any(nav.normalized_label(category) == "it" for category in categories):
            it_all += 1
            it_innlandet += in_innlandet
    saved_by_basis = {"confirmed_innlandet": 0, "remote_review_candidate": 0}
    for capture in db.execute("SELECT c.selection_basis FROM captures c WHERE c.rowid=("
                              "SELECT c2.rowid FROM captures c2 WHERE c2.uuid=c.uuid "
                              "ORDER BY c2.last_seen_at DESC,c2.captured_at DESC,c2.rowid DESC LIMIT 1)"):
        saved_by_basis[capture[0]] = saved_by_basis.get(capture[0], 0) + 1
    feed_dates = db.execute("SELECT min(change_at),max(change_at),sum(change_at IS NULL) FROM events").fetchone()
    return {
        "label": "metadata and current-text availability discovery; not representative market coverage",
        "since": state(db, "since"), "phase": state(db, "phase"),
        "scan_complete": state(db, "scan_complete"), "detail_complete": state(db, "phase") == "done",
        "pages_saved": state(db, "pages_done"),
        "earliest_feed_change_utc": feed_dates[0], "latest_feed_change_utc": feed_dates[1],
        "missing_feed_change_timestamps": feed_dates[2],
        "entries_saved": db.execute("SELECT count(*) FROM events").fetchone()[0],
        "distinct_ads": db.execute("SELECT count(*) FROM ads").fetchone()[0],
        "active_candidates": db.execute("SELECT count(*) FROM ads WHERE status='ACTIVE'").fetchone()[0],
        "details_saved": len(rows), "pending_details": pending_count(db),
        "pending_it_text_backfill": backfill_count(db),
        "text_capture_versions": db.execute("SELECT count(*) FROM captures").fetchone()[0],
        "distinct_ads_with_saved_text": db.execute("SELECT count(DISTINCT uuid) FROM captures").fetchone()[0],
        "confirmed_innlandet_with_saved_text": saved_by_basis["confirmed_innlandet"],
        "remote_review_candidates_with_saved_text": saved_by_basis["remote_review_candidate"],
        "cleaning_review_flags": db.execute("SELECT count(*) FROM capture_state "
                                            "WHERE outcome='review_blocked'").fetchone()[0],
        "capture_unavailable": db.execute("SELECT count(*) FROM capture_state "
                                          "WHERE outcome='unavailable'").fetchone()[0],
        "no_usable_text_in_details": no_text,
        "unavailable_content": no_content + db.execute(
            "SELECT count(*) FROM failures f JOIN ads a ON a.uuid=f.uuid "
            "AND a.last_order=f.feed_order WHERE a.status='ACTIVE' AND f.kind='detail_404'").fetchone()[0],
        "missing_categories": missing_categories, "missing_locations": missing_locations,
        "inactive_responses": inactive,
        "failures": db.execute("SELECT count(*) FROM failures f JOIN ads a ON a.uuid=f.uuid "
                               "AND a.last_order=f.feed_order WHERE a.status='ACTIVE' "
                               "AND f.kind!='detail_404'").fetchone()[0],
        "failure_reasons": dict(db.execute("SELECT f.kind,count(*) FROM failures f JOIN ads a "
                                           "ON a.uuid=f.uuid AND a.last_order=f.feed_order "
                                           "WHERE a.status='ACTIVE' GROUP BY f.kind").fetchall()),
        "by_occupation_level1_with_text": dict(sorted(by_occupation.items())),
        "by_occupation_level1_with_text_innlandet": dict(sorted(by_occupation_innlandet.items())),
        "it_with_text_all_locations": it_all, "it_with_text_innlandet": it_innlandet,
        "timestamp_regressions": state(db, "timestamp_regressions"),
        "equal_timestamp_status_changes": state(db, "equal_timestamp_status_changes"),
        "current_end_page_url": state(db, "end_url"),
        "last_stop": state(db, "last_stop"),
        "category_counts_may_overlap": True,
    }


def write_summary(folder, summary):
    target = folder / "summary.json"
    temporary = folder / "summary.tmp"
    temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def save_detail_success(db, body, ad_id, order, *, backfill):
    detail = nav.parse_json(body, "detail")
    record = detail_record(detail, ad_id, order)
    with db:
        db.execute("INSERT INTO details VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                   "last_order=excluded.last_order,status=excluded.status,"
                   "locations_json=excluded.locations_json,occupations_json=excluded.occupations_json,"
                   "published=excluded.published,updated=excluded.updated,source_link=excluded.source_link,"
                   "source_id=excluded.source_id,content_available=excluded.content_available,"
                   "has_text=excluded.has_text", record)
        store_capture(db, detail, record, backfill=backfill)
        db.execute("DELETE FROM failures WHERE uuid=? AND feed_order=?", (ad_id, order))


def record_request_failure(db, ad_id, order, kind, *, backfill):
    with db:
        db.execute("INSERT INTO failures VALUES(?,?,?) ON CONFLICT(uuid,feed_order) "
                   "DO UPDATE SET kind=excluded.kind", (ad_id, order, kind))
        if backfill:
            capture_outcome(db, ad_id, order, "UNKNOWN", "failed", kind)


def export_captures(db, folder):
    """Export edited captures from SQLite; no credentials or network access."""
    export_root = folder / "exports"
    export_root.mkdir(exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC-") + uuid.uuid4().hex[:8]
    output = export_root / run_id
    output.mkdir(exist_ok=False)
    count = 0
    rows = db.execute("SELECT c.*,s.current_status,s.outcome FROM captures c "
                      "LEFT JOIN capture_state s ON s.uuid=c.uuid ORDER BY c.uuid,c.captured_at")
    for row in rows:
        record = {
            "label": "edited contact-cleaned API text capture; not an unchanged NAV response",
            "uuid": row["uuid"], "cleaned_description": row["cleaned_text"],
            "content_hash_sha256": row["content_hash"],
            "captured_at_utc": row["captured_at"], "last_seen_at_utc": row["last_seen_at"],
            "source_status_at_capture": row["source_status"],
            "latest_checked_status": row["current_status"],
            "latest_capture_outcome": row["outcome"],
            "published": row["published"], "updated": row["updated"],
            "source_link": row["source_link"], "source_id": row["source_id"],
            "work_locations": json.loads(row["locations_json"]),
            "occupation_categories": json.loads(row["occupations_json"]),
            "selection_basis": row["selection_basis"],
            "cleaning_version": row["cleaning_version"],
            "cleaning_actions": json.loads(row["cleaning_actions_json"]),
            "review_state": row["review_state"],
        }
        target = output / (row["uuid"] + "-" + row["content_hash"][:12] + ".json")
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        count += 1
    return output, count


def run(db, folder, max_pages, max_details, max_seconds, opener=None):
    opener = opener or build_opener(nav.NoRedirect())
    deadline = time.monotonic() + max_seconds
    page_requests = detail_requests = backfill_requests = 0
    stop = None
    try:
        if state(db, "phase") == "done" and backfill_count(db):
            with db:
                put(db, "phase", "detail")
        if state(db, "phase") == "done":
            stop = "already_complete; use --mode poll to check the end page"
        else:
            token = get_token(opener, deadline)
            auth = {"Accept": "application/json", "Authorization": "Bearer " + token}
            while state(db, "phase") == "scan" and page_requests < max_pages:
                if time.monotonic() >= deadline:
                    stop = "time_limit"
                    break
                url = state(db, "cursor_url")
                if url != nav.FEED_URL:
                    url = nav.validated_nav_url(url, "pagination")
                headers = dict(auth)
                if state(db, "polling"):
                    if state(db, "end_etag"):
                        headers["If-None-Match"] = state(db, "end_etag")
                    if state(db, "end_last_modified"):
                        headers["If-Modified-Since"] = state(db, "end_last_modified")
                else:
                    headers["If-Modified-Since"] = format_datetime(nav.parse_since(state(db, "since")), usegmt=True)
                code, body, response_headers = fetch(opener, url, headers, deadline)
                if code == "time_limit":
                    stop = "time_limit"
                    break
                page_requests += 1
                if code == 304 and state(db, "polling"):
                    with db:
                        put(db, "scan_complete", True)
                        put(db, "phase", "detail")
                        put(db, "polling", False)
                    stop = "end_page_unchanged"
                    break
                if code in (401, 403, 429):
                    stop = f"feed: HTTP {code}"
                    break
                if code != 200:
                    stop = f"feed: {code}"
                    break
                try:
                    page = nav.parse_json(body, "feed")
                    at_end = save_page(db, page, url, response_headers)
                except (nav.CollectionError, DiscoveryError) as exc:
                    stop = str(exc)
                    break
                if page_requests % 25 == 0 or at_end:
                    print(f"Feed progress: pages this session={page_requests}, saved={state(db, 'pages_done')}, "
                          f"entries={db.execute('SELECT count(*) FROM events').fetchone()[0]}, "
                          f"current end={at_end}", flush=True)
            if state(db, "phase") == "scan" and stop is None:
                stop = "page_limit"
            backfill_exhausted = False
            while state(db, "phase") == "detail" and detail_requests < max_details:
                if time.monotonic() >= deadline:
                    stop = "time_limit"
                    break
                candidate = None if backfill_exhausted else next_backfill(db)
                backfill = candidate is not None
                if candidate is None:
                    backfill_exhausted = True
                    candidate = next_detail(db)
                if candidate is None:
                    with db:
                        put(db, "phase", "done")
                    stop = "detail_complete"
                    break
                ad_id, order = candidate["uuid"], candidate["last_order"]
                url = nav.validated_nav_url(candidate["detail_url"], "detail")
                code, body, _ = fetch(opener, url, auth, deadline)
                if code == "time_limit":
                    stop = "time_limit"
                    break
                detail_requests += 1
                backfill_requests += backfill
                if code != 200:
                    record_request_failure(db, ad_id, order, f"detail_{code}", backfill=backfill)
                    stop = f"detail: HTTP {code}" if isinstance(code, int) else f"detail: {code}"
                    break
                else:
                    try:
                        save_detail_success(db, body, ad_id, order, backfill=backfill)
                    except (nav.CollectionError, DiscoveryError):
                        record_request_failure(db, ad_id, order, "invalid_detail", backfill=backfill)
                        stop = "detail: invalid response"
                        break
                if detail_requests % 100 == 0:
                    print(f"Detail progress: requests this session={detail_requests}, "
                          f"backfill={backfill_requests}, pending={pending_count(db)}, "
                          f"backfill pending={backfill_count(db)}", flush=True)
            if state(db, "phase") == "detail" and stop is None:
                stop = "detail_limit"
    except (nav.CollectionError, DiscoveryError) as exc:
        stop = str(exc)
    except sqlite3.Error:
        stop = "database: operation failed"
    except OSError:
        stop = "output: operation failed"
    except KeyboardInterrupt:
        stop = "interrupted"
    finally:
        with db:
            put(db, "last_stop", stop)
        summary = summarize(db)
        summary["session_page_requests"] = page_requests
        summary["session_detail_requests"] = detail_requests
        summary["session_backfill_requests"] = backfill_requests
        write_summary(folder, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("start", "resume", "poll", "export"), required=True)
    parser.add_argument("--since", help="ISO-8601 UTC start, required with start")
    parser.add_argument("--db", type=Path, help="state.sqlite3 from an earlier discovery run")
    parser.add_argument("--max-pages", type=nav.positive_int, default=MAX_PAGES)
    parser.add_argument("--max-details", type=nav.positive_int, default=MAX_DETAILS)
    parser.add_argument("--max-seconds", type=nav.positive_int, default=MAX_SECONDS)
    args = parser.parse_args(argv)
    if args.max_pages > MAX_PAGES or args.max_details > MAX_DETAILS or args.max_seconds > MAX_SECONDS:
        parser.error("session limits cannot exceed 1000 pages, 2000 details, or 1200 seconds")
    if args.mode == "start":
        if args.since is None or args.db is not None:
            parser.error("start requires --since and no --db")
        since = nav.parse_since(args.since)
        folder, db = initialize(ROOT, since)
    else:
        if args.since is not None or args.db is None or not args.db.is_file():
            parser.error("resume/poll/export requires an existing --db and no --since")
        folder = args.db.resolve().parent
        backup_path = migrate_schema(args.db)
        if backup_path is not None:
            print(f"Database backup: {backup_path}")
        db = connect(args.db)
        if state(db, "since") is None:
            parser.error("database has no discovery state")
        if args.mode == "export":
            output, count = export_captures(db, folder)
            print(f"Exported edited captures: {count}; directory: {output}")
            return 0
        if args.mode == "poll":
            if state(db, "end_url") is None or not state(db, "scan_complete"):
                parser.error("poll requires a previously reached feed end")
            with db:
                put(db, "phase", "scan")
                put(db, "scan_complete", False)
                put(db, "cursor_url", state(db, "end_url"))
                put(db, "expected_next_id", None)
                put(db, "polling", True)
    summary = run(db, folder, args.max_pages, args.max_details, args.max_seconds)
    print(f"State: {folder / 'state.sqlite3'}")
    print(f"Summary: {folder / 'summary.json'}")
    print(f"Phase: {summary['phase']}; stop: {summary['last_stop']}; "
          f"pages this session: {summary['session_page_requests']}; "
          f"details this session: {summary['session_detail_requests']}; "
          f"pending details: {summary['pending_details']}")
    return 0 if summary["last_stop"] in ("detail_complete", "detail_limit", "page_limit", "time_limit",
                                          "end_page_unchanged", "already_complete; use --mode poll to check the end page") else 1


if __name__ == "__main__":
    sys.exit(main())
