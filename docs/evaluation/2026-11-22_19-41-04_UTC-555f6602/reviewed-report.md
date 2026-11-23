# Reviewed evaluation of prompt version 3, 22 November 2026

Five saved ads were tested once each. Four answers passed structure and quotation checks. Both intended changes appeared in the answers, but the energy ad failed quotation validation. The overall goal of five usable answers was missed.

## Prompt used in this test

The [complete version 3 prompt](prompt.txt) matches the instructions sent in all five saved requests, byte for byte. Its SHA-256 fingerprint is `a9985b39a0301fa61627c31172d9c74a7b8e4c6ebb4265b5e93f91b7826904a3`, as recorded in the [run record](record.json).

Compared with [version 2](../2026-11-22_18-54-11_UTC-07c529af/prompt.txt), version 3 added two instructions:

1. Exclude fields listed as routes to a degree or equivalent background. Include a field when another passage independently supports it as a technical mention, and quote that passage.
2. Before submitting, check that each `single` item has exactly one skill. Remove unsupported or generic names, separate distinct supported skills, and use `any_of` only for an explicit choice.

## Findings for the five advertisements

| Ad | Version 2 | Version 3 | What the final response shows |
| --- | --- | --- | --- |
| 1. Information management | Passed | Passed | The model separates AI development and AI use. It also calls “Intelligence” a preferred qualification, although the approved answer excludes the broad domain topic. |
| 2. Azure | Passed | Passed | All five named container tools are still preferred under “Ønskede kvalifikasjoner”. General Azure competence is required and its seven listed services have unclear individual status. |
| 3. Energy | Passed | Failed | The degree or equivalent-background list is gone. Items 9 and 10 both extend the source bullet “Videreutvikle den tekniske plattformen, KI-funksjonene og infrastrukturen.” with “i Rondekraft” before the period. The resulting quotation appears nowhere as a continuous passage. The answer received no skill score. |
| 4. ICT support | Failed | Passed | Each single item has one name. The answer now separates “ICT” and “Digital solutions” as interests. Only ICT is included in the approved answer, so a scope disagreement remains despite valid structure. |
| 5. Game development | Passed | Passed | The model preserves the required three-way choice of VR optimization, network programming and cross-disciplinary collaboration in development teams. The source says “Nettverkskode”, which the approved reference calls “Network code”. The collaboration branch belongs inside this choice. |

Across the four validated version 3 answers, **42 of 81 model items matched 73 reference items**. Precision was 51.9%, recall 57.5%, and F1 0.545. Both versions validated four ads, but they failed on different ads. The fair comparison therefore uses ads 1, 2 and 5, which passed in both runs.

| Same three ads | Exact matches | Model items | Reference items | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Version 2 | 37 | 65 | 63 | 56.9% | 58.7% | 0.578 |
| Version 3 | 38 | 70 | 63 | 54.3% | 60.3% | 0.571 |

Version 3 found one more exact match and produced five more items on those three ads. This final development run shows specific fixes and a new failure. It does not establish a general accuracy improvement.

[Prompt used](prompt.txt) · [Generated report](report.md) · [Run record](record.json) · [Saved answers](answers.json) · [Previous reviewed test](../2026-11-22_18-54-11_UTC-07c529af/reviewed-report.md)
