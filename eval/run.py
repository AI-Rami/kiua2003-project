"""Replay frozen NAV responses or run a bounded fresh-model evaluation."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
import nav_skeleton as extractor  # noqa: E402
import offline_cases  # noqa: E402
import reporting  # noqa: E402
import scoring  # noqa: E402


class EvaluationError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text_digest(data):
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return digest(normalized.replace(b"\n", b"\r\n"))


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise EvaluationError("missing or invalid evaluation JSON") from None


def pinned_bytes(path, expected):
    try:
        data = path.read_bytes()
    except OSError:
        raise EvaluationError("missing frozen artifact") from None
    if digest(data) != expected:
        raise EvaluationError("frozen artifact hash mismatch")
    return data


def pinned_text_bytes(path, expected):
    try:
        data = path.read_bytes()
    except OSError:
        raise EvaluationError("missing frozen text artifact") from None
    if text_digest(data) != expected:
        raise EvaluationError("frozen text artifact hash mismatch")
    return data


def artifacts_for_case(uuid_value, entries, baseline):
    prefix = f"out/current/{uuid_value}/"
    required = ("prepared_ad.txt", "request.json", "response.json", "validation.json", "result.json")
    artifacts = {}
    for entry in entries:
        path = entry.get("path", "")
        if not isinstance(path, str) or not path.startswith(prefix):
            continue
        name = path.rsplit("/", 1)[-1]
        if name in required:
            if name in artifacts:
                raise EvaluationError("ambiguous frozen case artifact")
            archive = entry.get("archive", "")
            if not isinstance(archive, str) or not re.fullmatch(r"data/[0-9]{3,}", archive):
                raise EvaluationError("unsafe frozen artifact path")
            artifacts[name] = pinned_bytes(baseline / archive, entry.get("sha256"))
    if set(artifacts) != set(required):
        raise EvaluationError("incomplete frozen case artifacts")
    return artifacts


def load_approved_references(suite):
    descriptor = suite.get("references")
    if descriptor is None:
        return {}
    if not isinstance(descriptor, dict) or set(descriptor) != {"path", "sha256"}:
        raise EvaluationError("invalid reference descriptor")
    if (not isinstance(descriptor["path"], str) or not descriptor["path"]
            or not isinstance(descriptor["sha256"], str)):
        raise EvaluationError("invalid reference path or hash")
    path = (ROOT / descriptor["path"]).resolve()
    if not path.is_relative_to(ROOT / "eval/references"):
        raise EvaluationError("reference path is outside eval/references")
    data = pinned_text_bytes(path, descriptor["sha256"])
    try:
        references = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise EvaluationError("invalid approved reference JSON") from None
    if (not isinstance(references, dict) or references.get("schema_version") != 1
            or not isinstance(references.get("reviewers"), list)
            or any(not isinstance(name, str) for name in references["reviewers"])
            or set(references["reviewers"]) != {"Rami", "Yehya"}
            or not isinstance(references.get("cases"), dict)
            or not isinstance(references.get("aliases", {}), dict)):
        raise EvaluationError("incomplete approved reference metadata")
    aliases = references.get("aliases", {})
    if any(not isinstance(a, str) or not isinstance(b, str) or not a or not b
           for a, b in aliases.items()):
        raise EvaluationError("invalid approved alias mapping")
    return references


def preflight(suite_path):
    suite = read_json(suite_path)
    if suite.get("suite_version") != 1 or not isinstance(suite.get("cases"), list):
        raise EvaluationError("unsupported suite")
    baseline = ROOT / "shared/baseline"
    manifest_bytes = pinned_text_bytes(baseline / "manifest.json", suite.get("baseline_manifest_sha256"))
    pinned_text_bytes(ROOT / "eval/history/first-attempt/gold.csv", suite.get("draft_gold_sha256"))
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise EvaluationError("invalid baseline manifest")
    references = load_approved_references(suite)
    cases, seen = [], set()
    for selected in suite["cases"]:
        if not isinstance(selected, dict):
            raise EvaluationError("invalid case selection")
        try:
            case_id = str(uuid.UUID(selected["uuid"]))
        except (KeyError, TypeError, ValueError):
            raise EvaluationError("invalid case UUID") from None
        if case_id in seen:
            raise EvaluationError("duplicate case UUID")
        seen.add(case_id)
        status = selected.get("reference_status")
        if status not in ("awaiting_joint_approval", "approved_complete"):
            raise EvaluationError("invalid case reference status")
        files = artifacts_for_case(case_id, entries, baseline)
        try:
            prepared = files["prepared_ad.txt"].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            request = json.loads(files["request.json"].decode("utf-8"))
            response = json.loads(files["response.json"].decode("utf-8"))
            old_validation = json.loads(files["validation.json"].decode("utf-8"))
            result = json.loads(files["result.json"].decode("utf-8"))
        except (UnicodeError, ValueError):
            raise EvaluationError("invalid frozen case encoding or JSON") from None
        text_settings = request.get("text")
        format_settings = text_settings.get("format") if isinstance(text_settings, dict) else None
        schema = format_settings.get("schema") if isinstance(format_settings, dict) else None
        if not isinstance(schema, dict):
            raise EvaluationError("frozen schema is missing")
        schema_hash = digest(json.dumps(schema, ensure_ascii=False, sort_keys=True,
                                        separators=(",", ":")).encode("utf-8"))
        checks = {
            "input": request.get("input") == prepared,
            "model": request.get("model") == suite.get("model"),
            "reasoning": request.get("reasoning") == {"effort": suite.get("reasoning_effort")},
            "output_limit": request.get("max_output_tokens") == suite.get("max_output_tokens"),
            "request_flags": request.get("stream") is False and request.get("store") is False,
            "strict_format": format_settings.get("type") == "json_schema"
                             and format_settings.get("name") == "skill_extraction_v2"
                             and format_settings.get("strict") is True,
            "prompt": isinstance(request.get("instructions"), str) and
                      digest(request["instructions"].encode("utf-8")) == suite.get("prompt_sha256"),
            "schema": schema_hash == suite.get("schema_sha256"),
            "saved_validation": old_validation.get("passed") is True,
            "result_identity": result.get("source_uuid") == case_id and result.get("validation") == "passed"
                               and result.get("response_id") == response.get("id")
                               and result.get("model") == response.get("model") == suite.get("model"),
        }
        source = result.get("source_url")
        try:
            parsed = urlsplit(source)
            checks["source_link"] = (parsed.scheme == "https" and bool(parsed.hostname)
                                     and parsed.username is None and parsed.password is None)
        except (TypeError, ValueError):
            checks["source_link"] = False
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise EvaluationError(f"frozen request or result differs from suite for {case_id}: {', '.join(failed)}")
        reference = references.get("cases", {}).get(case_id)
        if status == "approved_complete":
            if not isinstance(reference, dict) or reference.get("input_sha256") != digest(prepared.encode("utf-8")):
                raise EvaluationError(f"approved reference missing or input differs for {case_id}")
            try:
                scoring.check_reference(reference, prepared, references.get("aliases", {}))
            except scoring.ReferenceError as exc:
                raise EvaluationError(f"invalid approved reference for {case_id}: {exc}") from None
        elif isinstance(reference, dict) and reference.get("approval") == "approved_complete":
            raise EvaluationError(f"suite has not selected approved reference for {case_id}")
        cases.append({"uuid": case_id, "title": result.get("title"), "source_url": source,
                      "prepared": prepared, "request": request, "response": response,
                      "response_id": response.get("id"), "usage": response.get("usage"),
                      "elapsed_seconds": result.get("elapsed_seconds"),
                      "estimated_cost_usd": result.get("estimated_cost_usd"),
                      "artifact_hashes": {name: digest(data) for name, data in files.items()},
                      "reference_status": status, "reference": reference,
                      "aliases": references.get("aliases", {})})
    if not cases:
        raise EvaluationError("suite selects no cases")
    return suite, cases


def replay(suite_path, output_root):
    suite, cases = preflight(suite_path)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
    folder = output_root / f"{stamp}-{uuid.uuid4().hex[:8]}"
    folder.mkdir(parents=True, exist_ok=False)
    results = []
    for case in cases:
        validation, model_output = extractor.validate(case["response"], case["prepared"])
        accuracy = (scoring.score_items(case["reference"]["items"], model_output["items"], case["aliases"])
                    if validation["passed"] and case["reference_status"] == "approved_complete" else None)
        results.append({"uuid": case["uuid"], "title": case["title"], "source_url": case["source_url"],
                        "attempted": True,
                        "validation_passed": validation["passed"], "validation_errors": validation["errors"],
                        "model_item_count": len(model_output["items"]) if validation["passed"] else None,
                        "response_id": case["response_id"], "usage": case["usage"],
                        "elapsed_seconds": case["elapsed_seconds"],
                        "estimated_cost_usd": case["estimated_cost_usd"],
                        "reference_status": case["reference_status"],
                        "accuracy_score": accuracy,
                        "comparison": (reporting.comparison(accuracy, case["reference"]["items"],
                                                            model_output["items"]) if accuracy else None),
                        "artifact_hashes": case["artifact_hashes"]})
    validated = sum(item["validation_passed"] for item in results)
    scored = [item["accuracy_score"] for item in results if item["accuracy_score"] is not None]
    matched = sum(item["matched"] for item in scored)
    model_count = sum(item["model_count"] for item in scored)
    reference_count = sum(item["reference_count"] for item in scored)
    precision = matched / model_count if model_count else None
    recall = matched / reference_count if reference_count else None
    f1 = (2 * precision * recall / (precision + recall) if precision is not None and recall is not None
          and precision + recall else 0.0 if precision is not None and recall is not None else None)
    aggregate = ({"matched": matched, "model_count": model_count, "reference_count": reference_count,
                  "precision": precision, "recall": recall, "f1": f1,
                  "classification_errors": sum(len(item["classification_error_pairs"]) for item in scored),
                  "mention_type_errors": sum(len(item["mention_type_error_pairs"]) for item in scored),
                  "missing_alternative_groups": sum(len(item["missing_alternative_group_indexes"]) for item in scored)}
                 if scored else None)
    approved_selected = sum(case["reference_status"] == "approved_complete" for case in cases)
    record = {"mode": "replay", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "suite": str(suite_path.relative_to(ROOT)),
              "suite_sha256": text_digest(suite_path.read_bytes()), "model": suite["model"],
              "prompt_sha256": suite["prompt_sha256"], "schema_sha256": suite["schema_sha256"],
              "selected": len(cases), "attempted": len(results), "validated": validated,
              "failed": len(results) - validated, "not_run": 0,
              "approved_selected": approved_selected, "approved_scored": len(scored),
              "accuracy_score": aggregate, "cases": results,
              "accuracy_note": ("Accuracy covers only the named, approved and validated cases."
                                if scored else "No complete reference has joint approval. Structural replay only.")}
    (folder / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reporting.write_report(folder, record)
    return folder, record


def load_offline_catalog(suite, real_cases):
    descriptor = suite.get("offline_cases")
    if not isinstance(descriptor, dict) or set(descriptor) != {"path", "sha256"}:
        raise EvaluationError("offline case catalog descriptor is missing or invalid")
    relative = descriptor.get("path")
    if not isinstance(relative, str):
        raise EvaluationError("invalid offline case catalog path")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT / "eval/cases"):
        raise EvaluationError("offline case catalog is outside eval/cases")
    data = pinned_text_bytes(path, descriptor.get("sha256"))
    try:
        catalog = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise EvaluationError("invalid offline case catalog JSON") from None
    real = catalog.get("real_cases") if isinstance(catalog, dict) else None
    synthetic = catalog.get("synthetic_cases") if isinstance(catalog, dict) else None
    if (not isinstance(catalog, dict) or catalog.get("schema_version") != 1 or not isinstance(real, list)
            or not isinstance(synthetic, list) or not synthetic):
        raise EvaluationError("invalid offline case catalog")
    if ([entry.get("uuid") for entry in real if isinstance(entry, dict)]
            != [case["uuid"] for case in real_cases]):
        raise EvaluationError("offline catalog real cases differ from frozen selection")
    ids = []
    for entry in real:
        if (not isinstance(entry, dict) or set(entry) != {"id", "uuid", "role", "reason"}
                or entry["role"] not in {"typical wording pattern", "boundary"}
                or not isinstance(entry["reason"], str) or not entry["reason"].strip()):
            raise EvaluationError("invalid real case catalog entry")
        ids.append(entry["id"])
    if not {"typical wording pattern", "boundary"}.issubset({entry["role"] for entry in real}):
        raise EvaluationError("offline catalog lacks typical or boundary real case")
    for entry in synthetic:
        if (not isinstance(entry, dict) or set(entry) != {"id", "kind", "input", "expected"}
                or entry["kind"] not in offline_cases.RUNNERS
                or not isinstance(entry["input"], str) or not entry["input"].strip()
                or not isinstance(entry["expected"], dict) or not entry["expected"]):
            raise EvaluationError("invalid synthetic case catalog entry")
        ids.append(entry["id"])
    if len(ids) != len(set(ids)) or any(not isinstance(case_id, str) or not case_id for case_id in ids):
        raise EvaluationError("duplicate or invalid offline case ID")
    if {entry["kind"] for entry in synthetic} != set(offline_cases.RUNNERS):
        raise EvaluationError("offline catalog lacks a required synthetic boundary or rejection case")
    return catalog, text_digest(data)


def offline_suite(suite_path, output_root):
    suite, cases = preflight(suite_path)
    catalog, catalog_hash = load_offline_catalog(suite, cases)
    folder, record = replay(suite_path, output_root)
    results = []
    for case in catalog["synthetic_cases"]:
        try:
            expected, actual, passed = offline_cases.run_case(case)
            reason = "expected outcome observed" if passed else "actual outcome differs from expected"
        except Exception as exc:
            expected, actual, passed = case["expected"], {"exception_type": type(exc).__name__}, False
            reason = "synthetic check could not complete"
        results.append({"id": case["id"], "kind": case["kind"], "expected": expected,
                        "actual": actual, "passed": passed, "reason": reason})
    record["mode"] = "offline-suite"
    record["offline_case_catalog_sha256"] = catalog_hash
    record["real_case_roles"] = catalog["real_cases"]
    record["synthetic_cases"] = results
    record["synthetic_passed"] = sum(result["passed"] for result in results)
    record["synthetic_failed"] = len(results) - record["synthetic_passed"]
    record["suite_passed"] = record["synthetic_failed"] == 0 and record["validated"] == record["selected"]
    extractor.save_json(folder / "record.json", record)
    reporting.write_report(folder, record)
    return folder, record


def model_preflight(suite_path, max_requests, max_seconds, max_cost_usd, prompt_sha256):
    suite, cases = preflight(suite_path)
    if not isinstance(max_requests, int) or max_requests < len(cases):
        raise EvaluationError("max-requests must cover all selected cases")
    if (not math.isfinite(max_seconds) or not math.isfinite(max_cost_usd)
            or max_seconds <= 0 or max_cost_usd <= 0):
        raise EvaluationError("time and cost limits must be positive")
    if not re.fullmatch(r"[0-9a-f]{64}", prompt_sha256 or ""):
        raise EvaluationError("an explicit 64-character prompt hash is required")
    try:
        prompt = extractor.PROMPT.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise EvaluationError("current extraction prompt is unavailable") from None
    if digest(prompt.encode("utf-8")) != prompt_sha256:
        raise EvaluationError("current extraction prompt differs from the expected hash")
    if (extractor.MODEL != suite["model"] or extractor.MAX_OUTPUT_TOKENS != suite["max_output_tokens"]
            or extractor.ENDPOINT != "https://api.openai.com/v1/responses"):
        raise EvaluationError("extractor model, output limit or endpoint differs from the suite")
    schema_hash = digest(json.dumps(extractor.SCHEMA, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8"))
    if schema_hash != suite["schema_sha256"]:
        raise EvaluationError("current extraction schema differs from the suite")
    payloads, maximum = [], 0.0
    for case in cases:
        payload = dict(case["request"])
        payload["instructions"] = prompt
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(body) > extractor.MAX_BODY_BYTES:
            raise EvaluationError(f"request body exceeds the extractor bound for {case['uuid']}")
        # UTF-8 bytes plus framing allowance is a conservative input-token planning proxy.
        # The full output cap includes billed reasoning tokens.
        maximum += ((len(body) + 4096) * extractor.INPUT_RATE
                    + suite["max_output_tokens"] * extractor.OUTPUT_RATE) / 1_000_000
        payloads.append((case, payload, body))
    if maximum > max_cost_usd:
        raise EvaluationError(f"estimated maximum ${maximum:.6f} exceeds budget ${max_cost_usd:.6f}")
    return suite, cases, payloads, maximum


def write_model_progress(folder, record):
    scored = [case["accuracy_score"] for case in record["cases"] if case.get("accuracy_score") is not None]
    matched = sum(score["matched"] for score in scored)
    model_count = sum(score["model_count"] for score in scored)
    reference_count = sum(score["reference_count"] for score in scored)
    precision = matched / model_count if model_count else None
    recall = matched / reference_count if reference_count else None
    record["accuracy_score"] = {
        "matched": matched, "model_count": model_count, "reference_count": reference_count,
        "precision": precision, "recall": recall,
        "f1": (2 * precision * recall / (precision + recall) if precision is not None
               and recall is not None and precision + recall else None),
    } if scored else None
    record["approved_scored"] = len(scored)
    record["attempted"] = sum(case["status"] != "not_run" for case in record["cases"])
    record["validated"] = sum(case["status"] == "validated" for case in record["cases"])
    record["failed"] = record["attempted"] - record["validated"]
    record["not_run"] = record["selected"] - record["attempted"]
    record["partial"] = record["not_run"] > 0
    temporary = folder / "record.json.tmp"
    extractor.save_json(temporary, record)
    temporary.replace(folder / "record.json")
    reporting.write_report(folder, record)


def model(suite_path, output_root, max_requests, max_seconds, max_cost_usd, prompt_sha256,
          transport=urlopen, *, key=None):
    suite, cases, payloads, maximum = model_preflight(
        suite_path, max_requests, max_seconds, max_cost_usd, prompt_sha256)
    if key is None:
        key = os.environ.get("KIUA2003_API", "")
    if not key.strip():
        raise EvaluationError("KIUA2003_API is unavailable or empty")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
    folder = output_root / f"{stamp}-{uuid.uuid4().hex[:8]}"
    folder.mkdir(parents=True, exist_ok=False)
    record = {"mode": "model", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "suite": str(suite_path.relative_to(ROOT)),
              "suite_sha256": text_digest(suite_path.read_bytes()), "model": suite["model"],
              "prompt_sha256": prompt_sha256, "baseline_prompt_sha256": suite["prompt_sha256"],
              "schema_sha256": suite["schema_sha256"], "reasoning_effort": suite["reasoning_effort"],
              "max_output_tokens": suite["max_output_tokens"], "max_requests": max_requests,
              "max_seconds": max_seconds, "max_cost_usd": max_cost_usd,
              "estimated_max_cost_usd": maximum, "estimated_actual_cost_usd": 0.0,
              "pricing_usd_per_million": {"input": extractor.INPUT_RATE, "output": extractor.OUTPUT_RATE},
              "pricing_source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
              "selected": len(cases), "approved_selected": sum(c["reference_status"] == "approved_complete" for c in cases),
              "cases": [{"uuid": c["uuid"], "title": c["title"], "source_url": c["source_url"],
                         "status": "not_run", "reference_status": c["reference_status"],
                         "input_sha256": digest(c["prepared"].encode("utf-8"))} for c in cases]}
    write_model_progress(folder, record)
    started = time.monotonic()
    for number, (case, payload, body) in enumerate(payloads):
        remaining = max_seconds - (time.monotonic() - started)
        if remaining <= 0:
            record["stop_reason"] = "runtime limit"
            break
        entry = record["cases"][number]
        case_folder = folder / case["uuid"]
        case_folder.mkdir()
        extractor.save_json(case_folder / "request.json", payload)
        entry["request_sha256"] = digest(body)
        entry["status"] = "attempted"
        write_model_progress(folder, record)
        request = Request(extractor.ENDPOINT, data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json; charset=utf-8",
        }, method="POST")
        request_started = time.monotonic()
        try:
            with transport(request, timeout=min(extractor.TIMEOUT_SECONDS, remaining)) as reply:
                raw = reply.read(2_000_001)
        except HTTPError as exc:
            entry.update(status="failed", reason=f"HTTP {exc.code}")
            extractor.save_json(case_folder / "failure.json", {"type": "http", "status_code": exc.code})
            record["stop_reason"] = "API failure"
            write_model_progress(folder, record)
            break
        except (URLError, TimeoutError, OSError) as exc:
            entry.update(status="failed", reason=f"network {type(exc).__name__}")
            extractor.save_json(case_folder / "failure.json", {"type": "network", "exception_type": type(exc).__name__})
            record["stop_reason"] = "network failure"
            write_model_progress(folder, record)
            break
        entry["elapsed_seconds"] = time.monotonic() - request_started
        if len(raw) > 2_000_000:
            entry.update(status="failed", reason="response size limit")
            extractor.save_json(case_folder / "failure.json", {"type": "response_size_limit"})
            record["stop_reason"] = "invalid API response"
            write_model_progress(folder, record)
            break
        try:
            response = json.loads(raw.decode("utf-8"))
            if not isinstance(response, dict):
                raise ValueError
        except (UnicodeError, ValueError):
            entry.update(status="failed", reason="invalid API JSON")
            extractor.save_json(case_folder / "failure.json", {"type": "invalid_api_json"})
            record["stop_reason"] = "invalid API response"
            write_model_progress(folder, record)
            break
        (case_folder / "response.json").write_bytes(raw)
        entry["response_sha256"] = digest(raw)
        entry["response_id"] = response.get("id")
        entry["response_model"] = response.get("model")
        entry["usage"] = response.get("usage")
        usage = response.get("usage")
        if isinstance(usage, dict):
            input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                cost = (input_tokens * extractor.INPUT_RATE + output_tokens * extractor.OUTPUT_RATE) / 1_000_000
                entry["estimated_cost_usd"] = cost
                record["estimated_actual_cost_usd"] += cost
        if response.get("model") != suite["model"]:
            validation, model_output = {"passed": False, "errors": ["response model differs from suite"]}, None
        else:
            validation, model_output = extractor.validate(response, case["prepared"])
        extractor.save_json(case_folder / "validation.json", validation)
        entry["validation_passed"] = validation["passed"]
        entry["validation_errors"] = validation["errors"]
        if validation["passed"]:
            entry["status"] = "validated"
            if case["reference_status"] == "approved_complete":
                score = scoring.score_items(case["reference"]["items"], model_output["items"], case["aliases"])
                extractor.save_json(case_folder / "score.json", score)
                entry["accuracy_score"] = score
                entry["comparison"] = reporting.comparison(score, case["reference"]["items"],
                                                           model_output["items"])
        else:
            entry.update(status="failed", reason="structural or quotation validation failed")
        write_model_progress(folder, record)
    else:
        record["stop_reason"] = "all selected cases attempted"
    write_model_progress(folder, record)
    return folder, record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("replay", "offline-suite", "model"), required=True)
    parser.add_argument("--suite", type=Path, default=ROOT / "eval/cases/manifest.json")
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--max-seconds", type=float)
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--prompt-sha256")
    args = parser.parse_args(argv)
    try:
        suite_path = args.suite.resolve()
        if not suite_path.is_relative_to(ROOT / "eval/cases"):
            raise EvaluationError("suite must be inside eval/cases")
        if args.mode == "model":
            if None in (args.max_requests, args.max_seconds, args.max_cost_usd, args.prompt_sha256):
                raise EvaluationError("model mode requires max-requests, max-seconds, max-cost-usd and prompt-sha256")
            folder, record = model(suite_path, ROOT / "out/evaluation", args.max_requests,
                                   args.max_seconds, args.max_cost_usd, args.prompt_sha256)
        elif args.mode == "offline-suite":
            folder, record = offline_suite(suite_path, ROOT / "out/evaluation")
        else:
            folder, record = replay(suite_path, ROOT / "out/evaluation")
    except EvaluationError as exc:
        parser.exit(1, f"evaluation: {exc}\n")
    if args.mode == "model":
        print(f"Model evaluation: {record['validated']}/{record['selected']} validated; "
              f"{record['failed']} failed; {record['not_run']} not run")
        print(f"Planning maximum: ${record['estimated_max_cost_usd']:.6f}; "
              f"usage-based estimate: ${record['estimated_actual_cost_usd']:.6f}")
        print(f"Report: {folder / 'report.md'}")
        return 0 if record["failed"] == record["not_run"] == 0 else 1
    if args.mode == "offline-suite":
        print(f"Offline suite: {record['validated']}/{record['selected']} real ads validated; "
              f"{record['synthetic_passed']}/{len(record['synthetic_cases'])} synthetic checks passed")
        print(f"Report: {folder / 'report.md'}")
        return 0 if record["suite_passed"] else 1
    print(f"Replay: {record['validated']}/{record['selected']} validated")
    if record["approved_scored"]:
        print(f"Approved accuracy: {record['approved_scored']}/{record['approved_selected']} "
              "selected approved cases scored; see report")
    else:
        print("Approved accuracy: unavailable; no complete approved reference has been scored")
    print(f"Report: {folder / 'report.md'}")


if __name__ == "__main__":
    sys.exit(main())
