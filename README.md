# kiua2003-project

A two-person KIUA2003 project exploring an agentic workflow.

This is a project scaffold. See [SPEC.md](SPEC.md) for the problem, users, and definition of success, and [AGENTS.md](AGENTS.md) for working instructions.

- `tasks/`: task briefs with owner, reviewer, acceptance criteria, and status. The two people can alternate roles.
- `harness/`: the future workflow's stages, prompts, tools, and execution code.
- `eval/`: evaluation cases, expected outcomes, and scoring criteria; changes require permission.
- `fixtures/`: saved real public inputs without personal data for reproducible offline runs. Record source, retrieval date, and permission/license alongside future inputs.
- `docs/meetings/`: decisions and next actions using Person A and Person B.
- [docs/prompt-log.md](docs/prompt-log.md): corrected or rejected agent output and lessons.

No runnable checks exist yet. Empty `.gitkeep` files keep the initial folders trackable in Git.

## Secret-file protection

`.codex/config.toml` proposes project-scoped denied reads for root `.env` and `.env.local`, while leaving `.env.example` readable. `.gitignore` prevents accidental tracking; it does not prevent reads.

Protection is unverified: no fresh-session permission test has been run. Before adding real secrets, use only harmless dummy markers such as `DUMMY_SECRET=NOT_A_REAL_SECRET` in `.env` and `.env.local`.

In a fresh desktop session for this trusted project:

1. Confirm the effective permission profile is `kiua2003` and that legacy sandbox settings or managed requirements have not overridden it.
2. Attempt sandboxed direct reads of both dummy secret files; both must fail with permission denied.
3. Confirm `.env.example` and `README.md` remain readable, and test other available file-reading tools separately.
4. Do not approve elevated retries or use full access during the test.
5. Check Git ignore behavior and record the results in `docs/prompt-log.md`.

If protection fails, keep only dummy data while resolving compatibility. Add explicit protection before introducing secrets at other paths. Keep real secrets outside Codex's accessible environment until verification passes.
