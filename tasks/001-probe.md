## Goal

Build `harness/probe.py` to retrieve MET Norway's weather forecast for a fixed point in Hamar, save the original response, and produce `out/probe.json`.
Support an offline run using the saved response.

## Context

Read `AGENTS.md` and `eval/check_probe.py`.
Use these official documentation links:

- https://api.met.no/doc/GettingStarted
- https://api.met.no/doc/TermsOfService

Use this forecast URL:

https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.7945&lon=11.0680

The checker was already run before implementation.
It failed because `out/probe.json` was missing.

## Constraints

- Python 3 standard library only.
- Do not change `eval/` or its checker.
- Use public weather data without personal data.
- Identify requests with this User-Agent:
  `kiua2003-weather-probe/0.1 https://github.com/AI-Rami/kiua2003-project`
- Follow MET's terms, including compression and caching.
- Save the original JSON as `fixtures/met_hamar.json`.
- Save source URL, retrieval time, Expires, Last-Modified, attribution, and license information alongside it.
- Reuse cached data until Expires. After expiry, use If-Modified-Since when Last-Modified is available. Handle 304 by reusing the cached response.
- Use a request timeout and report errors clearly.
- `--offline` must make no network requests. Fail clearly if the saved response is unavailable.
- Write paths relative to the project, and use UTF-8.

## Output

`out/probe.json` must contain:

- `source_url`: the forecast URL above.
- `items`: one item for each forecast timeseries entry.
- Each item contains:
  - `title`: "Hamar weather forecast"
  - `date`: the source entry's time
  - `temperature_c`: its `instant.details.air_temperature`

Preserve source timestamps and temperatures.
Fail clearly if required source fields are missing.

## Acceptance

1. Run `harness/probe.py`, then `eval/check_probe.py`. The checker must print `PASS`.
2. Repeat with `harness/probe.py --offline`. The checker must print `PASS`.
3. Confirm output times and temperatures match the saved source response.
4. Confirm `eval/` is unchanged.
5. Identify an available Python interpreter and report the exact commands and actual results.

## Out of scope

No webpage, AI summaries, scheduling, or changes to the final project problem.
