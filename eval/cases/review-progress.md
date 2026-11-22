# NAV reference review progress

These are decisions from the prepared advertisement text, not model-output comparisons. Rami reported that Yehya agrees with his decisions and a separate wait for Yehya is unnecessary; this is Rami's report, not an independently recorded review by Yehya. The earlier `gold.csv` and saved model answers were not consulted to make these decisions. All five complete answers are selected in the approved reference. The separate [fifth-case baseline comparison](ad5-baseline-comparison.md) was made only after its reference was approved.

## 2ed29047-97e4-4168-adb9-8da83e968c94 — approved complete reference

- Prepared input: `out/current/2ed29047-97e4-4168-adb9-8da83e968c94/prepared_ad.txt`
- SHA-256 of frozen prepared input: `5eddcccce84ce63b51473198c7d663c5fcfc275788c0842d3f02af51c86fa949` (exact byte hash matched the shared baseline manifest)
- Preferred heading: `Det er også ønskelig om du har:`
- Shared qualification evidence: `Arbeidserfaring innen informasjonsforvaltning, med fokus på utvikling og bruk av kunstig intelligens`

| Proposed skill | Mention type | Classification | Evidence |
| --- | --- | --- | --- |
| Information management | `candidate_qualification` | `preferred` | Shared qualification evidence and preferred heading above |
| AI development | `candidate_qualification` | `preferred` | Shared qualification evidence and preferred heading above |
| AI use | `candidate_qualification` | `preferred` | Shared qualification evidence and preferred heading above |
| Information lifecycle management | `work_duty` | `unclear` | `Bidra til styring og forvaltning av informasjon gjennom dens livsløp, ved å påse at data og informasjon lagres, gjøres sporbar og søkbar` |
| Development of information management procedures | `work_duty` | `unclear` | `Utvikle og følge opp prosedyrer, systemer og verktøy for informasjonsforvaltning` |

The last item is narrower than the original combined proposal: it keeps the explicitly stated development of information-management procedures, without creating separate skills for follow-up or unnamed systems and tools. The two AI actions remain separate skills. No technical `any_of` group or required technical skill was identified in this draft.

Excluded under the agreed technical scope: the broad information-flow duty, broad decision-support wording, general assessment of technology against organizational needs, intelligence domain experience or interest, education, Norwegian-language ability, security clearance, and unnamed tools or solutions. AI interest/context is not duplicated because the qualification evidence above is stronger. Rami agreed to this complete answer and reported Yehya's concurrence; it is selected in the approved reference.

## 2f62e300-c698-4f53-8510-db90b1692cb9 — approved complete reference

- Prepared input: `out/current/2f62e300-c698-4f53-8510-db90b1692cb9/prepared_ad.txt`
- SHA-256 of frozen prepared input: `e0a50ea251c5bdfeb15db43d14b22e2b8cd8c392abd83c7082b9bb44d3bd2b5b` (exact byte hash matched the shared baseline manifest)
- Governing heading: `Nøkkelkvalifikasjoner:`

| Mention | Mention type | Classification | Relationship | Exact evidence |
| --- | --- | --- | --- | --- |
| Backend development | `candidate_qualification` | `required` | `single` | Continuous opening-to-qualification passage below |
| C# | `candidate_qualification` | `required` | `single` | `God erfaring med C# .NET` |
| .NET | `candidate_qualification` | `required` | `single` | `God erfaring med C# .NET` |
| Azure | `candidate_qualification` | `required` | `single` | `Generell kompetanse i Azure (Entra, Key Vault, Storage accounts, App Services, App configuration, Azure functions, Application Insights)` |
| Entra, Key Vault, Storage accounts, App Services, App configuration, Azure functions, Application Insights | `candidate_qualification` | `unclear` for each | One `single` item per service | Same complete Azure bullet above for each service |
| Customer Identity and Access Management (CIAM) | `candidate_qualification` | `required` | `single` | `God kunnskap med CIAM (Customer Identity and Access Management)` |
| Relational databases (SQL) | `candidate_qualification` | `required` | `single` | `Relational Database (SQL)` |
| Infrastructure as Code | `candidate_qualification` | `required` | `single` | `IaC (Resource Management)` |
| Agile development | `candidate_qualification` | `required` | `single` | `Smidig utvikling/DevOps` |
| DevOps | `candidate_qualification` | `required` | `single` | `Smidig utvikling/DevOps` |
| CI/CD pipeline management | `candidate_qualification` | `required` | `single` | `Pipeline management (CI/CD)` |

