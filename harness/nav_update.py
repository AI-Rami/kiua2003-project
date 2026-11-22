"""One resumable NAV catch-up command within operational safety ceilings.

run_update() is also the entry point for a future UI button. No UI is built here.
"""

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import uuid

import nav_collect as nav
import nav_discover as discovery
import nav_skeleton as extraction
import nav_skill_summary as statistics
from nav_text import CLEANING_VERSION, cleaned_input_issue


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3"
DEFAULT_INDEX = ROOT / "out/current/index.json"
DEFAULT_CURRENT = ROOT / "out/current"
DEFAULT_STATISTICS = ROOT / "out/statistics"
MAX_EXTRACTIONS = 20
MAX_ATTEMPTS = 2
LEGACY_INTENTIONAL_BLOCKS = {
    "8119dbb1-530f-4307-9ee0-e030c2b8e581",
    "1f614033-73b3-4c26-bda5-3d9abe281a12",
}


class UpdateError(Exception):
    """A sanitized workflow diagnostic."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_index(path, value):
    """Replace the complete selection atomically; interrupted writes leave the old index."""
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_index(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise UpdateError("current index: unreadable UTF-8 JSON") from None
    if not isinstance(value, dict) or value.get("schema_version") != 1 or not isinstance(value.get("entries"), list):
        raise UpdateError("current index: invalid structure")
    ids = [entry.get("uuid") for entry in value["entries"] if isinstance(entry, dict)]
    if len(ids) != len(value["entries"]) or len(ids) != len(set(ids)):
        raise UpdateError("current index: duplicate or invalid entries")
    return value


def entry_for(index, ad_id):
    return next((entry for entry in index["entries"] if entry["uuid"] == ad_id), None)


def replace_entry(index, entry):
    old = entry_for(index, entry["uuid"])
    if old is None:
        index["entries"].append(entry)
    else:
        index["entries"][index["entries"].index(old)] = entry


def record_queue(db, ad_id, state, *, digest=None, error=None):
    with db:
        db.execute("UPDATE processing_queue SET state=?,content_hash=COALESCE(?,content_hash),"
                   "error_kind=?,updated_at=? WHERE uuid=?",
                   (state, digest, error, utc_now(), ad_id))


def poll_or_resume(db, folder, max_pages, max_details, max_seconds, progress=None):
    """Use NAV's saved final-page cursor or continue its unfinished scan/detail phase."""
    phase = discovery.state(db, "phase")
    if phase == "done":
        end_url = discovery.state(db, "end_url")
        if not end_url or not discovery.state(db, "scan_complete"):
            raise UpdateError("discovery: no verified final-page continuation")
        with db:
            discovery.put(db, "phase", "scan")
            discovery.put(db, "scan_complete", False)
            discovery.put(db, "cursor_url", end_url)
            discovery.put(db, "expected_next_id", None)
            discovery.put(db, "polling", True)
    elif phase not in ("scan", "detail"):
        raise UpdateError("discovery: unsupported saved phase")
    return discovery.run(db, folder, max_pages, max_details, max_seconds, progress=progress)


def saved_capture(db, ad_id, order, digest):
    row = db.execute("SELECT cleaned_text,source_link,cleaning_version,review_state,published,updated,source_id "
                     "FROM captures WHERE uuid=? AND content_hash=?", (ad_id, digest)).fetchone()
    if row is not None and row["cleaning_version"] == CLEANING_VERSION:
        return row
    # The original nine-ad review used a separate version-2 table; do not read blocked entries here.
    row = db.execute("SELECT cleaned_text,source_link,cleaning_version,review_state,published,updated,source_id "
                     "FROM targeted_reprocess WHERE uuid=? AND content_hash=? AND outcome='saved'",
                     (ad_id, digest)).fetchone()
    return row if row is not None and row["cleaning_version"] == CLEANING_VERSION else None


def saved_title(db, ad_id, order):
    row = db.execute("SELECT title,checked_at FROM ad_titles WHERE uuid=? AND last_order=?",
                     (ad_id, order)).fetchone()
    return row if row is not None and isinstance(row["title"], str) and row["title"].strip() else None


