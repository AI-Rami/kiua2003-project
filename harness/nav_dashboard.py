"""Local NAV skill dashboard over the selected saved results.

The server binds only to loopback. Its update button calls nav_update.run_update().
"""

import argparse
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import parse_qs, urlsplit

import nav_skill_summary as statistics
import nav_update as update
from nav_text import cleaned_input_issue


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"
LAST_UPDATE = ROOT / "out" / "ui" / "last_update.json"
PERIODS = {"all", "this_month", "previous_month", "this_year", "custom"}
STATUSES = {"all", "active", "inactive"}


class DashboardError(Exception):
    """A message safe to return to the local browser."""


def parse_day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise DashboardError("Enter dates as YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise DashboardError("Enter a valid calendar date.") from None


def selected_range(period, start, end, today):
    if period == "all":
        return None, None
    if period == "custom":
        first, last = parse_day(start), parse_day(end)
        if first > last:
            raise DashboardError("The start date must be on or before the end date.")
        return first, last
    if period == "this_year":
        return date(today.year, 1, 1), date(today.year, 12, 31)
    first = date(today.year, today.month, 1)
    if period == "previous_month":
        first = (first - timedelta(days=1)).replace(day=1)
    next_month = date(first.year + 1, 1, 1) if first.month == 12 else date(first.year, first.month + 1, 1)
    return first, next_month - timedelta(days=1)


def evidence_for_display(value):
    if not isinstance(value, str) or cleaned_input_issue(value) is not None:
        return None
    return value


def support_rows(records):
    support = {}
    seen = {}
    for record in records:
        for item in record["items"]:
            kind = item["mention_type"]
            skills = item["skills"]
            if item["relationship"] == "single":
                group = "qualification" if kind == "candidate_qualification" else "other"
                key = group + ":" + skills[0]
            elif kind == "candidate_qualification":
                key = "qualification_or:" + json.dumps(skills, ensure_ascii=False)
            else:
                key = "other_or:" + kind + ":" + json.dumps(skills, ensure_ascii=False)
            row = {"uuid": record["uuid"], "title": record.get("title"),
                   "publication_date": record.get("publication_date"),
                   "activity_status": record.get("activity_status", "UNKNOWN"),
                   "classification": item["classification"], "mention_type": kind,
                   "skill_evidence": evidence_for_display(item["skill_evidence"]),
                   "classification_context": evidence_for_display(item.get("classification_context"))
                   if item.get("classification_context") else None,
                   "source_url": record["source_url"]}
            identity = (row["uuid"], row["classification"], row["mention_type"],
                        row["skill_evidence"], row["classification_context"])
            if identity not in seen.setdefault(key, set()):
                seen[key].add(identity)
                support.setdefault(key, []).append(row)
    return support


def dashboard_data(records, status_counts, params, *, today=None, quality=None):
    """Recount saved v2 items after filters; never filter precomputed totals."""
    today = today or datetime.now().astimezone().date()
    period = params.get("period", "all")
    status = params.get("status", "all")
    search = params.get("search", "").strip()
    if period not in PERIODS or status not in STATUSES or len(search) > 80:
        raise DashboardError("Invalid filter selection.")
    first, last = selected_range(period, params.get("from"), params.get("to"), today)
    selected = []
    missing_date_excluded = 0
    for record in records:
        if status != "all" and record.get("activity_status", "UNKNOWN").lower() != status:
            continue
        published = record.get("publication_date")
        if first is not None:
            if not published:
                missing_date_excluded += 1
                continue
            day = parse_day(published)
            if day < first or day > last:
                continue
        items = record["items"]
        if search:
            items = [item for item in items
                     if any(search.casefold() in skill.casefold() for skill in item["skills"])]
            if not items:
                continue
        selected.append({**record, "items": items})
    aggregated = statistics.aggregate(selected)
    selected_dates = sorted(record["publication_date"] for record in selected if record.get("publication_date"))
    saved_date_count = sum(bool(record.get("publication_date")) for record in records)
    tables = {
        "qualification": [{**row, "id": "qualification:" + row["skill"]}
                          for row in aggregated["qualification_single_skills"]],
        "alternatives": [{**row, "id": "qualification_or:" + json.dumps(row["skills"], ensure_ascii=False)}
                         for row in aggregated["qualification_or_groups"]],
        "other": [{**row, "id": "other:" + row["skill"]}
                  for row in aggregated["other_single_skills"]],
        "other_alternatives": [{**row, "id": "other_or:" + row["mention_type"] + ":" +
                                json.dumps(row["skills"], ensure_ascii=False)}
                               for row in aggregated["other_or_groups"]],
    }
    return {
        "cards": {"advertisements": len(selected),
                  "qualification_skill_names": len(tables["qualification"]),
                  "alternative_groups": len(tables["alternatives"])},
        "tables": tables, "support": support_rows(selected),
        "filter": {"period": period, "status": status, "search": search,
                   "from": first.isoformat() if first else (selected_dates[0] if selected_dates else None),
                   "to": last.isoformat() if last else (selected_dates[-1] if selected_dates else None),
                   "missing_dates_excluded": missing_date_excluded},
        "coverage": {"selected_dataset_ads": len(records),
                     "saved_date_count": saved_date_count,
                     "note": "Based on collected advertisements. This is not complete Innlandet market coverage."},
        "quality": quality or {"status_counts": status_counts},
    }


def quality_state(index_path=update.DEFAULT_INDEX, db_path=update.DEFAULT_DB):
    try:
        index = update.load_index(index_path)
    except update.UpdateError:
        raise DashboardError("The selected-result index is unavailable.") from None
    entries = index["entries"]
    statuses = {name: sum(row.get("status") == name for row in entries)
                for name in statistics.STATUSES}
    selected = [row for row in entries if row.get("status") == "current"]
    result = {"status_counts": statuses,
              "auto_contact_checked": sum(row.get("capture_review_state") == "auto_contact_checked"
                                          for row in selected),
              "earlier_cleaner_accepted": sum(row.get("capture_review_state") == "pending_human_review"
                                              for row in selected),
              "queue_remaining": None, "scan_phase": "unavailable", "feed_end_reached": None}
    if db_path.is_file():
        try:
            db = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=2)
            try:
                result["queue_remaining"] = db.execute(
                    "SELECT count(*) FROM processing_queue WHERE state NOT IN ('complete','blocked')").fetchone()[0]
                phase = db.execute("SELECT value FROM state WHERE key='phase'").fetchone()
                end = db.execute("SELECT value FROM state WHERE key='scan_complete'").fetchone()
                result["scan_phase"] = json.loads(phase[0]) if phase else "unavailable"
                result["feed_end_reached"] = bool(json.loads(end[0])) if end else None
            finally:
                db.close()
        except (sqlite3.Error, ValueError, OSError):
            pass
    return result


