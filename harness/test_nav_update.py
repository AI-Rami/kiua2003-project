"""Isolated, model-free checks for the incremental update workflow."""

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid

import nav_discover as discovery
import nav_skeleton as extraction
import nav_update as update
from nav_text import CLEANING_VERSION


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=update.ROOT / "out")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        folder, db = discovery.initialize(self.root / "nav_discovery", discovery.nav.parse_since("2026-08-01T00:00:00Z"))
        self.db_path = folder / "state.sqlite3"
        db.close()
        self.current = self.root / "current"
        self.current.mkdir()
        self.index_path = self.current / "index.json"
        self.index_path.write_text(json.dumps({"schema_version": 1, "entries": []}), encoding="utf-8")
        self.statistics = self.root / "statistics"
        self.ad_id = str(uuid.uuid4())
        self.source = "https://example.org/ad"
        self.calls = 0

    @staticmethod
    def no_changes(db, folder, pages, details, seconds):
        with db:
            discovery.put(db, "scan_complete", True)
            discovery.put(db, "phase", "done")
        return {"session_page_requests": 1, "session_detail_requests": 0,
                "last_stop": "end_page_unchanged"}

    @staticmethod
    def changed(db, folder, pages, details, seconds):
        with db:
            discovery.put(db, "scan_complete", True)
            discovery.put(db, "phase", "done")
        return {"session_page_requests": 1, "session_detail_requests": 1,
                "last_stop": "detail_complete"}

    def queue_ad(self, text="Du må kunne Python.", order=1, ad_id=None, *, outcome="saved", title=None):
        ad_id = ad_id or self.ad_id
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        db = discovery.connect(self.db_path)
        with db:
            db.execute("INSERT INTO ads VALUES(?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                       "last_order=excluded.last_order,status=excluded.status",
                       (ad_id, order, "2026-11-02T00:00:00Z", "ACTIVE",
                        "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + ad_id))
            db.execute("INSERT INTO details VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                       "last_order=excluded.last_order,status=excluded.status",
                       (ad_id, order, "ACTIVE", json.dumps([{"county": "INNLANDET", "municipal": "Hamar"}]),
                        json.dumps([{"level1": "IT", "level2": "Utvikling"}]), None, None,
                        self.source, "synthetic", 1, 1))
            if title is not None:
                db.execute("INSERT INTO ad_titles VALUES(?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                           "last_order=excluded.last_order,title=excluded.title,checked_at=excluded.checked_at",
                           (ad_id, order, title, "2026-11-02T00:00:00Z"))
            db.execute("INSERT INTO capture_state VALUES(?,?,?,?,?,?,?) ON CONFLICT(uuid) DO UPDATE SET "
                       "feed_order=excluded.feed_order,outcome=excluded.outcome,content_hash=excluded.content_hash",
                       (ad_id, order, "2026-11-02T00:00:00Z", "ACTIVE", outcome, None, digest))
            if outcome == "saved":
                db.execute("INSERT OR REPLACE INTO captures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (ad_id, digest, text, "2026-11-02T00:00:00Z", "2026-11-02T00:00:00Z", "ACTIVE",
                            None, None, self.source, "synthetic", "[]", "[]", "confirmed_innlandet",
                            CLEANING_VERSION, "{}", "auto_contact_checked"))
            db.execute("INSERT INTO processing_queue VALUES(?,?,?,'pending',NULL,0,NULL,?) "
                       "ON CONFLICT(uuid) DO UPDATE SET feed_order=excluded.feed_order,state='pending',"
                       "content_hash=NULL,attempts=0,error_kind=NULL",
                       (ad_id, order, "ACTIVE", "2026-11-02T00:00:00Z"))
        db.close()
        return digest

    def response(self, text):
        skill = "SQL" if "SQL" in text else "Python"
        item = {"skills": [skill], "relationship": "single", "classification": "required",
                "mention_type": "candidate_qualification", "skill_evidence": text,
                "classification_context": None}
        return {"status": "completed", "id": "resp-" + str(uuid.uuid4()), "model": extraction.MODEL,
                "output": [{"content": [{"type": "output_text", "text": json.dumps({"items": [item]})}]}],
                "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}}

    def fake_extract(self, text, stage, *, cleaned_capture):
        self.calls += 1
        extraction.save_json(stage / "request.json", extraction.request_payload(text, cleaned_capture=True))
        response = self.response(text)
        extraction.save_json(stage / "response.json", response)
        return response, 0.01

    def run_local(self, discover=None, extract=None):
        return update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                 max_pages=2, max_details=5, max_extractions=2, max_seconds=120,
                                 discover_fn=discover or self.changed,
                                 extract_fn=extract or self.fake_extract)

    def index(self):
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def test_no_updates_and_existing_statistics_remain(self):
        self.run_local(discover=self.no_changes)
        before = {p.name: p.read_bytes() for p in self.statistics.iterdir()}
        result = self.run_local(discover=self.no_changes)
        self.assertEqual(result["status"], "no_updates_found")
        self.assertEqual(result["extraction_requests"], 0)
        self.assertEqual({p.name: p.read_bytes() for p in self.statistics.iterdir()}, before)

    def test_no_updates_after_discovery_reports_detail_complete(self):
        def unchanged_final_page(db, folder, pages, details, seconds):
            with db:
                discovery.put(db, "scan_complete", True)
                discovery.put(db, "phase", "done")
            return {"session_page_requests": 1, "session_detail_requests": 0,
                    "last_stop": "detail_complete"}
        result = self.run_local(discover=unchanged_final_page)
        self.assertEqual(result["status"], "no_updates_found")
        self.assertEqual(result["extraction_requests"], 0)

    def test_extraction_limit_keeps_second_ad_pending(self):
        other_id = str(uuid.uuid4())
        self.queue_ad(order=1)
        self.queue_ad(order=2, ad_id=other_id)
        first = update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                  max_pages=2, max_details=5, max_extractions=1, max_seconds=120,
                                  discover_fn=self.changed, extract_fn=self.fake_extract)
        self.assertEqual((first["extraction_requests"], first["pending"], self.calls), (1, 1, 1))
        self.assertEqual(first["stop_reason"], "extraction_limit")
        second = self.run_local(discover=self.no_changes)
        self.assertEqual((second["extraction_requests"], second["pending"], self.calls), (1, 0, 2))
        self.assertEqual(len(self.index()["entries"]), 2)

    def test_unfinished_feed_scan_keeps_processing_pending(self):
        self.queue_ad()
        def page_limit(db, folder, pages, details, seconds):
            return {"session_page_requests": 2, "session_detail_requests": 0,
                    "last_stop": "page_limit"}
        result = self.run_local(discover=page_limit)
        self.assertEqual((result["status"], result["pending"], self.calls),
                         ("partial_pending", 1, 0))

    def test_time_limit_without_events_is_not_no_updates(self):
        def time_limit(db, folder, pages, details, seconds):
            return {"session_page_requests": 0, "session_detail_requests": 0,
                    "last_stop": "time_limit"}
        result = self.run_local(discover=time_limit)
        self.assertEqual(result["status"], "partial_pending")

    def test_discovery_auth_failure_stops_processing(self):
        self.queue_ad()
        def auth_failure(db, folder, pages, details, seconds):
            with db:
                discovery.put(db, "scan_complete", True)
            return {"session_page_requests": 1, "session_detail_requests": 0,
                    "last_stop": "feed: HTTP 401"}
        result = self.run_local(discover=auth_failure)
        self.assertEqual((result["status"], result["pending"], self.calls),
                         ("discovery_failed", 1, 0))

    def test_model_rate_limit_stops_batch_and_keeps_other_work(self):
        self.queue_ad(order=1)
        self.queue_ad(order=2, ad_id=str(uuid.uuid4()))
        def limited(text, stage, *, cleaned_capture):
            self.calls += 1
            raise extraction.SkeletonError("extract: HTTP 429")
        result = self.run_local(extract=limited)
        self.assertEqual((result["status"], result["extraction_requests"], result["pending"], self.calls),
                         ("processing_failed", 1, 2, 1))

    def test_new_then_unchanged_then_changed_is_one_uuid(self):
        first = self.queue_ad()
        result = self.run_local()
        self.assertEqual((result["processed"], self.calls), (1, 1))
        self.assertEqual(self.index()["entries"][0]["content_sha256"], first)
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 1)
        self.queue_ad(order=2)
        unchanged = self.run_local()
        self.assertEqual(unchanged["reused"], 1)
        self.assertEqual(self.calls, 1)
        second = self.queue_ad("Du må kunne SQL.", order=3)
        changed = self.run_local()
        self.assertEqual((changed["processed"], self.calls), (1, 2))
        self.assertEqual(len(self.index()["entries"]), 1)
        self.assertEqual(self.index()["entries"][0]["content_sha256"], second)
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 1)
        self.assertTrue((self.current / self.ad_id / "versions" / first / "result.json").is_file())

    def test_new_and_unchanged_ad_retain_saved_title_without_new_model_call(self):
        self.queue_ad(title="Synthetic developer role")
        self.run_local()
        first = self.index()["entries"][0]
        self.assertEqual(first["display_title"], "Synthetic developer role")
        saved = json.loads((self.current / self.ad_id / "versions" / first["content_sha256"] /
                            "result.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["title"], "Synthetic developer role")
        self.queue_ad(order=2, title="Updated synthetic developer role")
        result = self.run_local()
        self.assertEqual((result["reused"], self.calls), (1, 1))
        self.assertEqual(self.index()["entries"][0]["display_title"],
                         "Updated synthetic developer role")

    def test_blocked_input_never_calls_model(self):
        blocked = str(uuid.uuid4())
        self.index_path.write_text(json.dumps({"schema_version": 1, "entries": [
            {"uuid": blocked, "status": "blocked", "block_kind": "intentional",
             "result_path": None, "reason": "synthetic block"}]}), encoding="utf-8")
        self.queue_ad(ad_id=blocked)
        result = self.run_local()
        self.assertEqual((result["blocked"], result["extraction_requests"], self.calls), (1, 0, 0))
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 0)
        self.queue_ad(ad_id=blocked, order=2)
        later = self.run_local()
        self.assertEqual((later["blocked"], later["extraction_requests"], self.calls), (1, 0, 0))
        self.assertEqual(self.index()["entries"][0]["block_kind"], "intentional")

    def test_new_ambiguous_cleaning_is_blocked(self):
        self.queue_ad(outcome="review_blocked")
        result = self.run_local()
        self.assertEqual((result["blocked"], result["extraction_requests"], self.calls), (1, 0, 0))
        entry = self.index()["entries"][0]
        self.assertEqual((entry["status"], entry["block_kind"], entry["blocked_feed_order"],
                          entry["blocked_reason"]),
                         ("blocked", "version", 1, "input_review_blocked"))

    def test_pending_human_review_is_not_automatic_acceptance(self):
        self.queue_ad()
        db = discovery.connect(self.db_path)
        with db:
            db.execute("UPDATE captures SET review_state='pending_human_review' WHERE uuid=?", (self.ad_id,))
        db.close()
        result = self.run_local()
        self.assertEqual((result["blocked"], result["extraction_requests"], self.calls), (1, 0, 0))
        self.assertEqual(self.index()["entries"][0]["blocked_reason"], "capture_invalid_or_unavailable")

    def test_automatic_gate_holds_residual_contact_data(self):
        self.queue_ad("Du må kunne Python. Kontakt oss på test@example.org.")
        result = self.run_local()
        self.assertEqual((result["blocked"], result["extraction_requests"], self.calls), (1, 0, 0))

    def test_raw_ambiguous_contact_passage_is_held_before_model(self):
        self.queue_ad(outcome="review_blocked")
        detail = {"uuid": self.ad_id, "status": "ACTIVE", "ad_content": {
            "workLocations": [{"county": "INNLANDET", "municipal": "Hamar"}],
            "occupationCategories": [{"level1": "IT", "level2": "Utvikling"}],
            "description": "<p>Du må kunne Python og kontakt Kari Nord på kari@example.org for spørsmål.</p>",
            "contactList": [], "sourceurl": self.source}}
        db = discovery.connect(self.db_path)
        discovery.save_detail_success(db, json.dumps(detail).encode("utf-8"), self.ad_id, 1,
                                      backfill=False)
        outcome = db.execute("SELECT outcome,reason FROM capture_state WHERE uuid=?",
                             (self.ad_id,)).fetchone()
        db.close()
        self.assertEqual(tuple(outcome), ("review_blocked", "uncertain_mixed_contact_passage"))
        result = self.run_local()
        self.assertEqual((result["blocked"], result["extraction_requests"], self.calls), (1, 0, 0))
        self.assertEqual(self.index()["entries"][0]["status"], "blocked")
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 0)

    def test_held_capture_does_not_stop_next_ad(self):
        self.queue_ad("Du må kunne Python. Kontakt oss på test@example.org.")
        other = str(uuid.uuid4())
        self.queue_ad("Du må kunne SQL.", order=2, ad_id=other)
        result = self.run_local()
        self.assertEqual((result["blocked"], result["processed"], self.calls), (1, 1, 1))
        self.assertEqual(next(entry for entry in self.index()["entries"] if entry["uuid"] == other)["status"],
                         "current")

    def test_discovery_auto_checks_only_cleaned_capture(self):
        detail = {"uuid": self.ad_id, "status": "ACTIVE", "ad_content": {
            "workLocations": [{"county": "INNLANDET", "municipal": "Hamar"}],
            "occupationCategories": [{"level1": "IT", "level2": "Utvikling"}],
            "description": "<p>Du må kunne Python. Kontakt Kari Nord på kari@example.org.</p>",
            "contactList": [{"name": "Kari Nord", "email": "kari@example.org"}],
            "sourceurl": self.source}}
        db = discovery.connect(self.db_path)
        record = discovery.detail_record(detail, self.ad_id, 1)
        with db:
            outcome = discovery.store_capture(db, detail, record)
        row = db.execute("SELECT cleaned_text,cleaning_version,review_state FROM captures WHERE uuid=?",
                         (self.ad_id,)).fetchone()
        self.assertEqual(outcome, "saved")
        self.assertEqual(tuple(row), ("Du må kunne Python.", CLEANING_VERSION, "auto_contact_checked"))
        with db:
            db.execute("UPDATE captures SET cleaning_version='nav-contact-clean-v2',"
                       "review_state='pending_human_review' WHERE uuid=?", (self.ad_id,))
            repeated = discovery.store_capture(db, detail,
                         discovery.detail_record(detail, self.ad_id, 2))
        refreshed = db.execute("SELECT cleaned_text,cleaning_version,review_state FROM captures WHERE uuid=?",
                               (self.ad_id,)).fetchone()
        self.assertEqual(repeated, "saved")
        self.assertEqual(tuple(refreshed), ("Du må kunne Python.", CLEANING_VERSION,
                                          "auto_contact_checked"))
        self.assertEqual(db.execute("SELECT count(*) FROM captures WHERE uuid=?",
                                    (self.ad_id,)).fetchone()[0], 1)
        db.close()

    def test_discovery_saves_title_metadata_from_detail(self):
        detail = {"uuid": self.ad_id, "status": "ACTIVE", "ad_content": {
            "title": "Synthetic analyst role",
            "workLocations": [{"county": "INNLANDET", "municipal": "Hamar"}],
            "occupationCategories": [{"level1": "IT", "level2": "Analyse"}],
            "description": "<p>Du må kunne Python.</p>", "contactList": [],
            "sourceurl": self.source}}
        db = discovery.connect(self.db_path)
        discovery.save_detail_success(db, json.dumps(detail).encode("utf-8"), self.ad_id, 1,
                                      backfill=False)
        row = db.execute("SELECT last_order,title FROM ad_titles WHERE uuid=?", (self.ad_id,)).fetchone()
        self.assertEqual(tuple(row), (1, "Synthetic analyst role"))
        db.close()

    def test_version_block_skips_same_event_then_reassesses_new_event(self):
        self.queue_ad(outcome="review_blocked")
        self.run_local()
        db = discovery.connect(self.db_path)
        with db:
            db.execute("UPDATE processing_queue SET state='pending' WHERE uuid=?", (self.ad_id,))
        db.close()
        same = self.run_local(discover=self.no_changes)
        self.assertEqual((same["blocked"], same["extraction_requests"], self.calls), (1, 0, 0))
        self.queue_ad(order=2, outcome="saved")
        later = self.run_local()
        self.assertEqual((later["processed"], later["extraction_requests"], self.calls), (1, 1, 1))
        self.assertEqual(self.index()["entries"][0]["status"], "current")
        db = discovery.connect(self.db_path)
        history = db.execute("SELECT feed_order,reason FROM processing_blocks WHERE uuid=?",
                             (self.ad_id,)).fetchall()
        self.assertEqual([tuple(row) for row in history], [(1, "input_review_blocked")])
        db.close()

    def test_newer_uncertain_version_records_its_own_block(self):
        self.queue_ad(outcome="review_blocked")
        self.run_local()
        self.queue_ad(order=2, outcome="unavailable")
        later = self.run_local()
        self.assertEqual((later["blocked"], later["extraction_requests"], self.calls), (1, 0, 0))
        entry = self.index()["entries"][0]
        self.assertEqual((entry["block_kind"], entry["blocked_feed_order"], entry["blocked_reason"]),
                         ("version", 2, "input_unavailable"))
        db = discovery.connect(self.db_path)
        self.assertEqual([tuple(row) for row in db.execute(
            "SELECT feed_order,reason FROM processing_blocks WHERE uuid=? ORDER BY feed_order",
            (self.ad_id,)).fetchall()], [(1, "input_review_blocked"), (2, "input_unavailable")])
        db.close()

    def test_changed_block_retains_previous_result_until_newer_version_passes(self):
        self.queue_ad()
        self.run_local()
        previous = self.index()["entries"][0]["result_path"]
        self.queue_ad(order=2, outcome="review_blocked")
        self.run_local()
        entry = self.index()["entries"][0]
        self.assertEqual((entry["status"], entry["previous_result_path"], entry["blocked_feed_order"]),
                         ("stale", previous, 2))
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 0)
        self.queue_ad("Du må kunne SQL.", order=3)
        later = self.run_local()
        self.assertEqual((later["processed"], self.calls), (1, 2))
        self.assertEqual(self.index()["entries"][0]["status"], "current")
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 1)

    def test_inactive_event_keeps_historical_result(self):
        self.queue_ad()
        self.run_local()
        db = discovery.connect(self.db_path)
        with db:
            db.execute("UPDATE ads SET last_order=2,status='INACTIVE' WHERE uuid=?", (self.ad_id,))
            db.execute("UPDATE processing_queue SET feed_order=2,feed_status='INACTIVE',state='pending' WHERE uuid=?",
                       (self.ad_id,))
        db.close()
        result = self.run_local(discover=self.no_changes)
        self.assertEqual(result["extraction_requests"], 0)
        self.assertEqual(self.index()["entries"][0]["status"], "current")
        self.assertEqual(self.index()["entries"][0]["activity_status"], "INACTIVE")
        summary = json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["advertisement_count"], 1)
        self.assertEqual(summary["activity_counts"]["INACTIVE"], 1)

    def test_failed_change_marks_stale_and_next_run_can_resume(self):
        self.queue_ad()
        self.run_local()
        previous = self.index()["entries"][0]["result_path"]
        self.queue_ad("Du må kunne SQL.", order=2)
        def fail(text, stage, *, cleaned_capture):
            self.calls += 1
            raise extraction.SkeletonError("synthetic failure")
        failed = self.run_local(extract=fail)
        self.assertEqual(failed["status"], "processing_failed")
        self.assertEqual(self.index()["entries"][0]["status"], "stale")
        self.assertEqual(self.index()["entries"][0]["previous_result_path"], previous)
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 0)
        resumed = self.run_local(discover=self.no_changes)
        self.assertEqual(resumed["processed"], 1)
        self.assertEqual(self.index()["entries"][0]["status"], "current")
        self.assertEqual(self.calls, 3)

    def test_validation_failure_keeps_previous_version(self):
        self.queue_ad()
        self.run_local()
        previous = self.index()["entries"][0]["result_path"]
        self.queue_ad("Du må kunne SQL.", order=2)
        def invalid(text, stage, *, cleaned_capture):
            self.calls += 1
            extraction.save_json(stage / "request.json", extraction.request_payload(text, cleaned_capture=True))
            response = self.response(text)
            response["output"][0]["content"][0]["text"] = "not JSON"
            extraction.save_json(stage / "response.json", response)
            return response, 0.01
        result = self.run_local(extract=invalid)
        self.assertEqual(result["status"], "processing_failed")
        self.assertEqual(self.index()["entries"][0]["previous_result_path"], previous)
        self.assertEqual(self.index()["entries"][0]["status"], "stale")
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 0)
        self.assertEqual(self.calls, 2)
        retry = self.run_local(extract=invalid)
        self.assertEqual((retry["failed"], retry["earlier_failures"]), (1, 0))
        for _ in range(2):
            later = self.run_local(discover=self.no_changes)
            self.assertEqual((later["status"], later["failed"], later["earlier_failures"],
                              later["pending"], later["extraction_requests"]),
                             ("finished_with_cases", 0, 1, 1, 0))
        self.assertEqual(self.calls, 3)

    def test_saved_response_is_reused_after_interruption(self):
        self.queue_ad()
        def interrupted(text, stage, *, cleaned_capture):
            self.fake_extract(text, stage, cleaned_capture=cleaned_capture)
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.run_local(extract=interrupted)
        self.assertEqual(self.calls, 1)
        recovered = self.run_local(discover=self.no_changes)
        self.assertEqual((recovered["processed"], recovered["extraction_requests"], self.calls), (1, 0, 1))
        self.assertEqual(self.index()["entries"][0]["status"], "current")

    def test_page_checkpoint_and_queue_commit_together(self):
        db = discovery.connect(self.db_path)
        page_id = str(uuid.uuid4())
        entry = {"id": self.ad_id,
                 "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + self.ad_id,
                 "date_modified": "2026-11-02T00:00:00Z",
                 "_feed_entry": {"uuid": self.ad_id, "status": "ACTIVE"}}
        page = {"id": page_id, "items": [entry], "next_url": None, "next_id": None}
        self.assertTrue(discovery.save_page(db, page, discovery.nav.FEED_URL, {}))
        self.assertEqual(db.execute("SELECT uuid FROM processing_queue").fetchone()[0], self.ad_id)
        self.assertEqual(discovery.state(db, "cursor_url"), discovery.nav.FEED_URL)
        db.close()

    def test_queue_failure_rolls_back_page_and_cursor(self):
        db = discovery.connect(self.db_path)
        db.execute("CREATE TRIGGER synthetic_queue_failure BEFORE INSERT ON processing_queue "
                   "BEGIN SELECT RAISE(ABORT, 'synthetic'); END")
        db.commit()
        page = {"id": str(uuid.uuid4()), "items": [{
            "id": self.ad_id,
            "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + self.ad_id,
            "date_modified": "2026-11-02T00:00:00Z",
            "_feed_entry": {"uuid": self.ad_id, "status": "ACTIVE"}}],
            "next_url": None, "next_id": None}
        with self.assertRaises(sqlite3.DatabaseError):
            discovery.save_page(db, page, discovery.nav.FEED_URL, {})
        self.assertEqual(db.execute("SELECT count(*) FROM events").fetchone()[0], 0)
        self.assertEqual(discovery.state(db, "pages_done"), 0)
        self.assertEqual(discovery.state(db, "cursor_url"), discovery.nav.FEED_URL)
        db.close()

    def test_saved_poll_continuation_is_used(self):
        db = discovery.connect(self.db_path)
        with db:
            discovery.put(db, "end_url", "https://pam-stilling-feed.nav.no/api/v1/feed/" + str(uuid.uuid4()))
            discovery.put(db, "scan_complete", True)
            discovery.put(db, "phase", "done")
        original = discovery.run
        seen = {}
        def fake_run(connection, folder, pages, details, seconds, progress=None):
            seen["cursor"] = discovery.state(connection, "cursor_url")
            seen["polling"] = discovery.state(connection, "polling")
            return {"last_stop": "end_page_unchanged"}
        discovery.run = fake_run
        try:
            update.poll_or_resume(db, self.db_path.parent, 2, 5, 120)
        finally:
            discovery.run = original
            db.close()
        self.assertTrue(seen["polling"])
        self.assertTrue(seen["cursor"].startswith("https://pam-stilling-feed.nav.no/api/v1/feed/"))

    def test_three_feed_pages_stop_then_resume_to_end(self):
        page_ids = [str(uuid.uuid4()) for _ in range(3)]
        ad_ids = [str(uuid.uuid4()) for _ in range(3)]
        def entry(ad_id, status="INACTIVE"):
            return {"id": ad_id,
                    "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + ad_id,
                    "date_modified": "2026-11-02T00:00:00Z",
                    "_feed_entry": {"uuid": ad_id, "status": status}}
        pages = {}
        for n, page_id in enumerate(page_ids):
            next_id = page_ids[n + 1] if n < 2 else None
            page = {"id": page_id, "items": [entry(ad_ids[n - 1])] if n else [],
                    "next_id": next_id,
                    "next_url": "https://pam-stilling-feed.nav.no/api/v1/feed/" + next_id if next_id else None}
            page["items"].append(entry(ad_ids[n], "ACTIVE" if n == 2 else "INACTIVE"))
            url = discovery.nav.FEED_URL if n == 0 else "https://pam-stilling-feed.nav.no/api/v1/feed/" + page_id
            pages[url] = page
        requested = []
        def fake_fetch(opener, url, headers, deadline):
            requested.append(url)
            if url in pages:
                return 200, json.dumps(pages[url]).encode("utf-8"), {}
            detail = {"uuid": ad_ids[2], "status": "ACTIVE", "ad_content": {
                "workLocations": [{"county": "INNLANDET", "municipal": "Hamar"}],
                "occupationCategories": [{"level1": "IT", "level2": "Utvikling"}],
                "description": "Du må kunne Python.", "contactList": [], "sourceurl": self.source}}
            return 200, json.dumps(detail).encode("utf-8"), {}
        with patch.object(discovery, "get_token", return_value="synthetic"), patch.object(discovery, "fetch", side_effect=fake_fetch):
            first = update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                      max_pages=2, max_details=5, max_extractions=2, max_seconds=120,
                                      extract_fn=self.fake_extract)
            self.assertEqual((first["status"], first["pages"], first["pending"], first["feed_end_reached"]),
                             ("partial_pending", 2, 2, False))
            self.assertEqual(first["stop_reason"], "page_limit")
            db = discovery.connect(self.db_path)
            self.assertEqual(discovery.state(db, "cursor_url"), list(pages)[2])
            db.close()
            second = update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                       max_details=5, max_extractions=2, max_seconds=120,
                                       extract_fn=self.fake_extract)
        self.assertEqual((second["status"], second["pages"], second["details"],
                          second["processed"], second["pending"], second["feed_end_reached"]),
                         ("caught_up", 1, 1, 1, 0, True))
        self.assertEqual(len(requested), 4)
        self.assertEqual(self.calls, 1)
        self.assertEqual(second["new_feed_events"], 1)
        self.assertEqual(json.loads((self.statistics / "summary.json").read_text(encoding="utf-8"))["advertisement_count"], 1)

    def test_nonadvancing_cursor_is_rejected_without_checkpoint_change(self):
        db = discovery.connect(self.db_path)
        page_id = str(uuid.uuid4())
        page_url = "https://pam-stilling-feed.nav.no/api/v1/feed/" + page_id
        page = {"id": page_id, "items": [{"id": self.ad_id,
                "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + self.ad_id,
                "date_modified": "2026-11-02T00:00:00Z",
                "_feed_entry": {"uuid": self.ad_id, "status": "INACTIVE"}}],
                "next_id": page_id, "next_url": page_url}
        with self.assertRaisesRegex(discovery.DiscoveryError, "non-advancing"):
            discovery.save_page(db, page, page_url, {})
        self.assertEqual(db.execute("SELECT count(*) FROM events").fetchone()[0], 0)
        db.close()

    def test_repeated_page_cursor_is_rejected(self):
        db = discovery.connect(self.db_path)
        first_id, second_id = str(uuid.uuid4()), str(uuid.uuid4())
        def entry(ad_id):
            return {"id": ad_id,
                    "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + ad_id,
                    "date_modified": "2026-11-02T00:00:00Z",
                    "_feed_entry": {"uuid": ad_id, "status": "INACTIVE"}}
        first_url = "https://pam-stilling-feed.nav.no/api/v1/feed/" + first_id
        second_url = "https://pam-stilling-feed.nav.no/api/v1/feed/" + second_id
        first = {"id": first_id, "items": [entry(self.ad_id)],
                 "next_id": second_id, "next_url": second_url}
        second = {"id": second_id, "items": [entry(self.ad_id), entry(str(uuid.uuid4()))],
                  "next_id": first_id, "next_url": first_url}
        discovery.save_page(db, first, discovery.nav.FEED_URL, {})
        discovery.save_page(db, second, second_url, {})
        with self.assertRaisesRegex(discovery.DiscoveryError, "repeated page cursor"):
            discovery.save_page(db, first, first_url, {})
        self.assertEqual(discovery.state(db, "cursor_url"), first_url)
        self.assertEqual(discovery.state(db, "pages_done"), 2)
        db.close()

    def test_normal_defaults_use_operational_ceilings(self):
        seen = {}
        def finish(db, folder, pages, details, seconds):
            seen.update({"pages": pages, "details": details, "seconds": seconds})
            with db:
                discovery.put(db, "scan_complete", True)
                discovery.put(db, "phase", "done")
            return {"session_page_requests": 1, "session_detail_requests": 0,
                    "last_stop": "detail_complete"}
        result = update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                   discover_fn=finish, extract_fn=self.fake_extract)
        self.assertEqual(result["status"], "no_updates_found")
        self.assertEqual(seen["pages"], discovery.MAX_PAGES)
        self.assertEqual(seen["details"], discovery.MAX_DETAILS)
        self.assertGreater(seen["seconds"], 1100)

    def test_detail_404_is_coverage_gap_not_repeat_blocker(self):
        page_id = str(uuid.uuid4())
        other_id = str(uuid.uuid4())
        def entry(ad_id, status):
            return {"id": ad_id,
                    "url": "https://pam-stilling-feed.nav.no/api/v1/feedentry/" + ad_id,
                    "date_modified": "2026-11-02T00:00:00Z",
                    "_feed_entry": {"uuid": ad_id, "status": status}}
        page = {"id": page_id, "items": [entry(self.ad_id, "ACTIVE"), entry(other_id, "INACTIVE")],
                "next_url": None, "next_id": None}
        def fake_fetch(opener, url, headers, deadline):
            if url == discovery.nav.FEED_URL:
                return 200, json.dumps(page).encode("utf-8"), {}
            return 404, None, {}
        with patch.object(discovery, "get_token", return_value="synthetic"), patch.object(discovery, "fetch", side_effect=fake_fetch):
            result = update.run_update(self.db_path, self.index_path, self.current, self.statistics,
                                       max_details=5, max_extractions=2, max_seconds=120,
                                       extract_fn=self.fake_extract)
        self.assertEqual((result["status"], result["details"], result["blocked"], result["pending"]),
                         ("caught_up", 1, 1, 0))
        self.assertEqual(self.calls, 0)
        db = discovery.connect(self.db_path)
        self.assertEqual(discovery.pending_count(db), 0)
        self.assertEqual(db.execute("SELECT kind FROM failures WHERE uuid=?", (self.ad_id,)).fetchone()[0],
                         "detail_404")
        with db:
            db.execute("UPDATE ads SET last_order=last_order+1 WHERE uuid=?", (self.ad_id,))
        self.assertEqual(discovery.pending_count(db), 1)
        db.close()


if __name__ == "__main__":
    unittest.main()
