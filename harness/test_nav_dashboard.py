"""Model-free dashboard checks using synthetic records and a mocked updater."""

from datetime import date
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

import nav_dashboard as dashboard


def item(skill, classification="required", kind="candidate_qualification", relation="single"):
    return {"skills": skill if relation == "any_of" else [skill],
            "relationship": relation, "classification": classification,
            "mention_type": kind, "skill_evidence": "Technical requirement",
            "classification_context": None}


def record(ad_id, day, status, items):
    return {"uuid": ad_id, "title": None, "source_url": "https://arbeidsplassen.nav.no/stillinger/stilling/" + ad_id,
            "publication_date": day, "activity_status": status, "items": items}


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            record("one", "2026-11-01", "ACTIVE", [item("Python"), item("Python"),
                   item(["Python", "R"], "preferred", relation="any_of"),
                   item("Docker", "unclear", "work_duty")]),
            record("two", "2026-10-10", "INACTIVE", [item("Python", "preferred"),
                   item("Docker", "unclear", "work_context")]),
        ]
        self.today = date(2026, 11, 3)

    def data(self, **filters):
        return dashboard.dashboard_data(self.records, {}, filters, today=self.today)

    def test_counts_or_groups_and_repeated_mentions(self):
        data = self.data()
        self.assertEqual(data["cards"], {"advertisements": 2, "qualification_skill_names": 1,
                                         "alternative_groups": 1})
        python = data["tables"]["qualification"][0]
        self.assertEqual(python["counts"], {"required": 1, "preferred": 1, "unclear": 0, "total": 2})
        self.assertEqual(data["tables"]["alternatives"][0]["skills"], ["Python", "R"])
        self.assertEqual(data["tables"]["other"][0]["counts"]["total"], 2)
        self.assertEqual(len(data["support"]["qualification:Python"]), 2)

    def test_period_status_and_search_recount(self):
        self.assertEqual(self.data(period="this_month")["cards"]["advertisements"], 1)
        self.assertEqual(self.data(period="previous_month")["cards"]["advertisements"], 1)
        self.assertEqual(self.data(status="active")["cards"]["advertisements"], 1)
        self.assertEqual(self.data(search="r")["tables"]["alternatives"][0]["counts"]["total"], 1)
        self.assertEqual(self.data(search="nonexistent")["cards"]["advertisements"], 0)
        with self.assertRaises(dashboard.DashboardError):
            self.data(period="custom", **{"from": "2026-11-03", "to": "2026-11-01"})

    def test_missing_dates_excluded_by_period(self):
        self.records.append(record("three", None, "UNKNOWN", [item("Git")]))
        data = self.data(period="this_year")
        self.assertEqual(data["filter"]["missing_dates_excluded"], 1)
        self.assertEqual(data["cards"]["advertisements"], 2)

    def test_contact_pattern_evidence_withheld(self):
        self.assertIsNone(dashboard.evidence_for_display("Call 98765432 about Python"))
        self.assertEqual(dashboard.evidence_for_display("Du må kunne Python"), "Du må kunne Python")


class UpdateManagerTests(unittest.TestCase):
    def test_no_updates_and_duplicate_start_guard(self):
        with tempfile.TemporaryDirectory(dir=dashboard.ROOT) as directory:
            base = Path(directory)
            ready, release = threading.Event(), threading.Event()
            calls = []

            def run(db_path, progress):
                calls.append(db_path)
                progress({"stage": "discovery"})
                ready.set()
                release.wait(3)
                return {"status": "no_updates_found", "pages": 1, "details": 0,
                        "extraction_requests": 0, "processed": 0, "reused": 0,
                        "blocked": 0, "failed": 0, "pending": 0,
                        "feed_end_reached": True, "stop_reason": "feed_end", "statistics_ads": 11}

            manager = dashboard.UpdateManager(run_fn=run, db_path=base / "db",
                                              state_path=base / "last.json")
            original = dashboard.statistics.load_current_records
            dashboard.statistics.load_current_records = lambda *_: ([{"uuid": "saved"}], {})
            try:
                self.assertTrue(manager.start())
                self.assertTrue(ready.wait(3))
                self.assertFalse(manager.start())
                self.assertEqual(manager.records()[0][0]["uuid"], "saved")
                release.set()
                for _ in range(200):
                    if not manager.snapshot()["running"]:
                        break
                    time.sleep(.01)
                self.assertFalse(manager.snapshot()["running"])
                self.assertEqual(manager.snapshot()["last"]["status"], "no_updates_found")
                self.assertEqual(len(calls), 1)
                for _ in range(200):
                    if (base / "last.json").exists():
                        break
                    time.sleep(.01)
                self.assertEqual(json.loads((base / "last.json").read_text())["status"], "no_updates_found")
            finally:
                dashboard.statistics.load_current_records = original

    def test_button_endpoint_starts_once(self):
        class FakeManager:
            def __init__(self):
                self.calls = 0

            def start(self):
                self.calls += 1
                return self.calls == 1

            def snapshot(self):
                return {"running": True, "last": {"status": "running"}}

        class Handler(dashboard.DashboardHandler):
            manager = FakeManager()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            headers = {"Host": f"127.0.0.1:{server.server_port}",
                       "Origin": f"http://127.0.0.1:{server.server_port}",
                       "Content-Type": "application/json"}
            connection.request("POST", "/api/update", body="{}", headers=headers)
            self.assertEqual(connection.getresponse().status, 202)
            connection.request("POST", "/api/update", body="{}", headers=headers)
            self.assertEqual(connection.getresponse().status, 409)
            connection.close()
            self.assertEqual(Handler.manager.calls, 2)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


if __name__ == "__main__":
    unittest.main()
