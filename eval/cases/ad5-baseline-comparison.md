# Advertisement 5: frozen-prompt baseline comparison

This is a development/regression case, not an unseen accuracy estimate. The complete source-based reference was approved before the formal replay score; the current model output had been inspected earlier in the discussion. No prompt, model response, selected dashboard result or statistics were changed for this comparison.

- Advertisement UUID: `b69f0bbd-082e-4d36-baae-456fb23ca32a`
- Frozen prepared input SHA-256 after newline normalization: `57f8290a68b083851d0bb227373017dbb8d4a5ed2354d0053bad55e2d1b2fa85`
- Frozen prompt SHA-256: `789bf663f2303ff46257cd22e85ea2fa08f8fff020fda401bc18aa572258543b`
- Model: `gpt-6-luna`; saved response ID: `resp_0432a290789b921f016ae8270331d887d28ebd100dcf3052bc`
- Approved reference: `../references/development-v2-approved.json`, pinned by `manifest.json`
- Reproduce the offline check: `python eval/run.py --mode replay --suite eval/cases/manifest.json`

The saved response passed JSON and quotation validation. Exact item-name/group scoring matched 17 of 25 model items to 29 reference items (precision 0.680, recall 0.586, F1 0.630). Exact-name differences can include equivalent wording; this score alone does not decide semantic correctness.

## Confirmed interpretation and structure errors

1. **The required three-way choice was lost.** The ad says:

   ```text
   Erfaring med ett eller flere av følgende områder:

   - Optimalisering for VR

   - Nettverkskode

   - Tverrfaglig samarbeid i utviklingsteam
   ```

   The approved answer is one `required` `any_of` group: VR optimization OR Network code OR Cross-disciplinary collaboration in development teams. The saved model answer instead has separate `unclear` candidate items for VR optimization and Network code and omits the collaboration alternative. None of the three is independently mandatory, but at least one is expected.

2. **Two duty actions were combined.** `Utvikling og bygging av programfiler for Android, iOS, Windows, Mac og VR-enheter.` supports separate Software development and Software builds duties, plus the five named targets. The saved answer has one `Software development and build generation` item instead of the two agreed activity items. The five targets were retained.

3. **The model changed the action in a solution-building requirement.** `Kreativ og løsningsorientert, som evner å se det store bildet og bygge løsninger som er skalerbare, enkle å vedlikeholde og teknisk solide.` supports Building scalable solutions and Building maintainable solutions. The saved answer says `Scalable and maintainable software design`. The source says *build*, not *design*, and the two agreed aspects were combined.

4. **General and specific UX statements were merged.** `Har god forståelse for brukeropplevelse, ytelse og optimalisering.` is under the preferred heading. A later statement concerns how technical choices affect UX in VR/AR and supports a required ability. The saved answer has only `User experience in VR/AR environments` as required, losing the separate general preferred UX mention.

The approved reference also includes the stated interest in learning Unity and the offered XR work context; the saved answer omits these items.

## Differences needing careful interpretation

`Technical communication` versus `Technical concept communication`, `Technical architecture decision-making` versus `Technical architecture decision ownership`, and `Codebase comprehension and improvement` versus `Codebase comprehension` do not match by exact name. Some wording may be equivalent or reflect the agreed granularity rather than a wholly missing skill. No alias or manual correction was applied to improve the score. A later prompt version should be tested on the same frozen input, with its new response retained separately, so both improvements and regressions remain visible.
