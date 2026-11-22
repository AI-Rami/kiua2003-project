# Evaluation: gold labels vs model output

Scope: checked ads only. Ads: 5. Gold skills: 61. Model skills: 87.

| Measure | Value | Counts |
|---|---|---|
| Recall | 92 % | 56 of 61 gold skills found |
| Precision | 62 % | 54 of 87 model skills matched gold |
| F1 | 0.74 | |
| Label agreement | 71 % | 40 of 56 matched skills |

## Per advertisement

| ad_id | Gold | Model | Recall | Precision | Label agreement |
|---|---|---|---|---|---|
| 2ed29047 | 2 | 9 | 100 % | 22 % | 100 % |
| 2f62e300 | 26 | 28 | 100 % | 89 % | 54 % |
| 5ae61e99 | 13 | 17 | 77 % | 53 % | 100 % |
| a1613f9c | 4 | 7 | 100 % | 57 % | 100 % |
| b69f0bbd | 16 | 26 | 88 % | 54 % | 71 % |

## Error types

| Error | Count |
|---|---|
| model item not in gold | 33 |
| gold required -> model unclear | 10 |
| gold preferred -> model unclear | 5 |
| missed by model | 5 |
| gold required -> model preferred | 1 |

Matching is by word overlap of skill names (see eval/score.py), so a few matches may be
too loose or too strict. Check eval/results/matches.csv before quoting numbers.
