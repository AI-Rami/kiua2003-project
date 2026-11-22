"""Readable, dated reports and a local index for NAV evaluation runs."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re


def item_name(item):
    names = item.get("skills", []) if isinstance(item, dict) else []
    if not isinstance(names, list):
        return "Unknown item"
    return " OR ".join(str(name) for name in names) if item.get("relationship") == "any_of" else str(names[0]) if names else "Unknown item"


def comparison(score, reference_items, model_items):
    """Capture automatic name/group differences without calling them semantic errors."""
    return {
        "unmatched_model_names": [item_name(model_items[i]) for i in score["unsupported_model_indexes"]],
        "unmatched_reference_names": [item_name(reference_items[i]) for i in score["omitted_reference_indexes"]],
        "classification_differences": [
            {"name": item_name(reference_items[expected]),
             "reference": reference_items[expected]["classification"],
             "model": model_items[actual]["classification"]}
            for expected, actual in score["classification_error_pairs"]],
        "mention_type_differences": [
            {"name": item_name(reference_items[expected]),
             "reference": reference_items[expected]["mention_type"],
             "model": model_items[actual]["mention_type"]}
            for expected, actual in score["mention_type_error_pairs"]],
        "unmatched_or_groups": [item_name(reference_items[i])
                                for i in score["missing_alternative_group_indexes"]],
    }


def generated_time(record, folder):
    value = record.get("generated_at_utc")
    if isinstance(value, str):
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if instant.tzinfo is not None:
                return instant.astimezone(timezone.utc).strftime("%d %B %Y, %H:%M:%S UTC")
        except ValueError:
            pass
    match = re.match(r"^(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})_UTC-", folder.name)
    if match:
        instant = datetime.strptime(" ".join(match.groups()), "%Y-%m-%d %H %M %S")
        return instant.strftime("%d %B %Y, %H:%M:%S UTC")
    return "Time not recorded"


def rate(value, numerator, denominator):
    return f"{value:.1%} ({numerator} of {denominator})" if isinstance(value, (float, int)) else "not applicable"


def named_list(lines, heading, values):
    if values:
        lines += [f"**{heading} ({len(values)}):**", ""]
        lines.extend(f"- {value}" for value in values)
        lines.append("")


def synthetic_text(case):
    expected, actual = case["expected"], case["actual"]
    kind = case["kind"]
    if kind == "input_rejection":
        return ("Expected the uncertain contact passage to be held before extraction, with no model call "
                "or published result. Observed: "
                f"{actual.get('capture_outcome', 'unknown')}; reason {actual.get('reason', 'unknown')}; "
                f"model calls {actual.get('model_calls', 'unknown')}; "
                f"published {actual.get('published', 'unknown')}.")
    if kind == "alternative_group":
        return ("Expected one complete OR group to match and separate single skills to fail that match. "
                f"Observed: group matches {actual.get('same_group_matches', 'unknown')}; "
                f"split-single matches {actual.get('split_singles_match', 'unknown')}.")
    if kind == "heading_context":
        return ("Expected the skill passage and governing heading to match exactly. "
                f"Observed: skill {actual.get('skill_quote', 'unknown')}; "
                f"heading {actual.get('context_quote', 'unknown')}; "
                f"validation {'passed' if actual.get('validation_passed') else 'failed'}.")
    if kind == "duty_vs_qualification":
        return ("Expected the checker to notice that the same named technology was wrongly labelled "
                "as an applicant requirement instead of a duty. "
                f"Observed: {actual.get('classification_errors', 'unknown')} classification and "
                f"{actual.get('mention_type_errors', 'unknown')} mention-type differences.")
    if kind == "quotation_boundary":
        return ("Expected exact wording to pass and changed wording or spacing to fail. "
                f"Observed: exact {'passed' if actual.get('exact_passes') else 'failed'}; "
                f"changed word {'passed' if actual.get('changed_word_passes') else 'failed'}; "
                f"changed spacing {'passed' if actual.get('changed_whitespace_passes') else 'failed'}.")
    return f"Expected: {expected}. Observed: {actual}."


def report_text(record, folder):
    mode = record.get("mode", "unknown")
    mode_name = {"replay": "saved response replay", "offline-suite": "offline evaluation suite",
                 "model": "fresh model evaluation"}.get(mode, mode)
    selected = record.get("selected", 0)
    attempted = record.get("attempted", 0)
    validated = record.get("validated", 0)
    failed = record.get("failed", 0)
    not_run = record.get("not_run", 0)
    lines = ["# NAV skills evaluation report", "", f"**Generated:** {generated_time(record, folder)}", "",
             f"**Test type:** {mode_name}", "",
             f"**Prompt SHA-256:** `{record.get('prompt_sha256', 'not recorded')}`", "",
             f"**Model:** {record.get('model', 'not recorded')}", "", "## What happened", "",
             f"This run selected {selected} saved advertisements. It attempted {attempted}, "
             f"validated {validated}, failed {failed}, and left {not_run} not run.", ""]
    if not_run or failed:
        lines += ["This run is partial or contains failures. Scores below cover only approved cases "
                  "whose responses passed validation.", ""]
    else:
        lines += ["All selected advertisements were attempted and passed the format and quotation checks. "
                  "Those checks do not establish that the extracted skills are correct.", ""]
    score = record.get("accuracy_score")
    lines += ["## Skill comparison across the real advertisements", ""]
    if isinstance(score, dict):
        matched = score["matched"]
        model_count = score["model_count"]
        reference_count = score["reference_count"]
        lines += [f"The exact name and OR-group checker paired **{matched} items**. The model produced "
                  f"{model_count} items; the approved references contain {reference_count} items.", "",
                  f"- **Precision:** {rate(score.get('precision'), matched, model_count)} model items matched a reference item.",
                  f"- **Recall:** {rate(score.get('recall'), matched, reference_count)} reference items were matched.",
                  f"- **F1:** {score['f1']:.3f} (a combined precision and recall measure)." if isinstance(score.get('f1'), (int, float)) else "- **F1:** not applicable.",
                  "", "These are automatic item-name and complete-group matches. Equivalent wording can be "
                  "unmatched, so an unmatched item is not automatically a confirmed extraction mistake.", ""]
    else:
        lines += ["No real-advertisement accuracy score is available for this run.", ""]
    lines += ["## Advertisement results", ""]
    roles = {case["uuid"]: case for case in record.get("real_case_roles", [])}
    for number, case in enumerate(record.get("cases", []), start=1):
        uuid = case.get("uuid", "unknown")
        role = roles.get(uuid, {})
        title = case.get("title")
        heading = title if isinstance(title, str) and title.strip() else f"Advertisement {number}"
        lines += [f"### {heading}", "", f"**UUID:** `{uuid}`" +
                  (f" · **Case ID:** {role['id']}" if role.get("id") else ""), ""]
        if role.get("reason"):
            lines += [f"**Why this case is included:** {role['reason']}", ""]
        source = case.get("source_url")
        if isinstance(source, str) and source.startswith("https://"):
            lines += [f"**Source:** [Original advertisement]({source})", ""]
        case_status = case.get("status")
        passed = case.get("validation_passed", case_status == "validated")
        if case_status == "not_run":
            lines += ["No model request was made for this advertisement. It was not scored.", ""]
            continue
        if not passed:
            reason = case.get("reason") or "; ".join(case.get("validation_errors", [])) or "no validated response"
            lines += [f"The response did not pass validation: {reason}. It was not scored.", ""]
            continue
        lines += ["The response passed the format and quotation checks.", ""]
        per_ad = case.get("accuracy_score")
        if not isinstance(per_ad, dict):
            lines += ["No approved reference score is available for this advertisement.", ""]
            continue
        matched = per_ad["matched"]
        model_count = per_ad["model_count"]
        reference_count = per_ad["reference_count"]
        lines += [f"The checker matched **{matched} of {reference_count} reference items**. The model "
                  f"returned {model_count} items; {model_count - matched} model items and "
                  f"{reference_count - matched} reference items remained unmatched.", "",
                  f"Precision: {rate(per_ad.get('precision'), matched, model_count)}. "
                  f"Recall: {rate(per_ad.get('recall'), matched, reference_count)}. "
                  + (f"F1: {per_ad['f1']:.3f}." if isinstance(per_ad.get("f1"), (int, float)) else "F1: not applicable."), "",
                  f"Among matched names, the checker found {len(per_ad['classification_error_pairs'])} "
                  f"classification and {len(per_ad['mention_type_error_pairs'])} mention-type differences. "
                  f"It left {len(per_ad['missing_alternative_group_indexes'])} reference OR groups unmatched.", ""]
        details = case.get("comparison", {})
        named_list(lines, "Model items without an exact reference match", details.get("unmatched_model_names", []))
        named_list(lines, "Reference items without an exact model match", details.get("unmatched_reference_names", []))
        named_list(lines, "Unmatched OR groups", details.get("unmatched_or_groups", []))
        if details.get("classification_differences"):
            named_list(lines, "Different required/preferred/unclear labels",
                       [f"{d['name']} (reference {d['reference']}; model {d['model']})"
                        for d in details["classification_differences"]])
        if details.get("mention_type_differences"):
            named_list(lines, "Different mention types",
                       [f"{d['name']} (reference {d['reference']}; model {d['model']})"
                        for d in details["mention_type_differences"]])
    if mode == "offline-suite":
        synthetic = record.get("synthetic_cases", [])
        lines += ["## Synthetic boundary and rejection checks", "",
                  f"**{record.get('synthetic_passed', 0)} of {len(synthetic)} passed.** "
                  "These checks are separate from the real-advertisement skill score.", ""]
        for case in synthetic:
            lines += [f"### {case['id']} — {'Passed' if case['passed'] else 'Failed'}", "",
                      synthetic_text(case), ""]
    if mode == "model":
        lines += ["## Model requests and cost", "",
                  f"Requests attempted: {attempted} of {selected}. "
                  f"Planning maximum: ${record.get('estimated_max_cost_usd', 0):.6f}. "
                  f"Usage-based estimate so far: ${record.get('estimated_actual_cost_usd', 0):.6f}.", ""]
        for case in record.get("cases", []):
            usage = case.get("usage")
            if isinstance(usage, dict):
                lines += [f"- `{case['uuid']}`: {usage.get('input_tokens', 'unknown')} input tokens; "
                          f"{usage.get('output_tokens', 'unknown')} output tokens "
                          "(including any billed reasoning tokens); "
                          f"estimated ${case.get('estimated_cost_usd', 0):.6f}."]
        lines += [""]
    lines += ["## How to read this report", "",
              "The five real advertisements are development and regression cases, not an unseen or representative "
              "market sample. Exact quotation matching checks that words occur in the saved text; it does not "
              "establish correct interpretation. The automatic comparison does not replace human meaning review. "
              "This evaluation does not update dashboard statistics.", ""]
    return "\n".join(lines)


def update_index(root):
    entries = []
    if not root.exists():
        return
    for folder in root.iterdir():
        if not folder.is_dir() or not re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_UTC-[0-9a-f]{8}", folder.name):
            continue
        if not (folder / "report.md").is_file() or not (folder / "record.json").is_file():
            continue
        try:
            record = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        if not isinstance(record, dict):
            continue
        score = record.get("accuracy_score")
        f1 = score.get("f1") if isinstance(score, dict) else None
        result = (f"{record.get('validated', '?')}/{record.get('selected', '?')} validated"
                  + (f"; {record.get('synthetic_passed', '?')}/{len(record['synthetic_cases'])} synthetic passed"
                     if isinstance(record.get("synthetic_cases"), list) else ""))
        entries.append((folder.name, generated_time(record, folder), record.get("mode", "unknown"),
                        record.get("prompt_sha256", "unknown"), result,
                        f"{f1:.3f}" if isinstance(f1, (int, float)) else "not available"))
    lines = ["# NAV evaluation runs", "",
             "Each folder contains one report for all advertisements tested in that run. "
             "Older reports are kept as originally generated. The dates below are UTC.", "",
             "| Run time | Test type | Prompt SHA-256 | Completion | F1 | Report |",
             "| --- | --- | --- | --- | --- | --- |"]
    for name, when, mode, prompt, result, f1 in sorted(entries, reverse=True):
        lines.append(f"| {when} | {mode} | `{str(prompt)[:12]}` | {result} | {f1} | [Open report]({name}/report.md) |")
    lines += ["", "Real-ad skill scores and synthetic pass counts measure different things; open each report for details.", ""]
    temporary = root / "index.md.tmp"
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(root / "index.md")


def write_report(folder, record):
    temporary = folder / "report.md.tmp"
    temporary.write_text(report_text(record, folder), encoding="utf-8")
    temporary.replace(folder / "report.md")
    update_index(folder.parent)
