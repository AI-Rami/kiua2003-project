# Reviewed NAV skill-extraction evaluation

**Review completed:** 22 November 2026. **Original offline run:** 22 November 2026, 16:50:02 UTC.

**Original evidence:** [generated report](report.md), [machine-readable record](record.json), [frozen case manifest](../../../eval/cases/manifest.json), and [approved references](../../../eval/references/development-v2-approved.json). This review adds interpretation to that run; it does not replace or recalculate any saved answer, reference, score, or synthetic check.

This is the repository copy for sharing. The folder name identifies the original run. The `out/current/` result paths in the inventories below are restored locally by `python harness/start.py --check-only`; generated `out/` data is not stored as ordinary Git files.

## Result and limits

Five approved development advertisements were selected, attempted, and structurally validated. None failed or remained unrun. The original exact-name/group scorer paired **47 of 83 model items** with **47 of 90 reference items**: precision **56.6%**, recall **52.2%**, F1 **0.543**. Five paired items had different required/preferred/unclear labels. These are item-name/group figures, not a measure of how much advertisement meaning the model captured. The five synthetic boundary and rejection checks passed separately; the rejection made zero model calls and published zero results.

| Case | UUID | Exact pairs | Model items | Reference items | Qualitative finding |
| --- | --- | ---: | ---: | ---: | --- |
| REAL-01 | `2ed29047-97e4-4168-adb9-8da83e968c94` | 2 | 9 | 5 | AI actions combined; broad extra labels |
| REAL-02 | `2f62e300-c698-4f53-8510-db90b1692cb9` | 20 | 28 | 29 | Five container-tool classification differences |
| REAL-03 | `5ae61e99-0980-4eac-a120-8338820483cc` | 7 | 14 | 17 | Four-way OR preserved; duties combined |
| REAL-04 | `a1613f9c-1757-4351-81ea-1d0e5246fbd3` | 1 | 7 | 10 | Duties combined instead of split |
| REAL-05 | `b69f0bbd-082e-4d36-baae-456fb23ca32a` | 17 | 25 | 29 | Required three-way OR condition lost |

The complete model and reference item inventories, including relationship, classification, and mention type, appear in the appendix. Quotations below come from the frozen prepared inputs, whose byte hashes, along with the saved result hashes, matched the original run record during this review. A matching quotation proves the words were present, not that the label or governing context was interpreted correctly. The references are the agreed answers for this development set; judgments about how finely to split a phrase can still be revisited in a future, versioned evaluation. Eight other draft advertisements are outside this score. No fresh model request was made.

## REAL-01 — information management

**Source:** `2ed29047-97e4-4168-adb9-8da83e968c94`; [NAV advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2ed29047-97e4-4168-adb9-8da83e968c94).

> Det er også ønskelig om du har:
>
> Arbeidserfaring innen informasjonsforvaltning, med fokus på utvikling og bruk av kunstig intelligens

The model and reference agree on **Information management** as `preferred/candidate_qualification`. They also agree on **Information lifecycle management** as `unclear/work_duty`, supported by “Bidra til styring og forvaltning av informasjon gjennom dens livsløp, ved å påse at data og informasjon lagres, gjøres sporbar og søkbar”.

| Model answer | Approved reference | Review |
| --- | --- | --- |
| `Artificial intelligence development and use` — one preferred qualification | `AI development` and `AI use` — two preferred single qualifications | The source says both “utvikling og bruk”. This is a **grouping difference**, not evidence that either activity was omitted. The model did not follow the approved two-item split. |
| `Development and follow-up of information management procedures, systems, and tools` — unclear duty | `Development of information management procedures` — unclear duty | “Utvikle og følge opp prosedyrer, systemer og verktøy for informasjonsforvaltning” supports the core action. The model made one broader combined label; the reference deliberately keeps the narrower procedure-development item. |
| `Data storage, traceability, and searchability` — unclear duty | Covered within `Information lifecycle management` | The source explicitly says information is stored, traceable, and searchable. This model item overlaps a reference item rather than inventing those activities. |
| `Implementation of information management tools` — unclear duty | No separate item | “Implementere nye verktøy som tas i bruk innen fagområdet” supports an implementation duty, but names no particular tool. The approved technical-scope decision excludes unnamed tools. This is a **scope difference**, not a fabricated quotation. |
| `Decision support in the information management field`; `Information flow management` — unclear duties | No separate items | “Beslutningsstøtte innen ditt fagfelt” and “Legge til rette for effektiv informasjonsflyt” occur in the source. The approved answer excludes these broad phrases because no specific technical method is established. |
| `Assessment of technological solutions against organizational needs` — required qualification | No separate item | The source says “evner å se hvordan nye og eksisterende teknologiske løsninger kan møte virksomhetens behov.” Treating this general judgment as a distinct **required technical skill** is a confirmed scope/interpretation error under the approved rules. |

