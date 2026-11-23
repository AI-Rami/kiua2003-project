# How the NAV skills dashboard runs safely

The dashboard shows which skills employers mention in IT job advertisements in Innlandet. You can open it and read the saved results without using an AI service or spending money.

When you click **Run update**, the program asks NAV for new or changed advertisements. It checks which ads belong in the dashboard, cleans their text, and sends eligible ads to an AI model one at a time. The model lists the skills it finds and quotes the words that support each answer. The program then checks the answer before updating the dashboard on your computer.

## 1. Permissions: what can the AI do?

The AI can read the cleaned text of one ad and return an answer in the format the program asks for. It has no tool to open a file on your computer, run a command or visit a website. Even if an ad contains the words “open this file”, the model has no way to carry out that instruction.

The Python program does the work that needs access to files or the internet. It checks that NAV addresses lead to the expected service and refuses redirects to another address. It sends extraction requests to OpenAI. It saves collection progress in `out/nav_discovery/`, selected answers in `out/current/` and skill counts in `out/statistics/`. The dashboard accepts connections from the same computer, and its update button gives users no way to choose an arbitrary file to open.

These are rules built into the program. Python still runs with the permissions of the person who started it. We have not demonstrated that the operating system would prevent Python itself from reading other files.

## 2. Secrets: how are the access keys handled?

A live update uses the operator’s own OpenAI key. The operator supplies it through a private setting called `KIUA2003_API`. The program sends the key separately to OpenAI to identify the account. The instructions and advertisement sent to the model, and the copy saved in `request.json`, do not include that key. NAV also provides a temporary access token, which the program keeps in memory.

When a request fails, the program reports the type of error. Local working files can contain advertisement text, so Git ignores the `out/` folder. It also ignores the local settings files `.env` and `.env.local`. Before data is packaged for sharing, the program checks it for recognisable secrets. We have not checked every historical file or tested every log for accidental disclosure.

## 3. Cost and time: how much work can one update do?

| Limit                                              | What it means                                                                                                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **20 AI requests**                                 | The program counts each attempt before sending it. Each request allows up to 8,192 output tokens. Tokens are small pieces of text used to measure AI usage. Together, the limits allow at most 163,840 output tokens per update.                                                                                                                                                                  |
| **20,000 bytes per request**                       | This limits the size of the text and instructions sent to the model. OpenAI also charges for input. The dashboard shows an estimated cost and does not enforce a fixed price in dollars.                                                                                                                                                                                                          |
| **20 minutes per update**                          | The program checks how much time remains before starting more work. It allows up to 30 seconds for a NAV request and up to 60 seconds for an AI request. If fewer than 60 seconds remain, it skips starting another AI request. Saving progress can take additional time.                                                                                                                         |
| **1,000 NAV feed pages and 2,000 detail requests** | NAV sends a list of new or changed ads in batches called *feed pages*. One page can list many ads. When the program needs to read a particular ad, it asks NAV for that ad’s details, including its description. Each such request counts towards the 2,000 limit. The program saves both its place in the list and the ads still waiting to be checked. The next update can continue from there. |

**Testing a change to the AI instructions.** We keep five job advertisements and our agreed answers so we can repeat the same test. To see how the AI responds to revised instructions, we send it the five saved ads again, one at a time. We do not download them again from NAV. Before starting, the tester sets the maximum number of AI requests, the time allowed and the amount they are willing to spend. If the program estimates that the run could cost more than that amount, it stops before sending the first ad.

**Checking an earlier test.** If we only want to reproduce the earlier scores, the program can compare the AI’s saved answers with our agreed answers again. This works offline and costs nothing in API fees.

## 4. Human decisions: what can be sent or shown automatically?

- **Sending an ad to the AI.** Clicking **Run update** allows the program to send ads that pass the checks. For example, if a sentence mixes a skill requirement with contact instructions and the cleaner cannot safely separate them, the program holds that version for review. Other ads can continue. A person must resolve the held version before it can be used. If NAV later supplies a newer version, the program can check it again. Automatic cleaning can miss personal information.
- **Showing an answer on the dashboard.** The program checks that the answer is complete, uses the expected labels and contains quotations found in the ad. Answers that pass can appear locally without someone approving each skill. Readers can inspect the quotations to judge the meaning. If a changed ad produces an invalid answer, the program keeps the older result for reference and leaves it out of current counts.
- **Sharing results on GitHub.** This is a separate human decision. Before sharing a new starting dataset, the project requires screening the files and checking that a fresh copy of the project works. Clicking **Run update** does not upload files to GitHub.

## 5. Kill switch: when must the update stop?

