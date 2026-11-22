# NAV skill review rules (draft v2)

Rami and Yehya review together using the full cleaned text from the [review index](cases/review-index.md). This guide is for human review only.

## 1. Identify technical mentions

Read the whole ad. List technical skills, tools, technologies and methods in qualifications, duties, work context and interests.

Exclude education, years of experience, natural languages, personality traits and vague terms such as “tools”. Support, advice, communication and UX must be clearly technical. Record reasons for excluding technical-looking terms.

Use the ad alone: do not infer a skill from the title or employer alone. A title may clarify an explicitly stated technical qualification when the evidence shows the connection. Never consult model output while labeling.

## 2. Assign type and classification

| `mention_type` | Meaning | `classification` |
| --- | --- | --- |
| `candidate_qualification` | Applicant skill. | `required` if expected; `preferred` if optional or an advantage; otherwise `unclear`. |
| `work_duty` | Technical work the person will do. | `unclear` by itself. |
| `work_context` | Technology or method used by the team. | `unclear` by itself. |
| `interest_only` | Interest or willingness to learn. | `unclear`; this does not establish existing skill. |

Read each sentence with its governing heading. Specific wording takes precedence over a general heading.

Keep stated broad skills. Classify named examples using the whole sentence and its heading. A preferred heading can make named tools in a desired-knowledge bullet `preferred` without saying every tool must be known. A broad required skill does not automatically make each example `required`; use `unclear` when the individual status is not established. Parentheses alone decide neither case.

## 3. Name and group skills

- Use consistent English names and agreed aliases; no fuzzy matching or added meaning.
- `single`: one skill. Distinct skills joined by **and** are separate items.
- `any_of`: one group of two or more explicit **or** alternatives; no member is individually mandatory.
- Merge repeated mentions with the same meaning. Prefer an explicit qualification over a duty or context mention; flag conflicting qualification labels for review.

For a required `any_of` group, the applicant needs at least one member; none is individually mandatory. Every named member still shows what experience the employer accepts as an alternative. Collaboration explicitly tied to technical development work may be a technical work-practice skill; generic teamwork or personality wording is not. Keep all in-scope alternatives together rather than converting them into separate required `single` items.

When a duty explicitly combines two distinct actions with two distinct objects, represent each supported action–object combination separately. Apply this annotation convention consistently across the reference set; the split is a review choice, not the only possible reading. Do not automatically multiply actions by every named platform or target: decide whether those names describe separate capabilities or targets of shared activities. Do not count overlapping codebase activities as distinct skills without a supported distinction. Keep the skill name to the technical topic or activity, and use `mention_type` to express that it is only an interest.

## 4. Copy evidence

Copy `skill_evidence` exactly as one continuous passage from `prepared_ad.txt`, supporting any claimed action. Copy a governing heading into `classification_context` when needed; otherwise use `null`. Exact text alone does not prove correct interpretation.

## 5. Approve the complete answer

Follow the [reference format](reference-format.md). Check completeness, names, labels, groups and evidence. Record the input hash and disagreements. Both reviewers must approve the complete answer; unresolved ads stay outside the accuracy score.

**Example:** “Du må kunne Python eller R” is one `required` qualification with an `any_of` group.
