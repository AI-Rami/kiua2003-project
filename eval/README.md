# Evaluation

- `labeling-rules.md`: how we label skills by hand.
- `gold/gold.csv`: reference labels for the 13 ads. `checked` says whether the row has been checked line by line.
- `score.py`: compares the reference labels with the model output and writes `results/score.md` and `results/matches.csv`.

Run from the project root after `python harness/start.py` has restored the baseline once:

    python eval/score.py
    python eval/score.py --only-reviewed

The reference labels were first drafted with Claude (a different model from the extractor) and then checked and corrected by a group member.