**When the service asks us to stop.** Imagine two ads are waiting. The program sends the first ad to OpenAI and receives “too many requests” (error 429). This means the service is asking the program to stop sending requests for now. The program records the failed attempt and leaves the second ad waiting. It sends nothing more to OpenAI during this update. A person can click **Run update** later to continue. The same stop rule applies if the API key is missing, access is denied, the connection fails, or the service takes too long to reply.

**When one answer fails our checks.** Imagine OpenAI answers the first ad, but the answer quotes a sentence that does not appear in the ad. The program records the error and leaves that answer out of the dashboard. It can then send the second ad because the service is responding. A later update can try the first ad again. By default, the program allows two attempts in total for that version of the ad, including the first attempt.

## How we checked these controls

On 23 November 2026, we ran the project's automated tests on a local computer. **All 60 passed** (32 update tests, 6 dashboard tests and 22 evaluation tests). This is the total across the three test suites. The examples below focus on safe operation. The tests ran the program's code using saved data and simulated replies from NAV and OpenAI. No advertisements were sent to either service.

| What we tested                                             | What the program actually did                                                                                                                                                                                                                                                                                                                         |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Would it stop if OpenAI asked it to slow down?             | Two ads were waiting. On the first attempt, the test supplied OpenAI's “too many requests” error (429). The program recorded the failure and made no attempt on the second ad. Both stayed on the unfinished list: the first had failed and the second had never been tried.                                                                          |
| Would it send an ad to the AI if NAV refused access?       | The test supplied an “access denied” reply during collection. The program reported that collection had failed, kept the waiting ad and made zero AI requests.                                                                                                                                                                                         |
| Would a request limit cause an ad to be lost?              | Two ads were waiting, and we allowed one AI request per update. The first update processed one ad and saved the second for later. We started another update with no new ads. It picked up the waiting ad and finished it.                                                                                                                             |
| Would the dashboard report an unfinished update correctly? | We simulated an update that stopped before it finished checking NAV for new ads. The program correctly reported that the check was incomplete. This test verified the status shown for an interrupted check. It did not test whether the program stops after 20 minutes.                                                                              |
| Could an uncertain contact passage reach the AI?           | A test ad mentioned a Python skill requirement and gave contact instructions in the same sentence. The program held the ad for review before extraction. The test counted zero AI calls and zero new results. The earlier evaluation log records the same case as `SYN-REJECT-001` in `docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/record.json`. |
| Could two clicks start two updates?                        | The test started a simulated update and kept it running while requesting a second start. The dashboard refused the second start. The test counted exactly one update running.                                                                                                                                                                         |

### Where to find the tests and their results

To see how a check works, open the file in the middle column and search for the test name in the last column.

| Example from this report | File in the project | Test name to search for |
|---|---|---|
| OpenAI asks the program to slow down | `harness/test_nav_update.py` | `test_model_rate_limit_stops_batch_and_keeps_other_work` |
| NAV refuses access | `harness/test_nav_update.py` | `test_discovery_auth_failure_stops_processing` |
| One ad waits after the request limit is reached | `harness/test_nav_update.py` | `test_extraction_limit_keeps_second_ad_pending` |
| Collection reports that time ran out | `harness/test_nav_update.py` | `test_time_limit_without_events_is_not_no_updates` |
| A sentence mixes a skill requirement with contact details | `harness/test_nav_update.py` | `test_raw_ambiguous_contact_passage_is_held_before_model` |
| Someone starts a second update | `harness/test_nav_dashboard.py` | `test_no_updates_and_duplicate_start_guard` checks that only one update runs. `test_button_endpoint_starts_once` checks the replies sent to the browser. |

**Saved example.** To see a result without running anything, open `docs/evaluation/2026-11-22_16-50-02_UTC-d36c2f63/report.md` and search for `SYN-REJECT-001`. That entry gives the expected and observed outcomes for the contact case in the **22 November** evaluation. The test input is in `eval/cases/offline-suite.json`. The evaluation test that checks the reported outcomes is `test_pinned_catalog_and_separate_synthetic_results` in `eval/test_evaluation.py`.

**The 23 November run.** The three commands below printed their results in PowerShell. The totals are recorded above. We did not save a separate terminal log for that run. To see each test name and its result on your own computer, run these commands from the project folder. The `-v` option prints one line per test.

```powershell
python -m unittest discover -v -s harness -p test_nav_update.py
python -m unittest discover -v -s harness -p test_nav_dashboard.py
python -m unittest discover -v -s eval -p test_evaluation.py
```

To find the rules in the code, start with `harness/nav_update.py` for decisions and limits. NAV requests are handled in `harness/nav_collect.py` and `harness/nav_discover.py`, cleaning in `harness/nav_text.py`, and AI requests and answer checks in `harness/nav_skeleton.py`. The local dashboard is in `harness/nav_dashboard.py`, shared-data checks are in `harness/share_data.py`, and evaluation budgets are in `eval/run.py`.
