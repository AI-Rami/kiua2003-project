# Problem candidates

These reviewed summaries describe proposals, not verified demand, verified source access, or measured results. Success criteria are proposed evaluation targets, not achieved results.

## Candidate 1: Public Tender Monitoring for Innlandet

### 1. Problem hypothesis

SMEs may miss relevant tenders because finding and reviewing announcements takes time.

### 2. Proposed users

SMEs in one selected sector in Innlandet; construction is the current example, not a final selection.

### 3. Public source(s)

Doffin public procurement announcements, subject to verification of permitted automated access.

### 4. Proposed workflow

Collect announcements → filter by region and sector → extract key details → verify against originals → produce a structured report with links.

### 5. Definition of success

On a fixed labelled test set, achieve at least 90% precision and at least 90% recall, produce valid output structure for every result, and invent no deadlines.

### 6. Evidence and feasibility still to verify

- Evidence of unmet user need.
- Value beyond existing services.
- Permitted automated access to Doffin announcements.
- Sufficient data volume for the selected region and sector.
- Final sector selection.

## Candidate 2: Job Market Analyzer for Innlandet

### 1. Problem hypothesis

Understanding requested skills from many job advertisements may require time-consuming manual analysis.

### 2. Proposed users

Job seekers, students, and educational institutions.

### 3. Public source(s)

NAV job advertisements, preferably through an appropriate API, subject to verification of access terms.

### 4. Proposed workflow

Collect advertisements → filter by region and sector → extract skills and qualifications → verify → aggregate verified data into a report.

### 5. Definition of success

Achieve at least 90% classification precision and at least 90% classification recall, at least 90% skill-extraction F1, and correct aggregation of verified data.

### 6. Evidence and feasibility still to verify

- Evidence of user need.
- Applicable access terms and a suitable API.
- Sufficient advertisements for the selected region and sector.
- Sector selection.
- How to exclude personal information from collection and processing.

## Candidate 3: Plain-Language Municipal Planning Notices for Innlandet

### 1. Problem hypothesis

Residents may struggle to understand administrative notices and identify relevant consultation deadlines.

### 2. Proposed users

Residents affected by planning consultations.

### 3. Public source(s)

Public municipal planning notices; possible sources include Stange and Lillehammer, with other municipalities still to be selected. Source suitability and automated access terms remain unverified, including any municipal access or robots.txt claims in the PDF.

### 4. Proposed workflow

For one notice type across four municipalities: collect notices → extract key fields with supporting quotes → rewrite in plain Norwegian → verify facts → report, holding failed items for review.

### 5. Definition of success

Achieve at least 95% field-extraction accuracy, produce valid output structure for every result, invent no deadlines, and hold back every item that fails verification.

### 6. Evidence and feasibility still to verify

- Evidence of user need.
- Four suitable municipalities and one shared notice type.
- Automated access terms for each source.
- Complete field schema.
- A method for evaluating readability.
- How factual verification and review will work; verification does not guarantee factual correctness.

## Candidate 4: Flood and Severe-Weather Information Monitor for Innlandet

### 1. Problem hypothesis

Users may need to consult multiple official services to understand local flood and weather information.

### 2. Proposed users

Residents, farmers, and local businesses in one selected municipality; these are proposed users, and demand is unverified.

### 3. Public source(s)

NVE flood-warning and hydrological information, and MET Norway weather forecasts and alerts, subject to verification of suitable endpoints and terms.

### 4. Proposed workflow

Collect official information → select the relevant location → combine official information → verify location and freshness → produce a structured report.

### 5. Definition of success

On a fixed test set, correctly reproduce the relevant official warnings and weather fields, flag stale or unavailable data, and produce valid structured output without inventing warnings.

### 6. Evidence and feasibility still to verify

- Evidence of unmet user need.
- Value beyond existing official services.
- Suitable endpoints and applicable terms.
- Municipality selection and geographic matching.
- Freshness rules and handling of unavailable data.
- The role and value of an agent or LLM stage.
