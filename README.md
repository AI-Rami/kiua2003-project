# kiua2003-project

A two-person KIUA2003 project exploring an agentic workflow.

This is a project scaffold. See [SPEC.md](SPEC.md) for the problem, users, and definition of success, and [AGENTS.md](AGENTS.md) for working instructions.

- `tasks/`: task briefs with owner, reviewer, acceptance criteria, and status. The two people can alternate roles.
- `harness/`: the future workflow's stages, prompts, tools, and execution code.
- `eval/`: evaluation cases, expected outcomes, and scoring criteria; changes require permission.
- `fixtures/`: saved real public inputs without personal data for reproducible offline runs. Record source, retrieval date, and permission/license alongside future inputs.
- `docs/meetings/`: decisions and next actions using Person A and Person B.
- [docs/prompt-log.md](docs/prompt-log.md): corrected or rejected agent output and lessons.

The acceptance checker is eval/check_probe.py. It currently fails because out/probe.json has not been produced. The downloader has not been implemented.

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