The seven automatically unmatched model labels therefore mix grouping, overlap, scope decisions, and one clear overinterpretation. They are not seven proven hallucinations. The exact scorer's 2/5 recall reflects its strict item naming and the approved granularity.

## REAL-02 — Azure and container technologies

**Source:** `2f62e300-c698-4f53-8510-db90b1692cb9`; [NAV advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/2f62e300-c698-4f53-8510-db90b1692cb9).

> Nøkkelkvalifikasjoner:
>
> God erfaring med C# .NET
>
> Generell kompetanse i Azure (Entra, Key Vault, Storage accounts, App Services, App configuration, Azure functions, Application Insights)

Both answers treat general **Azure** competence as `required/candidate_qualification` and the seven individually named Azure services as `unclear/candidate_qualification`: the wording does not say each service is independently required. The model also agrees with the reference on backend development, CIAM, relational databases (SQL), agile development, DevOps, CI/CD pipeline management, full-stack development, microservices, distributed systems, containerization, and XR work context.

| Model answer | Approved reference | Review |
| --- | --- | --- |
| One required `C# .NET` item | Separate required `C#` and `.NET` single items | “God erfaring med C# .NET” names both. The model **combined** them; there is no OR relationship. |
| `Azure Storage accounts`, `Azure App Services`, `Azure App Configuration`, `Azure Functions` | `Storage accounts`, `App Services`, `App configuration`, `Azure functions` | These are **name differences** for named services in the same bullet. `Azure Functions` versus `Azure functions` differs only in capitalization. The scorer has no approved aliases or case folding, so it leaves them unmatched. |
| `Infrastructure as Code (IaC) resource management`; `Orchestration`; `NoSQL databases` | `Infrastructure as Code`; `Container orchestration`; `NoSQL` | “IaC (Resource Management)”, the container bullet, and “Forståelse for No-SQL” support the topics. The first and third differ mainly in wording. `Orchestration` loses the container qualifier and is less precise than the reference. |

The distinct classification error concerns this source passage:

> Ønskede kvalifikasjoner:
>
> God kunnskap innen containerization and orchestration (Docker, Kubernetes, Azure Container Apps, Azure Kubernetes Service, Helm)

The model labels **Docker, Kubernetes, Azure Container Apps, Azure Kubernetes Service, and Helm** `unclear` and gives them no separate classification-context quotation. The approved reference labels all five `preferred`, governed by “Ønskede kvalifikasjoner:”. This is **five confirmed classification/context disagreements** with the approved answer, not a claim that every named tool is independently mandatory. Both answers keep the five technologies as separate named items. The original automatic score counts these five as name matches with wrong classifications, so 20 name matches do not mean 20 fully correct items.

## REAL-03 — energy and IoT systems

**Source:** `5ae61e99-0980-4eac-a120-8338820483cc`; [NAV advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/5ae61e99-0980-4eac-a120-8338820483cc).

> God kjennskap til Modbus RTU (RS485), og Modbus TCP.
>
> Erfaring med sensorer, og sensorintegrasjon.

The model and reference agree on the four required single qualifications **Modbus RTU (RS485), Modbus TCP, Sensors, and Sensor integration**. They also agree on the unclear work duties **Local AI development, Anomaly alerting, and Predictive maintenance**. `Artificial intelligence (AI/KI)` in the model versus `Artificial intelligence (AI)` in the reference is a name difference for “Kunnskap om, og praktisk erfaring med AI/KI.”

