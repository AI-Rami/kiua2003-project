# What happens when a dashboard update goes wrong?

**NAV skills dashboard | Stress-test report | 23 November 2026**

The dashboard shows which technical skills employers mention in IT job advertisements in Innlandet. During an update, the program decides which ads belong in the dashboard, sends their text to an AI service, and checks each answer before counting its skills.

We tested two things that can go wrong: the program can receive an ad it should skip, or it can receive an unexpected reply from the AI service. **Three of our four tests passed on the first run.** The fourth exposed a problem: one bad reply stopped the program from processing the next ad. We fixed the answer checker and repeated the same four tests. **All four then passed.**

We ran the real program code on a local computer. Each test started with an empty test dashboard. A small test program stood in for the AI service so we could choose exactly what reply it gave and count the requests. We used temporary data throughout, with no live requests or charges.

## 1. Input perturbation — an advertisement has no description

We gave the program a saved ad with an empty description. With no text to read, the AI would have no evidence for any skills. We expected the program to stop before asking the AI for an answer.

**What happened:** The program reported that it needed a nonempty description. It made zero AI requests and produced zero results. Rejecting the ad was the expected outcome, so the test passed on both runs.

## 2. Input perturbation — an active IT job lists only Oslo

We created an ad for an active IT job that required Python. It had a readable description and met the IT rule. Its only listed county was Oslo. This let us check whether location alone was enough to keep it out of the Innlandet statistics.

**What happened:** The program read the job details, recorded that the ad fell outside the selection rules, and finished the update normally. It made zero AI requests. The dashboard count stayed at zero on both runs.

## 3. Dependency failure — the AI service says “too many requests”

Two eligible ads were waiting. On the first request, we made the simulated service reply “too many requests” (error 429). This is a signal to stop contacting the service for the current update. The second ad let us check whether the program respected that signal.

**What happened:** The program made exactly one request. It recorded the first ad as failed and left the second waiting without trying it. Both remained on the list of unfinished work, and neither appeared on the dashboard. This safeguard worked on both runs.

**What happens on the next update?** The test ended after checking that both ads were still on the list. The update code explains what can happen next. When someone clicks **Run update** again, the program checks unfinished work. If both ads are still eligible, the first has one attempt left under the default limit of two, and the second is waiting for its first attempt. If the service accepts requests again and the run has enough time and requests left, both can be processed. If the first request gets another “too many requests” reply, the program stops again and the second ad keeps waiting.

## 4. Dependency failure — both ads are valid, but the first reply is unusable

We used two ordinary, eligible ads. The first asked for Python and the second asked for SQL. We changed only what the simulated AI service would send back. For the Python ad, it returned just `[]`, an empty list. For the SQL ad, it was ready to return a complete answer identifying SQL and quoting the ad.

**Why was the first reply unusable?** Even when the AI finds no skills, the program expects a complete reply saying that the request finished and containing an answer it can check. The empty list had none of that information. The program could read the symbols `[]`, but it could not conclude that the employer had asked for no skills.

**Before the repair:** The checker tried to read the completion status from the empty list and crashed. The first ad stayed marked as “extracting”, even though processing had stopped. The program never asked for the second answer. The dashboard stayed empty.

**What we changed:** The checker now first asks whether the reply has the expected form before it tries to read any fields. If the reply is a list, it records a validation error. The update can then use its existing procedure for setting aside a failed answer and moving on.

**After the repair:** We supplied the same two ads and the same replies. The program marked the Python ad’s attempt as `validation_failed`. The checker saves the specific reason in that attempt’s `validation.json` file: “API response must be a JSON object”. In plain English, the service sent an empty list where the program needed named fields describing the answer. The program then requested and checked the SQL answer. It made two requests in total, and only the SQL ad appeared on the dashboard.

## Evidence and instructions for repeating the tests

The four tests are in `harness/test_nav_stress.py`. The empty ad is in `eval/stress/03_empty.json`. The repair is in the `validate` function in `harness/nav_skeleton.py`.

Run the following command from the project folder with Python 3:

```powershell
python -B -u harness/test_nav_stress.py
```

The original test output is saved beside this report in `before.txt` (three passed, one error) and `after.txt` (four passed). The first log shows where the checker crashed. Personal folder names in that log were shortened. To repeat the original failure, use a separate checkout of commit `a1fe1d23f3b5865808c5557c1cea7f5735926eb0`, copy the same stress-test file into its `harness/` folder, and run the command there.

We also checked whether the repair changed how the program handled previously tested answers. All five saved real-ad answers passed the format and quotation checks, and all five synthetic checks passed. The skill comparison reproduced the earlier 47 exact matches and combined score (F1) of 0.543. All 32 update tests and all 22 evaluation tests passed. To repeat these checks:

```powershell
python -B eval/run.py --mode offline-suite --suite eval/cases/manifest.json
python -B -m unittest discover -s harness -p test_nav_update.py
python -B -m unittest discover -s eval -p test_evaluation.py
```

The evaluation report from that run is in `out/evaluation/2026-11-23_20-13-36_UTC-2a21d643/report.md`. Running the evaluation again creates a new dated report.
