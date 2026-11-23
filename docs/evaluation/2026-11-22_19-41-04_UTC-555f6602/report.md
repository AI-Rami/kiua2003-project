# NAV skills evaluation report

**Generated:** 22 November 2026, 19:41:04 UTC

**Test type:** fresh model evaluation

**Prompt SHA-256:** `a9985b39a0301fa61627c31172d9c74a7b8e4c6ebb4265b5e93f91b7826904a3`

**Model:** gpt-6-luna

## What happened

This run selected 5 saved advertisements. It attempted 5, validated 4, failed 1, and left 0 not run.

This run is partial or contains failures. Scores below cover only approved cases whose responses passed validation.

## Skill comparison across the real advertisements

The exact name and OR-group checker paired **42 items**. The model produced 81 items; the approved references contain 73 items.

- **Precision:** 51.9% (42 of 81) model items matched a reference item.
- **Recall:** 57.5% (42 of 73) reference items were matched.
- **F1:** 0.545 (a combined precision and recall measure).

These are automatic item-name and complete-group matches. Equivalent wording can be unmatched, so an unmatched item is not automatically a confirmed extraction mistake.

## Advertisement results

### Advertisement 1

**UUID:** `2ed29047-97e4-4168-adb9-8da83e968c94`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2ed29047-97e4-4168-adb9-8da83e968c94)

The response passed the format and quotation checks.

The checker matched **2 of 5 reference items**. The model returned 11 items; 9 model items and 3 reference items remained unmatched.

Precision: 18.2% (2 of 11). Recall: 40.0% (2 of 5). F1: 0.250.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 0 reference OR groups unmatched.

**Model items without an exact reference match (9):**

- Information management procedure development and follow-up
- Artificial intelligence development
- Artificial intelligence use
- Information governance
- Data and information storage
- Data and information traceability
- Data and information searchability
- Intelligence
- Artificial intelligence

**Reference items without an exact model match (3):**

- AI development
- AI use
- Development of information management procedures

### Advertisement 2

**UUID:** `2f62e300-c698-4f53-8510-db90b1692cb9`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2f62e300-c698-4f53-8510-db90b1692cb9)

The response passed the format and quotation checks.

The checker matched **20 of 29 reference items**. The model returned 30 items; 10 model items and 9 reference items remained unmatched.

Precision: 66.7% (20 of 30). Recall: 69.0% (20 of 29). F1: 0.678.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 0 reference OR groups unmatched.

**Model items without an exact reference match (10):**

- Microsoft Entra
- Azure Key Vault
- Azure Storage accounts
- Azure App Services
- Azure App Configuration
- Azure Functions
- Azure Application Insights
- Relational databases
- SQL
- Infrastructure as Code (IaC)

**Reference items without an exact model match (9):**

- Entra
- Key Vault
- Storage accounts
- App Services
- App configuration
- Azure functions
- Application Insights
- Relational databases (SQL)
- Infrastructure as Code

### Systemingeniør (IoT/energi), Rondekraft

**UUID:** `5ae61e99-0980-4eac-a120-8338820483cc`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/5ae61e99-0980-4eac-a120-8338820483cc)

The response did not pass validation: structural or quotation validation failed. It was not scored.

### Advertisement 4

**UUID:** `a1613f9c-1757-4351-81ea-1d0e5246fbd3`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/a1613f9c-1757-4351-81ea-1d0e5246fbd3)

The response passed the format and quotation checks.

The checker matched **4 of 10 reference items**. The model returned 11 items; 7 model items and 6 reference items remained unmatched.

Precision: 36.4% (4 of 11). Recall: 40.0% (4 of 10). F1: 0.381.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 0 reference OR groups unmatched.

**Model items without an exact reference match (7):**

- ICT systems operations
- ICT infrastructure operations
- ICT systems development
- ICT infrastructure development
- Hardware configuration
- Software configuration
- Digital solutions

**Reference items without an exact model match (6):**

- IT systems operation
- IT systems development
- IT infrastructure operation
- IT infrastructure development
- Hardware setup
- Software setup

### Advertisement 5

**UUID:** `b69f0bbd-082e-4d36-baae-456fb23ca32a`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/b69f0bbd-082e-4d36-baae-456fb23ca32a)

The response passed the format and quotation checks.

The checker matched **16 of 29 reference items**. The model returned 29 items; 13 model items and 13 reference items remained unmatched.

Precision: 55.2% (16 of 29). Recall: 55.2% (16 of 29). F1: 0.552.

Among matched names, the checker found 1 classification and 6 mention-type differences. It left 1 reference OR groups unmatched.

**Model items without an exact reference match (13):**

- Application development
- Application build generation
- Agile development processes
- Game engine knowledge
- Performance
- Optimization
- Code comprehension
- VR optimization OR Network programming OR Cross-disciplinary collaboration in development teams
- Scalable, maintainable, technically sound solution design
- Explaining technical concepts
- Technical architecture decision-making
- User experience in VR/AR environments
- Working with multiple platforms and devices

**Reference items without an exact model match (13):**

- Software development
- Software builds
- Software performance
- Software optimization
- Codebase comprehension
- VR optimization OR Network code OR Cross-disciplinary collaboration in development teams
- Building scalable solutions
- Building maintainable solutions
- Technical concept communication
- Technical architecture decision ownership
- Understanding UX effects of technical choices in VR/AR
- Working across platforms and devices
- XR technology

**Unmatched OR groups (1):**

- VR optimization OR Network code OR Cross-disciplinary collaboration in development teams

**Different required/preferred/unclear labels (1):**

- Game engines (reference preferred; model unclear)

**Different mention types (6):**

- Android (reference work_duty; model work_context)
- iOS (reference work_duty; model work_context)
- Windows (reference work_duty; model work_context)
- Mac (reference work_duty; model work_context)
- VR devices (reference work_duty; model work_context)
- Game engines (reference candidate_qualification; model interest_only)

## Model requests and cost

Requests attempted: 5 of 5. Planning maximum: $0.030039. Usage-based estimate so far: $0.010023.

- `2ed29047-97e4-4168-adb9-8da83e968c94`: 3018 input tokens; 3574 output tokens (including any billed reasoning tokens); estimated $0.002089.
- `2f62e300-c698-4f53-8510-db90b1692cb9`: 2350 input tokens; 3645 output tokens (including any billed reasoning tokens); estimated $0.002057.
- `5ae61e99-0980-4eac-a120-8338820483cc`: 2606 input tokens; 3645 output tokens (including any billed reasoning tokens); estimated $0.002083.
- `a1613f9c-1757-4351-81ea-1d0e5246fbd3`: 3181 input tokens; 2336 output tokens (including any billed reasoning tokens); estimated $0.001486.
- `b69f0bbd-082e-4d36-baae-456fb23ca32a`: 2715 input tokens; 4071 output tokens (including any billed reasoning tokens); estimated $0.002307.

## How to read this report

The five real advertisements are development and regression cases, not an unseen or representative market sample. Exact quotation matching checks that words occur in the saved text; it does not establish correct interpretation. The automatic comparison does not replace human meaning review. This evaluation does not update dashboard statistics.
