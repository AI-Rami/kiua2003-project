# kiua2003-project

A two-person KIUA2003 project exploring an agentic workflow.

This project includes a scaffold and an implemented NAV saved-input walking skeleton. See [SPEC.md](SPEC.md) for the problem, users, and definition of success, and [AGENTS.md](AGENTS.md) for working instructions.

- `tasks/`: task briefs with owner, reviewer, acceptance criteria, and status. The two people can alternate roles.
- `harness/`: workflow stages, prompts, tools, and execution code.
- `eval/`: evaluation cases, expected outcomes, and scoring criteria; changes require permission.
- `fixtures/`: saved real public inputs without personal data for reproducible offline runs. Record source, retrieval date, and permission/license alongside future inputs.
- `docs/meetings/`: decisions and next actions using Person A and Person B.
- [docs/prompt-log.md](docs/prompt-log.md): corrected or rejected agent output and lessons.

The earlier MET Norway exercise is in `harness/probe.py`; its checker is `eval/check_probe.py`. The NAV walking skeleton is separate.

## NAV saved-input walking skeleton

Requires Python 3 and internet access with OpenAI API credits. Set the process environment variable `KIUA2003_API` to your API key before the saved-input run; do not put a real key in project files. The program never writes the key or Authorization header. In PowerShell, set it privately for the current process, then run:

```powershell
python harness/nav_skeleton.py --mode dry-run
python harness/nav_skeleton.py --mode saved-input
```

Use `--input path/to/ad.json` with either command for another compatible saved advertisement. The default is the edited fixture `fixtures/nav_ad_01.json`. Dry run only prints the plan and limits; it does not read or validate the input, require a key, make a network call, or change files. Saved-input mode automatically (1) reads the saved advertisement and prepares its entire HTML description as readable text, (2) calls `gpt-6-luna` through OpenAI's Responses API to extract technical skills, and (3) validates the response before creating the JSON result and Markdown report.

Each extracted item is `required` for an applicant qualification, `preferred` for an explicitly optional advantage, or `unclear` when the advertisement mentions a skill without establishing either. A `single` item contains exactly one skill. An `any_of` item preserves at least two explicit alternatives, such as “A or B”, without choosing between them. Validation checks JSON structure and that each supporting quotation occurs exactly in the prepared text. It does not establish extraction accuracy or completeness.

Each run has its own `out/nav_runs/<run-id>/` directory. New run IDs use the UTC date, time, and validated advertisement UUID, for example `2026-10-31_08-23-49_UTC_ad-8119dbb1-530f-4307-9ee0-e030c2b8e581`; the run ID matches the folder name. A run fails without overwriting anything if that folder already exists. Read `report.md` alongside the saved advertisement and its notes; `result.json` holds structured items. `prepared_ad.txt`, `request.json` without credentials, `response.json`, and `validation.json` aid inspection. A failed run has no successful result or report. The fixture's saved `ACTIVE` status is not a live status check.

Extraction accuracy and completeness remain to be evaluated against a human-reviewed reference. Planned extensions include live NAV collection and Python-calculated statistics across advertisements, with explicit rules for skill naming, alternative groups, and duplicates.

## Secret-file protection

`.codex/config.toml` proposes project-scoped denied reads for root `.env` and `.env.local`, while leaving `.env.example` readable. `.gitignore` prevents accidental tracking; it does not prevent reads.

Secret-file protection remains unverified: the permission tests below did not attempt secret-file reads. Before adding real secrets, use only harmless dummy markers such as `DUMMY_SECRET=NOT_A_REAL_SECRET` in `.env` and `.env.local`.

## Permission tests and CLI launch (2026-10-11)

- Desktop app: temporary-file creation in `eval/` succeeded; protection failed.
- CLI 0.162.1 was launched with the following command. Use this command for future CLI work:

  ```powershell
  codex.cmd -c windows.sandbox=mxc -c default_permissions=kiua2003
  ```

- In that CLI session, normal sandboxed exclusive creation of `__permission_test__.tmp` in the project root succeeded. Creation of `eval/__permission_test__.tmp` was denied with `UnauthorizedAccessException`.
- The SHA-256 hash of `eval/check_probe.py` remained unchanged: `34C98C2F6289BE236EE5EEEF325BF42EFC21A78BD7337235E64A6AF9C197383F`.
- No temporary files remained after the tests.

Verification is limited to the tested CLI temporary-file creation behavior. It does not verify desktop protection, secret-file protection, or other tools and sessions. See [docs/prompt-log.md](docs/prompt-log.md) for the recorded results.

## Future secret-file verification

In a fresh desktop session for this trusted project:

1. Confirm the effective permission profile is `kiua2003` and that legacy sandbox settings or managed requirements have not overridden it.
2. Attempt sandboxed direct reads of both dummy secret files; both must fail with permission denied.
3. Confirm `.env.example` and `README.md` remain readable, and test other available file-reading tools separately.
4. Do not approve elevated retries or use full access during the test.
5. Check Git ignore behavior and record the results in `docs/prompt-log.md`.

If protection fails, keep only dummy data while resolving compatibility. Add explicit protection before introducing secrets at other paths. Keep real secrets outside Codex's accessible environment until verification passes.
