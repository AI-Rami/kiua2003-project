"""Summarize only explicitly selected current NAV extractions, offline."""

import argparse
import copy
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import uuid
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT / "archive" / "comp2-generated-2026-11-02" / "nav_runs"
CURRENT_ROOT = ROOT / "out" / "current"
CURRENT_INDEX = CURRENT_ROOT / "index.json"
OUTPUT_ROOT = ROOT / "out" / "statistics"
SELECTED_REVIEW = ROOT / "reviews" / "current-v2.json"
CLASSES = ("required", "preferred", "unclear")
OTHER_TYPES = ("work_duty", "work_context", "interest_only")
EXPECTED_ADS = 10
STATUSES = ("current", "blocked", "failed", "stale", "pending")


class SummaryError(Exception):
    pass


def review_digest(raw):
    """Hash review text with stable line endings across Git checkouts."""
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest()


def publication_date(value):
    """Use the calendar date in NAV's saved timestamp and its supplied offset."""
    if value is None or value == "":
        return None, "missing"
    if not isinstance(value, str):
        return None, "invalid"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None, "invalid"
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None, "invalid"
    return parsed.date().isoformat(), "valid"


def load_current_records(index_path=CURRENT_INDEX, current_root=CURRENT_ROOT):
    """Read the authoritative selection; never discover runs by age or directory scan."""
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise SummaryError("current index: unreadable UTF-8 JSON") from None
    if not isinstance(index, dict) or index.get("schema_version") != 1 or not isinstance(index.get("entries"), list):
        raise SummaryError("current index: invalid structure")
    records, seen = [], set()
    counts = {status: 0 for status in STATUSES}
    for entry in index["entries"]:
        if not isinstance(entry, dict):
            raise SummaryError("current index: invalid entry")
        ad_id = entry.get("uuid")
        try:
            if not isinstance(ad_id, str) or str(uuid.UUID(ad_id)) != ad_id:
                raise ValueError()
        except ValueError:
            raise SummaryError("current index: invalid UUID") from None
        if ad_id in seen:
            raise SummaryError(f"current index: duplicate advertisement UUID {ad_id}")
        seen.add(ad_id)
        status = entry.get("status")
        if status not in STATUSES:
            raise SummaryError(f"current index: invalid status for {ad_id}")
        counts[status] += 1
        if status != "current":
            if entry.get("result_path") is not None:
                raise SummaryError(f"current index: excluded result path for {ad_id}")
            continue
        content_hash = entry.get("content_sha256")
        if not isinstance(content_hash, str) or re.fullmatch(r"[0-9a-f]{64}", content_hash) is None:
            raise SummaryError(f"current index: invalid content hash for {ad_id}")
        classic = (current_root / ad_id / "result.json").relative_to(ROOT).as_posix()
        versioned = (current_root / ad_id / "versions" / content_hash / "result.json").relative_to(ROOT).as_posix()
        selected_path = entry.get("result_path")
        if selected_path not in (classic, versioned):
            raise SummaryError(f"current index: result path is not selected UUID directory for {ad_id}")
        expected = current_root / ad_id if selected_path == classic else current_root / ad_id / "versions" / content_hash
        result_path = expected / "result.json"
        if expected.is_symlink() or not expected.resolve().is_relative_to(current_root.resolve()):
            raise SummaryError(f"current index: selected directory escapes current output for {ad_id}")
        if selected_path != result_path.resolve().relative_to(ROOT).as_posix():
            raise SummaryError(f"current index: result path is not selected UUID directory for {ad_id}")
        if (entry.get("validation_status") != "passed" or entry.get("format_version") != 2
                or not isinstance(entry.get("review_warnings"), list)
                or entry.get("activity_status", "UNKNOWN") not in ("ACTIVE", "INACTIVE", "UNKNOWN")
                or any(not isinstance(w, str) for w in entry["review_warnings"])):
            raise SummaryError(f"current index: selected metadata invalid for {ad_id}")
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
            validation = json.loads((expected / "validation.json").read_text(encoding="utf-8"))
            request = json.loads((expected / "request.json").read_text(encoding="utf-8"))
            response = json.loads((expected / "response.json").read_text(encoding="utf-8"))
            prepared = (expected / "prepared_ad.txt").read_text(encoding="utf-8")
            (expected / "report.md").read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError):
            raise SummaryError(f"current index: missing or unreadable selected run artifacts for {ad_id}") from None
        text_format = request.get("text") if isinstance(request, dict) else None
        text_format = text_format.get("format") if isinstance(text_format, dict) else None
        valid_schema = (isinstance(text_format, dict)
                        and text_format.get("type") == "json_schema"
                        and text_format.get("name") == "skill_extraction_v2"
                        and text_format.get("strict") is True
                        and isinstance(text_format.get("schema"), dict)
                        and hashlib.sha256(json.dumps(text_format["schema"], ensure_ascii=False,
                                                      sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
                        == entry.get("schema_sha256"))
        if (not isinstance(result, dict) or not isinstance(validation, dict)
                or not isinstance(request, dict) or not isinstance(response, dict)
                or not valid_schema
                or validation.get("passed") is not True or result.get("validation") != "passed"
                or result.get("format_version") != 2 or result.get("source_uuid") != ad_id
                or result.get("run_id") != entry.get("original_run_id")
                or result.get("source_url") != entry.get("source_url")
                or result.get("response_id") != response.get("id")
                or result.get("model") != request.get("model") or result.get("model") != response.get("model")
                or result.get("model") != entry.get("model_id")
                or request.get("reasoning") != {"effort": entry.get("reasoning_effort")}
                or request.get("max_output_tokens") != entry.get("max_output_tokens")
                or request.get("stream") is not False or request.get("store") is not False
                or request.get("input") != prepared
                or not isinstance(request.get("instructions"), str)
                or hashlib.sha256(prepared.encode("utf-8")).hexdigest() != entry.get("content_sha256")
                or hashlib.sha256(request["instructions"].encode("utf-8")).hexdigest() != entry.get("prompt_sha256")
                or not isinstance(result.get("capture_provenance"), dict)
                or result["capture_provenance"].get("revised_version") != entry.get("cleaning_version")):
            raise SummaryError(f"current index: selected run does not match index for {ad_id}")
        source = entry.get("source_url")
        try:
            parsed = urlsplit(source)
            safe = parsed.scheme == "https" and bool(parsed.hostname) and parsed.username is None and parsed.password is None
        except (TypeError, ValueError):
            safe = False
        if not safe or not isinstance(result.get("items"), list):
            raise SummaryError(f"current index: invalid source or items for {ad_id}")
        title = entry.get("display_title", result.get("title"))
        if title is not None and (not isinstance(title, str) or not title.strip()):
            raise SummaryError(f"current index: invalid display title for {ad_id}")
        checked_at = entry.get("title_checked_at_utc")
        if checked_at is not None and (not isinstance(checked_at, str) or not checked_at.strip()):
            raise SummaryError(f"current index: invalid title check time for {ad_id}")
        for item in result["items"]:
            if (not isinstance(item, dict)
                    or set(item) != {"skills", "relationship", "classification", "mention_type", "skill_evidence", "classification_context"}
                    or not isinstance(item["skills"], list) or not item["skills"]
                    or any(not isinstance(skill, str) or not skill.strip() for skill in item["skills"])
                    or len(set(item["skills"])) != len(item["skills"])
                    or item["relationship"] not in ("single", "any_of")
                    or (item["relationship"] == "single" and len(item["skills"]) != 1)
                    or (item["relationship"] == "any_of" and len(item["skills"]) < 2)
                    or item["classification"] not in CLASSES
                    or item["mention_type"] not in ("candidate_qualification", "work_duty", "work_context", "interest_only")
                    or (item["mention_type"] != "candidate_qualification" and item["classification"] != "unclear")
                    or not isinstance(item["skill_evidence"], str) or not item["skill_evidence"].strip()
                    or item["skill_evidence"] not in prepared
                    or (item["classification_context"] is not None
                        and (not isinstance(item["classification_context"], str)
                             or not item["classification_context"].strip()
                             or item["classification_context"] not in prepared))):
                raise SummaryError(f"current index: invalid v2 item for {ad_id}")
        date, date_status = publication_date(result["capture_provenance"].get("published"))
        records.append({"uuid": ad_id, "source_url": source, "report": expected / "report.md",
                        "content_sha256": content_hash,
                        "title": title.strip() if title else None, "title_checked_at_utc": checked_at,
                        "items": result["items"], "review_warnings": entry["review_warnings"],
                        "activity_status": entry.get("activity_status", "UNKNOWN"),
                        "publication_date": date, "publication_date_status": date_status})
    return records, counts


def index_rows(text):
    """Read only the advertisement rows and their explicitly linked reports."""
    rows = []
    seen = set()
    for line in text.splitlines():
        if not re.match(r"^\|\s*[0-9a-fA-F]{8}-[0-9a-fA-F-]{27}\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            raise SummaryError("index: advertisement row has unexpected columns")
        try:
            ad_id = str(uuid.UUID(cells[0]))
        except ValueError:
            raise SummaryError("index: invalid advertisement UUID") from None
        if ad_id in seen:
            raise SummaryError(f"index: duplicate advertisement UUID {ad_id}")
        seen.add(ad_id)
        if cells[1] not in ("success", "previous success; no new request"):
            raise SummaryError(f"index: advertisement {ad_id} is not successful")
        link = re.fullmatch(r"\[report\]\(([^)]+)\)", cells[2])
        if link is None:
            raise SummaryError(f"index: advertisement {ad_id} has no report link")
        rows.append((ad_id, link.group(1)))
    if len(rows) != EXPECTED_ADS:
        raise SummaryError(f"index: expected {EXPECTED_ADS} distinct successful advertisements; found {len(rows)}")
    return rows


def load_records(index_path, runs_root=RUNS_ROOT):
    try:
        rows = index_rows(index_path.read_text(encoding="utf-8"))
    except OSError:
        raise SummaryError("index: cannot read UTF-8 batch index") from None
    records = []
    allowed_root = runs_root.resolve()
    for ad_id, link in rows:
        report = (index_path.parent / link).resolve()
        if not report.is_relative_to(allowed_root) or report.name != "report.md":
            raise SummaryError(f"index: unsafe report link for {ad_id}")
        try:
            report.read_text(encoding="utf-8")
            result = json.loads((report.parent / "result.json").read_text(encoding="utf-8"))
            validation = json.loads((report.parent / "validation.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            raise SummaryError(f"result: unreadable report, JSON result or validation for {ad_id}") from None
        if (not isinstance(result, dict) or not isinstance(validation, dict)
                or validation.get("passed") is not True or result.get("validation") != "passed"
                or result.get("source_uuid") != ad_id or result.get("run_id") != report.parent.name):
            raise SummaryError(f"result: identity or successful validation mismatch for {ad_id}")
        source = result.get("source_url")
        if not isinstance(source, str):
            raise SummaryError(f"result: missing source URL for {ad_id}")
        try:
            parts = urlsplit(source)
            safe_url = (parts.scheme == "https" and bool(parts.hostname)
                        and parts.username is None and parts.password is None)
        except ValueError:
            safe_url = False
        if not safe_url:
            raise SummaryError(f"result: invalid source URL for {ad_id}")
        items = result.get("items")
        if not isinstance(items, list):
            raise SummaryError(f"result: missing items array for {ad_id}")
        for number, item in enumerate(items, 1):
            if not isinstance(item, dict) or set(item) != {"skills", "relationship", "classification", "evidence"}:
                raise SummaryError(f"result: invalid item {number} for {ad_id}")
            skills = item["skills"]
            relation = item["relationship"]
            if (not isinstance(skills, list) or not skills
                    or any(not isinstance(skill, str) or not skill.strip() for skill in skills)
                    or len(set(skills)) != len(skills)
                    or relation not in ("single", "any_of")
                    or (relation == "single" and len(skills) != 1)
                    or (relation == "any_of" and len(skills) < 2)
                    or item["classification"] not in CLASSES
                    or not isinstance(item["evidence"], str) or not item["evidence"].strip()):
                raise SummaryError(f"result: invalid item {number} for {ad_id}")
        records.append({"uuid": ad_id, "source_url": source, "report": report, "items": items})
    return records


def item_digest(item):
    return hashlib.sha256(json.dumps(item, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def apply_selected_review(records, review_path=SELECTED_REVIEW):
    """Apply version- and item-hash-checked v2 decisions to copies of results."""
    try:
        raw = review_path.read_bytes()
        review = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise SummaryError("selected review: unreadable UTF-8 JSON") from None
    if (not isinstance(review, dict) or review.get("schema_version") != 1
            or not isinstance(review.get("advertisements"), list)):
        raise SummaryError("selected review: invalid structure")
    revised = copy.deepcopy(records)
    by_uuid = {record["uuid"]: record for record in revised}
    applied, stale, seen_ads = 0, [], set()
    fields = {"skills", "relationship", "classification", "mention_type",
              "skill_evidence", "classification_context"}
    for ad in review["advertisements"]:
        if not isinstance(ad, dict) or not isinstance(ad.get("uuid"), str) or ad["uuid"] in seen_ads:
            raise SummaryError("selected review: invalid advertisement")
        seen_ads.add(ad["uuid"])
        record = by_uuid.get(ad["uuid"])
        if record is None or record.get("content_sha256") != ad.get("content_sha256"):
            stale.append(ad["uuid"])
            continue
        decisions = ad.get("decisions")
        if not isinstance(decisions, list):
            raise SummaryError("selected review: missing decisions")
        source = ((record["report"].parent / "prepared_ad.txt").read_text(encoding="utf-8")
                  if any(decision.get("action") in ("replace", "split")
                         for decision in decisions if isinstance(decision, dict)) else "")
        originals = record["items"]
        by_number = {}
        for decision in decisions:
            if not isinstance(decision, dict):
                raise SummaryError("selected review: invalid decision")
            number = decision.get("item_number")
            if (not isinstance(number, int) or isinstance(number, bool) or number < 1
                    or number > len(originals) or number in by_number):
                raise SummaryError("selected review: missing or repeated item")
            original = originals[number - 1]
            if decision.get("item_sha256") != item_digest(original):
                raise SummaryError("selected review: item hash mismatch")
            if decision.get("expected_skills") != original["skills"]:
                raise SummaryError("selected review: item label mismatch")
            action = decision.get("action")
            if action == "remove":
                if "changes" in decision:
                    raise SummaryError("selected review: remove has changes")
                by_number[number] = []
            elif action in ("replace", "split"):
                patches = [decision.get("changes")] if action == "replace" else decision.get("changes")
                if not isinstance(patches, list) or not patches or any(not isinstance(p, dict) for p in patches):
                    raise SummaryError("selected review: invalid replacement")
                replacements = []
                for patch in patches:
                    if not set(patch).issubset(fields) or "skill_evidence" in patch:
                        raise SummaryError("selected review: invalid changed fields")
                    item = {**original, **patch}
                    skills = item.get("skills")
                    if (set(item) != fields or not isinstance(skills, list) or not skills
                            or any(not isinstance(skill, str) or not skill.strip() for skill in skills)
                            or len(set(skills)) != len(skills)
                            or item.get("relationship") not in ("single", "any_of")
                            or (item["relationship"] == "single" and len(skills) != 1)
                            or (item["relationship"] == "any_of" and len(skills) < 2)
                            or item.get("classification") not in CLASSES
                            or item.get("mention_type") not in ("candidate_qualification", *OTHER_TYPES)
                            or (item["mention_type"] != "candidate_qualification"
                                and item["classification"] != "unclear")
                            or item["skill_evidence"] not in source
                            or (item["classification_context"] is not None
                                and (not isinstance(item["classification_context"], str)
                                     or not item["classification_context"].strip()
                                     or item["classification_context"] not in source))):
                        raise SummaryError("selected review: invalid v2 replacement")
                    replacements.append(item)
                if action == "split" and len(replacements) < 2:
                    raise SummaryError("selected review: split needs multiple items")
                by_number[number] = replacements
            else:
                raise SummaryError("selected review: unknown action")
            applied += 1
        record["items"] = [item for number, original in enumerate(originals, 1)
                           for item in by_number.get(number, [original])]
    info = {"path": review_path.resolve().relative_to(ROOT).as_posix(),
            "sha256": review_digest(raw), "decision_count": applied,
            "correction_count": applied,
            "unapplied_uuids": stale, "status": "provisional agent review; not approved ground truth"}
    return revised, info


def apply_review(records, review_path):
    """Apply explicit source-text audit decisions without changing saved model outputs."""
    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise SummaryError("review: unreadable UTF-8 JSON") from None
    if not isinstance(review, dict) or not isinstance(review.get("corrections"), list) or not isinstance(review.get("aliases"), dict):
        raise SummaryError("review: expected corrections list and aliases object")
    revised = copy.deepcopy(records)
    by_uuid = {record["uuid"]: record for record in revised}
    touched = set()
    for correction in review["corrections"]:
        if not isinstance(correction, dict):
            raise SummaryError("review: invalid correction")
        ad_id = correction.get("uuid")
        number = correction.get("item_number")
        if ad_id not in by_uuid or not isinstance(number, int) or isinstance(number, bool) or number < 1:
            raise SummaryError("review: unknown advertisement or invalid item number")
        items = by_uuid[ad_id]["items"]
        if number > len(items) or (ad_id, number) in touched:
            raise SummaryError("review: missing or duplicate item")
        touched.add((ad_id, number))
        original = items[number - 1]
        if correction.get("original_sha256") != item_digest(original):
            raise SummaryError(f"review: original item changed for {ad_id} item {number}")
        action = correction.get("action")
        if action == "remove":
            if "replacement" in correction:
                raise SummaryError("review: remove cannot have replacement")
            items[number - 1] = None
        elif action == "replace":
            replacement = correction.get("replacement")
            if not isinstance(replacement, dict) or set(replacement) != set(original):
                raise SummaryError("review: replacement has invalid fields")
            skills = replacement.get("skills")
            relation = replacement.get("relationship")
            if (not isinstance(skills, list) or not skills or
                    any(not isinstance(skill, str) or not skill.strip() for skill in skills) or
                    len(set(skills)) != len(skills) or
                    relation not in ("single", "any_of") or
                    (relation == "single" and len(skills) != 1) or
                    (relation == "any_of" and len(skills) < 2) or
                    replacement.get("classification") not in CLASSES or
                    replacement.get("evidence") != original["evidence"]):
                raise SummaryError("review: invalid replacement or changed evidence")
            items[number - 1] = replacement
        else:
            raise SummaryError("review: unknown action")
    for record in revised:
        record["items"] = [item for item in record["items"] if item is not None]
    aliases = review["aliases"]
    for old, new in aliases.items():
        if (not isinstance(old, str) or not isinstance(new, str) or not old.strip() or
                not new.strip() or old == new or new in aliases):
            raise SummaryError("review: invalid or chained skill alias")
    names = {skill for record in revised for item in record["items"] for skill in item["skills"]}
    if any(old not in names for old in aliases):
        raise SummaryError("review: alias source not in reviewed results")
    for record in revised:
        for item in record["items"]:
            mapped = [aliases.get(skill, skill) for skill in item["skills"]]
            if len(set(mapped)) != len(mapped):
                raise SummaryError("review: alias collapsed alternatives within one item")
            item["skills"] = mapped
    return revised, {"path": review_path.resolve().relative_to(ROOT).as_posix(),
                     "correction_count": len(touched), "aliases": aliases}


def add(mapping, key, classification, ad_id):
    if key not in mapping:
        mapping[key] = {label: set() for label in CLASSES}
    mapping[key][classification].add(ad_id)


def count_rows(mapping, key_name):
    rows = []
    for key, buckets in mapping.items():
        supporting = {label: sorted(buckets[label]) for label in CLASSES}
        supporting["total"] = sorted(set().union(*(buckets[label] for label in CLASSES)))
        counts = {label: len(supporting[label]) for label in (*CLASSES, "total")}
        value = list(key) if key_name == "skills" else key
        rows.append({key_name: value, "counts": counts, "supporting_uuids": supporting})
    rows.sort(key=lambda row: (-row["counts"]["total"],
                               str(row[key_name]).casefold(), str(row[key_name])))
    return rows


def count_other_rows(mapping):
    rows = []
    for skill, buckets in mapping.items():
        supporting = {kind: sorted(buckets[kind]) for kind in OTHER_TYPES}
        supporting["total"] = sorted(set().union(*(buckets[kind] for kind in OTHER_TYPES)))
        rows.append({"skill": skill,
                     "counts": {kind: len(supporting[kind]) for kind in (*OTHER_TYPES, "total")},
                     "supporting_uuids": supporting})
    rows.sort(key=lambda row: (-row["counts"]["total"], row["skill"].casefold(), row["skill"]))
    return rows


def count_other_groups(mapping):
    rows = [{"mention_type": kind, "skills": list(skills), "count": len(ids),
             "supporting_uuids": sorted(ids)}
            for (kind, skills), ids in mapping.items()]
    rows.sort(key=lambda row: (-row["count"], row["mention_type"],
                               tuple(skill.casefold() for skill in row["skills"])))
    return rows


def aggregate(records):
    seen = set()
    all_skills = {}
    single_skills = {}
    alternative_skills = {}
    alternative_groups = {}
    qualification_single = {}
    qualification_or_groups = {}
    other_single = {}
    other_or_groups = {}
    for record in records:
        ad_id = record["uuid"]
        if ad_id in seen:
            raise SummaryError(f"aggregate: duplicate advertisement UUID {ad_id}")
        seen.add(ad_id)
        for item in record["items"]:
            classification = item["classification"]
            skills = item["skills"]
            mention_type = item.get("mention_type")  # Legacy v1 records remain in the broad counts only.
            if item["relationship"] == "single":
                add(single_skills, skills[0], classification, ad_id)
                if mention_type == "candidate_qualification":
                    add(qualification_single, skills[0], classification, ad_id)
                elif mention_type in OTHER_TYPES:
                    if skills[0] not in other_single:
                        other_single[skills[0]] = {kind: set() for kind in OTHER_TYPES}
                    other_single[skills[0]][mention_type].add(ad_id)
            else:
                add(alternative_groups, tuple(skills), classification, ad_id)
                for skill in skills:
                    add(alternative_skills, skill, classification, ad_id)
                if mention_type == "candidate_qualification":
                    add(qualification_or_groups, tuple(skills), classification, ad_id)
                elif mention_type in OTHER_TYPES:
                    other_or_groups.setdefault((mention_type, tuple(skills)), set()).add(ad_id)
            for skill in skills:
                add(all_skills, skill, classification, ad_id)
    return {
        "advertisement_count": len(seen),
        "all_skills": count_rows(all_skills, "skill"),
        "single_skills": count_rows(single_skills, "skill"),
        "alternative_skills": count_rows(alternative_skills, "skill"),
        "alternative_groups": count_rows(alternative_groups, "skills"),
        "qualification_single_skills": count_rows(qualification_single, "skill"),
        "qualification_or_groups": count_rows(qualification_or_groups, "skills"),
        "other_single_skills": count_other_rows(other_single),
        "other_or_groups": count_other_groups(other_or_groups),
    }


def markdown_cell(value):
    return html.escape(str(value), quote=False).replace("|", "\\|").replace("\r", "<br>").replace("\n", "<br>")


def count_table(rows, key_name):
    heading = "OR group" if key_name == "skills" else "Skill"
    lines = [f"| {heading} | Required | Preferred | Unclear | Total distinct ads |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        label = " OR ".join(row["skills"]) if key_name == "skills" else row["skill"]
        counts = row["counts"]
        lines.append(f"| {markdown_cell(label)} | {counts['required']} | {counts['preferred']} | "
                     f"{counts['unclear']} | {counts['total']} |")
    return lines


def other_table(rows):
    lines = ["| Skill | Duty ads | Work-context ads | Interest-only ads | Total distinct ads |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        counts = row["counts"]
        lines.append(f"| {markdown_cell(row['skill'])} | {counts['work_duty']} | "
                     f"{counts['work_context']} | {counts['interest_only']} | {counts['total']} |")
    return lines


def other_or_table(rows):
    if not rows:
        return ["No such groups in the selected results."]
    lines = ["| Mention type | OR group | Distinct ads |",
             "| --- | --- | ---: |"]
    for row in rows:
        label = " OR ".join(row["skills"])
        lines.append(f"| {markdown_cell(row['mention_type'])} | {markdown_cell(label)} | {row['count']} |")
    return lines


def render_summary(summary):
    coverage = summary["publication_coverage"]
    date_range = (f"{coverage['earliest']} through {coverage['latest']}"
                  if coverage["known"] else "unavailable")
    lines = ["# Prototype skills in selected NAV advertisements", "",
             f"Included: {summary['advertisement_count']} distinct validated model extractions. "
             f"Excluded: {sum(summary['status_counts'][key] for key in STATUSES if key != 'current')} "
             f"({summary['status_counts']['blocked']} blocked, {summary['status_counts']['failed']} failed, "
             f"{summary['status_counts']['stale']} stale, {summary['status_counts']['pending']} pending).", "",
             f"Activity at last saved check among included ads: {summary['activity_counts']['ACTIVE']} ACTIVE, "
             f"{summary['activity_counts']['INACTIVE']} INACTIVE, "
             f"{summary['activity_counts']['UNKNOWN']} UNKNOWN. These are not live status checks. "
             "All included ads contribute to the historical counts; no active-only table is produced.", "",
             "This is a small-sample prototype, not complete Innlandet market coverage or manually approved "
             "extraction ground truth. Some selected extractions have known interpretation warnings.", "",
             "## Saved publication dates and coverage", "",
             f"Publication date available for {coverage['known']} of {summary['advertisement_count']} selected ads "
             f"({coverage['missing']} missing, {coverage['invalid']} invalid). "
             f"Their saved publication dates span {date_range}.", "",
             "These are dates among selected ads, not the period covered by NAV collection. An older publication "
             "date on an updated ad does not establish historical collection coverage. No weekly, monthly or "
             "yearly statistics are calculated.", "",
             "## Counting rules", "",
             "- Saved skill names are used except for explicit version-checked provisional corrections. No aliases or similar names are merged.",
             "- Each UUID counts once per skill and classification. Total is the union of UUIDs, "
             "so it can be smaller than the sum of the three classification columns.",
             "- The main table counts only single applicant qualifications. A duty, team practice or interest "
             "does not become an applicant requirement.",
             "- OR choices are listed as groups, not as independently required skills. The saved order is "
             "preserved; each exact group counts once per UUID and classification.",
             "- Duties, work context and interest-only single mentions are counted separately below. "
             "Their counts describe mentions, not applicant demand.",
             "- Rows and category totals can overlap; do not add rows to obtain a number of unique ads.", "",
             ]
    if summary.get("review"):
        lines += ["## Review basis", "",
                  f"Applied {summary['review']['correction_count']} item corrections from "
                  f"`{summary['review']['path']}`. Original run files are unchanged. "
                  "Review decisions and unresolved cases are in the review file. These are provisional, not approved ground truth.", "",
                  "An `unclear` mention is not evidence of applicant demand. A named OR alternative is not independently mandatory.", ""]
    lines += [
             "## Applicant qualifications: single skills", "",
             *count_table(summary["qualification_single_skills"], "skill"), "",
             "## Applicant qualifications: OR alternatives", "",
             "A required group means the applicant may satisfy the stated choice; no member is counted "
             "as independently mandatory here.", "",
             *count_table(summary["qualification_or_groups"], "skills"), "",
             "## Other technical single mentions", "",
             *other_table(summary["other_single_skills"]), "",
             "## Other technical OR mentions", "",
             *other_or_table(summary["other_or_groups"]), ""]
    return "\n".join(lines)


def render_advertisements(records, output_dir):
    lines = ["# Advertisements behind the skill summary", "",
             f"{len(records)} explicitly selected validated model extractions. Source links are retained as saved; "
             "titles and missing publication dates are not inferred. Titles come from saved extraction "
             "or a later NAV detail lookup. Dates are from saved capture provenance, "
             "not live NAV status checks. Interpretation warnings remain in the evaluation review.", "",
             "| Title | Advertisement UUID | Saved publication date | Extraction report | NAV source URL | Review warnings |",
             "| --- | --- | --- | --- | --- | ---: |"]
    for record in records:
        report_link = os.path.relpath(record["report"], output_dir).replace("\\", "/")
        lines.append(f"| {markdown_cell(record.get('title') or 'Title unavailable')} | "
                     f"{record['uuid']} | {record.get('publication_date') or 'Unavailable'} | "
                     f"[report]({report_link}) | "
                     f"[source]({record['source_url']}) | {len(record['review_warnings'])} |")
    return "\n".join(lines + [""])


def write_outputs(index_path, records, summary, output_root=OUTPUT_ROOT, review_info=None):
    output_root.mkdir(parents=True, exist_ok=True)
    folder = output_root
    summary["activity_counts"] = {status: sum(record.get("activity_status") == status for record in records)
                                  for status in ("ACTIVE", "INACTIVE", "UNKNOWN")}
    dates = sorted(record["publication_date"] for record in records if record.get("publication_date"))
    summary["publication_coverage"] = {
        "known": len(dates),
        "missing": sum(record.get("publication_date_status", "missing") == "missing" for record in records),
        "invalid": sum(record.get("publication_date_status") == "invalid" for record in records),
        "earliest": dates[0] if dates else None, "latest": dates[-1] if dates else None,
        "scope": "saved dates among selected advertisements; not collection-period coverage",
    }
    summary["dataset"] = "selected validated extractions with provisional source-review decisions; small-sample prototype, not complete market coverage"
    summary["source_index"] = index_path.resolve().relative_to(ROOT).as_posix()
    summary["source_index_sha256"] = hashlib.sha256(index_path.read_bytes()).hexdigest()
    summary["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    if review_info:
        summary["review"] = review_info
    summary["counting_rules"] = [
        "Saved skill names except explicit version-checked provisional corrections; no aliasing or fuzzy matching",
        "One advertisement UUID per skill and classification; total is the UUID union",
        "Main table includes single candidate qualifications only",
        "OR-group membership is separate from independently required single skills",
        "Duties, work context and interest-only mentions are separate from applicant qualifications",
        "Saved OR-group order is preserved",
    ]
    summary["advertisements"] = [
        {"uuid": record["uuid"], "source_url": record["source_url"],
         "report_path": os.path.relpath(record["report"], folder).replace("\\", "/"),
         "publication_date": record.get("publication_date"),
         "title": record.get("title"), "title_checked_at_utc": record.get("title_checked_at_utc")}
        for record in records
    ]
    outputs = {"summary.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
               "summary.md": render_summary(summary),
               "advertisements.md": render_advertisements(records, folder)}
    staged = []
    try:
        for name, content in outputs.items():
            temporary = folder / ("." + name + "." + uuid.uuid4().hex + ".tmp")
            temporary.write_text(content, encoding="utf-8")
            staged.append((temporary, folder / name))
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    try:
        records, counts = load_current_records(CURRENT_INDEX, CURRENT_ROOT)
        records, review_info = apply_selected_review(records)
        summary = aggregate(records)
        summary["status_counts"] = counts
        folder = write_outputs(CURRENT_INDEX, records, summary, output_root=OUTPUT_ROOT,
                               review_info=review_info)
    except (SummaryError, OSError, ValueError) as exc:
        print(f"Skill summary failed: {exc}", file=sys.stderr)
        return 1
    print(f"Advertisements: {summary['advertisement_count']}")
    print(f"Applicant single-skill names: {len(summary['qualification_single_skills'])}; "
          f"applicant OR groups: {len(summary['qualification_or_groups'])}; "
          f"other single-mention names: {len(summary['other_single_skills'])}")
    print(f"Summary: {folder / 'summary.md'}")
    print(f"Structured counts: {folder / 'summary.json'}")
    print(f"Advertisement index: {folder / 'advertisements.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
