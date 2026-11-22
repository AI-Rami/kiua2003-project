"""Deterministic item-level comparison for approved NAV v2 references."""

class ReferenceError(ValueError):
    pass


LABELS = {"required", "preferred", "unclear"}
MENTIONS = {"candidate_qualification", "work_duty", "work_context", "interest_only"}


def key(item, aliases=None):
    """Use only exact names and explicitly approved alias mappings."""
    aliases = aliases or {}
    if not isinstance(item, dict):
        raise ReferenceError("item must be an object")
    names = item.get("skills")
    relation = item.get("relationship")
    if (not isinstance(names, list) or not names or
            any(not isinstance(name, str) or not name.strip() for name in names) or
            relation not in ("single", "any_of") or
            (relation == "single" and len(names) != 1) or
            (relation == "any_of" and len(names) < 2)):
        raise ReferenceError("invalid skill relationship")
    canonical = tuple(aliases.get(name, name) for name in names)
    if len(set(canonical)) != len(canonical):
        raise ReferenceError("duplicate names after alias mapping")
    return relation, tuple(sorted(canonical))


def check_reference(reference, prepared, aliases=None):
    """Reject malformed or duplicate approved items before they can be scored."""
    if (not isinstance(reference, dict) or reference.get("approval") != "approved_complete"
            or not isinstance(reference.get("items"), list)):
        raise ReferenceError("reference is not approved and complete")
    seen = set()
    for item in reference["items"]:
        if (not isinstance(item, dict) or set(item) !=
                {"skills", "relationship", "classification", "mention_type",
                 "skill_evidence", "classification_context"}):
            raise ReferenceError("reference item has wrong fields")
        item_key = key(item, aliases)
        if item_key in seen:
            raise ReferenceError("duplicate reference item")
        seen.add(item_key)
        if item.get("classification") not in LABELS or item.get("mention_type") not in MENTIONS:
            raise ReferenceError("reference has invalid classification or mention type")
        if item["mention_type"] != "candidate_qualification" and item["classification"] != "unclear":
            raise ReferenceError("non-qualification reference mention must be unclear")
        for field in ("skill_evidence", "classification_context"):
            quote = item.get(field)
            if field == "classification_context" and quote is None:
                continue
            if not isinstance(quote, str) or not quote.strip() or quote not in prepared:
                raise ReferenceError("reference quotation is not a continuous input passage")


def score_items(reference_items, model_items, aliases=None):
    """Pair each complete skill/group key once; duplicate output stays unsupported."""
    aliases = aliases or {}
    remaining = {}
    for index, item in enumerate(reference_items):
        remaining.setdefault(key(item, aliases), []).append(index)
    pairs, extra = [], []
    for model_index, item in enumerate(model_items):
        item_key = key(item, aliases)
        if remaining.get(item_key):
            pairs.append((remaining[item_key].pop(0), model_index))
        else:
            extra.append(model_index)
    missing = sorted(index for indexes in remaining.values() for index in indexes)
    matched = len(pairs)
    precision = matched / len(model_items) if model_items else None
    recall = matched / len(reference_items) if reference_items else None
    f1 = (2 * precision * recall / (precision + recall) if precision is not None and recall is not None
          and precision + recall else 0.0 if precision is not None and recall is not None else None)
    label_errors = [(a, b) for a, b in pairs if reference_items[a]["classification"] != model_items[b]["classification"]]
    mention_errors = [(a, b) for a, b in pairs if reference_items[a]["mention_type"] != model_items[b]["mention_type"]]
    return {"reference_count": len(reference_items), "model_count": len(model_items),
            "matched": matched, "unsupported_model_indexes": extra, "omitted_reference_indexes": missing,
            "classification_error_pairs": label_errors, "mention_type_error_pairs": mention_errors,
            "missing_alternative_group_indexes": [index for index in missing
                                                   if reference_items[index]["relationship"] == "any_of"],
            "precision": precision, "recall": recall, "f1": f1}
