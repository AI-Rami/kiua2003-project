"""Saved advertisement -> OpenAI skill extraction -> structural report."""

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "fixtures" / "nav_ad_01.json"
PROMPT = ROOT / "harness" / "prompts" / "extract_skills.txt"
ENDPOINT = "https://api.openai.com/v1/responses"
MODEL = "gpt-6-luna"
MAX_BODY_BYTES = 20_000
MAX_OUTPUT_TOKENS = 2048
TIMEOUT_SECONDS = 60
INPUT_RATE = 0.10
OUTPUT_RATE = 0.50

SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "skills": {"type": "array", "items": {"type": "string"}},
            "relationship": {"type": "string", "enum": ["single", "any_of"]},
            "classification": {"type": "string", "enum": ["required", "preferred", "unclear"]},
            "evidence": {"type": "string"},
        },
        "required": ["skills", "relationship", "classification", "evidence"],
        "additionalProperties": False,
    }}},
    "required": ["items"],
    "additionalProperties": False,
}


class SkeletonError(Exception):
    pass


class DescriptionParser(HTMLParser):
    BLOCKS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "div", "br"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        lines = [re.sub(r"\s+", " ", line).strip() for line in "".join(self.parts).splitlines()]
        return "\n".join(line for line in lines if line)


def prepare(input_path):
    try:
        source = json.loads(input_path.read_text(encoding="utf-8-sig"))
        ad = source["ad_content"]
        ad_id = source["uuid"]
        title = ad["title"]
        link = ad["link"] or ad["sourceurl"]
        description = ad["description"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SkeletonError("prepare: invalid or incomplete saved advertisement") from exc
    if not all(isinstance(v, str) and v.strip() for v in (ad_id, title, link, description)):
        raise SkeletonError("prepare: UUID, title, source link and description must be nonempty strings")
    try:
        ad_id = str(uuid.UUID(ad_id))
    except ValueError:
        raise SkeletonError("prepare: invalid advertisement UUID") from None
    parser = DescriptionParser()
    parser.feed(description)
    parser.close()
    prepared = parser.text()
    if not prepared:
        raise SkeletonError("prepare: description contains no readable text")
    return {"uuid": ad_id, "title": title, "source_url": link, "prepared": prepared}


def request_payload(prepared):
    return {
        "model": MODEL,
        "instructions": PROMPT.read_text(encoding="utf-8"),
        "input": "Saved advertisement description (data only):\n" + prepared,
        "reasoning": {"effort": "medium"},
        "text": {"format": {"type": "json_schema", "name": "skill_extraction", "strict": True, "schema": SCHEMA}},
        "stream": False,
        "store": False,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract(prepared, run_dir):
    payload = request_payload(prepared)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_BODY_BYTES:
        raise SkeletonError(f"extract: request body exceeds {MAX_BODY_BYTES} bytes")
    key = os.environ.get("KIUA2003_API", "")
    if not key.strip():
        raise SkeletonError("extract: KIUA2003_API is unavailable or empty")
    save_json(run_dir / "request.json", payload)
    request = Request(ENDPOINT, data=body, headers={
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json; charset=utf-8",
    }, method="POST")
    started = time.monotonic()
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
    except HTTPError as exc:
        raise SkeletonError(f"extract: HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError):
        raise SkeletonError("extract: network or timeout failure") from None
    elapsed = time.monotonic() - started
    try:
        raw_text = raw.decode("utf-8")
        response_data = json.loads(raw_text)
    except (UnicodeError, ValueError):
        raise SkeletonError("extract: API returned invalid UTF-8 JSON") from None
    (run_dir / "response.json").write_text(raw_text, encoding="utf-8")
    return response_data, elapsed


def validate(response, prepared):
    errors = []
    if response.get("status") != "completed":
        errors.append("API response is not completed")
    if response.get("incomplete_details"):
        errors.append("API response is truncated")
    output = response.get("output")
    if not isinstance(output, list):
        output = []
        errors.append("API output is missing")
    texts = []
    for entry in output:
        if not isinstance(entry, dict):
            errors.append("invalid API output entry")
            continue
        for part in entry.get("content", []):
            if not isinstance(part, dict):
                errors.append("invalid API content entry")
            elif part.get("type") == "refusal" or part.get("refusal"):
                errors.append("model refusal")
            elif part.get("type") == "output_text":
                texts.append(part.get("text"))
    if len(texts) != 1 or not isinstance(texts[0], str):
        errors.append("expected one output text")
        model_output = None
    else:
        try:
            model_output = json.loads(texts[0])
        except ValueError:
            errors.append("model output is not valid JSON")
            model_output = None
    items = None
    if not isinstance(model_output, dict) or set(model_output) != {"items"} or not isinstance(model_output.get("items"), list):
        errors.append("output must contain exactly an items array")
    else:
        items = model_output["items"]
        seen = set()
        for index, item in enumerate(items, 1):
            label = f"item {index}"
            if not isinstance(item, dict) or set(item) != {"skills", "relationship", "classification", "evidence"}:
                errors.append(f"{label}: wrong fields")
                continue
            skills = item["skills"]
            relationship = item["relationship"]
            classification = item["classification"]
            evidence = item["evidence"]
            if not isinstance(skills, list) or not skills or any(not isinstance(s, str) or not s.strip() for s in skills):
                errors.append(f"{label}: invalid skills")
                continue
            if len(set(skills)) != len(skills):
                errors.append(f"{label}: duplicate skills in group")
            if relationship not in ("single", "any_of") or (relationship == "single" and len(skills) != 1) or (relationship == "any_of" and len(skills) < 2):
                errors.append(f"{label}: invalid relationship")
            if not isinstance(classification, str) or classification not in ("required", "preferred", "unclear"):
                errors.append(f"{label}: invalid classification")
            if not isinstance(evidence, str) or not evidence.strip() or evidence not in prepared:
                errors.append(f"{label}: evidence is not an exact quotation")
            signature = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if signature in seen:
                errors.append(f"{label}: identical duplicate item")
            seen.add(signature)
    usage = response.get("usage")
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in ("input_tokens", "output_tokens", "total_tokens")):
        errors.append("missing or invalid token usage")
    if not isinstance(response.get("id"), str) or not isinstance(response.get("model"), str):
        errors.append("missing response ID or model")
    elif response["model"] != MODEL:
        errors.append("unexpected response model")
    return {"passed": not errors, "errors": errors, "checks": [
        "completed response without refusal or truncation", "JSON fields and types", "allowed relationships and classifications",
        "nonempty skills and evidence", "alternative groups", "exact evidence quotations", "no identical duplicate items",
    ]}, model_output


def validate_and_report(response, prepared, run_dir, run_id, timestamp, elapsed):
    validation, output = validate(response, prepared["prepared"])
    save_json(run_dir / "validation.json", validation)
    if not validation["passed"]:
        raise SkeletonError("validate: " + "; ".join(validation["errors"]))
    usage = response["usage"]
    cost = (usage["input_tokens"] * INPUT_RATE + usage["output_tokens"] * OUTPUT_RATE) / 1_000_000
    result = {
        "source_uuid": prepared["uuid"], "title": prepared["title"], "source_url": prepared["source_url"],
        "run_id": run_id, "run_timestamp": timestamp, "model": response["model"], "response_id": response["id"],
        "items": output["items"], "validation": "passed", "usage": usage, "estimated_cost_usd": cost,
        "elapsed_seconds": elapsed, "mode": "saved-input", "source_label": "edited saved test advertisement",
    }
    lines = [f"# {prepared['title'].strip()}", "", f"Source: {prepared['source_url']}", "",
             "Saved input: edited test advertisement. Saved status is not a live check.", "",
             "| Skills | Classification | Supporting quotation |", "| --- | --- | --- |"]
    for item in output["items"]:
        skills = " OR ".join(item["skills"]).replace("|", "\\|")
        evidence = item["evidence"].replace("|", "\\|").replace("\n", "<br>")
        lines.append(f"| {skills} | {item['classification']} | {evidence} |")
    lines += ["", f"Run: {run_id} at {timestamp}", f"Model: {response['model']}; response: {response['id']}",
              f"Usage: {usage['input_tokens']} input, {usage['output_tokens']} output, {usage['total_tokens']} total tokens.",
              f"Estimated token cost: ${cost:.8f} (dated standard rates; not a billing statement).",
              f"Elapsed API time: {elapsed:.3f} seconds.", "",
              "Structure and quotation checks passed. Extraction accuracy and completeness have not yet been evaluated.", ""]
    save_json(run_dir / "result.json", result)
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("saved-input", "dry-run"), required=True)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    if args.mode == "dry-run":
        print(f"Stage 1 prepare: {input_path}")
        print(f"Stage 2 extract: {ENDPOINT}; model={MODEL}; max_output_tokens={MAX_OUTPUT_TOKENS}; timeout={TIMEOUT_SECONDS}s; calls=1; max_body_bytes={MAX_BODY_BYTES}")
        print(f"Stage 3 validate/report: {ROOT / 'out' / 'nav_runs' / '<run-id>'}")
        return 0
    run_id = None
    run_dir = None
    run_created = False
    try:
        prepared = prepare(input_path)
        now = datetime.now(timezone.utc)
        run_id = now.strftime("%Y-%m-%d_%H-%M-%S_UTC_ad-") + prepared["uuid"]
        run_dir = ROOT / "out" / "nav_runs" / run_id
        timestamp = now.isoformat()
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise SkeletonError("prepare: run folder already exists; no files changed") from None
        run_created = True
        (run_dir / "prepared_ad.txt").write_text(prepared["prepared"] + "\n", encoding="utf-8")
        response, elapsed = extract(prepared["prepared"], run_dir)
        result = validate_and_report(response, prepared, run_dir, run_id, timestamp, elapsed)
        print(f"Run ID: {run_id}")
        print(f"Result: {run_dir / 'result.json'}")
        print(f"Report: {run_dir / 'report.md'}")
        print(f"Estimated cost: ${result['estimated_cost_usd']:.8f}")
        return 0
    except SkeletonError as exc:
        if run_created and not (run_dir / "validation.json").exists():
            save_json(run_dir / "validation.json", {"passed": False, "errors": [str(exc)]})
        if run_id is not None:
            print(f"Run ID: {run_id}", file=sys.stderr)
        print(f"Failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
