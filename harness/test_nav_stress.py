"""Task 007. Four offline experiments against isolated update state."""

import io
import json
import os
import sys
import unittest
from contextlib import closing, redirect_stderr
from unittest.mock import patch

import test_nav_update as fixtures


class StressTests(unittest.TestCase):
    def setUp(self):
        self.app = fixtures.UpdateTests()
        (fixtures.update.ROOT / "out").mkdir(exist_ok=True)
        self.addCleanup(self.app.doCleanups)
        self.app.setUp()
        self.app.run_local(discover=self.app.no_changes)

    def observe(self):
        with closing(fixtures.discovery.connect(self.app.db_path)) as db:
            queue = [tuple(row) for row in db.execute(
                "SELECT state, attempts, error_kind FROM processing_queue ORDER BY feed_order")]
        selected = [entry["uuid"] for entry in self.app.index()["entries"] if entry.get("result_path")]
        count = json.loads((self.app.statistics / "summary.json").read_text("utf-8"))["advertisement_count"]
        print(f"calls={self.app.calls}, queue={queue}, selected={len(selected)}, dashboard_ads={count}")
        return queue, selected, count

    def test_01_empty_capture(self):
        extractor = fixtures.extraction
        capture = extractor.ROOT / "eval/stress/03_empty.json"
        with patch.object(extractor, "ROOT", self.app.root), patch.object(extractor, "extract") as model, \
                patch.object(sys, "argv", ["nav_skeleton", "--mode", "cleaned-capture", "--capture", str(capture)]), \
                redirect_stderr(io.StringIO()) as message:
            status = extractor.main()
        results = list(self.app.root.rglob("result.json"))
        print(f"{message.getvalue().strip()}; exit={status}, calls={model.call_count}, results={len(results)}")
        self.assertIn("nonempty cleaned text", message.getvalue())
        self.assertEqual((status, model.call_count, len(results)), (1, 0, 0))

    def test_02_oslo_it(self):
        app = self.app
        app.queue_ad(outcome="pending")
        detail = {"uuid": app.ad_id, "status": "ACTIVE", "ad_content": {
            "workLocations": [{"county": "Oslo"}], "occupationCategories": [{"level1": "IT"}],
            "description": "<p>Du må kunne Python.</p>", "sourceurl": app.source}}
        with closing(fixtures.discovery.connect(app.db_path)) as db:
            fixtures.discovery.save_detail_success(db, json.dumps(detail).encode(), app.ad_id, 1, backfill=False)
        result = app.run_local()
        print(f"update={result['status']}")
        self.assertEqual(self.observe(), ([("complete", 0, "relevance_nonmatch")], [], 0))
        self.assertEqual((result["status"], app.calls), ("caught_up", 0))

    def test_03_rate_limit(self):
        self.app.test_model_rate_limit_stops_batch_and_keeps_other_work()
        self.assertEqual(self.observe(), (
            [("failed", 1, "model_request_failed"), ("pending", 0, None)], [], 0))

    def test_04_wrong_reply_then_valid(self):
        app = self.app
        second = "00000000-0000-4000-8000-000000000002"
        app.queue_ad(order=1)
        app.queue_ad("Du må kunne SQL.", order=2, ad_id=second)

        def transport(request, *, timeout):
            app.calls += 1
            text = json.loads(request.data)["input"]
            reply = [] if app.calls == 1 else app.response(text)
            return io.BytesIO(json.dumps(reply).encode())

        with patch.dict(os.environ, {"KIUA2003_API": "synthetic-test-key"}), \
                patch.object(fixtures.extraction, "urlopen", side_effect=transport):
            try:
                result = app.run_local(extract=fixtures.extraction.extract)
            finally:
                queue, selected, count = self.observe()
        self.assertEqual((result["failed"], app.calls, selected, count), (1, 2, [second], 1))
        self.assertEqual(queue, [("failed", 1, "validation_failed"), ("complete", 1, None)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
