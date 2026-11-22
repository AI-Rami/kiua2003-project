# Reviewed comparison of the revised NAV extraction prompt

**Review completed:** 22 November 2026. **Fresh model run:** 22 November 2026, 18:54:11 UTC.
**Original evidence:** [generated report](report.md), [run record](record.json), [approved references](../../../eval/references/development-v2-approved.json), and the [first run's reviewed report](../2026-11-22_16-50-02_UTC-d36c2f63/reviewed-report.md).

This review uses the five fixed, approved development advertisements and their unchanged prepared texts. Their normalized input hashes in the fresh run match the approved reference hashes. The first run replayed saved responses with prompt SHA-256 `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`. The second run made one new `gpt-6-luna` request per advertisement with revised prompt SHA-256 `efc10a5a9a3e05b7aaf1b42dc8c48a8da31e433331d9ca09ce689ecb9ed6cae1`. The schema, model settings, case texts, references and exact-name/group scoring rule stayed the same. No response or reference was manually repaired. The fresh responses and validation records remain in the local dated `out/evaluation/` run; that folder is Git-ignored.

## What the numbers say

The first run validated and scored all five ads: **47 exact item/group matches, 83 model items, 90 reference items; precision 56.6%, recall 52.2%, F1 0.543**. The revised run attempted all five, validated four, failed one and left none unrun. Its published score covers **only four ads**: **50 matches, 84 model items, 80 reference items; precision 59.5%, recall 62.5%, F1 0.610**. Comparing those two headline F1 values directly would hide the failed fifth case.

For the **same four scored advertisements**, the comparison is:

| Measure | Original prompt | Revised prompt |
| --- | ---: | ---: |
| Ads attempted and validated within this four-ad subset | 4/4 | 4/4 |
| Exact name or complete OR-group pairs | 46 | 50 |
| Model items | 76 | 84 |
| Approved reference items | 80 | 80 |
| Precision | 60.5% | 59.5% |
| Recall | 57.5% | 62.5% |
| F1 | 0.590 | 0.610 |

| Case | Original pairs / model / reference | Revised pairs / model / reference | Revised validation | Main interpretation change |
| --- | ---: | ---: | --- | --- |
| REAL-01 · `2ed29047-97e4-4168-adb9-8da83e968c94` | 2 / 9 / 5 | 2 / 9 / 5 | Passed | AI activities are split, but names still differ; a reference-scope question remains. |
| REAL-02 · `2f62e300-c698-4f53-8510-db90b1692cb9` | 20 / 28 / 29 | 18 / 28 / 29 | Passed | Five named container tools now have the approved preferred label; exact name matching fell. |
| REAL-03 · `5ae61e99-0980-4eac-a120-8338820483cc` | 7 / 14 / 17 | 13 / 19 / 17 | Passed | Duty splitting improved; an excluded education route was added. |
| REAL-04 · `a1613f9c-1757-4351-81ea-1d0e5246fbd3` | 1 / 7 / 10 | Not scored | **Failed** | The response contains two names in a `single` item. |
| REAL-05 · `b69f0bbd-082e-4d36-baae-456fb23ca32a` | 17 / 25 / 29 | 17 / 28 / 29 | Passed | The complete mixed three-way OR condition is now present, though exact group names differ. |

Precision counts matched model items divided by model items; recall counts matched approved-reference items divided by reference items. F1 combines them. A pair can have the same name while its classification or mention type differs. The scorer uses exact names and complete OR groups; its unmatched lists are **automatic differences**, not lists of proven hallucinations or omissions. The source review below judges meaning separately. The original run passed five separate synthetic checks; the fresh-model run did **not** execute those synthetic checks.

## REAL-01 — information management

**UUID:** `2ed29047-97e4-4168-adb9-8da83e968c94`. The revised response passed structural and quotation validation.

> Arbeidserfaring innen informasjonsforvaltning, med fokus på utvikling og bruk av kunstig intelligens

The model now gives **Artificial intelligence development** and **Use of artificial intelligence** as separate `preferred/candidate_qualification/single` items. The reference has **AI development** and **AI use** with the same labels and the same source passage. This repairs the first run's combined “Artificial intelligence development and use” item in substance. The exact scorer still leaves both names unmatched because its approved names use `AI` rather than “artificial intelligence.” **Information management** and **Information lifecycle management** remain supported and correctly labelled.

> Utvikle og følge opp prosedyrer, systemer og verktøy for informasjonsforvaltning

The reference includes **Development of information management procedures** as an `unclear/work_duty` item. The new model does not include this action. That is a confirmed omission relative to the approved answer. Its **Data storage**, **Information traceability** and **Information searchability** items are backed by “ved å påse at data og informasjon lagres, gjøres sporbar og søkbar,” but split details already represented in the reference's information-lifecycle duty. They are overlap/granularity differences, not invented source text.

The model also returns **Technology development** and **Artificial intelligence** as `unclear/interest_only` from “stor interesse for teknologiutvikling” and “spesielt kunstig intelligens.” These phrases occur in the prepared text. The reference omits both. The revised prompt and current labeling guide include technical interest topics, including a separate interest in a technology also named as a qualification. Whether these two topics should be added to a **future version** of this complete reference is an unresolved reference-scope question; this review does not change the frozen answer or score. The first run's unsupported required “Assessment of technological solutions against organizational needs” is absent in the new response.

## REAL-02 — Azure and container technologies

**UUID:** `2f62e300-c698-4f53-8510-db90b1692cb9`. The revised response passed structural and quotation validation.

> Nøkkelkvalifikasjoner:
>
> God erfaring med C# .NET
>
> Generell kompetanse i Azure (Entra, Key Vault, Storage accounts, App Services, App configuration, Azure functions, Application Insights)

The model and reference agree that broad **Azure** competence is `required/candidate_qualification` and that the seven named Azure services have individually `unclear` status. The model supplies the governing `Nøkkelkvalifikasjoner:` heading separately. It still combines **C#/.NET** into one required item, whereas the reference has two required singles, **C#** and **.NET**. The source has no OR condition there. Its service labels add `Azure`, change case, or use singular forms (for example, **Azure App Service** against **App Services**). These exact-name losses do not establish missing services.

> Ønskede kvalifikasjoner:
>
> God kunnskap innen containerization and orchestration (Docker, Kubernetes, Azure Container Apps, Azure Kubernetes Service, Helm)

All five named container tools are now `preferred/candidate_qualification` with **Ønskede kvalifikasjoner:** as a separate classification-context quotation. This fixes the first run's five `unclear` tool labels relative to the approved reference. It does **not** claim that every tool is independently mandatory. The model still uses broad **Orchestration** instead of the reference's **Container orchestration**; the container qualifier is supported by the same bullet and would make the name more precise. **Infrastructure as Code (IaC)** versus **Infrastructure as Code**, and **Azure Kubernetes Service (AKS)** versus the unexpanded service name, are further exact-name differences. No new confirmed category-status error was found among the other named qualifications.

## REAL-03 — energy and IoT systems

**UUID:** `5ae61e99-0980-4eac-a120-8338820483cc`. The revised response passed structural and quotation validation.

> Konfigurere, og integrere invertere, batterier og sensorer over Modbus RTU, og Modbus TCP.

The revised model separately lists **Inverter configuration**, **Inverter integration**, **Battery configuration**, **Battery integration** and **Sensor configuration** as `unclear/work_duty`. These are the five action/object entries in the reference and a substantive improvement over the first run's one combined Modbus duty. It additionally lists **Sensor integration over Modbus**. The action and object are present in the source, but the reference already has a required **Sensor integration** qualification and does not count a second duty for it. Whether the Modbus detail warrants a distinct item is an overlap/granularity question, not a fabricated quotation.

> Relevant høyere utdanning, eller tilsvarende erfaring, innen elektro, automasjon, kybernetikk eller data.

The model adds a required `any_of` group of **Electrical engineering OR Automation OR Cybernetics OR Computer science**. This sentence specifies education or equivalent-background routes. The approved technical-skill scope explicitly excludes education/background here. Adding the group is a **confirmed scope error**, even though it correctly recognizes the sentence's alternatives. The first run did not include it.

The source says “God kjennskap til Modbus RTU (RS485), og Modbus TCP.” The new model names **Modbus RTU**, omitting `(RS485)` from the reference's **Modbus RTU (RS485)**; the full detail remains in its evidence. The source also says “Erfaring med oppsett, og drift av VPN-løsninger er en fordel i denne rollen.” The model splits **VPN configuration** and **VPN operation**, improving on the first combined VPN item, but “configuration” does not exactly match the reference's **VPN setup**. Both answers preserve the four-member preferred solar/battery/edge/electrical-safety OR condition; **Battery systems** versus **Battery installations** prevents an exact group pair. The encrypted-data label also differs by wording (**transmission** versus **transfer**). These name mismatches should not be described as missing technical topics.

## REAL-04 — ICT support

**UUID:** `a1613f9c-1757-4351-81ea-1d0e5246fbd3`. The API response completed, and all eight model quotations matched the prepared input, but local validation failed: **item 8 has relationship `single` with two names, `ICT` and `Digital solutions`**. The schema requires exactly one name for `single`. No accuracy score is reported for this ad. This is a model-output structure error, not a token-limit or connection failure. The prompt already stated the one-name rule before this run; this response was not silently split or retried.

> drift og utvikling av IKT-systemer og infrastruktur
>
> installasjon og oppsett av maskinvare og programvare

The saved invalid answer can still be inspected as evidence, but its items must not enter the scored set. It now separates **Hardware installation**, **Hardware setup**, **Software installation** and **Software setup**, matching four reference items that the first run had combined. It still combines systems with infrastructure in **Operation of ICT systems and infrastructure** and **Development of ICT systems and infrastructure**, while the reference uses four separate action/object entries. **User support** is less specific than the reference's **IT user support**. The source interest phrase is “har interesse for IKT, teknologi og digitale løsninger”; it contains no explicit OR choice. The reference includes one `unclear/interest_only` **ICT** item and excludes generic “Digital solutions” as a separate skill. These observations are qualitative only; **none is a replacement score for the failed response**.

## REAL-05 — game development and the three-way choice

**UUID:** `b69f0bbd-082e-4d36-baae-456fb23ca32a`. The revised response passed structural and quotation validation.

> Erfaring med ett eller flere av følgende områder:
>
> - Optimalisering for VR
> - Nettverkskode
> - Tverrfaglig samarbeid i utviklingsteam

The first run returned **VR optimization** and **Network code** as separate `unclear` singles, omitting the third branch. The new response retains **all three alternatives in one required `any_of` candidate qualification**, including the development-team collaboration branch. This is the main substantive improvement. Collaboration in this context is retained only to preserve the employer's complete condition; it is not thereby a standalone technical skill. The exact scorer still marks the whole group unmatched because the model says **Network programming** and **Interdisciplinary collaboration in development teams**, while the reference says **Network code** and **Cross-disciplinary collaboration in development teams**. `Network programming` may suggest an activity beyond the source's noun “Nettverkskode”; that translation remains a naming judgment, not an OR-structure failure.

> Erfaring med Unity eller annen spillmotor og sterkt ønske om å lære Unity.

The model keeps the required **Unity OR Other game engine experience** choice and separately records a `Unity` interest in learning. The approved group is **Unity OR Other game engine** and has a separate `Unity` interest. The word “experience” explains another exact group-name mismatch; the group structure and labels are substantively aligned.

> Har god forståelse for brukeropplevelse, ytelse og optimalisering.

The model now includes a separate `preferred/candidate_qualification` **User experience** item; the first run omitted this distinct preferred mention. It also records preferred software performance and optimization. Its five named target platforms in “Utvikling og bygging av programfiler for Android, iOS, Windows, Mac og VR-enheter” are labelled `work_context`, whereas the reference calls them `work_duty` because they are targets of the stated development/build duty. This is five **mention-type disagreements** despite exact name matches. The model's **Building program files** corresponds to the reference's **Software builds** in subject matter, but its separate **Software development** uses the broader evidence “Bidra til utvikling og leveranser mot eksisterende og nye kunder,” which does not itself say software. Exact quotation validation therefore did not establish adequate support for that label.

The scorer pairs the model's separate **Game engines** `unclear/interest_only` item with the reference's **Game engines** `preferred/candidate_qualification`, producing one classification and one further mention-type difference. The model also has **Game engine knowledge** as a preferred qualification supported by “Har god forståelse for spillmotorer og arkitektur i spillutvikling.” This is a **matching/naming limitation**: the preferred idea is present under a different name, while a distinct interest mention is also source-supported. It should not be called a simple failure to recognize the preferred qualification.

> Kreativ og løsningsorientert, som evner å se det store bildet og bygge løsninger som er skalerbare, enkle å vedlikeholde og teknisk solide.

The model calls this **Designing scalable, maintainable and technically robust solutions**. The quotation says *build* (`bygge`), not *design*; the action in the model label is unsupported. It also merges the reference's separate scalable and maintainable solution items. The model still omits the explicit “Kan jobbe med ulike plattformer og enheter” required capability. **Technical communication** and **Technical architecture decision-making** retain the topics but are broader than the reference's explaining-technical-concepts and taking-ownership labels. Its `XR` interest and work-context names are less specific than the corresponding reference items. These are interpretation and granularity findings, not all additional hallucinations.

## Conclusion and next evaluation step

The revised prompt improved several intended behaviors, particularly the Azure tool classifications, the energy-ad duty splits, and the game-ad three-way choice. It also produced a new excluded education group and one invalid response. On the four ads scored by both runs, exact-name/group F1 rose from **0.590 to 0.610**, while precision fell from **60.5% to 59.5%** and recall rose from **57.5% to 62.5%**. The five-ad validation rate fell from **5/5 to 4/5**. Those figures and the reviewed examples do not prove improved extraction accuracy overall. The apparent interest-only reference gap in REAL-01 and the exact matcher issue around two Game engines mentions in REAL-05 should be resolved explicitly before changing reference or scoring rules. The current test set was used for prompt development; performance on unseen advertisements remains unknown.

This review preserves both runs, approved references, scores, prompt versions and raw saved model outputs. It makes no new model or NAV request and does not update application statistics.
