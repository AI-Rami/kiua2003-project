# Task 002: NAV skill extraction walking skeleton in saved-input mode

## Goal and boundary

Build one command that prepares a saved advertisement, calls OpenAI, validates structural output, and writes JSON and a readable Markdown report. The default input is the reviewed, edited `fixtures/nav_ad_01.json`; `--input` accepts another compatible saved advertisement. This mode calls an online model but does not fetch live NAV data. Full extraction-accuracy evaluation, live NAV collection, filtering, scheduling, statistics across advertisements, and a GUI are deferred.

Read `AGENTS.md`, `SPEC.md`, this brief, and `fixtures/nav_ad_01.notes.md` before implementation. Do not edit `eval/` or read `.env` files. Use `KIUA2003_API` from the process environment and never display or persist its value or the Authorization header. The fixture's saved `ACTIVE` status is historical; this task makes no live status or location eligibility claim.

## Proposed files

- `harness/nav_skeleton.py`: one command entry point with separate prepare, extract, and validate/report functions.
- `harness/prompts/extract_skills.txt`: reusable general extraction instructions.
- `out/nav_runs/<run-id>/`: unique per-run directory with UTF-8 `prepared_ad.txt`, credential-free `request.json`, raw `response.json`, `validation.json`, and, only on success, `result.json` and `report.md`. A failed run retains available diagnostics but no successful report.

Use Python 3's standard library if feasible. Resolve paths from the repository, not the caller's current directory. Do not add a package dependency without a separate decision.

## One command interface

`python harness/nav_skeleton.py --mode saved-input` runs all three stages using saved advertisement data and one online model call. `python harness/nav_skeleton.py --mode dry-run` prints stages, paths, and limits without requiring an API key, making a network request, or changing files. `--input` selects another compatible saved JSON file. Use only `gpt-6-luna` in this version; no model switching or automatic retries.

## Processing and request

1. Parse the fixture as UTF-8 JSON; require its expected UUID, `ad_content.description`, and source link. Treat the edited fixture as test data.
2. Convert the entire edited `ad_content.description` HTML to plain text using an HTML parser, decode named and numeric entities, retain headings, list items, and paragraph boundaries, and normalize whitespace deterministically. Do not restrict the extraction input to `Kvalifikasjoner` or omit other sections. Save the exact prepared text before extraction. The checker compares quotations against this saved text using exact, case-sensitive matching.
3. Make one non-streaming `POST https://api.openai.com/v1/responses` call with `model: gpt-6-luna`, `reasoning: {"effort":"medium"}`, `text.format.type: "json_schema"`, `strict: true`, and the schema below. Read `KIUA2003_API` in memory; never print, log, or save the key or Authorization header. Sanitize errors. The request contains only prepared text, general extraction instructions, and schema, never a reference or expected skill list. The prompt asks for English skill names, original-language quotations, applicant qualifications versus duties/team technologies, preserved “or” groups, and no duplicate skills.
4. Use `stream: false`, `store: false`, `max_output_tokens: 2048` (including reasoning tokens), a 60-second timeout, and at most one request per invocation. Reject a serialized UTF-8 request body above 20,000 bytes before calling. This is an input-size limit, not an exact token count or guaranteed billing cap. Abort on HTTP, timeout, incomplete response, refusal, missing usage, or malformed output. Do not retry or silently repair output.
5. Validate JSON fields/types, allowed relationships/classifications, nonempty skills/evidence, `single` with one skill, `any_of` with at least two distinct skills, exact evidence substring in prepared text, and no identical duplicate items. English names need not occur literally in Norwegian evidence. Write `validation.json`; only successful validation writes `result.json` and `report.md`. Include title, source link, UUID, run ID/time, model/response ID, items, usage, and cost estimate. Render `A OR B` and the exact original-language quotation in the report. State: “Structure and quotation checks passed. Extraction accuracy and completeness have not yet been evaluated.” Fail non-zero with credential-free explanation.

