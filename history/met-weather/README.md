# Hamar weather exercise

This earlier course exercise reads a MET Norway forecast and produces a checked JSON file. The original code, fixtures and task brief are kept together so the exercise can still run independently.

From the repository root, run these commands to use the saved forecast offline:

```powershell
cd history/met-weather
python harness/probe.py --offline
python eval/check_probe.py
python -m unittest discover -s harness -p test_probe.py
```

The first command after changing directories writes `out/probe.json` inside this exercise. The checker should print `PASS`.
