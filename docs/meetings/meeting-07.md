# Meeting 7 — Sunday, November 22, 2026

**Participants:** Rami and Yahye

## Discussion

- Discussed how to solve sections 3.1, 3.2 and 3.3 of the exam assignment (evaluation harness, safe operation and stress testing), and why each part is needed.
- Discussed the evaluation plan: first run the test cases offline without sending anything to the model, then change the prompt, run the model again online and compare the new results with our reference tests.
- Discussed secret management: where the API key is stored, how it is kept out of the repository, prompts and logs, and what happens if the key is missing.
- Discussed how to carry out the stress tests using the synthetic test advertisements in eval/stress/.

## Decisions and next steps

1. Yahye will write the safe operation section, starting with secret management.
2. Rami will run the stress tests that need the API key (prompt injection, non-IT advertisement and noise-only advertisement).
3. We will change the prompt, produce new results and compare them with the reference tests.