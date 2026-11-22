# Reference review checklist

Run `python harness/start.py --check-only` first. The paths below are the **frozen prepared inputs** selected by `manifest.json`. The rows in `eval/history/first-attempt/gold.csv` are historical draft notes, not approved answers. Build each complete reference from the prepared text without looking at the model response. After approval, the evaluator compares the reference with the model output automatically.

| Advertisement UUID | Frozen prepared text after restore | Existing question to resolve |
| --- | --- | --- |
| `2ed29047-97e4-4168-adb9-8da83e968c94` | `out/current/2ed29047-97e4-4168-adb9-8da83e968c94/prepared_ad.txt` | Broad technical labels and personal-trait scope. |
| `2f62e300-c698-4f53-8510-db90b1692cb9` | `out/current/2f62e300-c698-4f53-8510-db90b1692cb9/prepared_ad.txt` | Broad Azure competence versus named services, combined `C# .NET`, and IaC granularity. |
| `5ae61e99-0980-4eac-a120-8338820483cc` | `out/current/5ae61e99-0980-4eac-a120-8338820483cc/versions/f00301a8ee964f077b9b77d63b47cfb4df9960b8d77d785fcf824204281091f6/prepared_ad.txt` | Current selected extraction says no human meaning review; check that older draft labels refer to this exact input version. |
| `a1613f9c-1757-4351-81ea-1d0e5246fbd3` | `out/current/a1613f9c-1757-4351-81ea-1d0e5246fbd3/prepared_ad.txt` | Whether a generic digital-solutions label is in technical scope. |
| `b69f0bbd-082e-4d36-baae-456fb23ca32a` | `out/current/b69f0bbd-082e-4d36-baae-456fb23ca32a/prepared_ad.txt` | Grouped experience areas, technical scope of personality wording, and explicit OR alternatives. |

For **each whole advertisement**, Rami and Yehya should record: all included items; all intentionally excluded technical-looking mentions; `single` or complete `any_of` group; precise skill names and approved aliases; required/preferred/unclear; mention type; continuous skill quotation; optional governing context quotation; unresolved judgments; and whether the **complete** answer is approved. Leave an advertisement outside the accuracy denominator while any relevant decision is unresolved. The eight `checked=no` advertisements are drafts and remain outside the initial score.
