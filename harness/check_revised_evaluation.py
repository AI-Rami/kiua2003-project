"""Verify the saved second evaluation using the original validator and scorer."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import run as evaluation

EVIDENCE = ROOT / "docs/evaluation/2026-11-22_18-54-11_UTC-07c529af"


def main():
    suite, cases = evaluation.preflight(ROOT / "eval/cases/manifest.json")
    record = evaluation.read_json(EVIDENCE / "record.json")
    answers = evaluation.read_json(EVIDENCE / "answers.json")
    if list(answers) != [case["uuid"] for case in cases] or list(answers) != [
            entry["uuid"] for entry in record["cases"]]:
        raise evaluation.EvaluationError("saved cases differ from the frozen suite")
    validated = matched = model_items = reference_items = 0
    for case, entry in zip(cases, record["cases"]):
        uid = case["uuid"]
        answer = answers[uid]
        if (answer["model"] != suite["model"] or
                evaluation.digest(case["prepared"].encode()) != entry["input_sha256"]):
            raise evaluation.EvaluationError(f"{uid}: model or input differs")
        validation, output = evaluation.extractor.validate(answer, case["prepared"])
        if (validation["passed"] != entry["validation_passed"] or
                validation["errors"] != entry["validation_errors"]):
            raise evaluation.EvaluationError(f"{uid}: validation differs from recorded result")
        if not validation["passed"]:
            print(uid, "failed as recorded:", ", ".join(validation["errors"]))
            continue
        score = evaluation.scoring.score_items(case["reference"]["items"], output["items"], case["aliases"])
        # The scorer returns index pairs as tuples. JSON stores them as arrays.
        if json.loads(json.dumps(score)) != entry["accuracy_score"]:
            raise evaluation.EvaluationError(f"{uid}: score differs from recorded result")
        validated += 1
        matched += score["matched"]
        model_items += score["model_count"]
        reference_items += score["reference_count"]
        print(uid, "validated,", score["matched"], "matches")
    print(f"Reproduced {validated}/{len(cases)} validated, {len(cases)-validated} failed. "
          f"{matched} matches, {model_items} model items, {reference_items} reference items.")


if __name__ == "__main__":
    try:
        main()
    except evaluation.EvaluationError as error:
        sys.exit(str(error))