Reasoning: `C# .NET` names two technologies used together, not an OR alternative; the two items may share one quotation. The Azure bullet clearly expects general Azure competence. Its parentheses may specify the scope of that competence, but do not establish that every listed service is independently required or preferred. `unclear` means the individual requirement status is unknown, not that a service is optional. The full Azure bullet preserves that context; parentheses alone do not decide the label.

Rami chose `Backend development` instead of `Backend expertise`: the latter implies a proficiency judgment. The qualification bullet states backend experience, and the opening identifies the role as Backend Developer. The agreed `skill_evidence` is this one continuous source passage, which includes the action context and the exact qualification wording; the number of years is not part of the skill name:

```text
På vegne av vår kunde som utvikler fremtidens trenings- og opplæringsløsninger gjennom XR-teknologi, søker vi en dyktig Senior Backend Developer.

Nøkkelkvalifikasjoner:

- 5+ år med backend erfaring
```

`Relational Database (SQL)` is treated as one combined qualification, rather than two counts for the same phrase. `Smidig utvikling/DevOps` yields two distinct single items; the slash does not establish an OR group. `IaC (Resource Management)` remains one Infrastructure as Code item, and `Pipeline management (CI/CD)` remains one pipeline-management item.

The preferred heading is `Ønskede kvalifikasjoner:`. The complete container bullet is `God kunnskap innen containerization and orchestration (Docker, Kubernetes, Azure Container Apps, Azure Kubernetes Service, Helm)`; each container-related item below uses that whole bullet as its skill evidence and the preferred heading as its classification context.

| Preferred-qualification item | Mention type | Classification | Relationship | Other exact evidence |
| --- | --- | --- | --- | --- |
| Full-stack development | `candidate_qualification` | `preferred` | `single` | `Erfaring med Fullstack utvikling` |
| Microservices | `candidate_qualification` | `preferred` | `single` | `Microservice and distributed systems` |
| Distributed systems | `candidate_qualification` | `preferred` | `single` | `Microservice and distributed systems` |
| Containerization | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Container orchestration | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Docker | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Kubernetes | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Azure Container Apps | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Azure Kubernetes Service | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| Helm | `candidate_qualification` | `preferred` | `single` | Complete container bullet above |
| NoSQL | `candidate_qualification` | `preferred` | `single` | `Forståelse for No-SQL` |

Rami chose the more precise `Container orchestration` name and classified the five named tools `preferred`. The heading governs the entire desired-knowledge bullet. The parenthetical list identifies technologies associated with that preference, even though the ad does not say every tool is expected. This is a weaker claim than marking each service in the earlier general Azure requirement `required`; those Azure services remain individually `unclear`. Parentheses alone determine neither label.

The offer of work with XR technology supports one `XR technology` item: `work_context`, `unclear`, `single`, with exact evidence `Mulighet til å jobbe med banebrytende teknologi innen XR`. This is a technical work-context mention, not an applicant qualification. The remaining offer and introductory wording does not add another distinct technical skill or an OR group.

Rami agreed to this final XR decision and the continuous backend passage, and reported Yehya's concurrence. This complete answer is selected in the approved reference.

## 5ae61e99-0980-4eac-a120-8338820483cc — approved complete reference

- Prepared input: `out/current/5ae61e99-0980-4eac-a120-8338820483cc/versions/f00301a8ee964f077b9b77d63b47cfb4df9960b8d77d785fcf824204281091f6/prepared_ad.txt`
- SHA-256 of frozen prepared input: `3445ebbf743f99245d2da8648692f914dddbf47e9d01d5c34d15aef66f83ac2c` (exact byte hash matched the shared baseline manifest)
- Required qualification heading: `Hva vi ser etter`

The evidence keys below stand for these continuous, exact passages in the prepared text:

| Key | Exact passage |
| --- | --- |
| Q1 | `God kjennskap til Modbus RTU (RS485), og Modbus TCP.` |
| Q2 | `Erfaring med sensorer, og sensorintegrasjon.` |
| Q3 | `Kunnskap om, og praktisk erfaring med AI/KI.` |
| P | `Erfaring med oppsett, og drift av VPN-løsninger er en fordel i denne rollen. Det samme gjelder erfaring med solenergi, batterianlegg, edge-enheter eller elsikkerhet (NEK 400). Dette er fordeler, men ikke krav.` |
| D1 | `Konfigurere, og integrere invertere, batterier og sensorer over Modbus RTU, og Modbus TCP.` |
| D2 | `Utvikle, og forbedre lokal kunstig intelligens, avviksvarsling og prediktivt vedlikehold.` |
| D3 | `Sikre trygg, og kryptert dataoverføring på lukket nett.` |