| Model answer | Approved reference | Review |
| --- | --- | --- |
| One preferred `VPN configuration and operation` | Two preferred singles, `VPN setup` and `VPN operation` | “Erfaring med oppsett, og drift av VPN-løsninger er en fordel i denne rollen.” Both activities are represented, but the approved answer splits them. “Configuration” is the model's rendering of “oppsett”. |
| Preferred `any_of`: Solar energy OR Battery systems OR Edge devices OR Electrical safety (NEK 400) | Preferred `any_of`: Solar energy OR Battery installations OR Edge devices OR Electrical safety (NEK 400) | The source says “solenergi, batterianlegg, edge-enheter eller elsikkerhet (NEK 400)” and then “Dette er fordeler, men ikke krav.” **Both answers retain four alternatives and the preferred OR relationship.** “Battery systems” versus “Battery installations” blocks an exact group match; whether to approve that translation as an alias remains a separate judgment. |
| One `Modbus-based configuration and integration of inverters, batteries, and sensors` duty | Five duties: inverter configuration/integration, battery configuration/integration, sensor configuration | “Konfigurere, og integrere invertere, batterier og sensorer over Modbus RTU, og Modbus TCP.” The model includes the actions and objects but **combines** them. The agreed reference uses finer action–object items and does not duplicate the required Sensor integration qualification as a duty. |
| `Secure and encrypted data transmission` | `Encrypted data transfer` | “Sikre trygg, og kryptert dataoverføring på lukket nett.” The labels overlap in meaning; the exact mismatch is primarily wording. |
| `Technical platform and infrastructure development`; `System operation and monitoring` | No separate items | “Videreutvikle den tekniske plattformen, KI-funksjonene og infrastrukturen” and “Drifte, overvåke og videreutvikle løsningen” support duties. The approved answer omits broad platform and unnamed-solution labels to avoid overlap. Whether either merits a separate technical item is a **remaining scope judgment**, not proof of a fabricated model skill. |

Thus the scored unmatched OR group is not evidence of lost OR logic. The principal differences are exact naming and the reference's finer splitting of duties. No independent classification disagreement was found in the name-matched items.

## REAL-04 — IT support duties and interest

**Source:** `a1613f9c-1757-4351-81ea-1d0e5246fbd3`; [NAV advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/a1613f9c-1757-4351-81ea-1d0e5246fbd3).

> Typiske arbeidsoppgaver vil være:
>
> drift og utvikling av IKT-systemer og infrastruktur
>
> installasjon og oppsett av maskinvare og programvare
>
> brukerstøtte til ansatte

The model and reference both classify the duties `unclear/work_duty`; **IT user support** is an exact match. The source also says “har interesse for IKT, teknologi og digitale løsninger”. Both answers identify an ICT interest as `unclear/interest_only`, without claiming existing competence.

| Model answer | Approved reference | Review |
| --- | --- | --- |
| `IT systems and infrastructure operations` and `IT systems and infrastructure development` | Four singles: IT systems operation/development and IT infrastructure operation/development | The model includes both actions and both objects, but combines systems with infrastructure. This is an agreed **item-splitting difference**. |
| `Hardware installation and setup` and `Software installation and setup` | Four singles: hardware installation/setup and software installation/setup | The model includes the actions and objects, but combines installation with setup. The reference's action–object split is an annotation convention; installation and setup may overlap in practice. |
| `Information and communications technology (ICT)` | `ICT` | Same interest topic, different name. |
| `Digital solutions` — unclear interest | No separate item | The words “digitale løsninger” are in the interest phrase, but the approved answer excludes a separate generic digital-solutions item. This is a **scope difference**, not a nonexistent source quotation. |

The original 10.0% recall is **one of ten exact item matches**, not a finding that 90% of the advertisement's technical meaning was missed. The model combined many of the reference's separate items. Neither answer finds an explicit required or preferred existing technical qualification in this advertisement.

## REAL-05 — game development and a mixed OR condition

