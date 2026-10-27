# Project specification

## Purpose

The project is a job advertisement analyser using NAV's job vacancy API as the chosen data source, initially focused on IT roles in Innlandet. Its planned purpose is to make skill requirements across job advertisements easier to compare by extracting skills and classifying them as required, preferred, or unclear.

Education and experience extraction are possible future extensions and are outside the current scope.

The project will begin with a small end-to-end walking skeleton. Later capabilities will be added through separate, narrowly scoped tasks. The detailed scope and acceptance criteria for the walking skeleton will be defined in the next task brief.

## Users

The intended primary users are IT jobseekers in Innlandet, particularly recent graduates. Career advisers are potential secondary users.

The intended user need has not yet been demonstrated or validated. The project currently treats easier comparison of advertisement requirements as a working assumption to investigate.

## Intended workflow

The following workflow is planned:

1. Collect advertisement updates from NAV's job vacancy API, after verifying the relevant endpoints, access requirements, and usage terms.
2. Select active IT advertisements for Innlandet using NAV's IT categories and Innlandet location filtering where supported by the API. Verify the available API fields and filters before implementation; do not assume website filters are exposed through the API. Use deadline and source status, where available, to exclude expired or withdrawn advertisements. Handling of remote jobs and multiple locations remains open.
3. Remove duplicate versions of the same advertisement.
4. Use an AI agent to extract skills. Each extracted skill must have a skill name, a classification of required, preferred, or unclear, and an exact supporting quotation from the advertisement. Preserve a link to the source advertisement. Flag ambiguous wording as unclear without forcing a required or preferred classification.
5. Validate output structure and check with code that each quotation occurs in the source text. Use reviewed reference examples to evaluate skill extraction, classification, omissions, and invented skills. A matching quotation alone does not prove that the interpretation is correct. Flag uncertain results without numerical confidence scores.
6. Calculate totals using ordinary code rather than the AI agent.
7. Produce structured JSON and a readable report with links to the source advertisements.
8. Eventually run the workflow automatically each week.

JSON and a readable report with source links are agreed outputs. The final JSON schema has not yet been defined.

The AI model remains undecided until candidate models have been tested. Model selection will consider extraction accuracy, cost, speed, and access through the project's setup. The model must remain configurable.

## Definition of success

Success means that the project:

- extracts skills accurately, distinguishes required from preferred skills, and marks ambiguous wording as unclear, with omissions and invented skills assessed against reviewed reference examples;
- makes each extracted skill traceable to an exact supporting quotation and a source link, while evaluating interpretation separately from quotation matching;
- supports reproducible execution from documented inputs and steps; and
- reports failures and uncertain results clearly rather than presenting them as reliable output.

Numerical success thresholds have not yet been defined. Appropriate evaluation cases, scoring methods, and acceptance thresholds must be established in later task briefs.

## Open questions

- Which endpoints, access requirements, and usage terms apply to NAV's job vacancy API?
- Which API fields and filters support NAV's IT categories, Innlandet locations, deadlines, and source status, and how should selection work when these are unavailable?
- How should remote jobs and advertisements with multiple locations be handled?
- How should different versions of the same advertisement be detected and deduplicated?
- Which candidate AI models should be tested, and which best meets the extraction accuracy, cost, speed, and access needs of the project?
- Which prompting approach and final JSON schema should be used for extraction?
- How should advertisement text be prepared so exact supporting quotations can be reliably checked against the source?
- Which reviewed reference examples and review process should evaluate extraction, classification, omissions, invented skills, and ambiguous wording?
- What mechanism should schedule and monitor eventual weekly runs?

## Current implementation status

The repository contains an earlier MET Norway weather exercise, separate from the planned NAV workflow. The task brief in `tasks/001-probe.md` describes retrieving a Hamar weather forecast, saving the response, and producing `out/probe.json`, with offline support. It explicitly excludes changes to the final project problem.

Code inspection for this specification update confirmed that `harness/probe.py` contains MET forecast retrieval, caching, offline reading, transformation, and JSON output code. `harness/test_probe.py` contains synthetic tests for the weather exercise, and `eval/check_probe.py` checks weather output rather than NAV advertisements or extracted skills. The saved weather fixture and metadata are present, and `out/probe.json` exists.

The README still states that the downloader is unimplemented and the output is missing; those documentation statements do not reflect the files inspected. The weather code and tests were inspected but not executed for this update, and the existing output's correctness was not tested. No runtime success is claimed here.

The NAV collection, advertisement selection, deduplication, AI skill extraction, validation, aggregation, reporting, and weekly automation described above remain planned behaviour. No implementation of these NAV capabilities was found in the inspected repository files, and no NAV workflow was executed or tested.