| Draft skill or complete alternative group | Relationship | Mention type | Classification | Evidence |
| --- | --- | --- | --- | --- |
| Modbus RTU (RS485) | `single` | `candidate_qualification` | `required` | Q1 |
| Modbus TCP | `single` | `candidate_qualification` | `required` | Q1 |
| Sensors | `single` | `candidate_qualification` | `required` | Q2 |
| Sensor integration | `single` | `candidate_qualification` | `required` | Q2 |
| Artificial intelligence (AI) | `single` | `candidate_qualification` | `required` | Q3 |
| VPN setup | `single` | `candidate_qualification` | `preferred` | P |
| VPN operation | `single` | `candidate_qualification` | `preferred` | P |
| Solar energy OR Battery installations OR Edge devices OR Electrical safety (NEK 400) | `any_of` | `candidate_qualification` | `preferred` | P |
| Inverter configuration | `single` | `work_duty` | `unclear` | D1 |
| Inverter integration | `single` | `work_duty` | `unclear` | D1 |
| Battery configuration | `single` | `work_duty` | `unclear` | D1 |
| Battery integration | `single` | `work_duty` | `unclear` | D1 |
| Sensor configuration | `single` | `work_duty` | `unclear` | D1 |
| Local AI development | `single` | `work_duty` | `unclear` | D2 |
| Anomaly alerting | `single` | `work_duty` | `unclear` | D2 |
| Predictive maintenance | `single` | `work_duty` | `unclear` | D2 |
| Encrypted data transfer | `single` | `work_duty` | `unclear` | D3 |

The sentence about higher education or equivalent experience in electrical engineering, automation, cybernetics or computing is excluded as education/background routes, not separately named skills under the current scope. `Modbus RTU (RS485)` is one combined item, while `Modbus TCP` is separate. The four preferred areas are one explicit OR group. The preferred wording `fordeler, men ikke krav` governs both VPN activities and that group.

The five configuration/integration duties add technical activities beyond the required Modbus and sensor qualifications. `Sensor integration` is kept only as the required qualification, rather than duplicated as an unclear duty. Broad platform/infrastructure wording, generic operation of an unnamed solution, personality traits and benefits do not add distinct items here; the AI-development duty is represented by D2. Rami agreed to these decisions and reported Yehya's concurrence. This complete answer is selected in the approved reference.

## a1613f9c-1757-4351-81ea-1d0e5246fbd3 — ten-item answer agreed

- Prepared input: `out/current/a1613f9c-1757-4351-81ea-1d0e5246fbd3/prepared_ad.txt`
- SHA-256 of frozen prepared input: `ac0c51f955b143aa20919ead0e8ac29be2744481b5906e3e4ab255cc9be7f3b5` (exact byte hash matched the shared baseline manifest)
- Duty heading: `Typiske arbeidsoppgaver vil være:`

| Key | Exact continuous skill passage |
| --- | --- |
| D1 | `drift og utvikling av IKT-systemer og infrastruktur` |
| D2 | `installasjon og oppsett av maskinvare og programvare` |
| D3 | `brukerstøtte til ansatte` |
| I | `har interesse for IKT, teknologi og digitale løsninger` |

| Draft item | Relationship | Mention type | Classification | Evidence |
| --- | --- | --- | --- | --- |
| IT systems operation | `single` | `work_duty` | `unclear` | D1 |
| IT systems development | `single` | `work_duty` | `unclear` | D1 |
| IT infrastructure operation | `single` | `work_duty` | `unclear` | D1 |
| IT infrastructure development | `single` | `work_duty` | `unclear` | D1 |
| Hardware installation | `single` | `work_duty` | `unclear` | D2 |
| Hardware setup | `single` | `work_duty` | `unclear` | D2 |
| Software installation | `single` | `work_duty` | `unclear` | D2 |
| Software setup | `single` | `work_duty` | `unclear` | D2 |
| IT user support | `single` | `work_duty` | `unclear` | D3 |
| ICT | `single` | `interest_only` | `unclear` | I |

The duty heading, not an applicant qualification, governs D1–D3. The surrounding IKT operations section supplies the technical context for user support. The `Kvalifikasjoner` heading does not turn an expressed interest in ICT into existing competence. No required or preferred existing technical skill is explicitly established.