**Source:** `b69f0bbd-082e-4d36-baae-456fb23ca32a`; [NAV advertisement](https://arbeidsplassen.nav.no/stillinger/stilling/b69f0bbd-082e-4d36-baae-456fb23ca32a).

> Erfaring med ett eller flere av følgende områder:
>
> - Optimalisering for VR
> - Nettverkskode
> - Tverrfaglig samarbeid i utviklingsteam

The approved answer keeps **one `required/candidate_qualification/any_of` item with all three alternatives**: VR optimization OR Network code OR Cross-disciplinary collaboration in development teams. “Ett eller flere” means the employer seeks at least one, not all three independently. The third branch is a development-team collaboration practice, rather than a standalone technical technology. It is included in the reference **to preserve the complete mixed technical/nontechnical choice**. Its omission should be called a missing **alternative in the condition**, not automatically a missing technical skill. The model instead returned two `unclear/candidate_qualification/single` items, **VR optimization** and **Network code**, and no third alternative. This is a confirmed relationship and qualification-status error. Because the items did not pair by exact group name, the automatic five-classification-difference total does not include this error.

The model correctly retains the separate required **Unity OR Other game engine** experience group. It also matches 16 other reference names, including the five named platform targets, multiplayer platform development, Git, version control, agile development methodologies, Scrum, game engines, game development architecture, software performance, software optimization, XR solution development interest, and working across platforms/devices. Those exact name matches do not settle every possible context judgment.

| Source wording | Model answer | Approved reference | Review |
| --- | --- | --- | --- |
| “Utvikling og bygging av programfiler for Android, iOS, Windows, Mac og VR-enheter.” | `Software development and build generation` | Separate unclear duties `Software development` and `Software builds`; five platform targets retained | Both actions and all targets appear in the model answer, but the two activities were combined. |
| “Har god forståelse for brukeropplevelse, ytelse og optimalisering.” under “Ønskede kvalifikasjoner” | No separate preferred `User experience`; model has only required `User experience in VR/AR environments` from a later sentence | Preferred `User experience`, plus a separate required `Understanding UX effects of technical choices in VR/AR` | This is a **confirmed omission of a distinct preferred UX mention** and a merger of two differently classified contexts. The later sentence says technical choices affect user experience in VR/AR. |
| “Er komfortabel med å sette deg inn i eksisterende kode og forstå sammenhenger for å videreutvikle og forbedre.” | `Codebase comprehension and improvement` | `Codebase comprehension` | The core comprehension is present. Adding “improvement” to an existing qualification may overstate the phrase's purpose; treat its severity as a granularity/wording judgment. |
| “Erfaring med Unity eller annen spillmotor og sterkt ønske om å lære Unity.” | Correct required Unity/other-engine OR group; no separate Unity interest | Same OR group, plus `Unity` as `unclear/interest_only` | The experience group is correct. The additional wish to learn Unity is a separate **omitted interest mention**, not a second required Unity skill. |
| “Kreativ og løsningsorientert, som evner å se det store bildet og bygge løsninger som er skalerbare, enkle å vedlikeholde og teknisk solide.” | Required `Scalable and maintainable software design` | Required `Building scalable solutions` and `Building maintainable solutions` | The source says **build**, not **design**. The action in the model label is unsupported; it also combines two agreed aspects. |
| “Tar eierskap til arkitekturvalg og tekniske beslutninger” and “kan forklare tekniske konsepter” | `Technical architecture decision-making`; `Technical communication` | `Technical architecture decision ownership`; `Technical concept communication` | The model retained the technical topics but lost the more precise **ownership** and **explaining concepts** actions. These are imprecise labels, not proof the complete topics were omitted. |
| “Mulighet til å jobbe med banebrytende teknologi innen XR” | No separate `XR technology` work-context item | `XR technology` — `unclear/work_context` | A **confirmed omission relative to the approved technical-context scope**. It is offered work context, not an applicant requirement. |

These findings are also consistent with the earlier [fifth-case baseline comparison](../../../eval/cases/ad5-baseline-comparison.md), which remains unchanged. The complete inventories below show exactly which names, relationships, classifications and mention types were saved. No model answer was manually repaired.

## What this evaluation establishes

The frozen responses passed structural and quotation validation, and the synthetic workflow checks behaved as expected. Human review found a real OR-interpretation failure in REAL-05, five container-tool classification disagreements in REAL-02, and some source-supported naming and grouping differences that exact scoring treats as misses. It also identified scope and granularity judgments that should remain explicit rather than silently resolved by fuzzy matching. The five advertisements were used during development and do not establish accuracy on unseen NAV advertisements or complete market coverage. Any later alias, reference, or scoring-rule change needs its own version and a new comparison; this report leaves the original baseline intact.

## Complete saved item inventories

The following lists transcribe each saved `result.json` and approved reference item in original item order. Each line records the name or complete `OR` group, relationship, classification, and mention type. They are **answer inventories**, not additional scores. Source quotations and full evidence fields remain in the linked saved results and approved reference.

### REAL-01 — 2ed29047-97e4-4168-adb9-8da83e968c94

**Model answer** (saved result: `out/current/2ed29047-97e4-4168-adb9-8da83e968c94/result.json`) — 9 items:

- **Information management** — single; preferred; candidate_qualification.
- **Artificial intelligence development and use** — single; preferred; candidate_qualification.
- **Development and follow-up of information management procedures, systems, and tools** — single; unclear; work_duty.
- **Implementation of information management tools** — single; unclear; work_duty.
- **Information lifecycle management** — single; unclear; work_duty.
- **Data storage, traceability, and searchability** — single; unclear; work_duty.
- **Decision support in the information management field** — single; unclear; work_duty.
- **Information flow management** — single; unclear; work_duty.
- **Assessment of technological solutions against organizational needs** — single; required; candidate_qualification.

**Approved reference** ([source file](../../../eval/references/development-v2-approved.json)) — 5 items:

- **Information management** — single; preferred; candidate_qualification.
- **AI development** — single; preferred; candidate_qualification.
- **AI use** — single; preferred; candidate_qualification.
- **Information lifecycle management** — single; unclear; work_duty.
- **Development of information management procedures** — single; unclear; work_duty.

### REAL-02 — 2f62e300-c698-4f53-8510-db90b1692cb9

**Model answer** (saved result: `out/current/2f62e300-c698-4f53-8510-db90b1692cb9/result.json`) — 28 items:

- **Backend development** — single; required; candidate_qualification.
- **C# .NET** — single; required; candidate_qualification.
- **Azure** — single; required; candidate_qualification.
- **Entra** — single; unclear; candidate_qualification.
- **Key Vault** — single; unclear; candidate_qualification.
- **Azure Storage accounts** — single; unclear; candidate_qualification.
- **Azure App Services** — single; unclear; candidate_qualification.
- **Azure App Configuration** — single; unclear; candidate_qualification.
- **Azure Functions** — single; unclear; candidate_qualification.
- **Application Insights** — single; unclear; candidate_qualification.
- **Customer Identity and Access Management (CIAM)** — single; required; candidate_qualification.
- **Relational databases (SQL)** — single; required; candidate_qualification.
- **Infrastructure as Code (IaC) resource management** — single; required; candidate_qualification.
- **Agile development** — single; required; candidate_qualification.
- **DevOps** — single; required; candidate_qualification.
- **CI/CD pipeline management** — single; required; candidate_qualification.
- **Full-stack development** — single; preferred; candidate_qualification.
- **Microservices** — single; preferred; candidate_qualification.
- **Distributed systems** — single; preferred; candidate_qualification.
- **Containerization** — single; preferred; candidate_qualification.
- **Orchestration** — single; preferred; candidate_qualification.
- **Docker** — single; unclear; candidate_qualification.
- **Kubernetes** — single; unclear; candidate_qualification.
- **Azure Container Apps** — single; unclear; candidate_qualification.
- **Azure Kubernetes Service** — single; unclear; candidate_qualification.
- **Helm** — single; unclear; candidate_qualification.
- **NoSQL databases** — single; preferred; candidate_qualification.
- **XR technology** — single; unclear; work_context.

**Approved reference** ([source file](../../../eval/references/development-v2-approved.json)) — 29 items:

- **Backend development** — single; required; candidate_qualification.
- **C#** — single; required; candidate_qualification.
- **.NET** — single; required; candidate_qualification.
- **Azure** — single; required; candidate_qualification.
- **Entra** — single; unclear; candidate_qualification.
- **Key Vault** — single; unclear; candidate_qualification.
- **Storage accounts** — single; unclear; candidate_qualification.
- **App Services** — single; unclear; candidate_qualification.
- **App configuration** — single; unclear; candidate_qualification.
- **Azure functions** — single; unclear; candidate_qualification.
- **Application Insights** — single; unclear; candidate_qualification.
- **Customer Identity and Access Management (CIAM)** — single; required; candidate_qualification.
- **Relational databases (SQL)** — single; required; candidate_qualification.
- **Infrastructure as Code** — single; required; candidate_qualification.
- **Agile development** — single; required; candidate_qualification.
- **DevOps** — single; required; candidate_qualification.
- **CI/CD pipeline management** — single; required; candidate_qualification.
- **Full-stack development** — single; preferred; candidate_qualification.
- **Microservices** — single; preferred; candidate_qualification.
- **Distributed systems** — single; preferred; candidate_qualification.
- **Containerization** — single; preferred; candidate_qualification.
- **Container orchestration** — single; preferred; candidate_qualification.
- **Docker** — single; preferred; candidate_qualification.
- **Kubernetes** — single; preferred; candidate_qualification.
- **Azure Container Apps** — single; preferred; candidate_qualification.
- **Azure Kubernetes Service** — single; preferred; candidate_qualification.
- **Helm** — single; preferred; candidate_qualification.
- **NoSQL** — single; preferred; candidate_qualification.
- **XR technology** — single; unclear; work_context.

### REAL-03 — 5ae61e99-0980-4eac-a120-8338820483cc

**Model answer** (saved result: `out/current/5ae61e99-0980-4eac-a120-8338820483cc/versions/f00301a8ee964f077b9b77d63b47cfb4df9960b8d77d785fcf824204281091f6/result.json`) — 14 items:

- **Modbus RTU (RS485)** — single; required; candidate_qualification.
- **Modbus TCP** — single; required; candidate_qualification.
- **Sensors** — single; required; candidate_qualification.
- **Sensor integration** — single; required; candidate_qualification.
- **Artificial intelligence (AI/KI)** — single; required; candidate_qualification.
- **VPN configuration and operation** — single; preferred; candidate_qualification.
- **Solar energy OR Battery systems OR Edge devices OR Electrical safety (NEK 400)** — any_of; preferred; candidate_qualification.
- **Technical platform and infrastructure development** — single; unclear; work_duty.
- **Modbus-based configuration and integration of inverters, batteries, and sensors** — single; unclear; work_duty.
- **Local AI development** — single; unclear; work_duty.
- **Anomaly alerting** — single; unclear; work_duty.
- **Predictive maintenance** — single; unclear; work_duty.
- **Secure and encrypted data transmission** — single; unclear; work_duty.
- **System operation and monitoring** — single; unclear; work_duty.

**Approved reference** ([source file](../../../eval/references/development-v2-approved.json)) — 17 items:

- **Modbus RTU (RS485)** — single; required; candidate_qualification.
- **Modbus TCP** — single; required; candidate_qualification.
- **Sensors** — single; required; candidate_qualification.
- **Sensor integration** — single; required; candidate_qualification.
- **Artificial intelligence (AI)** — single; required; candidate_qualification.
- **VPN setup** — single; preferred; candidate_qualification.
- **VPN operation** — single; preferred; candidate_qualification.
- **Solar energy OR Battery installations OR Edge devices OR Electrical safety (NEK 400)** — any_of; preferred; candidate_qualification.
- **Inverter configuration** — single; unclear; work_duty.
- **Inverter integration** — single; unclear; work_duty.
- **Battery configuration** — single; unclear; work_duty.
- **Battery integration** — single; unclear; work_duty.
- **Sensor configuration** — single; unclear; work_duty.
- **Local AI development** — single; unclear; work_duty.
- **Anomaly alerting** — single; unclear; work_duty.
- **Predictive maintenance** — single; unclear; work_duty.
- **Encrypted data transfer** — single; unclear; work_duty.

### REAL-04 — a1613f9c-1757-4351-81ea-1d0e5246fbd3

**Model answer** (saved result: `out/current/a1613f9c-1757-4351-81ea-1d0e5246fbd3/result.json`) — 7 items:

- **IT systems and infrastructure operations** — single; unclear; work_duty.
- **IT systems and infrastructure development** — single; unclear; work_duty.
- **Hardware installation and setup** — single; unclear; work_duty.
- **Software installation and setup** — single; unclear; work_duty.
- **IT user support** — single; unclear; work_duty.
- **Information and communications technology (ICT)** — single; unclear; interest_only.
- **Digital solutions** — single; unclear; interest_only.

**Approved reference** ([source file](../../../eval/references/development-v2-approved.json)) — 10 items:

- **IT systems operation** — single; unclear; work_duty.
- **IT systems development** — single; unclear; work_duty.
- **IT infrastructure operation** — single; unclear; work_duty.
- **IT infrastructure development** — single; unclear; work_duty.
- **Hardware installation** — single; unclear; work_duty.
- **Hardware setup** — single; unclear; work_duty.
- **Software installation** — single; unclear; work_duty.
- **Software setup** — single; unclear; work_duty.
- **IT user support** — single; unclear; work_duty.
- **ICT** — single; unclear; interest_only.

### REAL-05 — b69f0bbd-082e-4d36-baae-456fb23ca32a

**Model answer** (saved result: `out/current/b69f0bbd-082e-4d36-baae-456fb23ca32a/result.json`) — 25 items:

- **Software development and build generation** — single; unclear; work_duty.
- **Android** — single; unclear; work_duty.
- **iOS** — single; unclear; work_duty.
- **Windows** — single; unclear; work_duty.
- **Mac** — single; unclear; work_duty.
- **VR devices** — single; unclear; work_duty.
- **Multiplayer platform development** — single; unclear; work_duty.
- **Game engines** — single; preferred; candidate_qualification.
- **Game development architecture** — single; preferred; candidate_qualification.
- **User experience in VR/AR environments** — single; required; candidate_qualification.
- **Software performance** — single; preferred; candidate_qualification.
- **Software optimization** — single; preferred; candidate_qualification.
- **Codebase comprehension and improvement** — single; preferred; candidate_qualification.
- **Unity OR Other game engine** — any_of; required; candidate_qualification.
- **Git** — single; required; candidate_qualification.
- **Version control** — single; required; candidate_qualification.
- **Agile development methodologies** — single; required; candidate_qualification.
- **Scrum** — single; unclear; candidate_qualification.
- **VR optimization** — single; unclear; candidate_qualification.
- **Network code** — single; unclear; candidate_qualification.
- **XR solution development** — single; unclear; interest_only.
- **Scalable and maintainable software design** — single; required; candidate_qualification.
- **Technical architecture decision-making** — single; required; candidate_qualification.
- **Technical communication** — single; required; candidate_qualification.
- **Working across platforms and devices** — single; required; candidate_qualification.

**Approved reference** ([source file](../../../eval/references/development-v2-approved.json)) — 29 items:

- **Multiplayer platform development** — single; unclear; work_duty.
- **Software development** — single; unclear; work_duty.
- **Software builds** — single; unclear; work_duty.
- **Android** — single; unclear; work_duty.
- **iOS** — single; unclear; work_duty.
- **Windows** — single; unclear; work_duty.
- **Mac** — single; unclear; work_duty.
- **VR devices** — single; unclear; work_duty.
- **Game engines** — single; preferred; candidate_qualification.
- **Game development architecture** — single; preferred; candidate_qualification.
- **XR solution development** — single; unclear; interest_only.
- **User experience** — single; preferred; candidate_qualification.
- **Software performance** — single; preferred; candidate_qualification.
- **Software optimization** — single; preferred; candidate_qualification.
- **Codebase comprehension** — single; preferred; candidate_qualification.
- **Unity OR Other game engine** — any_of; required; candidate_qualification.
- **Unity** — single; unclear; interest_only.
- **Git** — single; required; candidate_qualification.
- **Version control** — single; required; candidate_qualification.
- **Agile development methodologies** — single; required; candidate_qualification.
- **Scrum** — single; unclear; candidate_qualification.
- **VR optimization OR Network code OR Cross-disciplinary collaboration in development teams** — any_of; required; candidate_qualification.
- **Building scalable solutions** — single; required; candidate_qualification.
- **Building maintainable solutions** — single; required; candidate_qualification.
- **Technical concept communication** — single; required; candidate_qualification.
- **Technical architecture decision ownership** — single; required; candidate_qualification.
- **Understanding UX effects of technical choices in VR/AR** — single; required; candidate_qualification.
- **Working across platforms and devices** — single; required; candidate_qualification.
- **XR technology** — single; unclear; work_context.
