# Run the four offline NAV stress tests

From the project root, run:

```powershell
python -B -u harness/test_nav_stress.py
```

The [test program](../../harness/test_nav_stress.py) reads [03_empty.json](03_empty.json) for the empty-ad case. It sets up the Oslo ad, the rate limit and the unusable AI reply in Python. No API key is needed.

Read the [stress-test report](../../docs/stress/2026-11-23/report.md) for the results before and after the repair. The [first attempt](../history/first-attempt-stress/README.md) contains the earlier examples and [observations](../history/first-attempt-stress/RESULTS.md).
