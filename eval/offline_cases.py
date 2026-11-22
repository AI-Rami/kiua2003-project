"""Fixed synthetic cases for the NAV evaluation; no network or model calls."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
import nav_skeleton as extractor  # noqa: E402
import scoring  # noqa: E402


def item(skills, relationship, classification, mention_type, evidence, context=None):
    return {"skills": skills, "relationship": relationship, "classification": classification,
            "mention_type": mention_type, "skill_evidence": evidence,
            "classification_context": context}


def response(items):
    return {"status": "completed", "incomplete_details": None,
            "id": "resp_synthetic", "model": extractor.MODEL,
            "output": [{"content": [{"type": "output_text",
                                     "text": json.dumps({"items": items}, ensure_ascii=False)}]}],
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}}


def alternative_group(case):
    quote = case["input"]
    expected_item = item(["Python", "R"], "any_of", "required", "candidate_qualification", quote)
    same = item(["R", "Python"], "any_of", "required", "candidate_qualification", quote)
    split = [item([skill], "single", "required", "candidate_qualification", quote)
             for skill in ("Python", "R")]
    same_score = scoring.score_items([expected_item], [same])
    split_score = scoring.score_items([expected_item], split)
    return {"same_group_matches": same_score["matched"],
            "split_singles_match": split_score["matched"],
            "split_singles_extra": len(split_score["unsupported_model_indexes"]),
            "split_singles_omitted": len(split_score["omitted_reference_indexes"])}


def heading_context(case):
    source = case["input"]
    skill = item(["Docker"], "single", "preferred", "candidate_qualification",
                 "God kjennskap til Docker.", "Ønskede kvalifikasjoner:")
    validation, _ = extractor.validate(response([skill]), source)
    matches = validation["quotation_matches"][0]
    return {"validation_passed": validation["passed"], "skill_quote": matches["skill_evidence"],
            "context_quote": matches["classification_context"]}


def duty_vs_qualification(case):
    source = case["input"]
    quote = "Bruke PostgreSQL i teamets dataløsning."
    reference = item(["PostgreSQL"], "single", "unclear", "work_duty", quote)
    incorrect = item(["PostgreSQL"], "single", "required", "candidate_qualification", quote)
    scoring.check_reference({"approval": "approved_complete", "items": [reference]}, source)
    score = scoring.score_items([reference], [incorrect])
    return {"name_matches": score["matched"],
            "classification_errors": len(score["classification_error_pairs"]),
            "mention_type_errors": len(score["mention_type_error_pairs"])}


def quotation_boundary(case):
    source = case["input"]
    def passes(evidence):
        skill = item(["Python"], "single", "required", "candidate_qualification", evidence)
        validation, _ = extractor.validate(response([skill]), source)
        return validation["passed"]
    return {"exact_passes": passes("Du må kunne Python."),
            "changed_word_passes": passes("Du må kunne PyThon."),
            "changed_whitespace_passes": passes("Du må  kunne Python.")}


def input_rejection(case):
    # The existing isolated update fixture exercises detail cleaning, the input gate,
    # model-call counting and publication against a temporary SQLite database.
    import nav_discover as discovery
    from test_nav_update import UpdateTests
    fixture = UpdateTests(methodName="test_raw_ambiguous_contact_passage_is_held_before_model")
    fixture.setUp()
    try:
        fixture.queue_ad(outcome="review_blocked")
        detail = {"uuid": fixture.ad_id, "status": "ACTIVE", "ad_content": {
            "workLocations": [{"county": "INNLANDET", "municipal": "Hamar"}],
            "occupationCategories": [{"level1": "IT", "level2": "Utvikling"}],
            "description": case["input"], "contactList": [], "sourceurl": fixture.source}}
        db = discovery.connect(fixture.db_path)
        try:
            discovery.save_detail_success(db, json.dumps(detail).encode("utf-8"), fixture.ad_id, 1,
                                          backfill=False)
            outcome = db.execute("SELECT outcome,reason FROM capture_state WHERE uuid=?",
                                 (fixture.ad_id,)).fetchone()
        finally:
            db.close()
        result = fixture.run_local()
        summary = json.loads((fixture.statistics / "summary.json").read_text(encoding="utf-8"))
        return {"capture_outcome": outcome[0], "reason": outcome[1],
                "model_calls": fixture.calls, "published": summary["advertisement_count"],
                "blocked_in_index": fixture.index()["entries"][0]["status"] == "blocked",
                "extraction_requests": result["extraction_requests"]}
    finally:
        fixture.doCleanups()


RUNNERS = {"alternative_group": alternative_group, "heading_context": heading_context,
           "duty_vs_qualification": duty_vs_qualification,
           "quotation_boundary": quotation_boundary, "input_rejection": input_rejection}


def run_case(case):
    actual = RUNNERS[case["kind"]](case)
    if case["kind"] == "input_rejection":
        # Include these two checks in the pass condition without duplicating them in prose.
        expected = dict(case["expected"], blocked_in_index=True, extraction_requests=0)
    else:
        expected = case["expected"]
    return expected, actual, actual == expected