def proposed_stale(old, reason, *, pending_hash=None, activity=None):
    if old is None:
        return None
    revised = dict(old)
    if old.get("status") == "current":
        revised["previous_result_path"] = old.get("result_path")
        revised["previous_content_sha256"] = old.get("content_sha256")
        revised["result_path"] = None
        revised["status"] = "stale"
    revised["processing_status"] = reason
    if pending_hash:
        revised["pending_content_sha256"] = pending_hash
    if activity:
        revised["activity_status"] = activity
    return revised


def block_version(db, index, index_path, ad_id, order, reason, *, digest=None, source_url=None):
    """Record a sanitized block for one feed event, retaining any prior result."""
    old = entry_for(index, ad_id)
    revised = proposed_stale(old, reason) if old is not None else {"uuid": ad_id}
    if revised.get("status") != "stale":
        revised["status"] = "blocked"
    revised["result_path"] = None
    revised["block_kind"] = "version"
    revised["blocked_feed_order"] = order
    revised["blocked_reason"] = reason
    revised["reason"] = reason
    revised.pop("pending_content_sha256", None)
    if digest is not None:
        revised["blocked_content_sha256"] = digest
    else:
        revised.pop("blocked_content_sha256", None)
    if source_url and not revised.get("source_url"):
        revised["source_url"] = source_url
    replace_entry(index, revised)
    write_index(index_path, index)
    now = utc_now()
    with db:
        db.execute("INSERT INTO processing_blocks VALUES(?,?,?,?,?) ON CONFLICT(uuid,feed_order) "
                   "DO UPDATE SET reason=excluded.reason,content_hash=excluded.content_hash",
                   (ad_id, order, reason, digest, now))
        db.execute("UPDATE processing_queue SET state='blocked',content_hash=COALESCE(?,content_hash),"
                   "error_kind=?,updated_at=? WHERE uuid=? AND feed_order=?",
                   (digest, reason, now, ad_id, order))


def release_older_version_block(index, index_path, old, order):
    """A later feed event may be reassessed; the old block remains in SQLite history."""
    blocked_order = old.get("blocked_feed_order")
    if type(blocked_order) is not int or blocked_order <= 0 or blocked_order > order:
        raise UpdateError("current index: invalid version-specific block")
    if blocked_order == order:
        return old
    if old["status"] == "blocked":
        index["entries"].remove(old)
        write_index(index_path, index)
        return None
    revised = dict(old)
    for field in ("block_kind", "blocked_feed_order", "blocked_reason", "blocked_content_sha256"):
        revised.pop(field, None)
    replace_entry(index, revised)
    write_index(index_path, index)
    return revised


def existing_response(stage):
    path = stage / "response.json"
    if not path.is_file():
        return None
    try:
        response = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise UpdateError("extraction: saved response is invalid JSON") from None
    if not isinstance(response, dict):
        raise UpdateError("extraction: saved response is not an object")
    return response


def prepare_stage(stage, prepared, run_id, timestamp):
    stage.mkdir(parents=True, exist_ok=False)
    (stage / "prepared_ad.txt").write_text(prepared["prepared"], encoding="utf-8")
    extraction.save_json(stage / "run_meta.json", {"run_id": run_id, "timestamp": timestamp})


