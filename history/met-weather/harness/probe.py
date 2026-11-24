"""Retrieve and cache MET Norway's Hamar forecast using only the standard library."""

import argparse
import gzip
import json
import math
import sys
import zlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
SOURCE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.7945&lon=11.0680"
USER_AGENT = "kiua2003-weather-probe/0.1 https://github.com/AI-Rami/kiua2003-project"
SOURCE_PATH = ROOT / "fixtures" / "met_hamar.json"
METADATA_PATH = ROOT / "fixtures" / "met_hamar.metadata.json"
OUTPUT_PATH = ROOT / "out" / "probe.json"
TIMEOUT = 30


def transform(raw):
    """Validate required source fields and preserve their values in the output."""
    try:
        source = json.loads(raw)
        entries = source["properties"]["timeseries"]
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f"Invalid source JSON or missing properties.timeseries: {error}") from error
    if not isinstance(entries, list) or not entries:
        raise ValueError("properties.timeseries must be a non-empty list")
    items = []
    for index, entry in enumerate(entries):
        try:
            date = entry["time"]
            temperature = entry["data"]["instant"]["details"]["air_temperature"]
        except (KeyError, TypeError) as error:
            raise ValueError(f"timeseries[{index}] missing required source field: {error}") from error
        if not isinstance(date, str) or not date:
            raise ValueError(f"timeseries[{index}].time must be a timestamp")
        try:
            datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"timeseries[{index}].time is not an ISO timestamp") from error
        if (isinstance(temperature, bool) or not isinstance(temperature, (int, float))
                or (isinstance(temperature, float) and not math.isfinite(temperature))):
            raise ValueError(f"timeseries[{index}] air_temperature must be a finite number")
        items.append({"title": "Hamar weather forecast", "date": date,
                      "temperature_c": temperature})
    return {"source_url": SOURCE_URL, "items": items}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8")


def read_metadata():
    if not METADATA_PATH.exists():
        return {}
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or metadata.get("source_url") != SOURCE_URL:
        raise ValueError("Saved metadata must be an object for the Hamar forecast URL")
    return metadata


def cache_fresh(metadata, now):
    expires = metadata.get("expires")
    if not expires:
        return False
    try:
        expiry = parsedate_to_datetime(expires)
        return expiry.tzinfo is not None and now < expiry
    except (ValueError, TypeError, OverflowError):
        return False


def decode_response(body, encoding):
    encoding = encoding.strip().lower()
    if encoding == "gzip":
        body = gzip.decompress(body)
    elif encoding == "deflate":
        try:
            body = zlib.decompress(body)
        except zlib.error:
            body = zlib.decompress(body, -zlib.MAX_WBITS)
    elif encoding not in ("", "identity"):
        raise ValueError(f"Unsupported Content-Encoding: {encoding}")
    return body.decode("utf-8")


def retrieve(offline=False):
    if offline:
        if not SOURCE_PATH.exists():
            raise ValueError("Offline response unavailable: fixtures/met_hamar.json is missing")
        return SOURCE_PATH.read_text(encoding="utf-8"), "offline"

    metadata = read_metadata()
    cached = SOURCE_PATH.read_text(encoding="utf-8") if SOURCE_PATH.exists() else None
    if cached is not None:
        transform(cached)
    if cached is not None and cache_fresh(metadata, datetime.now(timezone.utc)):
        return cached, "cached (before Expires)"

    headers = {"User-Agent": USER_AGENT, "Accept": "application/json",
               "Accept-Encoding": "gzip, deflate"}
    if cached is not None and metadata.get("last_modified"):
        headers["If-Modified-Since"] = metadata["last_modified"]
    request = Request(SOURCE_URL, headers=headers)
    try:
        response = urlopen(request, timeout=TIMEOUT)
    except HTTPError as error:
        if error.code != 304:
            error.close()
            raise
        response = error

    with response:
        status = response.code
        response_headers = response.headers
        if status == 304:
            if cached is None:
                raise ValueError("MET returned 304 but no saved response is available")
            raw = cached
            mode = "cached (304 Not Modified)"
        elif status in (200, 203):
            raw = decode_response(response.read(), response_headers.get("Content-Encoding", ""))
            transform(raw)
            mode = "downloaded"
            if status == 203:
                print("WARNING: MET returned 203 (beta or deprecated product)", file=sys.stderr)
        else:
            raise ValueError(f"Unexpected MET HTTP status: {status}")

        checked_at = datetime.now(timezone.utc).isoformat()
        metadata.update({
            "source_url": SOURCE_URL,
            "retrieved_at": metadata.get("retrieved_at", checked_at) if status == 304 else checked_at,
            "checked_at": checked_at,
            "expires": response_headers.get("Expires"),
            "last_modified": response_headers.get("Last-Modified", metadata.get("last_modified"))
                             if status == 304 else response_headers.get("Last-Modified"),
            "attribution": "Weather data from MET Norway (Norwegian Meteorological Institute).",
            "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "terms_url": "https://api.met.no/doc/TermsOfService",
            "changes": "Original response preserved; output selects timestamps and air temperatures.",
        })
    if status != 304:
        SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SOURCE_PATH.open("w", encoding="utf-8", newline="") as handle:
            handle.write(raw)
    write_json(METADATA_PATH, metadata)
    return raw, mode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use saved response without network requests")
    args = parser.parse_args()
    try:
        raw, mode = retrieve(args.offline)
        output = transform(raw)
        write_json(OUTPUT_PATH, output)
    except (OSError, ValueError, TypeError, URLError, zlib.error) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Wrote out/probe.json: {len(output['items'])} forecasts ({mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
