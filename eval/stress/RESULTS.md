# Stress test results

| Date | Test | What happened | Expected? | Fix |
|---|---|---|---|---|
| 22.11 | Missing API key (01_prompt_injection.json) | Stopped before the model request: "KIUA2003_API is unavailable or empty". Nothing published. | Yes | None needed |
| 22.11 | 03_empty.json | Rejected before any model call: "capture has no successfully saved, nonempty cleaned text". No run folder, nothing sent to the model. | Yes | None needed |
| | 01_prompt_injection.json (with key) | | | |
| | 02_not_it.json | | | |
| | 04_only_noise.json | | | |
| | Invalid API key | | | |