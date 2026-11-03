"""Synthetic, model-free checks for the saved-result skill summary."""

import unittest
import json
import hashlib
from pathlib import Path
import tempfile
from unittest.mock import patch

import nav_skill_summary as summary


def item(skills, relationship, classification):
    return {"skills": skills, "relationship": relationship,
            "classification": classification, "evidence": "synthetic evidence"}


def record(ad_id, items):
    return {"uuid": ad_id, "items": items}


def v2_item(skills, relationship, classification, mention_type):
    return {**item(skills, relationship, classification), "mention_type": mention_type}


class SkillSummaryTests(unittest.TestCase):
    def setUp(self):
        self.a = "00000000-0000-0000-0000-000000000001"
        self.b = "00000000-0000-0000-0000-000000000002"
        self.c = "00000000-0000-0000-0000-000000000003"
        self.records = [
            record(self.a, [item(["Python"], "single", "required"),
                            item(["Python"], "single", "required"),
                            item(["Python"], "single", "preferred"),
                            item(["Python", "SQL"], "any_of", "required"),
                            item(["Python", "SQL"], "any_of", "required"),
                            item(["Go", "Rust"], "any_of", "preferred")]),
            record(self.b, [item(["Python"], "single", "required"),
                            item(["SQL", "Python"], "any_of", "required")]),
            record(self.c, [item(["Python"], "single", "unclear"),
                            item(["Python", "SQL"], "any_of", "preferred")]),
        ]

    def test_counts_use_uuid_sets_and_preserve_or_groups(self):
        result = summary.aggregate(self.records)
        all_python = next(row for row in result["all_skills"] if row["skill"] == "Python")
        self.assertEqual(all_python["counts"],
                         {"required": 2, "preferred": 2, "unclear": 1, "total": 3})
        self.assertEqual(all_python["supporting_uuids"]["total"], [self.a, self.b, self.c])
        single_python = next(row for row in result["single_skills"] if row["skill"] == "Python")
        self.assertEqual(single_python["counts"],
                         {"required": 2, "preferred": 1, "unclear": 1, "total": 3})
        alt_python = next(row for row in result["alternative_skills"] if row["skill"] == "Python")
        self.assertEqual(alt_python["counts"],
                         {"required": 2, "preferred": 1, "unclear": 0, "total": 3})
        groups = {tuple(row["skills"]): row for row in result["alternative_groups"]}
        self.assertEqual(groups[("Python", "SQL")]["counts"],
                         {"required": 1, "preferred": 1, "unclear": 0, "total": 2})
        self.assertEqual(groups[("SQL", "Python")]["counts"]["total"], 1)
        self.assertEqual(groups[("Go", "Rust")]["counts"]["preferred"], 1)

    def test_duplicate_uuid_is_rejected(self):
        with self.assertRaisesRegex(summary.SummaryError, "duplicate advertisement UUID"):
            summary.aggregate(self.records + [record(self.a, [])])

    def test_applicant_qualifications_and_other_mentions_are_separate(self):
        records = [record(self.a, [
            v2_item(["Python"], "single", "required", "candidate_qualification"),
            v2_item(["Python"], "single", "required", "candidate_qualification"),
            v2_item(["Python", "R"], "any_of", "required", "candidate_qualification"),
            v2_item(["Docker"], "single", "unclear", "work_duty"),
            v2_item(["Docker"], "single", "unclear", "work_context"),
            v2_item(["Kubernetes", "Linux"], "any_of", "unclear", "work_context"),
            v2_item(["AI"], "single", "unclear", "interest_only"),
        ]), record(self.b, [
            v2_item(["Python"], "single", "preferred", "candidate_qualification"),
            v2_item(["Docker"], "single", "unclear", "work_duty"),
        ])]
        result = summary.aggregate(records)
        main = {row["skill"]: row for row in result["qualification_single_skills"]}
        self.assertEqual(set(main), {"Python"})
        self.assertEqual(main["Python"]["counts"],
                         {"required": 1, "preferred": 1, "unclear": 0, "total": 2})
        self.assertEqual(result["qualification_or_groups"][0]["skills"], ["Python", "R"])
        self.assertEqual(result["qualification_or_groups"][0]["counts"]["required"], 1)
        other = {row["skill"]: row for row in result["other_single_skills"]}
        self.assertEqual(other["Docker"]["counts"],
                         {"work_duty": 2, "work_context": 1, "interest_only": 0, "total": 2})
        self.assertEqual(other["AI"]["counts"]["interest_only"], 1)
        self.assertEqual(result["other_or_groups"][0]["skills"], ["Kubernetes", "Linux"])
        self.assertEqual(result["other_or_groups"][0]["mention_type"], "work_context")

    def test_publication_date_is_saved_date_not_a_period_claim(self):
        self.assertEqual(summary.publication_date("2026-10-27T00:30:00+01:00"),
                         ("2026-10-27", "valid"))
        self.assertEqual(summary.publication_date("2026-10-27T23:30:00Z"),
                         ("2026-10-27", "valid"))
        self.assertEqual(summary.publication_date(None), (None, "missing"))
        self.assertEqual(summary.publication_date("2026-10-27T00:30:00"), (None, "invalid"))

    def test_index_requires_ten_unique_successes(self):
        rows = [f"| 00000000-0000-0000-0000-{number:012d} | success | "
                f"[report](../../run-{number}/report.md) | 12 |"
                for number in range(1, 11)]
        self.assertEqual(len(summary.index_rows("\n".join(rows))), 10)
        with self.assertRaisesRegex(summary.SummaryError, "duplicate advertisement UUID"):
            summary.index_rows("\n".join(rows + [rows[0]]))
        with self.assertRaisesRegex(summary.SummaryError, "not successful"):
            summary.index_rows("\n".join([rows[0].replace("success", "failed")] + rows[1:]))
        with self.assertRaisesRegex(summary.SummaryError, "expected 10"):
            summary.index_rows("\n".join(rows[:9]))

    def test_review_applies_exact_item_corrections_without_changing_saved_results(self):
        original = item(["Infrastructure as Code (IaC)"], "single", "required")
        original_records = [record(self.a, [original, item(["Project work"], "single", "preferred")])]
        review = {"corrections": [
            {"uuid": self.a, "item_number": 1, "original_sha256": summary.item_digest(original),
             "action": "replace", "replacement": {**original, "classification": "unclear"}},
            {"uuid": self.a, "item_number": 2,
             "original_sha256": summary.item_digest(original_records[0]["items"][1]),
             "action": "remove"}],
            "aliases": {"Infrastructure as Code (IaC)": "Infrastructure as Code"}}
        with tempfile.TemporaryDirectory(dir=summary.ROOT / "out") as temp:
            path = Path(temp) / "review.json"
            path.write_text(json.dumps(review), encoding="utf-8")
            revised, info = summary.apply_review(original_records, path)
            self.assertEqual(info["correction_count"], 2)
            self.assertEqual(revised[0]["items"],
                             [{**original, "skills": ["Infrastructure as Code"], "classification": "unclear"}])
            self.assertEqual(original_records[0]["items"][0], original)
            self.assertEqual(len(original_records[0]["items"]), 2)
            review["corrections"][0]["original_sha256"] = "0" * 64
            path.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaisesRegex(summary.SummaryError, "original item changed"):
                summary.apply_review(original_records, path)


class CurrentSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=summary.ROOT / "out")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.current = self.root / "current"
        self.current.mkdir()
        self.index = self.current / "index.json"
        self.stats = self.root / "statistics"
        self.uid = "00000000-0000-0000-0000-000000000001"
        self.text = "Du må kunne Python."
        self.instructions = "Synthetic extraction instructions"
        self.run_id = "synthetic-run"
        self.source = "https://example.org/ad"
        folder = self.current / self.uid
        folder.mkdir()
        (folder / "prepared_ad.txt").write_text(self.text, encoding="utf-8")
        self.schema = {"type": "object", "properties": {"items": {"type": "array"}}}
        (folder / "request.json").write_text(json.dumps({"input": self.text, "instructions": self.instructions,
                                                          "model": "synthetic-model", "reasoning": {"effort": "medium"},
                                                          "max_output_tokens": 8192, "stream": False, "store": False,
                                                          "text": {"format": {"type": "json_schema",
                                                                              "name": "skill_extraction_v2", "strict": True,
                                                                              "schema": self.schema}}}), encoding="utf-8")
        (folder / "response.json").write_text(json.dumps({"id": "synthetic-response", "model": "synthetic-model"}), encoding="utf-8")
        (folder / "validation.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
        (folder / "result.json").write_text(json.dumps({"source_uuid": self.uid, "source_url": self.source,
                                                        "run_id": self.run_id, "format_version": 2,
                                                        "validation": "passed", "model": "synthetic-model",
                                                        "response_id": "synthetic-response",
                                                        "capture_provenance": {"revised_version": "synthetic-cleaner"},
                                                        "items": [{"skills": ["Python"], "relationship": "single",
                                                                   "classification": "required", "mention_type": "candidate_qualification",
                                                                   "skill_evidence": self.text, "classification_context": None}]}), encoding="utf-8")
        (folder / "report.md").write_text("Synthetic report\n", encoding="utf-8")
        self.entry = {"uuid": self.uid, "status": "current", "source_url": self.source,
                      "result_path": (folder / "result.json").resolve().relative_to(summary.ROOT).as_posix(),
                      "original_run_id": self.run_id, "content_sha256": hashlib.sha256(self.text.encode()).hexdigest(),
                      "prompt_sha256": hashlib.sha256(self.instructions.encode()).hexdigest(),
                      "schema_sha256": hashlib.sha256(json.dumps(self.schema, sort_keys=True,
                                                                     separators=(",", ":")).encode()).hexdigest(),
                      "model_id": "synthetic-model", "reasoning_effort": "medium", "max_output_tokens": 8192,
                      "format_version": 2, "validation_status": "passed", "cleaning_version": "synthetic-cleaner",
                      "review_warnings": ["Synthetic warning"]}
        self.save([self.entry])

    def save(self, entries):
        self.index.write_text(json.dumps({"schema_version": 1, "entries": entries}), encoding="utf-8")

    def test_only_explicit_current_entries_are_counted(self):
        self.save([self.entry, {"uuid": "00000000-0000-0000-0000-000000000002",
                                "status": "blocked", "result_path": None},
                   {"uuid": "00000000-0000-0000-0000-000000000003",
                    "status": "failed", "result_path": None},
                   {"uuid": "00000000-0000-0000-0000-000000000004",
                    "status": "stale", "result_path": None}])
        records, counts = summary.load_current_records(self.index, self.current)
        self.assertEqual([r["uuid"] for r in records], [self.uid])
        self.assertEqual(counts, {"current": 1, "blocked": 1, "failed": 1, "stale": 1, "pending": 0})
        self.assertEqual(summary.aggregate(records)["advertisement_count"], 1)
        with self.assertRaisesRegex(summary.SummaryError, "duplicate advertisement UUID"):
            self.save([self.entry, self.entry])
            summary.load_current_records(self.index, self.current)

    def test_later_verified_title_is_display_metadata_only(self):
        self.save([{**self.entry, "display_title": "Synthetic role",
                    "title_checked_at_utc": "2026-11-03T10:00:00Z"}])
        records, counts = summary.load_current_records(self.index, self.current)
        self.assertEqual((counts["current"], records[0]["title"]), (1, "Synthetic role"))
        self.assertEqual(records[0]["items"][0]["skills"], ["Python"])
        with tempfile.TemporaryDirectory(dir=summary.ROOT / "out") as folder:
            aggregated = summary.aggregate(records)
            aggregated["status_counts"] = counts
            summary.write_outputs(self.index, records, aggregated, Path(folder))
            written = json.loads((Path(folder) / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(written["advertisements"][0]["title"], "Synthetic role")
            self.assertIn("Synthetic role", (Path(folder) / "advertisements.md").read_text(encoding="utf-8"))

    def test_archive_path_and_excluded_result_cannot_enter(self):
        old = {**self.entry, "result_path": "archive/synthetic/result.json"}
        self.save([old])
        with self.assertRaisesRegex(summary.SummaryError, "not selected UUID directory"):
            summary.load_current_records(self.index, self.current)
        self.save([{**self.entry, "status": "blocked"}])
        with self.assertRaisesRegex(summary.SummaryError, "excluded result path"):
            summary.load_current_records(self.index, self.current)

    def test_failed_replacement_preserves_existing_statistics(self):
        with (patch.object(summary, "CURRENT_INDEX", self.index),
              patch.object(summary, "CURRENT_ROOT", self.current),
              patch.object(summary, "OUTPUT_ROOT", self.stats)):
            self.assertEqual(summary.main([]), 0)
            before = {p.name: p.read_bytes() for p in self.stats.iterdir()}
            self.save([{**self.entry, "content_sha256": "0" * 64}])
            self.assertEqual(summary.main([]), 1)
            self.assertEqual({p.name: p.read_bytes() for p in self.stats.iterdir()}, before)

    def test_failed_new_attempt_does_not_replace_selected_result(self):
        selected_index = self.index.read_bytes()
        selected_result = (self.current / self.uid / "result.json").read_bytes()
        failed = self.root / "nav_runs" / "newer-failed-attempt"
        failed.mkdir(parents=True)
        (failed / "validation.json").write_text(json.dumps({"passed": False}), encoding="utf-8")
        records, counts = summary.load_current_records(self.index, self.current)
        self.assertEqual(counts["current"], 1)
        self.assertEqual(records[0]["uuid"], self.uid)
        self.assertEqual(self.index.read_bytes(), selected_index)
        self.assertEqual((self.current / self.uid / "result.json").read_bytes(), selected_result)


if __name__ == "__main__":
    unittest.main()
