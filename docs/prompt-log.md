# Prompt correction log

Record corrected or rejected agent output using: date, task reference, sanitized prompt/output excerpt, reason, correction, and lesson. Never include personal data or secrets.

## 2026-10-10 — Scaffold planning: data policy

- Task: Initial scaffold planning.
- Rejected output: "Use only synthetic data."
- Reason: The project should support permitted public data and reproducible offline runs with saved real public inputs.
- Correction: "Use permitted public data without personal data; synthetic data may supplement tests."
- Lesson: Do not impose a synthetic-only data restriction. Record source, retrieval date, and permission/license for future public fixtures.

## 2026-10-10 — Scaffold planning: environment variables

- Task: Initial scaffold planning.
- Rejected output: Assume `OPENAI_API_KEY` and `OPENAI_MODEL` belong in `.env.example`.
- Reason: The workflow's provider and configuration requirements have not been selected.
- Correction: Keep `.env.example` comment-only: "Variable names will be added when needed; never put real secrets here."
- Lesson: Add variable names only when a concrete requirement exists; never add real secrets.

## Permission-test status

Project secret-file protection remains unverified. The 2026-10-11 tests below covered temporary-file creation, not secret-file reads. Use only harmless dummy data for future secret-file testing and record the effective profile, tool paths tested, denied-read results, readable-file results, and Git ignore results here when that test is performed.

## 2026-10-11 - Permission tests: desktop and CLI

- Task: Test the current `kiua2003` permission profile using harmless temporary files, without changing configuration or the checker.
- Test conclusion: Desktop eval/ protection failed. CLI temporary-file creation protection passed in the tested session. Secret-file protection remains unverified.
- Reason: In the desktop app, temporary-file creation in `eval/` succeeded; protection failed. Secret-file reads were not tested.
- Correction: Limit verification to the tested CLI behavior described below; keep secret-file protection marked unverified.
- CLI version: 0.162.1. Launch command for this test and future CLI work:

  ```powershell
  codex.cmd -c windows.sandbox=mxc -c default_permissions=kiua2003
  ```

- CLI results: Normal sandboxed exclusive creation (`FileMode.CreateNew`) of root `__permission_test__.tmp` succeeded and cleanup succeeded. Creation of `eval/__permission_test__.tmp` failed with error ID `UnauthorizedAccessException`; the reported error was `Exception calling "Open" with "4" argument(s): "Access to the path '...\eval\__permission_test__.tmp' is denied."` Cleanup for that path was skipped because the test did not create the file.
- Checker integrity: The SHA-256 hash of `eval/check_probe.py` was identical before and after: `34C98C2F6289BE236EE5EEEF325BF42EFC21A78BD7337235E64A6AF9C197383F`.
- Cleanup: No temporary files remained after the tests.
- Lesson: The observed CLI behavior supports root creation and denied `eval/` creation in that tested session only. It does not establish protection in the desktop app, for secret-file reads, or through other tools and sessions.
