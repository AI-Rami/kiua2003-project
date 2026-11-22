"""Compare the human gold labels with the model's extracted skills.

Usage (from the project root):
    python eval/score.py
    python eval/score.py --only-reviewed

Reads eval/gold/gold.csv and the model results in out/current/<uuid>/result.json
(created when harness/start.py restores the shared baseline). Writes
eval/results/score.md and eval/results/matches.csv. Makes no network calls.

How a gold skill is matched to a model item:
  1. Names are lower-cased and split into words ("Relational databases (SQL)"
     becomes {relational, database, sql}). A trailing plural "s" is removed.
  2. A gold skill matches a model item when every gold word appears in the
     model item's words. "SQL" therefore matches "Relational databases (SQL)".
  3. If several model items match, the one with the fewest extra words wins,
     so "Azure" matches "Azure" before "Azure Functions".

Measures:
  recall     = gold skills found by the model / all gold skills
  precision  = model items matched by at least one gold skill / all model items
  F1         = 2 * precision * recall / (precision + recall)
  label agreement = matched gold skills where the model's classification
                    (required, preferred, unclear) equals the gold label
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "eval" / "gold" / "gold.csv"
RESULTS = ROOT / "out" / "current"
OUT = ROOT / "eval" / "results"


# Spelling variants that mean the same thing. Kept short on purpose:
# only wording differences, never different skills.
SYNONYMS = {
    "artificial intelligence": "ai",
    "large language model": "language model",
    "geospatial": "geographic",
    "statistics production": "statistical production",
}


def words(name):
    """Turn a skill name into a set of simple lower-case words."""
    text = name.lower().replace("/", " ")
    for long, short in SYNONYMS.items():
        text = text.replace(long, short)
    tokens = re.findall(r"[a-z0-9#+.]+", text)
    clean = set()
    for t in tokens:
        t = t.strip(".") if t not in (".net",) else t
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        if t:
            clean.add(t)
    return clean


def load_gold(only_reviewed):
    gold = defaultdict(list)
    with open(GOLD, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if only_reviewed and row["checked"] != "yes":
                continue
            gold[row["ad_id"]].append(row)
    return gold


def load_model(ad_id):
    """Find the current model result for one ad through out/current/index.json."""
    index = RESULTS / "index.json"
    if not index.exists():
        raise SystemExit("No out/current/index.json. Run harness/start.py once first.")
    paths = [e["result_path"] for e in json.loads(index.read_text(encoding="utf-8"))["entries"]
             if e["uuid"].startswith(ad_id)]
    if not paths:
        raise SystemExit(f"No model result for {ad_id}.")
    path = Path(paths[0])
    if not path.is_absolute():
        path = ROOT / path
    items = []
    for it in json.loads(path.read_text(encoding="utf-8"))["items"]:
        for skill in it["skills"]:
            items.append({"name": skill, "classification": it["classification"],
                          "mention_type": it.get("mention_type", "")})
    return items


def best_match(gold_name, items):
    g = words(gold_name)
    candidates = [(len(words(it["name"]) - g), i) for i, it in enumerate(items) if g and g <= words(it["name"])]
    return min(candidates)[1] if candidates else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-reviewed", action="store_true", help="use only checked ads")
    args = ap.parse_args()

    gold = load_gold(args.only_reviewed)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, per_ad = [], []
    tot = Counter()
    errors = Counter()

    for ad_id, golds in gold.items():
        items = load_model(ad_id)
        used = set()
        found = agree = 0
        for g in golds:
            i = best_match(g["skill"], items)
            m = items[i] if i is not None else None
            if m:
                used.add(i)
                found += 1
                same = m["classification"] == g["label"]
                agree += same
                if not same:
                    errors[f'gold {g["label"]} -> model {m["classification"]}'] += 1
            else:
                errors["missed by model"] += 1
            rows.append([ad_id, g["skill"], g["label"],
                         m["name"] if m else "", m["classification"] if m else "",
                         m["mention_type"] if m else "", "yes" if m else "no"])
        extra = len(items) - len(used)
        errors["model item not in gold"] += extra
        per_ad.append((ad_id, len(golds), len(items), found, len(used), agree))
        tot.update(gold=len(golds), model=len(items), found=found, used=len(used), agree=agree)

    with open(OUT / "matches.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ad_id", "gold_skill", "gold_label", "model_skill", "model_label",
                    "model_mention_type", "found"])
        w.writerows(sorted(rows))

    def pct(a, b):
        return f"{100 * a / b:.0f} %" if b else "–"

    p = tot["used"] / tot["model"] if tot["model"] else 0
    r = tot["found"] / tot["gold"] if tot["gold"] else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    scope = "checked ads only" if args.only_reviewed else "all ads (some gold labels are drafts)"
    lines = [
        "# Evaluation: gold labels vs model output", "",
        f"Scope: {scope}. Ads: {len(per_ad)}. Gold skills: {tot['gold']}. Model skills: {tot['model']}.", "",
        "| Measure | Value | Counts |", "|---|---|---|",
        f"| Recall | {pct(tot['found'], tot['gold'])} | {tot['found']} of {tot['gold']} gold skills found |",
        f"| Precision | {pct(tot['used'], tot['model'])} | {tot['used']} of {tot['model']} model skills matched gold |",
        f"| F1 | {f1:.2f} | |",
        f"| Label agreement | {pct(tot['agree'], tot['found'])} | {tot['agree']} of {tot['found']} matched skills |", "",
        "## Per advertisement", "",
        "| ad_id | Gold | Model | Recall | Precision | Label agreement |", "|---|---|---|---|---|---|",
    ]
    for a, g, m, fd, u, ag in sorted(per_ad):
        lines.append(f"| {a} | {g} | {m} | {pct(fd, g)} | {pct(u, m)} | {pct(ag, fd)} |")
    lines += ["", "## Error types", "", "| Error | Count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in errors.most_common()]
    lines += ["", "Matching is by word overlap of skill names (see eval/score.py), so a few matches may be",
              "too loose or too strict. Check eval/results/matches.csv before quoting numbers."]
    (OUT / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