def publish_result(index, index_path, current_root, ad_id, digest, stage, prepared, result):
    """Make immutable version visible, then flip the one selected index pointer."""
    destination = current_root / ad_id / "versions" / digest
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        os.replace(stage, destination)
    elif not (destination / "result.json").is_file():
        raise UpdateError("publish: existing version directory is incomplete")
    request = json.loads((destination / "request.json").read_text(encoding="utf-8"))
    schema = request["text"]["format"]["schema"]
    schema_hash = hashlib.sha256(json.dumps(schema, ensure_ascii=False, sort_keys=True,
                                            separators=(",", ":")).encode("utf-8")).hexdigest()
    old = entry_for(index, ad_id)
    warning = "No human meaning review has been performed on this updated extraction."
    selected = {"uuid": ad_id, "status": "current", "source_url": result["source_url"],
                "content_sha256": digest, "cleaning_version": CLEANING_VERSION,
                "result_path": (destination / "result.json").relative_to(ROOT).as_posix(),
                "original_run_id": result["run_id"],
                "original_run_path": destination.relative_to(ROOT).as_posix(),
                "prompt_sha256": sha256_text(request["instructions"]),
                "schema_sha256": schema_hash, "format_version": 2,
                "model_id": request["model"], "reasoning_effort": request["reasoning"]["effort"],
                "max_output_tokens": request["max_output_tokens"],
                "validation_status": "passed", "capture_review_state": prepared["capture_provenance"]["review_state"],
                "activity_status": "ACTIVE", "activity_checked_at_utc": utc_now(),
                "processing_status": "complete", "review_warnings": [warning]}
    if isinstance(result.get("title"), str) and result["title"].strip():
        selected["display_title"] = result["title"].strip()
        checked_at = prepared.get("title_checked_at_utc")
        if isinstance(checked_at, str) and checked_at:
            selected["title_checked_at_utc"] = checked_at
    if old and old.get("content_sha256") != digest:
        selected["previous_result_path"] = old.get("result_path") or old.get("previous_result_path")
        selected["previous_content_sha256"] = old.get("previous_content_sha256") or old.get("content_sha256")
    replace_entry(index, selected)
    write_index(index_path, index)


def generate_statistics(index_path, current_root, statistics_root):
    records, counts = statistics.load_current_records(index_path, current_root)
    records, review_info = statistics.apply_selected_review(records)
    summary = statistics.aggregate(records)
    summary["status_counts"] = counts
    statistics.write_outputs(index_path, records, summary, output_root=statistics_root,
                             review_info=review_info)
    return summary


def statistics_need_refresh(index_path, statistics_root):
    path = statistics_root / "summary.json"
    if not path.is_file():
        return True
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
        review_hash = statistics.review_digest(statistics.SELECTED_REVIEW.read_bytes())
        return (summary.get("source_index_sha256") != hashlib.sha256(index_path.read_bytes()).hexdigest()
                or summary.get("review", {}).get("sha256") != review_hash)
    except (OSError, UnicodeError, ValueError):
        return True


