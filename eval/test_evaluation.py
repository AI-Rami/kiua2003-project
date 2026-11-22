"""Model-free evaluation checks with synthetic items and frozen replay."""

import json
from io import BytesIO
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run
import reporting
import scoring


def item(names, relationship="single", classification="required", mention_type="candidate_qualification",
         evidence="Du må kunne Python."):
    return {"skills": names, "relationship": relationship, "classification": classification,
            "mention_type": mention_type, "skill_evidence": evidence, "classification_context": None}


class ScoringTests(unittest.TestCase):
    def test_order_independence_and_one_to_one_duplicates(self):
        expected = [item(["Python"]), item(["SQL"])]
        actual = [item(["SQL"]), item(["Python"]), item(["Python"])]
        score = scoring.score_items(expected, actual)
        self.assertEqual((score["matched"], score["unsupported_model_indexes"], score["omitted_reference_indexes"]),
                         (2, [2], []))
        self.assertAlmostEqual(score["precision"], 2 / 3)

    def test_or_group_is_one_complete_item(self):
        expected = [item(["Python", "R"], "any_of")]
        same = [item(["R", "Python"], "any_of")]
        split = [item(["Python"]), item(["R"])]
        self.assertEqual(scoring.score_items(expected, same)["matched"], 1)
        result = scoring.score_items(expected, split)
        self.assertEqual((result["matched"], len(result["unsupported_model_indexes"]),
                          len(result["omitted_reference_indexes"])), (0, 2, 1))

    def test_explicit_alias_only_and_combined_name(self):
        expected = [item(["C#"]), item([".NET"])]
        combined = [item(["C# .NET"])]
        self.assertEqual(scoring.score_items(expected, combined)["matched"], 0)
        self.assertEqual(scoring.score_items([item(["C sharp"])], [item(["C#"])],
                                             {"C#": "C sharp"})["matched"], 1)

    def test_label_and_mention_errors_do_not_hide_detection(self):
        expected = [item(["Python"])]
        actual = [item(["Python"], classification="unclear", mention_type="work_duty")]
        result = scoring.score_items(expected, actual)
        self.assertEqual((result["matched"], result["classification_error_pairs"],
                          result["mention_type_error_pairs"]), (1, [(0, 0)], [(0, 0)]))

    def test_unapproved_reference_rejected_and_quotations_checked(self):
        reference = {"approval": "draft", "items": [item(["Python"])]}
        with self.assertRaises(scoring.ReferenceError):
            scoring.check_reference(reference, "Du må kunne Python.")
        reference["approval"] = "approved_complete"
        scoring.check_reference(reference, "Du må kunne Python.")
        with self.assertRaises(scoring.ReferenceError):
            scoring.check_reference(reference, "Du må kunne SQL.")

    def test_reference_requires_exact_fields_and_valid_mention_classification(self):
        prepared = "Du må kunne Python."
        valid = item(["Python"], evidence=prepared)
        for changed in (dict(valid, unexpected="extra"),
                        {name: value for name, value in valid.items() if name != "classification_context"},
                        dict(valid, mention_type="work_duty"),
                        dict(valid, mention_type="interest_only", classification="preferred")):
            with self.subTest(changed=changed), self.assertRaises(scoring.ReferenceError):
                scoring.check_reference({"approval": "approved_complete", "items": [changed]}, prepared)
        scoring.check_reference({"approval": "approved_complete", "items": [valid]}, prepared)

    def test_reference_alias_collision_rejected(self):
        prepared = "Du må kunne Python."
        reference = {"approval": "approved_complete", "items": [item(["Python"]), item(["Py"])]}
        scoring.check_reference(reference, prepared)
        with self.assertRaisesRegex(scoring.ReferenceError, "duplicate reference item"):
            scoring.check_reference(reference, prepared, {"Py": "Python"})


