# NAV skills evaluation report

**Generated:** 22 November 2026, 18:54:11 UTC

**Test type:** fresh model evaluation

**Prompt SHA-256:** `efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1`

**Model:** gpt-6-luna

## What happened

This run selected 5 saved advertisements. It attempted 5, validated 4, failed 1, and left 0 not run.

This run is partial or contains failures. Scores below cover only approved cases whose responses passed validation.

## Skill comparison across the real advertisements

The exact name and OR-group checker paired **50 items**. The model produced 84 items; the approved references contain 80 items.

- **Precision:** 59.5% (50 of 84) model items matched a reference item.
- **Recall:** 62.5% (50 of 80) reference items were matched.
- **F1:** 0.610 (a combined precision and recall measure).

These are automatic item-name and complete-group matches. Equivalent wording can be unmatched, so an unmatched item is not automatically a confirmed extraction mistake.

## Advertisement results

### Advertisement 1

**UUID:** `2ed29047-97e4-4168-adb9-8da83e968c94`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2ed29047-97e4-4168-adb9-8da83e968c94)

The response passed the format and quotation checks.

The checker matched **2 of 5 reference items**. The model returned 9 items; 7 model items and 3 reference items remained unmatched.

Precision: 22.2% (2 of 9). Recall: 40.0% (2 of 5). F1: 0.286.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 0 reference OR groups unmatched.

**Model items without an exact reference match (7):**

- Artificial intelligence development
- Use of artificial intelligence
- Data storage
- Information traceability
- Information searchability
- Technology development
- Artificial intelligence

**Reference items without an exact model match (3):**

- AI development
- AI use
- Development of information management procedures

### Advertisement 2

**UUID:** `2f62e300-c698-4f53-8510-db90b1692cb9`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2f62e300-c698-4f53-8510-db90b1692cb9)

The response passed the format and quotation checks.

The checker matched **18 of 29 reference items**. The model returned 28 items; 10 model items and 11 reference items remained unmatched.

Precision: 64.3% (18 of 28). Recall: 62.1% (18 of 29). F1: 0.632.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 0 reference OR groups unmatched.

**Model items without an exact reference match (10):**

- C#/.NET
- Azure Key Vault
- Azure Storage Accounts
- Azure App Service
- Azure App Configuration
- Azure Functions
- Azure Application Insights
- Infrastructure as Code (IaC)
- Orchestration
- Azure Kubernetes Service (AKS)

**Reference items without an exact model match (11):**

- C#
- .NET
- Key Vault
- Storage accounts
- App Services
- App configuration
- Azure functions
- Application Insights
- Infrastructure as Code
- Container orchestration
- Azure Kubernetes Service

### Systemingeniør (IoT/energi), Rondekraft

**UUID:** `5ae61e99-0980-4eac-a120-8338820483cc`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/5ae61e99-0980-4eac-a120-8338820483cc)

The response passed the format and quotation checks.

The checker matched **13 of 17 reference items**. The model returned 19 items; 6 model items and 4 reference items remained unmatched.

Precision: 68.4% (13 of 19). Recall: 76.5% (13 of 17). F1: 0.722.

Among matched names, the checker found 0 classification and 0 mention-type differences. It left 1 reference OR groups unmatched.

**Model items without an exact reference match (6):**

- Modbus RTU
- Electrical engineering OR Automation OR Cybernetics OR Computer science
- VPN configuration
- Solar energy OR Battery systems OR Edge devices OR Electrical safety (NEK 400)
- Sensor integration over Modbus
- Encrypted data transmission

**Reference items without an exact model match (4):**

- Modbus RTU (RS485)
- VPN setup
- Solar energy OR Battery installations OR Edge devices OR Electrical safety (NEK 400)
- Encrypted data transfer

**Unmatched OR groups (1):**

- Solar energy OR Battery installations OR Edge devices OR Electrical safety (NEK 400)

### Advertisement 4

**UUID:** `a1613f9c-1757-4351-81ea-1d0e5246fbd3`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/a1613f9c-1757-4351-81ea-1d0e5246fbd3)

The response did not pass validation: structural or quotation validation failed. It was not scored.

### Advertisement 5

**UUID:** `b69f0bbd-082e-4d36-baae-456fb23ca32a`

**Source:** [Original advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/b69f0bbd-082e-4d36-baae-456fb23ca32a)

The response passed the format and quotation checks.

The checker matched **17 of 29 reference items**. The model returned 28 items; 11 model items and 12 reference items remained unmatched.

Precision: 60.7% (17 of 28). Recall: 58.6% (17 of 29). F1: 0.596.

Among matched names, the checker found 1 classification and 6 mention-type differences. It left 2 reference OR groups unmatched.

**Model items without an exact reference match (11):**

- Building program files
- Game engine knowledge
- XR
- Code comprehension and maintenance
- Unity OR Other game engine experience
- VR optimization OR Network programming OR Interdisciplinary collaboration in development teams
- Designing scalable, maintainable and technically robust solutions
- Technical communication
- Technical architecture decision-making
- User experience in VR/AR environments
- XR

**Reference items without an exact model match (12):**

- Software builds
- XR solution development
- Codebase comprehension
- Unity OR Other game engine
- VR optimization OR Network code OR Cross-disciplinary collaboration in development teams
- Building scalable solutions
- Building maintainable solutions
- Technical concept communication
- Technical architecture decision ownership
- Understanding UX effects of technical choices in VR/AR
- Working across platforms and devices
- XR technology

**Unmatched OR groups (2):**

- Unity OR Other game engine
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

Requests attempted: 5 of 5. Planning maximum: $0.029749. Usage-based estimate so far: $0.009579.

- `2ed29047-97e4-4168-adb9-8da83e968c94`: 2907 input tokens; 2722 output tokens (including any billed reasoning tokens); estimated $0.001652.
- `2f62e300-c698-4f53-8510-db90b1692cb9`: 2239 input tokens; 2856 output tokens (including any billed reasoning tokens); estimated $0.001652.
- `5ae61e99-0980-4eac-a120-8338820483cc`: 2495 input tokens; 4289 output tokens (including any billed reasoning tokens); estimated $0.002394.
- `a1613f9c-1757-4351-81ea-1d0e5246fbd3`: 3070 input tokens; 1894 output tokens (including any billed reasoning tokens); estimated $0.001254.
- `b69f0bbd-082e-4d36-baae-456fb23ca32a`: 2604 input tokens; 4733 output tokens (including any billed reasoning tokens); estimated $0.002627.

## How to read this report

The five real advertisements are development and regression cases, not an unseen or representative market sample. Exact quotation matching checks that words occur in the saved text; it does not establish correct interpretation. The automatic comparison does not replace human meaning review. This evaluation does not update dashboard statistics.