def run_update(db_path=DEFAULT_DB, index_path=DEFAULT_INDEX, current_root=DEFAULT_CURRENT,
               statistics_root=DEFAULT_STATISTICS, *, max_pages=None,
               max_details=discovery.MAX_DETAILS, max_extractions=MAX_EXTRACTIONS,
               max_seconds=discovery.MAX_SECONDS, max_attempts=MAX_ATTEMPTS,
               discover_fn=None, extract_fn=None, progress=None):
    """Catch up from saved state within operational ceilings; reusable by a future UI button."""
    if ((max_pages is not None and not 1 <= max_pages <= discovery.MAX_PAGES)
            or not 1 <= max_details <= discovery.MAX_DETAILS
            or not 1 <= max_extractions <= MAX_EXTRACTIONS or not 1 <= max_seconds <= discovery.MAX_SECONDS
            or not 1 <= max_attempts <= 10):
        raise UpdateError("limits: nonpositive or above supported maximum")
    page_ceiling = discovery.MAX_PAGES if max_pages is None else max_pages
    db_path, index_path, current_root, statistics_root = map(Path,
        (db_path, index_path, current_root, statistics_root))
    if not db_path.is_file():
        raise UpdateError("discovery: saved database is missing")
    index = load_index(index_path)
    fixed_blocked = {entry["uuid"] for entry in index["entries"]
                     if entry.get("status") == "blocked"
                     and (entry.get("block_kind") == "intentional"
                          or entry["uuid"] in LEGACY_INTENTIONAL_BLOCKS)}
    started = time.monotonic()
    deadline = started + max_seconds
    report = {"pages": 0, "details": 0, "extraction_requests": 0, "processed": 0,
              "reused": 0, "blocked": 0, "failed": 0, "pending": 0,
              "discovery_stop": None, "status": "running", "statistics_refreshed": False}
    emit = progress or (lambda event: None)
    db = discovery.connect(db_path)
    try:
        emit({"stage": "limits", "pages": page_ceiling, "details": max_details,
              "extractions": max_extractions, "seconds": max_seconds})
        prior_feed_events = db.execute("SELECT count(*) FROM events").fetchone()[0]
        emit({"stage": "discovery", "message": "polling saved final page or resuming unfinished work"})
        remaining = max(1, int(deadline - time.monotonic()))
        if discover_fn is None:
            disc = poll_or_resume(db, db_path.parent, page_ceiling, max_details, remaining, emit)
        else:
            disc = discover_fn(db, db_path.parent, page_ceiling, max_details, remaining)
        report["pages"] = disc.get("session_page_requests", 0)
        report["details"] = disc.get("session_detail_requests", 0)
        report["discovery_stop"] = disc.get("last_stop")
        report["new_feed_events"] = db.execute("SELECT count(*) FROM events").fetchone()[0] - prior_feed_events
        emit({"stage": "discovery", "pages": report["pages"], "details": report["details"],
              "stop": report["discovery_stop"]})
        discovery_failed = (isinstance(report["discovery_stop"], str)
                            and (report["discovery_stop"].startswith(("feed:", "detail:", "token:",
                                                                       "database:", "output:"))
                                 or report["discovery_stop"] in ("interrupted", "already_complete; use --mode poll to check the end page")))
        # An unread feed page can supersede a candidate. Process only after the scan reaches its end.
        rows = (db.execute("SELECT * FROM processing_queue WHERE state!='complete' AND state!='blocked' "
                           "ORDER BY feed_order").fetchall()
                if discovery.state(db, "scan_complete") and not discovery_failed else [])
        for queue in rows:
            if time.monotonic() >= deadline:
                break
            ad_id, order = queue["uuid"], queue["feed_order"]
            old = entry_for(index, ad_id)
            if ad_id in fixed_blocked:
                record_queue(db, ad_id, "blocked", error="intentional_block")
                report["blocked"] += 1
                continue
            if old is not None and old.get("block_kind") == "version":
                blocked_order = old.get("blocked_feed_order")
                old = release_older_version_block(index, index_path, old, order)
                if blocked_order == order:
                    block_version(db, index, index_path, ad_id, order, old["blocked_reason"],
                                  digest=old.get("blocked_content_sha256"),
                                  source_url=old.get("source_url"))
                    report["blocked"] += 1
                    continue
            ad = db.execute("SELECT * FROM ads WHERE uuid=?", (ad_id,)).fetchone()
            if ad is None or ad["last_order"] != order:
                continue
            if ad["status"] == "INACTIVE":
                if old is not None:
                    revised = dict(old)
                    revised["activity_status"] = "INACTIVE"
                    revised["activity_checked_at_utc"] = utc_now()
                    replace_entry(index, revised)
                    write_index(index_path, index)
                record_queue(db, ad_id, "complete")
                report["reused"] += 1
                continue
            detail = db.execute("SELECT * FROM details WHERE uuid=? AND last_order=?", (ad_id, order)).fetchone()
            if detail is None:
                unavailable = db.execute("SELECT 1 FROM failures WHERE uuid=? AND feed_order=? AND kind='detail_404'",
                                         (ad_id, order)).fetchone()
                if unavailable:
                    block_version(db, index, index_path, ad_id, order, "detail_unavailable")
                    report["blocked"] += 1
                continue  # Discovery's detail phase or a later bounded run must finish first.
            if detail["status"] == "INACTIVE":
                if old is not None:
                    revised = dict(old)
                    revised["activity_status"] = "INACTIVE"
                    revised["activity_checked_at_utc"] = utc_now()
                    replace_entry(index, revised)
                    write_index(index_path, index)
                record_queue(db, ad_id, "complete")
                report["reused"] += 1
                continue
            saved = {"status": detail["status"], "ad_content": {
                "workLocations": json.loads(detail["locations_json"]),
                "occupationCategories": json.loads(detail["occupations_json"])}}
            relevance, reason = nav.relevance(saved)
            if relevance != "match":
                if relevance == "unknown":
                    block_version(db, index, index_path, ad_id, order,
                                  "relevance_unknown:" + str(reason), source_url=detail["source_link"])
                else:
                    replacement = proposed_stale(old, "relevance_nonmatch", activity=detail["status"])
                    if replacement is not None:
                        replace_entry(index, replacement)
                        write_index(index_path, index)
                    record_queue(db, ad_id, "complete", error="relevance_nonmatch")
                report["blocked" if relevance == "unknown" else "reused"] += 1
                continue
            capture_state = db.execute("SELECT * FROM capture_state WHERE uuid=? AND feed_order=?",
                                       (ad_id, order)).fetchone()
            if capture_state is None or capture_state["outcome"] != "saved" or not capture_state["content_hash"]:
                reason = ("input_" + capture_state["outcome"] if capture_state is not None
                          else "input_state_missing")
                block_version(db, index, index_path, ad_id, order, reason,
                              source_url=detail["source_link"])
                report["blocked"] += 1
                continue
            digest = capture_state["content_hash"]
            title_row = saved_title(db, ad_id, order)
            if old is not None and old.get("status") == "current" and old.get("content_sha256") == digest:
                revised = dict(old)
                revised["activity_status"] = "ACTIVE"
                revised["activity_checked_at_utc"] = utc_now()
                revised["processing_status"] = "reused_unchanged"
                if title_row is not None:
                    revised["display_title"] = title_row["title"].strip()
                    revised["title_checked_at_utc"] = title_row["checked_at"]
                replace_entry(index, revised)
                write_index(index_path, index)
                record_queue(db, ad_id, "complete", digest=digest)
                report["reused"] += 1
                continue
            if old is not None and old.get("status") == "stale" and old.get("pending_content_sha256") == digest:
                pass
            else:
                replacement = proposed_stale(old, "pending_changed_version", pending_hash=digest,
                                             activity="ACTIVE")
                if replacement is not None:
                    replace_entry(index, replacement)
                    write_index(index_path, index)
            capture = saved_capture(db, ad_id, order, digest)
            if (capture is None or not isinstance(capture["cleaned_text"], str)
                    or sha256_text(capture["cleaned_text"]) != digest
                    or capture["review_state"] != "auto_contact_checked"
                    or cleaned_input_issue(capture["cleaned_text"]) is not None
                    or not isinstance(capture["source_link"], str)
                    or not capture["source_link"].startswith("https://")):
                block_version(db, index, index_path, ad_id, order, "capture_invalid_or_unavailable",
                              digest=digest, source_url=detail["source_link"])
                report["blocked"] += 1
                continue
            if entry_for(index, ad_id) is None:
                replace_entry(index, {"uuid": ad_id, "status": "pending", "result_path": None,
                                      "source_url": capture["source_link"], "pending_content_sha256": digest,
                                      "processing_status": "pending_extraction", "activity_status": "ACTIVE"})
                write_index(index_path, index)
            if queue["content_hash"] != digest:
                with db:
                    db.execute("UPDATE processing_queue SET content_hash=?,attempts=0,state='pending',"
                               "error_kind=NULL,updated_at=? WHERE uuid=?", (digest, utc_now(), ad_id))
                attempts = 0
            else:
                attempts = queue["attempts"]
            work_root = db_path.parent / "processing" / ad_id / digest
            final_dir = current_root / ad_id / "versions" / digest
            if (final_dir / "result.json").is_file():
                try:
                    saved_response = json.loads((final_dir / "response.json").read_text(encoding="utf-8"))
                    saved_result = json.loads((final_dir / "result.json").read_text(encoding="utf-8"))
                    validation, _ = extraction.validate(saved_response, capture["cleaned_text"])
                    if (not validation["passed"] or saved_result.get("source_uuid") != ad_id
                            or (final_dir / "prepared_ad.txt").read_text(encoding="utf-8") != capture["cleaned_text"]):
                        raise UpdateError("publish: saved version failed recovery validation")
                except (OSError, UnicodeError, ValueError):
                    raise UpdateError("publish: saved version is unreadable") from None
                prepared = {"capture_provenance": {"review_state": capture["review_state"]},
                            "title_checked_at_utc": title_row["checked_at"] if title_row else None}
                publish_result(index, index_path, current_root, ad_id, digest, final_dir, prepared, saved_result)
                record_queue(db, ad_id, "complete", digest=digest)
                report["processed"] += 1
                emit({"stage": "published", "uuid": ad_id, "message": "recovered saved response"})
                continue
            prior_stage = work_root / f"attempt-{attempts}"
            response = (existing_response(prior_stage)
                        if attempts > 0 and queue["error_kind"] != "validation_failed" else None)
            if attempts >= max_attempts and response is None:
                record_queue(db, ad_id, "failed", digest=digest, error="attempt_limit")
                report["failed"] += 1
                emit({"stage": "failed", "uuid": ad_id, "reason": "attempt_limit"})
                continue
            if response is None and report["extraction_requests"] >= max_extractions:
                continue
            if response is None and deadline - time.monotonic() < extraction.TIMEOUT_SECONDS:
                break
            prepared = {"uuid": ad_id, "title": title_row["title"].strip() if title_row else None,
                        "title_checked_at_utc": title_row["checked_at"] if title_row else None,
                        "source_url": capture["source_link"],
                        "prepared": capture["cleaned_text"], "input_format": "cleaned-capture",
                        "capture_provenance": {"revised_version": CLEANING_VERSION,
                                               "content_hash_sha256": digest,
                                               "review_state": capture["review_state"],
                                               "published": capture["published"],
                                               "updated": capture["updated"],
                                               "source_id": capture["source_id"]}}
            if response is None:
                attempts += 1
                stage = work_root / f"attempt-{attempts}"
                run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC_ad-") + ad_id
                timestamp = utc_now()
                stage.parent.mkdir(parents=True, exist_ok=True)
                prepare_stage(stage, prepared, run_id, timestamp)
                with db:
                    db.execute("UPDATE processing_queue SET attempts=?,state='extracting',"
                               "error_kind=NULL,updated_at=? WHERE uuid=?", (attempts, utc_now(), ad_id))
                report["extraction_requests"] += 1
                emit({"stage": "extraction", "uuid": ad_id, "attempt": attempts})
                try:
                    response, elapsed = (extract_fn or extraction.extract)(prepared["prepared"], stage,
                                                                             cleaned_capture=True)
                except extraction.SkeletonError as exc:
                    record_queue(db, ad_id, "failed", digest=digest, error="model_request_failed")
                    revised = dict(entry_for(index, ad_id))
                    revised["status"] = "stale" if revised.get("previous_result_path") else "failed"
                    revised["processing_status"] = "model_request_failed"
                    replace_entry(index, revised)
                    write_index(index_path, index)
                    report["failed"] += 1
                    emit({"stage": "failed", "uuid": ad_id, "reason": "model_request_failed"})
                    if str(exc) in ("extract: HTTP 401", "extract: HTTP 403", "extract: HTTP 429",
                                    "extract: network or timeout failure",
                                    "extract: KIUA2003_API is unavailable or empty"):
                        break
                    continue
            else:
                stage = prior_stage
                meta = json.loads((stage / "run_meta.json").read_text(encoding="utf-8"))
                run_id, timestamp = meta["run_id"], meta["timestamp"]
                elapsed = 0.0
                emit({"stage": "extraction", "uuid": ad_id, "message": "reusing saved response"})
            try:
                result = extraction.validate_and_report(response, prepared, stage, run_id, timestamp, elapsed)
            except extraction.SkeletonError:
                record_queue(db, ad_id, "failed", digest=digest, error="validation_failed")
                revised = dict(entry_for(index, ad_id))
                revised["status"] = "stale" if revised.get("previous_result_path") else "failed"
                revised["processing_status"] = "validation_failed"
                replace_entry(index, revised)
                write_index(index_path, index)
                report["failed"] += 1
                emit({"stage": "failed", "uuid": ad_id, "reason": "validation_failed"})
                continue
            publish_result(index, index_path, current_root, ad_id, digest, stage, prepared, result)
            record_queue(db, ad_id, "complete", digest=digest)
            report["processed"] += 1
            emit({"stage": "published", "uuid": ad_id})
        report["pending"] = db.execute("SELECT count(*) FROM processing_queue WHERE state NOT IN ('complete','blocked')").fetchone()[0]
        report["feed_end_reached"] = bool(discovery.state(db, "scan_complete"))
        report["phase"] = discovery.state(db, "phase")
        if statistics_need_refresh(index_path, statistics_root):
            summary = generate_statistics(index_path, current_root, statistics_root)
            report["statistics_refreshed"] = True
            report["statistics_ads"] = summary["advertisement_count"]
        else:
            report["statistics_ads"] = json.loads((statistics_root / "summary.json").read_text(encoding="utf-8"))["advertisement_count"]
        if discovery_failed:
            report["status"] = "discovery_failed"
        elif report["failed"]:
            report["status"] = "processing_failed"
        elif report["pending"] or discovery.state(db, "phase") != "done":
            report["status"] = "partial_pending"
        elif (report["new_feed_events"] == 0
                and report["details"] == report["processed"] == report["reused"] == report["blocked"] == 0):
            report["status"] = "no_updates_found"
        else:
            report["status"] = "caught_up"
        if report["status"] == "partial_pending":
            if report["discovery_stop"] in ("page_limit", "detail_limit", "time_limit"):
                report["stop_reason"] = report["discovery_stop"]
            elif time.monotonic() >= deadline:
                report["stop_reason"] = "time_limit"
            elif report["extraction_requests"] >= max_extractions:
                report["stop_reason"] = "extraction_limit"
            else:
                report["stop_reason"] = "work_pending"
        elif report["status"] == "discovery_failed":
            report["stop_reason"] = report["discovery_stop"]
        elif report["status"] == "processing_failed":
            report["stop_reason"] = "processing_failure"
        else:
            report["stop_reason"] = report["status"]
        emit({"stage": "complete", **report})
        return report
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--max-pages", type=int, default=None,
                        help="optional test limit; normal mode uses the 1000-page operational ceiling")
    parser.add_argument("--max-details", type=int, default=discovery.MAX_DETAILS)
    parser.add_argument("--max-extractions", type=int, default=MAX_EXTRACTIONS)
    parser.add_argument("--max-seconds", type=int, default=discovery.MAX_SECONDS)
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    args = parser.parse_args(argv)
    def show(event):
        stage = event.get("stage")
        if stage == "complete":
            print(f"Update {event['status']}: pages={event['pages']}, details={event['details']}, "
                  f"model_requests={event['extraction_requests']}, processed={event['processed']}, "
                  f"reused={event['reused']}, blocked={event['blocked']}, failed={event['failed']}, "
                  f"pending={event['pending']}, feed_end_reached={event['feed_end_reached']}, "
                  f"statistics_ads={event['statistics_ads']}, stop_reason={event['stop_reason']}", flush=True)
        elif stage == "limits":
            print(f"Operational limits: pages={event['pages']}, details={event['details']}, "
                  f"model_requests={event['extractions']}, seconds={event['seconds']}", flush=True)
        elif stage == "feed_page" and (event["pages"] % 10 == 0 or event["at_end"]):
            print(f"Feed progress: pages={event['pages']}, total_saved={event['total_pages']}, "
                  f"feed_end_reached={event['at_end']}", flush=True)
        elif stage == "detail" and event["details"] % 25 == 0:
            print(f"Detail progress: requests={event['details']}", flush=True)
        elif stage == "detail_unavailable":
            print(f"Detail unavailable: {event['uuid']} (HTTP 404)", flush=True)
        elif stage == "extraction":
            print(f"Extraction: {event['uuid']} attempt={event.get('attempt', 'saved response')}", flush=True)
        elif stage == "published":
            print(f"Published: {event['uuid']}", flush=True)
        elif stage == "failed":
            print(f"Failed: {event['uuid']} reason={event['reason']}", flush=True)
        elif stage == "discovery" and "stop" in event:
            print(f"Discovery: pages={event['pages']}, details={event['details']}, stop={event['stop']}", flush=True)
        elif stage == "discovery":
            print("Discovery: polling saved state or resuming", flush=True)
    try:
        result = run_update(args.db, max_pages=args.max_pages, max_details=args.max_details,
                            max_extractions=args.max_extractions, max_seconds=args.max_seconds,
                            max_attempts=args.max_attempts, progress=show)
    except (UpdateError, sqlite3.Error, OSError, ValueError, statistics.SummaryError) as exc:
        print(f"Update failed: {type(exc).__name__ if not isinstance(exc, UpdateError) else str(exc)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Update interrupted; saved discovery and processing progress can be resumed with the same command.",
              file=sys.stderr)
        return 130
    return 1 if result["status"] in ("discovery_failed", "processing_failed") else 0


if __name__ == "__main__":
    sys.exit(main())