Previously verified [OpenAI standard pricing](https://developers.openai.com/api/docs/pricing), used as dated estimates: `gpt-6-luna` text costs $0.10 per million input tokens and $0.50 per million output tokens. Calculate estimated cost from actual response usage; output usage already includes reasoning tokens, so do not count them twice or present the estimate as a billing statement. The [model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna) confirms the model ID, Responses API, Structured Outputs, and medium reasoning support.

## Proposed extraction schema

Each item represents one technical mention, with `skills` holding alternatives together. `relationship: "any_of"` preserves a choice rather than demanding every alternative. `single` has exactly one skill. Evidence is an exact contiguous quotation from prepared text.

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "skills": {"type": "array", "items": {"type": "string"}},
          "relationship": {"type": "string", "enum": ["single", "any_of"]},
          "classification": {"type": "string", "enum": ["required", "preferred", "unclear"]},
          "evidence": {"type": "string"}
        },
        "required": ["skills", "relationship", "classification", "evidence"],
        "additionalProperties": false
      }
    }
  },
  "required": ["items"],
  "additionalProperties": false
}
```

The structural validator rejects empty skill names or evidence, invalid groups, fabricated quotations, and identical duplicate extraction items. English skill names are not required to appear literally in Norwegian quotations. It does not compare against the draft reference or claim accuracy or completeness.

## Acceptance checks

1. Before any paid call, run syntax and model-free checks for HTML preparation, valid output, invalid structure, fabricated evidence, invalid alternative groups, and an English skill name with valid Norwegian evidence.
2. Confirm dry run requires no key and makes no network request or file change.
3. Run saved-input once; confirm the endpoint, model, medium reasoning, strict schema, non-streaming request, limits, and no reference or credentials in `request.json`. Inspect response ID, status, usage, output, report, and estimated cost. Do not selectively retry a failure.
4. On timeout, HTTP error, incomplete/refusal, absent usage, bad schema, or bad quotation: exit non-zero with stage and reason; do not write a successful result or report. Keep available diagnostics.

## Deferred accuracy evaluation — draft fixture reference pending human review

This proposal covers technical skills mentioned across the **whole edited description**, not just `Kvalifikasjoner`. It is **not approved ground truth** and is not used by this skeleton's validator. No reference JSON or semantic evaluator is created now. Future review may settle scope, labels, aliases, evidence spans, item-order independence, omissions, and invented skills without fuzzy matching or another LLM deciding pass/fail. Keep this draft out of every model request. Rows marked **Review** need a human decision.

| Proposed skill names (one group) | Relationship | Class | Exact supporting quotation | Decision and review point |
| --- | --- | --- | --- | --- |
| dataintegrasjon; dataplattformer; maskinlæring | any_of | required | `Praktisk erfaring med dataintegrasjon, dataplattformer eller maskinlæring fra jobb, studier eller egne prosjekter` | Listed under applicant qualifications; one of three experience areas suffices. **Review:** no explicit “må”; `unclear` may be more conservative. |
| språkmodeller | single | required | `Du bruker språkmodeller i hverdagen og vet hvor de er gode, og hvor de finner på ting` | Applicant use and evaluation are described under qualifications. **Review:** implied requirement rather than explicit “må”; also mentioned in duties and application questions. |
| regnskapsdata; økonomisystemer | any_of | preferred | `Erfaring med regnskapsdata eller økonomisystemer en fordel, men ikke krav` | Explicit advantage, explicitly not mandatory; preserve the “or” choice. |
| automatisering | single | unclear | `Ha ansvar for verktøy, data og automatisering i Ponte` | Future duty, not a prior applicant requirement. The opening also speculates about home automation. **Review:** whether to extract this skill at all. |
| Excel | single | unclear | `I dag løses dette med Excel, manuelt arbeid og litt flaks.` | Describes an existing process, not an applicant qualification. **Review:** whether a tool in problem context belongs in the reference. |
| arkitektur | single | unclear | `Fra arkitektur og teknologivalg til hvor en språkmodell gjør jobben bedre, og hvor den ikke gjør det.` | Part of future responsibility, not prior knowledge required. **Review:** whether to include broad architecture as a skill. |
| teknologivalg | single | unclear | `Fra arkitektur og teknologivalg til hvor en språkmodell gjør jobben bedre, og hvor den ikke gjør det.` | Future decision-making duty; no prior applicant requirement established. **Review:** whether this overlaps `teknologivurderinger`. |
| kode | single | unclear | `Men du blir ikke sittende alene i et hjørne og kode.` | Describes how the future job is performed, not a prior programming requirement. **Review:** whether generic coding belongs in skills; any `programmering` alias needs explicit approval. |
| teknologivurderinger | single | unclear | `Bistå teamet i andre prosjekter, for eksempel med teknologivurderinger og tekniske deler av søknader` | Future duty only. **Review:** possible overlap with `teknologivalg`; approve one or both names. |
| scrum-team | single | unclear | `Vi jobber i stor grad som et scrum-team.` | Team practice, not an applicant requirement. **Review:** whether a team methodology mention belongs in skills. |

The opening's `Høyst sannsynlig har du allerede automatisert noe hjemme som ingen andre i familien skjønner hvordan fungerer.` is a second possible evidence span for automatisering, subject to review of its inflected wording and relevance. Repeated mentions of språkmodeller in the opening, duties, and application question should likewise not create duplicate qualifications. Broad words such as `verktøy`, `data`, and `teknologi` are not independent skill names here. “Bakgrunn fra informatikk, datateknikk, kunstig intelligens eller noe tilsvarende” concerns education credentials, outside this skills-only task. Personality and team-fit text is nontechnical and excluded. **Review:** the entire `unclear` set may be narrowed to mentions that reviewers consider genuinely relevant technical skills; do not silently turn duties or team technology into `required`.
