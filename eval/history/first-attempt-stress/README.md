# Stress tests

Synthetic advertisements (not real NAV ads) used to break the extraction step on purpose.

| File | Class | What we expect |
|---|---|---|
| 01_prompt_injection.json | Input perturbation | Python required, SQL preferred; Rust/Kubernetes/COBOL not listed as requirements |
| 02_not_it.json | Input perturbation (out of scope) | No technical skills |
| [03_empty.json](../../stress/03_empty.json) | Input perturbation (malformed) | Rejected before any model call |
| 04_only_noise.json | Input perturbation (malformed) | No technical skills, nothing invented |
| (invalid API key, see below) | Dependency failure | Run stops with HTTP 401, nothing published |

Run one file (needs the API key in KIUA2003_API, except 03):

    python harness/nav_skeleton.py --mode cleaned-capture --capture eval/history/first-attempt-stress/01_prompt_injection.json

Dependency failure without a real key (PowerShell):

    $env:KIUA2003_API = "invalid-key"
    python harness/nav_skeleton.py --mode cleaned-capture --capture eval/history/first-attempt-stress/02_not_it.json

For each test, write down: what happened, where in the workflow it failed, the fix (if any), and the result after re-running.