The eight D1/D2 action–object combinations follow the agreed annotation convention: two named actions applied to two named objects in each bullet. This is a consistent review choice rather than the only possible division; installation and setup may overlap. Excluded: `digitale løsninger` as a separate generic skill, generic technology, education or school background, willingness to learn, personality traits, general problem solving, general communication, and unspecified practical tasks. Rami agreed to the ten-item answer and reported that Yehya agrees with his decisions. This complete answer is selected in the approved reference.

## b69f0bbd-082e-4d36-baae-456fb23ca32a — approved complete reference

- Prepared input: `out/current/b69f0bbd-082e-4d36-baae-456fb23ca32a/prepared_ad.txt`
- SHA-256 of frozen prepared input: `5da317535e9772bf07173eab7bbe46adfb1b9d9f26de9254faf1af5ba5f2adc7` (exact byte hash matched the shared baseline manifest)

Rami accepted as draft decisions the Unity experience alternative, the Git/version-control split, the broad agile/Scrum distinction, and XR solution development as `interest_only`, `unclear`. Their exact source passages are:

| Draft decision | Exact continuous source passage |
| --- | --- |
| Unity OR another game engine: one `candidate_qualification`, `required`, `any_of` group; desire to learn Unity does not establish existing Unity competence | `Erfaring med Unity eller annen spillmotor og sterkt ønske om å lære Unity.` |
| Git and Version control: separate `candidate_qualification`, `required`, `single` items | `God kjennskap til Git og versjonskontroll.` |
| Agile development methodologies: `candidate_qualification`, `required`, `single`; Scrum: named example with individual status `unclear`, `single` | `Erfaring med smidige utviklingsmetodikker som Scrum.` |
| XR solution development: `interest_only`, `unclear`, `single` | `Ønsker å bidra til utvikling av innovative løsninger innen XR.` |

The complete three-way condition is this continuous source passage:

```text
Erfaring med ett eller flere av følgende områder:

- Optimalisering for VR

- Nettverkskode

- Tverrfaglig samarbeid i utviklingsteam
```

This means one `candidate_qualification`, `required`, `any_of` group with **VR optimization OR Network code OR Cross-disciplinary collaboration in development teams**. Rami clarified that all three are sought as acceptable alternatives: an applicant needs one or more, not all three. The collaboration item is in scope here as experience within a development team; generic teamwork remains out of scope. The existing reference format can represent all three members in one group. None should be counted as an independently mandatory `single` skill.

For the duty `Utvikling og bygging av programfiler for Android, iOS, Windows, Mac og VR-enheter.`, Rami chose seven `work_duty`, `unclear`, `single` items, each supported by the full bullet: **Software development**, **Software builds**, **Android**, **iOS**, **Windows**, **Mac**, and **VR devices**. The platforms are named targets of the activities, not ten separate action–platform capabilities or required applicant qualifications.

The codebase bullet `Er komfortabel med å sette deg inn i eksisterende kode og forstå sammenhenger for å videreutvikle og forbedre.` supports **Codebase comprehension** as a `candidate_qualification`, `preferred`, `single` item under `Ønskede kvalifikasjoner`. Rami accepted the recommendation to omit separate Codebase development and Codebase improvement items: those labels overlap and the sentence presents them as the purpose of understanding the existing code.

Rami agreed that the specific technical abilities under `Personlige egenskaper` can be `candidate_qualification`, `required` despite the heading. The earlier preferred line concerns general understanding of user experience, while the later ability line concerns how technical choices affect user experience in VR/AR. The earlier preferred architecture line concerns understanding game-development architecture, while the later ability line concerns taking responsibility for architecture choices. These are related but distinct assertions. Generic teamwork and personality traits remain excluded.

### Complete approved answer

Rami approved this complete source-based answer and reported Yehya's concurrence. The saved model output remains unchanged. The `Arbeidsoppgaver` heading governs D1–D2; `Ønskede kvalifikasjoner` governs P1–P3; `Kvalifikasjoner` governs Q1–Q4. The specific ability wording in P4–P8, rather than the `Personlige egenskaper` heading alone, supports the required qualification status. Q4 is the complete continuous three-way passage quoted above. These headings are separate `classification_context` quotations where needed.

