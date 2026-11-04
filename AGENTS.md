# Working instructions
Project: A two-person KIUA2003 NAV job-advertisement skills dashboard.
- Read README.md, SPEC.md and the relevant task brief before implementation.
- On a fresh checkout, `python harness/start.py --check-only` restores and validates the shared baseline without network or model requests. `python harness/start.py` opens the local dashboard. Do not replace an updated local `out/` with the baseline.
- Keep changes small and within the assigned task.
- Use permitted public data; screen shared data for contact details and credentials. Automatic screening does not prove all personal information is absent. Synthetic data may supplement tests.
- Never edit eval/ without asking the user and receiving permission.
- Never read, modify, or print secret .env files.
- Keep .env.example readable and free of real secrets.
- Record corrected or rejected agent output in docs/prompt-log.md.
- Preserve the other person's work and unrelated changes.
- Run relevant checks and report their actual results; never claim a failed check passed.
- Keep generated local `out/` ignored. Shared, checked starting data belongs in `shared/baseline/`; changes there require a new audit and fresh-checkout test.
- Do not commit or push unless explicitly requested.