class UpdateManager:
    def __init__(self, *, run_fn=None, index_path=update.DEFAULT_INDEX,
                 current_root=update.DEFAULT_CURRENT, db_path=update.DEFAULT_DB,
                 state_path=LAST_UPDATE):
        self.run_fn = run_fn or update.run_update
        self.index_path = Path(index_path)
        self.current_root = Path(current_root)
        self.db_path = Path(db_path)
        self.state_path = Path(state_path)
        self.lock = threading.Lock()
        self.running = False
        self.frozen = None
        self.last = self._load_last()

    def _load_last(self):
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except (OSError, UnicodeError, ValueError):
            return None

    def snapshot(self):
        with self.lock:
            return {"running": self.running, "last": dict(self.last) if self.last else None}

    def records(self):
        with self.lock:
            if self.running and self.frozen is not None:
                return self.frozen
        return statistics.load_current_records(self.index_path, self.current_root)

    def _progress(self, event):
        stage = event.get("stage")
        labels = {"discovery": "Reading NAV updates", "feed_page": "Reading NAV updates",
                  "detail": "Checking advertisements and preparing text", "detail_unavailable": "Checking advertisements",
                  "extraction": "Extracting skills", "published": "Refreshing statistics",
                  "failed": "Checking an advertisement", "complete": "Finishing update"}
        with self.lock:
            if self.last is not None:
                self.last["stage"] = labels.get(stage, "Preparing text")
                if stage == "feed_page":
                    self.last["pages"] = event.get("pages", 0)
                elif stage == "detail":
                    self.last["details"] = event.get("details", 0)
                elif stage == "extraction":
                    self.last["extractions"] = self.last.get("extractions", 0) + 1

    def start(self):
        with self.lock:
            if self.running:
                return False
        # Validate and freeze visible tables before the worker can change the index.
        frozen = statistics.load_current_records(self.index_path, self.current_root)
        with self.lock:
            if self.running:
                return False
            self.frozen = frozen
            self.running = True
            self.last = {"status": "running", "stage": "Preparing update",
                         "started_at_utc": datetime.now(timezone.utc).isoformat(),
                         "pages": 0, "details": 0, "extractions": 0}
        threading.Thread(target=self._work, name="nav-dashboard-update", daemon=True).start()
        return True

    def _work(self):
        try:
            report = self.run_fn(self.db_path, progress=self._progress)
            status = report.get("status", "failed")
            safe = {key: report.get(key) for key in
                    ("pages", "details", "extraction_requests", "processed", "reused", "blocked",
                     "failed", "pending", "feed_end_reached", "stop_reason", "statistics_ads")}
            completed = {"status": status, "stage": "Finished", "report": safe}
        except Exception as exc:
            message = str(exc) if isinstance(exc, update.UpdateError) else type(exc).__name__
            completed = {"status": "failed", "stage": "Update failed", "error": message}
        completed["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        with self.lock:
            completed["started_at_utc"] = self.last.get("started_at_utc") if self.last else None
            self.last = completed
            self.running = False
            self.frozen = None
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            update.write_index(self.state_path, completed)
        except OSError:
            pass  # The SQLite checkpoint still retains workflow progress.


class DashboardHandler(BaseHTTPRequestHandler):
    manager = None

    def log_message(self, format, *args):
        pass

    def send_json(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlsplit(self.path)
        if route.path == "/api/status":
            try:
                quality = quality_state(self.manager.index_path, self.manager.db_path)
            except DashboardError as exc:
                self.send_json(503, {"error": str(exc)})
                return
            self.send_json(200, {**self.manager.snapshot(), "quality": quality})
            return
        if route.path == "/api/data":
            try:
                params = {key: values[-1] for key, values in parse_qs(route.query, keep_blank_values=True).items()}
                records, counts = self.manager.records()
                value = dashboard_data(records, counts, params,
                                       quality=quality_state(self.manager.index_path, self.manager.db_path))
            except DashboardError as exc:
                self.send_json(400, {"error": str(exc)})
                return
            except (statistics.SummaryError, OSError, ValueError):
                self.send_json(503, {"error": "Saved statistics are temporarily unavailable."})
                return
            self.send_json(200, value)
            return
        files = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/app.css": ("app.css", "text/css; charset=utf-8"),
                 "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if route.path not in files:
            self.send_error(404)
            return
        name, mime = files[route.path]
        try:
            body = (UI / name).read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/update":
            self.send_error(404)
            return
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if (self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}"
                or self.headers.get("Origin") not in (None, expected)
                or self.headers.get("Content-Type", "").split(";", 1)[0] != "application/json"):
            self.send_json(403, {"error": "Update request must come from this dashboard."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > 1024:
            self.send_json(400, {"error": "Invalid update request."})
            return
        body = self.rfile.read(length)
        if body not in (b"", b"{}"):
            self.send_json(400, {"error": "Update settings are not accepted here."})
            return
        try:
            started = self.manager.start()
        except (statistics.SummaryError, OSError, ValueError):
            self.send_json(503, {"error": "Saved statistics are unavailable; update was not started."})
            return
        if not started:
            self.send_json(409, {"error": "An update is already running."})
            return
        self.send_json(202, self.manager.snapshot())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    DashboardHandler.manager = UpdateManager()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), DashboardHandler)
    print(f"Dashboard: http://127.0.0.1:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
