# Labeling rules for the gold set

These rules describe how we label skills by hand, so our labels can be compared with the model's output.

## 1. What counts as a technical skill
- Include: programming languages, named tools and technologies, and technical methods (Python, SQL, Docker, machine learning, etc).
- Exclude: education, years of experience, personal traits, social skills such as collaboration, and natural languages such as Norwegian.
- Test: "Could this be learned in a technical course?" Important is not the same as technical.

## 2. Classification
- required: listed as an applicant qualification, with no optional wording. "Must" does not need to appear.
- preferred: explicitly optional, e.g. "fordel", "ønskelig", "fortrinnsvis".
- unclear: mentioned, but not as something the applicant must have. Duties, team tools and interest-only mentions are unclear.

## 3. Alternatives and lists
- "A or B": one any_of group [A, B]. The applicant needs only one.
- "A and B": two separate skills, each with its own label.

## 4. Example from a real ad
"Erfaring med og/eller interesse for koding- og programmeringsverktøy – fortrinnsvis Python"
→ Python: preferred, because "fortrinnsvis" means preferably, not required.