# Complete reference format for the next review step

This is a **format example using synthetic text**, not an approved answer for a NAV advertisement. Rami and Yehya must review each complete frozen input in `cases/review-index.md` before an advertisement can be scored.

```json
{
  "schema_version": 1,
  "reviewers": ["Rami", "Yehya"],
  "aliases": {},
  "cases": {
    "00000000-0000-0000-0000-000000000001": {
      "approval": "approved_complete",
      "input_sha256": "SHA-256 of the prepared UTF-8 text after universal newline reading",
      "items": [
        {
          "skills": ["Python"],
          "relationship": "single",
          "classification": "required",
          "mention_type": "candidate_qualification",
          "skill_evidence": "Du må kunne Python.",
          "classification_context": null
        }
      ]
    }
  }
}
```

An approved file must contain the complete answer for each approved advertisement, including `any_of` groups. Quotations must be continuous passages in its frozen prepared text. Leave a whole advertisement out when any relevant item or omission remains disputed. Put only explicitly approved name aliases in `aliases`; the evaluator does no fuzzy matching. Once approved, store the reviewed file under `eval/references/`, add its relative path and line-ending-stable SHA-256 to `eval/cases/manifest.json`, and set only its approved case entries to `approved_complete`. The original model response remains separate and must never be used as an unreviewed reference.
