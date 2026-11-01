"""Bounded NAV change-feed preview for active IT ads listing Innlandet."""

import argparse
import calendar
from datetime import datetime, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import re
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "out" / "nav_collection"
HOST = "pam-stilling-feed.nav.no"
BASE_URL = f"https://{HOST}"
TOKEN_URL = f"{BASE_URL}/api/publicToken"
FEED_URL = f"{BASE_URL}/api/v1/feed"
TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 16_000_000
JWT_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])")
CHANGE_TIME_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.(\d{1,9}))?(?:Z|[+-]\d{2}:\d{2})\Z"
)


class CollectionError(Exception):
    """An error safe to show without request or response content."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def utc_now():
    return datetime.now(timezone.utc)


def iso_utc(value):
    return value.isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_since(value):
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        elif value.endswith("Z"):
            parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise CollectionError("arguments: --since must be an ISO-8601 UTC date or timestamp") from None


def positive_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("limit must be a positive integer") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("limit must be a positive integer")
    return number


def validated_nav_url(value, kind):
    if not isinstance(value, str) or not value:
        raise CollectionError(f"{kind}: missing URL")
    try:
        parts = urlsplit(urljoin(BASE_URL + "/", value))
        safe_origin = (parts.scheme == "https" and parts.hostname == HOST and parts.port in (None, 443)
                       and parts.username is None and parts.password is None)
    except ValueError:
        raise CollectionError(f"{kind}: invalid URL") from None
    pattern = r"/api/v1/feed/[0-9a-fA-F-]{36}" if kind == "pagination" else r"/api/v1/feedentry/[0-9a-fA-F-]{36}"
    if (not safe_origin or parts.query or parts.fragment or not re.fullmatch(pattern, parts.path)):
        raise CollectionError(f"{kind}: unsafe NAV URL")
    try:
        uuid.UUID(parts.path.rsplit("/", 1)[1])
    except ValueError:
        raise CollectionError(f"{kind}: invalid URL UUID") from None
    return parts.geturl()


def request_bytes(opener, url, headers, stage, *, allow_empty=False):
    request = Request(url, headers=headers, method="GET")
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        if allow_empty and exc.code == 304:
            return None
        raise CollectionError(f"{stage}: HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise CollectionError(f"{stage}: network {type(exc).__name__}") from None
    if len(body) > MAX_RESPONSE_BYTES:
        raise CollectionError(f"{stage}: response exceeds memory limit")
    return body


def parse_json(data, stage):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise CollectionError(f"{stage}: invalid UTF-8 JSON") from None
    if not isinstance(value, dict):
        raise CollectionError(f"{stage}: expected JSON object")
    return value


def experimental_token(opener):
    raw = request_bytes(opener, TOKEN_URL, {"Accept": "text/plain"}, "token")
    try:
        content = raw.decode("utf-8")
    except UnicodeError:
        raise CollectionError("token: invalid UTF-8") from None
    matches = JWT_PATTERN.findall(content)
    if len(matches) != 1 or not matches[0] or re.search(r"\s", matches[0]):
        raise CollectionError("token: expected one nonempty JWT")
    return matches[0]


def normalized_label(value):
    return value.strip().casefold() if isinstance(value, str) and value.strip() else None


def field_match(ad, field, label, target):
    values = ad.get(field)
    if not isinstance(values, list) or not values:
        return None
    unknown = False
    for entry in values:
        if not isinstance(entry, dict):
            unknown = True
            continue
        value = normalized_label(entry.get(label))
        if value == target:
            return True
        if value is None:
            unknown = True
    return None if unknown else False


def relevance(detail):
    if detail.get("status") == "INACTIVE":
        return "inactive", None
    if detail.get("status") != "ACTIVE":
        return "unknown", "missing_or_other_status"
    ad = detail.get("ad_content")
    if not isinstance(ad, dict):
        return "unknown", "missing_or_invalid_ad_content"
    county = field_match(ad, "workLocations", "county", "innlandet")
    occupation = field_match(ad, "occupationCategories", "level1", "it")
    if county is True and occupation is True:
        return "match", None
    if county is False or occupation is False:
        reasons = {
            (False, True): "outside_innlandet_only",
            (True, False): "non_it_only",
            (False, False): "outside_innlandet_and_non_it",
            (False, None): "outside_innlandet_occupation_unknown",
            (None, False): "non_it_county_unknown",
        }
        return "nonmatch", reasons[(county, occupation)]
    reasons = {
        (None, True): "county_unknown_only",
        (True, None): "occupation_unknown_only",
        (None, None): "both_conditions_unknown",
    }
    return "unknown", reasons[(county, occupation)]


def usable_uuid(value):
    try:
        parsed = uuid.UUID(value) if isinstance(value, str) else None
        return str(parsed) if parsed else None
    except ValueError:
        return None


def change_timestamp(value):
    """Return a UTC second/nanosecond key and lossless UTC display value."""
    if not isinstance(value, str):
        return None
    match = CHANGE_TIME_PATTERN.fullmatch(value)
    if match is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        whole = parsed.replace(microsecond=0).astimezone(timezone.utc)
        seconds = calendar.timegm(whole.timetuple())
        nanos = int((match.group(1) or "").ljust(9, "0") or "0")
    except (ValueError, OverflowError):
        return None
    fraction = f".{nanos:09d}".rstrip("0") if nanos else ""
    display = whole.strftime("%Y-%m-%dT%H:%M:%S") + fraction + "Z"
    return (seconds, nanos), display


def page_candidates(items, seen_details, seen_uuids):
    counts = {"entries": len(items), "active": 0, "inactive": 0,
              "missing_or_other_status": 0, "skipped_no_usable_uuid": 0,
              "missing_change_timestamps": 0, "invalid_change_timestamps": 0,
              "earliest_valid_change_utc": None, "latest_valid_change_utc": None,
              "uuids_with_unusable_change_timestamp": 0, "ambiguous_latest_uuids": 0}
    candidates = []
    groups = {}
    valid_times = []
    for item in items:
        if not isinstance(item, dict):
            raise CollectionError("feed page: invalid items entry")
        header = item.get("_feed_entry")
        if not isinstance(header, dict):
            header = {}
        status = header.get("status")
        if status == "ACTIVE":
            counts["active"] += 1
        elif status == "INACTIVE":
            counts["inactive"] += 1
        else:
            counts["missing_or_other_status"] += 1
        raw_time = item.get("date_modified")
        changed = change_timestamp(raw_time)
        if raw_time is None or raw_time == "":
            counts["missing_change_timestamps"] += 1
        elif changed is None:
            counts["invalid_change_timestamps"] += 1
        else:
            valid_times.append(changed)
        ad_id = usable_uuid(header.get("uuid"))
        if ad_id is None:
            counts["skipped_no_usable_uuid"] += 1
            continue
        seen_uuids.add(ad_id)
        groups.setdefault(ad_id, []).append((item, status, changed))
    if valid_times:
        counts["earliest_valid_change_utc"] = min(valid_times, key=lambda t: t[0])[1]
        counts["latest_valid_change_utc"] = max(valid_times, key=lambda t: t[0])[1]
    for ad_id, entries in groups.items():
        if any(changed is None for _, _, changed in entries):
            counts["uuids_with_unusable_change_timestamp"] += 1
            continue
        latest_key = max(changed[0] for _, _, changed in entries)
        latest = [(item, status) for item, status, changed in entries if changed[0] == latest_key]
        if any(status != latest[0][1] or item.get("url") != latest[0][0].get("url")
               for item, status in latest[1:]):
            counts["ambiguous_latest_uuids"] += 1
            continue
        item, status = latest[0]
        if status == "ACTIVE" and ad_id not in seen_details:
            candidates.append((ad_id, item.get("url"), latest_key))
    candidates.sort(key=lambda candidate: (-candidate[2][0], -candidate[2][1], candidate[0]))
    return counts, candidates


def metadata_record(detail, ad_id):
    ad = detail["ad_content"]
    locations = [{"county": item.get("county"), "municipality": item.get("municipal")}
                 for item in ad["workLocations"] if isinstance(item, dict)]
    occupations = [{"level1": item.get("level1"), "level2": item.get("level2")}
                   for item in ad["occupationCategories"] if isinstance(item, dict)]
    source_url = next((ad[key] for key in ("sourceurl", "link")
                       if isinstance(ad.get(key), str) and ad[key].strip()), None)
    return {"uuid": ad_id, "status": "ACTIVE", "workLocations": locations,
            "occupationCategories": occupations, "published": ad.get("published"),
            "updated": ad.get("updated"), "source_url": source_url}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect(since, max_pages, max_details, *, opener=None, output_root=OUTPUT_ROOT):
    opener = opener or build_opener(NoRedirect())
    now = utc_now()
    run_id = now.strftime("%Y-%m-%d_%H-%M-%S_UTC-") + uuid.uuid4().hex[:8]
    run_dir = output_root / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except (OSError, FileExistsError):
        raise CollectionError("output: could not create a unique run directory") from None
    summary = {"label": "bounded preview of NAV changes since the chosen date; not all active ads or a synchronization checkpoint",
               "run_id": run_id, "starting_date_utc": iso_utc(since), "executed_at_utc": iso_utc(now),
               "max_pages": max_pages, "max_details": max_details, "page_requests": 0,
               "pages_fetched": 0, "detail_requests": 0, "distinct_uuids_encountered": 0,
               "matches": 0, "nonmatches": 0, "inactive_details": 0,
               "unknown_relevance": 0, "nonmatch_reasons": {}, "unknown_reasons": {},
               "missing_source_links": 0, "failures": [],
               "page_summaries": [], "pagination_ended": False, "stop_reason": None,
               "fetched_page_entries_left_unprocessed": False,
               "unprocessed_active_candidates_on_fetched_pages": 0, "status": "failed"}
    matches = []
    seen_uuids = set()
    seen_details = set()
    pending_on_page = 0
    try:
        token = experimental_token(opener)
        detail_headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
        feed_headers = {**detail_headers, "If-Modified-Since": format_datetime(since, usegmt=True)}
        page_url = FEED_URL
        for page_number in range(1, max_pages + 1):
            summary["page_requests"] += 1
            raw = request_bytes(opener, page_url, feed_headers, "feed page", allow_empty=True)
            if raw is None:
                summary["pagination_ended"] = True
                summary["stop_reason"] = "no_new_page_content"
                break
            page = parse_json(raw, "feed page")
            items = page.get("items")
            if not isinstance(items, list):
                raise CollectionError("feed page: items is missing or not an array")
            summary["pages_fetched"] += 1
            counts, candidates = page_candidates(items, seen_details, seen_uuids)
            counts["page"] = page_number
            summary["page_summaries"].append(counts)
            summary["distinct_uuids_encountered"] = len(seen_uuids)
            remaining = max_details - summary["detail_requests"]
            selected = candidates[:remaining]
            pending_on_page = len(selected)
            deferred = len(candidates) - len(selected)
            if deferred:
                summary["fetched_page_entries_left_unprocessed"] = True
                summary["unprocessed_active_candidates_on_fetched_pages"] += deferred
            for ad_id, detail_path, _ in selected:
                detail_url = validated_nav_url(detail_path, "detail")
                seen_details.add(ad_id)
                summary["detail_requests"] += 1
                detail = parse_json(request_bytes(opener, detail_url, detail_headers, "detail"), "detail")
                if usable_uuid(detail.get("uuid")) != ad_id:
                    raise CollectionError("detail: UUID missing or inconsistent")
                outcome, reason = relevance(detail)
                if outcome == "inactive":
                    summary["inactive_details"] += 1
                elif outcome == "unknown":
                    summary["unknown_relevance"] += 1
                    summary["unknown_reasons"][reason] = summary["unknown_reasons"].get(reason, 0) + 1
                elif outcome == "nonmatch":
                    summary["nonmatches"] += 1
                    summary["nonmatch_reasons"][reason] = summary["nonmatch_reasons"].get(reason, 0) + 1
                else:
                    ad = detail["ad_content"]
                    if not isinstance(ad.get("workLocations"), list) or not isinstance(ad.get("occupationCategories"), list):
                        raise CollectionError("detail: selection fields invalid")
                    record = metadata_record(detail, ad_id)
                    matches.append(record)
                    summary["matches"] += 1
                    if record["source_url"] is None:
                        summary["missing_source_links"] += 1
                pending_on_page -= 1
            if summary["detail_requests"] >= max_details:
                summary["stop_reason"] = "detail_limit"
                break
            next_path = page.get("next_url")
            if next_path is None:
                summary["pagination_ended"] = True
                summary["stop_reason"] = "pagination_end"
                break
            page_url = validated_nav_url(next_path, "pagination")
        if summary["stop_reason"] is None:
            summary["stop_reason"] = "page_limit"
        summary["status"] = "completed_bounded_preview"
        write_json(run_dir / "matches.json", matches)
        write_json(run_dir / "summary.json", summary)
        return run_dir, summary
    except Exception as exc:
        message = str(exc) if isinstance(exc, CollectionError) else f"internal: {type(exc).__name__}"
        summary["failures"].append(message)
        summary["stop_reason"] = "failure"
        if pending_on_page:
            summary["fetched_page_entries_left_unprocessed"] = True
            summary["unprocessed_active_candidates_on_fetched_pages"] += pending_on_page
        summary["distinct_uuids_encountered"] = len(seen_uuids)
        write_json(run_dir / "summary.json", summary)
        raise CollectionError(f"{message}; summary: {run_dir / 'summary.json'}") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "collect"), required=True)
    parser.add_argument("--since", help="ISO-8601 UTC date or timestamp; required for collect")
    parser.add_argument("--max-pages", type=positive_int, default=2)
    parser.add_argument("--max-details", type=positive_int, default=50)
    args = parser.parse_args(argv)
    if args.mode == "dry-run":
        print("Stages: validate --since (required for collect); get public JWT; read bounded NAV feed pages; select each page's newest timestamped entry per UUID; inspect ACTIVE details; classify; save sanitized matches and summary.")
        print(f"Limits: pages={args.max_pages}, details={args.max_details}, timeout={TIMEOUT_SECONDS}s per request, no retries.")
        print("Dry-run makes no network requests, reads no credentials and creates no files.")
        return 0
    if args.since is None:
        parser.error("--since is required for collect")
    try:
        since = parse_since(args.since)
        print(f"Starting date (UTC): {iso_utc(since)}")
        run_dir, summary = collect(since, args.max_pages, args.max_details)
    except CollectionError as exc:
        print(f"Collection failed: {exc}", file=sys.stderr)
        return 1
    print(f"Run directory: {run_dir}")
    print(f"Summary: {run_dir / 'summary.json'}")
    print(f"Matches: {run_dir / 'matches.json'}")
    print(f"Bounded preview: pages={summary['pages_fetched']}, detail requests={summary['detail_requests']}, matches={summary['matches']}, nonmatches={summary['nonmatches']}, inactive={summary['inactive_details']}, unknown={summary['unknown_relevance']}; stopped by {summary['stop_reason']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
