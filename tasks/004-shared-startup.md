# Task 004: Reproducible shared dashboard snapshot

## Goal

Make the selected NAV results and saved checkpoint available to a fresh checkout so a collaborator can view the same local dashboard without an OpenAI key. Later updates use that collaborator's own key and local `out/` state.

## Scope and constraints

- Share only the selected current extraction artifacts, their index, provisional review decisions, current statistics and a consistent copy of the NAV continuation database.
- Screen the package for credentials and contact patterns. Exclude flagged unused database text. Keep older runs and backups out of the package; do not alter the working database or existing outputs.
- Restore once into ignored `out/`, validate hashes and selected results, and never overwrite an existing local index and checkpoint.
- Provide `python harness/start.py` to restore and launch the local UI, plus `--check-only` for an offline startup check.
- Do not make NAV or model requests while building or checking the package.

## Acceptance

- A fresh clone restores 13 distinct selected advertisements and the same statistics as the source snapshot.
- The local UI serves those saved results without an API key.
- A subsequent startup leaves existing local updated state untouched.
- The restored database retains the saved feed continuation and can be used by the existing update command. Check continuation without a live NAV/model request; live continuation is a separate operation.
- Model-free tests, syntax checks and `git diff --check` pass.

## Status

Implemented and locally verified. The committed Git contents were tested through a fresh `git archive` export because `git clone` could not start its helper process in this desktop environment. The fresh copy restored thirteen selected ads, served the local UI and exercised the update entry point with injected offline discovery and zero model requests. See [the prompt log](../docs/prompt-log.md) for the actual checks. This task does not establish complete market coverage, extraction accuracy or live NAV continuation on another computer.
