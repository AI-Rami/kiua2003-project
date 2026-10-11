"""Validate out/probe.json without fetching or creating forecast data."""

import json
import math
import sys
from datetime import date, datetime
from pathlib import Path


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "out" / "probe.json"
SOURCE_PREFIX = "https://api.met.no/weatherapi/locationforecast/2.0/"


def fail(message):
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def valid_iso_date(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        pass
    # Accept ISO timestamps with a UTC Z suffix on older Python versions too.
    timestamp = value[:-1] + "+00:00" if value.endswith("Z") else value
    # ISO date/time separators are T (or t) and the conventional space.
    if not any(separator in timestamp for separator in ("T", "t", " ")):
        return False
    try:
        datetime.fromisoformat(timestamp)
        return True
    except ValueError:
        return False


def main():
    try:
        with OUTPUT_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return fail("out/probe.json is missing.")
    except (OSError, UnicodeError, ValueError) as error:
        return fail(f"Could not read out/probe.json as JSON: {error}")

    if not isinstance(data, dict):
        return fail("The JSON root must be an object.")

    source_url = data.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith(SOURCE_PREFIX):
        return fail(f"source_url must start with {SOURCE_PREFIX}")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        return fail("items must be a list containing at least one forecast.")

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return fail(f"items[{index}] must be an object.")

        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            return fail(f"items[{index}].title must be a non-empty string.")

        if not valid_iso_date(item.get("date")):
            return fail(f"items[{index}].date must be a valid ISO date/time string.")

        temperature = item.get("temperature_c")
        if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
            return fail(f"items[{index}].temperature_c must be a number, not a boolean.")
        if isinstance(temperature, float) and not math.isfinite(temperature):
            return fail(f"items[{index}].temperature_c must be finite.")

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
