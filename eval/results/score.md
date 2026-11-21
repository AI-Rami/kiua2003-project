# Evaluation: gold labels vs model output

Scope: all ads (some gold labels are drafts). Ads: 13. Gold skills: 175. Model skills: 304.

| Measure | Value | Counts |
|---|---|---|
| Recall | 93 % | 162 of 175 gold skills found |
| Precision | 52 % | 159 of 304 model skills matched gold |
| F1 | 0.67 | |
| Label agreement | 81 % | 132 of 162 matched skills |

## Per advertisement

| ad_id | Gold | Model | Recall | Precision | Label agreement |
|---|---|---|---|---|---|
| 1f614033 | 23 | 38 | 96 % | 58 % | 68 % |
| 2ed29047 | 2 | 9 | 100 % | 22 % | 100 % |
| 2f62e300 | 26 | 28 | 100 % | 89 % | 54 % |
| 4135497b | 19 | 28 | 89 % | 57 % | 88 % |
| 5ae61e99 | 13 | 17 | 77 % | 53 % | 100 % |
| 8119dbb1 | 9 | 18 | 100 % | 50 % | 100 % |
| 8d77969c | 5 | 7 | 100 % | 71 % | 80 % |
| a1613f9c | 4 | 7 | 100 % | 57 % | 100 % |
| a5dabb26 | 29 | 52 | 90 % | 50 % | 100 % |
| b35c3ca3 | 7 | 29 | 86 % | 21 % | 67 % |
| b69f0bbd | 16 | 26 | 88 % | 54 % | 71 % |
| dc0bdd91 | 9 | 21 | 100 % | 43 % | 100 % |
| fbae0d93 | 13 | 24 | 92 % | 50 % | 83 % |

## Error types

| Error | Count |
|---|---|
| model item not in gold | 145 |
| gold required -> model unclear | 16 |
| missed by model | 13 |
| gold preferred -> model unclear | 11 |
| gold preferred -> model required | 2 |
| gold required -> model preferred | 1 |

Matching is by word overlap of skill names (see eval/score.py), so a few matches may be
too loose or too strict. Check eval/results/matches.csv before quoting numbers.