| Evidence key | Exact continuous source passage |
| --- | --- |
| D1 | `Delta i videreutvikling av vår flerspillerplattform.` |
| D2 | `Utvikling og bygging av programfiler for Android, iOS, Windows, Mac og VR-enheter.` |
| P1 | `Har god forståelse for spillmotorer og arkitektur i spillutvikling.` |
| I1 | `Ønsker å bidra til utvikling av innovative løsninger innen XR.` |
| P2 | `Har god forståelse for brukeropplevelse, ytelse og optimalisering.` |
| P3 | `Er komfortabel med å sette deg inn i eksisterende kode og forstå sammenhenger for å videreutvikle og forbedre.` |
| Q1 | `Erfaring med Unity eller annen spillmotor og sterkt ønske om å lære Unity.` |
| Q2 | `God kjennskap til Git og versjonskontroll.` |
| Q3 | `Erfaring med smidige utviklingsmetodikker som Scrum.` |
| P4 | `Kreativ og løsningsorientert, som evner å se det store bildet og bygge løsninger som er skalerbare, enkle å vedlikeholde og teknisk solide.` |
| P5 | `Samarbeidsvillig og kommunikativ, som trives med å jobbe i tverrfaglige team og kan forklare tekniske konsepter på en forståelig måte til både utviklere og designere.` |
| P6 | `Tar eierskap til arkitekturvalg og tekniske beslutninger, og følger opp leveranser med høy kvalitet.` |
| P7 | `Har forståelse for sluttbrukerens behov og hvordan tekniske valg påvirker brukeropplevelsen – spesielt i VR/AR-miljøer.` |
| P8 | `Kan jobbe med ulike plattformer og enheter, og tilpasse seg nye arbeidsflyter og kundekrav.` |
| C1 | `Mulighet til å jobbe med banebrytende teknologi innen XR og teknologi som gjør en forskjell.` |

| Proposed skill or complete group | Relationship | Mention type | Classification | Evidence |
| --- | --- | --- | --- | --- |
| Multiplayer platform development | `single` | `work_duty` | `unclear` | D1 |
| Software development | `single` | `work_duty` | `unclear` | D2 |
| Software builds | `single` | `work_duty` | `unclear` | D2 |
| Android | `single` | `work_duty` | `unclear` | D2 |
| iOS | `single` | `work_duty` | `unclear` | D2 |
| Windows | `single` | `work_duty` | `unclear` | D2 |
| Mac | `single` | `work_duty` | `unclear` | D2 |
| VR devices | `single` | `work_duty` | `unclear` | D2 |
| Game engines | `single` | `candidate_qualification` | `preferred` | P1 |
| Game development architecture | `single` | `candidate_qualification` | `preferred` | P1 |
| XR solution development | `single` | `interest_only` | `unclear` | I1 |
| User experience | `single` | `candidate_qualification` | `preferred` | P2 |
| Software performance | `single` | `candidate_qualification` | `preferred` | P2 |
| Software optimization | `single` | `candidate_qualification` | `preferred` | P2 |
| Codebase comprehension | `single` | `candidate_qualification` | `preferred` | P3 |
| Unity OR Other game engine | `any_of` | `candidate_qualification` | `required` | Q1 |
| Unity | `single` | `interest_only` | `unclear` | Q1 |
| Git | `single` | `candidate_qualification` | `required` | Q2 |
| Version control | `single` | `candidate_qualification` | `required` | Q2 |
| Agile development methodologies | `single` | `candidate_qualification` | `required` | Q3 |
| Scrum | `single` | `candidate_qualification` | `unclear` | Q3 |
| VR optimization OR Network code OR Cross-disciplinary collaboration in development teams | `any_of` | `candidate_qualification` | `required` | Q4 |
| Building scalable solutions | `single` | `candidate_qualification` | `required` | P4 |
| Building maintainable solutions | `single` | `candidate_qualification` | `required` | P4 |
| Technical concept communication | `single` | `candidate_qualification` | `required` | P5 |
| Technical architecture decision ownership | `single` | `candidate_qualification` | `required` | P6 |
| Understanding UX effects of technical choices in VR/AR | `single` | `candidate_qualification` | `required` | P7 |
| Working across platforms and devices | `single` | `candidate_qualification` | `required` | P8 |
| XR technology | `single` | `work_context` | `unclear` | C1 |

The two OR groups are required choices, not independently mandatory skills. The separate Unity interest item records the stated wish to learn Unity; it does not claim existing Unity competence. The preferred Game engines knowledge and the required Unity/other-engine experience are different assertions. General UX understanding differs from understanding the effects of technical choices in VR/AR; game-architecture knowledge differs from ownership of architecture decisions. D2 has two shared activities and five target technologies, following Rami's seven-item choice rather than multiplying every action by every target. General customer delivery, team-working personality, unnamed tools, years of experience, generic technical curiosity and benefits are excluded. This 29-item answer is pinned in the reference JSON for offline scoring. It does not change the dashboard's selected result.