class ReplayTests(unittest.TestCase):
    def test_replay_cli_reports_approved_scoring_when_available(self):
        record = {"validated": 1, "selected": 1, "approved_scored": 1, "approved_selected": 1}
        output = StringIO()
        with patch.object(run, "replay", return_value=(Path("out/evaluation/synthetic"), record)):
            with redirect_stdout(output):
                run.main(["--mode", "replay"])
        self.assertIn("Approved accuracy: 1/1 selected approved cases scored", output.getvalue())
        self.assertNotIn("not yet available", output.getvalue())

    def test_frozen_text_hash_is_line_ending_portable(self):
        self.assertEqual(run.text_digest(b"first\nsecond\n"),
                         run.text_digest(b"first\r\nsecond\r\n"))
        self.assertNotEqual(run.text_digest(b"first\nsecond\n"),
                            run.text_digest(b"first\nchanged\n"))

    def test_fresh_checkout_startup_with_lf_and_crlf(self):
        for endings in (b"\n", b"\r\n"):
            with self.subTest(endings=endings), tempfile.TemporaryDirectory() as folder:
                checkout = Path(folder)
                shutil.copytree(run.ROOT / "shared/baseline", checkout / "shared/baseline")
                shutil.copytree(run.ROOT / "harness", checkout / "harness",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                shutil.copytree(run.ROOT / "eval", checkout / "eval",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                review = (run.ROOT / "reviews/current-v2.json").read_bytes()
                review = review.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", endings)
                (checkout / "reviews").mkdir()
                (checkout / "reviews/current-v2.json").write_bytes(review)
                for relative in ("shared/baseline/manifest.json", "eval/history/first-attempt/gold.csv",
                                 "eval/cases/manifest.json"):
                    path = checkout / relative
                    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                    path.write_bytes(content.replace(b"\n", endings))
                command = [sys.executable, str(checkout / "harness/start.py"), "--check-only"]
                first = subprocess.run(command, cwd=checkout, capture_output=True, text=True, timeout=60)
                if first.returncode:
                    trace = subprocess.run([sys.executable, "-c",
                                            "import sys;sys.path.insert(0,'harness');"
                                            "import share_data;share_data.restore()"],
                                           cwd=checkout, capture_output=True, text=True, timeout=60)
                    self.fail(first.stdout + first.stderr + trace.stderr)
                self.assertIn("selected advertisements: 13", first.stdout)
                second = subprocess.run(command, cwd=checkout, capture_output=True, text=True, timeout=60)
                self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
                self.assertIn("Saved data: existing", second.stdout)
                replay = subprocess.run([sys.executable, str(checkout / "eval/run.py"), "--mode", "replay",
                                         "--suite", "eval/cases/manifest.json"],
                                        cwd=checkout, capture_output=True, text=True, timeout=60)
                self.assertEqual(replay.returncode, 0, replay.stdout + replay.stderr)
                self.assertIn("Replay: 5/5 validated", replay.stdout)
                offline = subprocess.run([sys.executable, str(checkout / "eval/run.py"), "--mode", "offline-suite",
                                          "--suite", "eval/cases/manifest.json"],
                                         cwd=checkout, capture_output=True, text=True, timeout=60)
                self.assertEqual(offline.returncode, 0, offline.stdout + offline.stderr)
                self.assertIn("Offline suite: 5/5 real ads validated; 5/5 synthetic checks passed", offline.stdout)

    def test_frozen_replay_does_not_use_current_index(self):
        suite = run.ROOT / "eval/cases/manifest.json"
        with tempfile.TemporaryDirectory() as folder:
            first_folder, first = run.replay(suite, Path(folder))
            second_folder, second = run.replay(suite, Path(folder))
            self.assertNotEqual(first_folder, second_folder)
            self.assertEqual(first["selected"], 5)
            self.assertEqual(first["validated"], 5)
            self.assertEqual(first["approved_scored"], 5)
            self.assertIsNotNone(first["accuracy_score"])
            self.assertEqual(first["accuracy_score"], second["accuracy_score"])
            self.assertEqual(first["cases"], second["cases"])

    def test_changed_manifest_hash_fails_preflight(self):
        original = run.read_json(run.ROOT / "eval/cases/manifest.json")
        original["baseline_manifest_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "suite.json"
            path.write_text(json.dumps(original), encoding="utf-8")
            with self.assertRaisesRegex(run.EvaluationError, "hash mismatch"):
                run.preflight(path)

    def test_synthetic_approved_reference_scores_only_selected_case(self):
        original_suite = run.ROOT / "eval/cases/manifest.json"
        _, original_cases = run.preflight(original_suite)
        case = original_cases[0]
        validation, output = run.extractor.validate(case["response"], case["prepared"])
        self.assertTrue(validation["passed"])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(run.ROOT / "shared/baseline", root / "shared/baseline")
            (root / "eval/cases").mkdir(parents=True)
            (root / "eval/history/first-attempt").mkdir(parents=True)
            (root / "eval/references").mkdir()
            shutil.copyfile(run.ROOT / "eval/history/first-attempt/gold.csv",
                            root / "eval/history/first-attempt/gold.csv")
            suite = json.loads(original_suite.read_text(encoding="utf-8"))
            suite["cases"][0]["reference_status"] = "approved_complete"
            for selected in suite["cases"][1:]:
                selected["reference_status"] = "awaiting_joint_approval"
            # Synthetic contract fixture only; this does not record human approval.
            reference = {"schema_version": 1, "reviewers": ["Rami", "Yehya"], "aliases": {},
                         "cases": {case["uuid"]: {
                             "approval": "approved_complete",
                             "input_sha256": run.digest(case["prepared"].encode("utf-8")),
                             "items": output["items"]}}}
            reference_path = root / "eval/references/synthetic.json"
            reference_path.write_text(json.dumps(reference, ensure_ascii=False), encoding="utf-8")
            suite["references"] = {"path": "eval/references/synthetic.json",
                                   "sha256": run.text_digest(reference_path.read_bytes())}
            suite_path = root / "eval/cases/synthetic.json"
            suite_path.write_text(json.dumps(suite), encoding="utf-8")
            with patch.object(run, "ROOT", root):
                _, record = run.replay(suite_path, root / "out/evaluation")
            self.assertEqual((record["approved_selected"], record["approved_scored"]), (1, 1))
            self.assertEqual(record["accuracy_score"]["f1"], 1.0)


class OfflineSuiteTests(unittest.TestCase):
    suite_path = run.ROOT / "eval/cases/manifest.json"

    def test_pinned_catalog_and_separate_synthetic_results(self):
        suite, cases = run.preflight(self.suite_path)
        catalog, catalog_hash = run.load_offline_catalog(suite, cases)
        self.assertEqual((len(catalog["real_cases"]), len(catalog["synthetic_cases"])), (5, 5))
        self.assertEqual(catalog_hash, suite["offline_cases"]["sha256"])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, baseline = run.replay(self.suite_path, root)
            report_path, full = run.offline_suite(self.suite_path, root)
            self.assertEqual(full["accuracy_score"], baseline["accuracy_score"])
            self.assertEqual((full["validated"], full["synthetic_passed"], full["synthetic_failed"]), (5, 5, 0))
            rejected = next(case for case in full["synthetic_cases"] if case["kind"] == "input_rejection")
            self.assertTrue(rejected["passed"])
            self.assertEqual((rejected["actual"]["model_calls"], rejected["actual"]["published"]), (0, 0))
            report = (report_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("REAL-01", report)
            self.assertIn("SYN-REJECT-001", report)
            self.assertIn("5 of 5 passed", report)

    def test_changed_catalog_hash_fails_before_replay(self):
        suite, cases = run.preflight(self.suite_path)
        suite["offline_cases"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(run.EvaluationError, "hash mismatch"):
            run.load_offline_catalog(suite, cases)

    def test_failed_synthetic_check_is_reported_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(run.offline_cases, "run_case", return_value=({"expected": True},
                                                                           {"expected": False}, False)):
                report_path, record = run.offline_suite(self.suite_path, Path(folder))
            self.assertEqual((record["synthetic_failed"], record["suite_passed"]), (5, False))
            self.assertIn("SYN-REJECT-001 — Failed", (report_path / "report.md").read_text(encoding="utf-8"))
            output = StringIO()
            with patch.object(run, "offline_suite", return_value=(report_path, record)):
                with redirect_stdout(output):
                    code = run.main(["--mode", "offline-suite"])
            self.assertEqual(code, 1)

    def test_dated_report_index_and_older_report_remain(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first_path, first = run.offline_suite(self.suite_path, root)
            first_report = (first_path / "report.md").read_bytes()
            text = first_report.decode("utf-8")
            self.assertIn("**Generated:**", text)
            self.assertIn("UTC", text)
            self.assertIn("47 items", text)
            self.assertEqual(text.count("**UUID:**"), 5)
            self.assertIn("SYN-REJECT-001", text)
            self.assertEqual(first["accuracy_score"]["matched"], 47)
            second_path, _ = run.offline_suite(self.suite_path, root)
            self.assertNotEqual(first_path, second_path)
            self.assertEqual((first_path / "report.md").read_bytes(), first_report)
            index = (root / "index.md").read_text(encoding="utf-8")
            for path in (first_path, second_path):
                self.assertIn(f"{path.name}/report.md", index)
                self.assertTrue((path / "report.md").is_file())
            self.assertEqual(index.count("[Open report]"), 2)

    def test_explicit_utc_time_and_case_metrics_are_readable(self):
        when = reporting.generated_time({"generated_at_utc": "2026-11-22T17:25:03+00:00"}, Path("unused"))
        self.assertEqual(when, "22 November 2026, 17:25:03 UTC")
        score = {"unsupported_model_indexes": [1], "omitted_reference_indexes": [0],
                 "classification_error_pairs": [], "mention_type_error_pairs": [],
                 "missing_alternative_group_indexes": [0]}
        expected = [item(["Python", "R"], relationship="any_of")]
        actual = [item(["SQL"]), item(["Python"])]
        details = reporting.comparison(score, expected, actual)
        self.assertEqual(details["unmatched_or_groups"], ["Python OR R"])
        self.assertEqual(details["unmatched_model_names"], ["Python"])


class ModelModeTests(unittest.TestCase):
    suite_path = run.ROOT / "eval/cases/manifest.json"

    def prompt_hash(self):
        return run.digest(run.extractor.PROMPT.read_text(encoding="utf-8").encode("utf-8"))

    def test_limits_hash_and_cost_fail_before_requests(self):
        expected = self.prompt_hash()
        with self.assertRaisesRegex(run.EvaluationError, "cover all selected"):
            run.model_preflight(self.suite_path, 4, 900, .05, expected)
        with self.assertRaisesRegex(run.EvaluationError, "prompt differs"):
            run.model_preflight(self.suite_path, 5, 900, .05, "0" * 64)
        with self.assertRaisesRegex(run.EvaluationError, "exceeds budget"):
            run.model_preflight(self.suite_path, 5, 900, .001, expected)
        suite, cases, payloads, maximum = run.model_preflight(self.suite_path, 5, 900, .05, expected)
        self.assertEqual(len(cases), len(payloads))
        self.assertLessEqual(maximum, .05)
        self.assertEqual(suite["max_output_tokens"], 8192)
        for case, payload, body in payloads:
            self.assertEqual(payload["input"], case["prepared"])
            self.assertNotIn("reference", payload)
            self.assertLessEqual(len(body), run.extractor.MAX_BODY_BYTES)

    def test_five_mocked_requests_save_complete_records_without_credentials(self):
        calls = []
        _, cases = run.preflight(self.suite_path)
        def transport(request, timeout):
            index = len(calls)
            calls.append((json.loads(request.data), timeout))
            return BytesIO(json.dumps(cases[index]["response"], ensure_ascii=False).encode("utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            path, record = run.model(self.suite_path, Path(folder), 5, 900, .05,
                                     self.prompt_hash(), transport=transport, key="synthetic-test-key")
            self.assertEqual((record["selected"], record["attempted"], record["validated"],
                              record["failed"], record["not_run"]), (5, 5, 5, 0, 0))
            self.assertEqual(record["approved_scored"], 5)
            self.assertEqual(len(calls), 5)
            self.assertGreater(record["estimated_actual_cost_usd"], 0)
            self.assertTrue((path / "report.md").is_file())
            for case in cases:
                case_path = path / case["uuid"]
                for name in ("request.json", "response.json", "validation.json", "score.json"):
                    self.assertTrue((case_path / name).is_file())
                self.assertEqual(run.read_json(case_path / "request.json")["input"], case["prepared"])
            for saved in path.rglob("*"):
                if saved.is_file():
                    self.assertNotIn("synthetic-test-key", saved.read_text(encoding="utf-8"))

    def test_api_failure_stops_and_preserves_partial_progress(self):
        calls = 0
        _, cases = run.preflight(self.suite_path)
        def transport(request, timeout):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise HTTPError(request.full_url, 429, "secret response not saved", None, None)
            return BytesIO(json.dumps(cases[0]["response"], ensure_ascii=False).encode("utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            path, record = run.model(self.suite_path, Path(folder), 5, 900, .05,
                                     self.prompt_hash(), transport=transport, key="synthetic-test-key")
            self.assertEqual(calls, 2)
            self.assertEqual((record["validated"], record["failed"], record["not_run"]), (1, 1, 3))
            self.assertEqual(record["cases"][1]["reason"], "HTTP 429")
            self.assertTrue(record["partial"])
            self.assertIn("left 3 not run", (path / "report.md").read_text(encoding="utf-8"))
            self.assertIn("HTTP 429", (path / "report.md").read_text(encoding="utf-8"))
            self.assertIn(path.name + "/report.md", (Path(folder) / "index.md").read_text(encoding="utf-8"))

    def test_invalid_model_output_is_recorded_and_next_case_runs(self):
        _, cases = run.preflight(self.suite_path)
        calls = 0
        def transport(request, timeout):
            nonlocal calls
            response = dict(cases[calls]["response"])
            if calls == 0:
                response["status"] = "incomplete"
            calls += 1
            return BytesIO(json.dumps(response, ensure_ascii=False).encode("utf-8"))
        with tempfile.TemporaryDirectory() as folder:
            path, record = run.model(self.suite_path, Path(folder), 5, 900, .05,
                                     self.prompt_hash(), transport=transport, key="synthetic-test-key")
            self.assertEqual((calls, record["validated"], record["failed"], record["not_run"]), (5, 4, 1, 0))
            self.assertFalse(run.read_json(path / cases[0]["uuid"] / "validation.json")["passed"])
            self.assertEqual(record["approved_scored"], 4)


if __name__ == "__main__":
    unittest.main()
