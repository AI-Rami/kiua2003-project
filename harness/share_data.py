"""Package and restore the reviewed current NAV state for a fresh checkout.

The package contains selected run artifacts and a consistent SQLite backup.
It never changes the working database or overwrites local runtime files.
"""

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import uuid

import nav_skill_summary as statistics
from nav_text import cleaned_input_issue


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "shared" / "baseline"
DB_TARGET = Path("out/nav_discovery/2026-11-01_12-02-24_UTC-3a430b9a/state.sqlite3")
ARTIFACTS = ("prepared_ad.txt", "request.json", "response.json",
             "validation.json", "result.json", "report.md")
STATISTICS = ("summary.json", "summary.md", "advertisements.md")
SECRET_PATTERNS = (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
                   re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{20,}"),
                   re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\b"))


class ShareError(Exception):
    """A diagnostic that contains no advertisement text or credentials."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def safe_relative(value):
    if not isinstance(value, str):
        raise ShareError("baseline: invalid target path")
    path = Path(value)
    if (not value.startswith("out/")
            or path.is_absolute() or ".." in path.parts or "\\" in value):
        raise ShareError("baseline: invalid target path")
    return path


def package_source(baseline, item):
    name = item.get("archive")
    if not isinstance(name, str) or not re.fullmatch(r"data/[0-9]{3}", name):
        raise ShareError("baseline: invalid package file name")
    return baseline / name


def check_secret(data):
    text = data.decode("utf-8")
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise ShareError("baseline: potential credential in selected data")


def audit_database(db):
    """Check all stored text for common credential patterns without displaying values."""
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' "
                               "AND name NOT LIKE 'sqlite_%'"):
        columns = [row[1] for row in db.execute(f'PRAGMA table_info("{table}")')]
        for row in db.execute(f'SELECT * FROM "{table}"'):
            for value in row:
                if isinstance(value, str):
                    check_secret(value.encode("utf-8"))


def current_files(root):
    index_path = root / "out/current/index.json"
    index_bytes = index_path.read_bytes()
    index = json.loads(index_bytes.decode("utf-8"))
    records, _ = statistics.load_current_records(index_path, root / "out/current")
    reviewed, _ = statistics.apply_selected_review(records)
    expected_count = len(reviewed)
    if expected_count == 0:
        raise ShareError("baseline: no selected advertisements")
    review_bytes = (root / "reviews/current-v2.json").read_bytes()
    check_secret(review_bytes)
    summary = json.loads((root / "out/statistics/summary.json").read_text(encoding="utf-8"))
    if (summary.get("advertisement_count") != expected_count
            or summary.get("source_index_sha256") != digest(index_bytes)
            or summary.get("review", {}).get("sha256") != digest(review_bytes)):
        raise ShareError("baseline: saved statistics do not match current results")
    selected = [entry for entry in index["entries"] if entry["status"] == "current"]
    paths = [Path("out/current/index.json")]
    for entry in selected:
        parent = safe_relative(entry["result_path"]).parent
        prepared = (root / parent / "prepared_ad.txt").read_text(encoding="utf-8")
        if cleaned_input_issue(prepared):
            raise ShareError("baseline: selected input failed contact screen")
        paths.extend(parent / name for name in ARTIFACTS)
    paths.extend(Path("out/statistics") / name for name in STATISTICS)
    if len(set(paths)) != len(paths):
        raise ShareError("baseline: duplicate selected path")
    return sorted(paths), expected_count, digest(index_bytes), digest(review_bytes)


def package(root=ROOT, baseline=BASELINE, db_target=DB_TARGET):
    """Create one immutable package; refuse to replace an existing package."""
    if baseline.exists():
        raise ShareError("baseline: package already exists")
    paths, count, index_hash, review_hash = current_files(root)
    source_db = root / db_target
    if not source_db.is_file():
        raise ShareError("baseline: saved NAV checkpoint is missing")
    staging = baseline.with_name(baseline.name + ".tmp-" + uuid.uuid4().hex[:8])
    staging.mkdir(parents=True)
    try:
        files = []
        for number, relative in enumerate(paths, 1):
            source = root / relative
            if not source.is_file() or source.is_symlink():
                raise ShareError("baseline: selected artifact is missing or linked")
            data = source.read_bytes()
            check_secret(data)
            archive_name = f"data/{number:03d}"
            target = staging / archive_name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append({"path": relative.as_posix(), "archive": archive_name,
                          "sha256": digest(data), "bytes": len(data)})

        db_copy = staging / "db" / "state.sqlite3"
        db_copy.parent.mkdir(parents=True)
        source = sqlite3.connect(f"file:{source_db.as_posix()}?mode=ro", uri=True)
        try:
            version_before = source.execute("PRAGMA data_version").fetchone()[0]
            target = sqlite3.connect(db_copy)
            try:
                source.backup(target)
                selected_uuids = {row["uuid"] for row in
                                  json.loads((root / "out/current/index.json").read_text(encoding="utf-8"))["entries"]
                                  if row["status"] == "current"}
                unsafe = [(ad_id, content_hash) for ad_id, content_hash, cleaned in
                          target.execute("SELECT uuid,content_hash,cleaned_text FROM captures")
                          if cleaned_input_issue(cleaned)]
                if any(ad_id in selected_uuids for ad_id, _ in unsafe):
                    raise ShareError("baseline: selected database capture failed contact screen")
                for ad_id, content_hash in unsafe:
                    target.execute("DELETE FROM captures WHERE uuid=? AND content_hash=?",
                                   (ad_id, content_hash))
                    target.execute("UPDATE capture_state SET outcome='review_blocked',"
                                   "reason='shared_snapshot_contact_screen',content_hash=NULL "
                                   "WHERE uuid=? AND content_hash=?", (ad_id, content_hash))
                unsafe_targeted = [(ad_id, content_hash) for ad_id, content_hash, cleaned in
                                   target.execute("SELECT uuid,content_hash,cleaned_text "
                                                  "FROM targeted_reprocess")
                                   if cleaned_input_issue(cleaned or "")]
                for ad_id, content_hash in unsafe_targeted:
                    target.execute("DELETE FROM targeted_reprocess "
                                   "WHERE uuid=? AND content_hash=?", (ad_id, content_hash))
                target.commit()
                audit_database(target)
                if target.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    raise ShareError("baseline: copied database integrity check failed")
                pending = target.execute("SELECT count(*) FROM processing_queue "
                                         "WHERE state NOT IN ('complete','blocked')").fetchone()[0]
                if pending:
                    raise ShareError("baseline: pending work requires saved attempts audit")
            finally:
                target.close()
            if source.execute("PRAGMA data_version").fetchone()[0] != version_before:
                raise ShareError("baseline: NAV checkpoint changed during packaging")
        finally:
            source.close()
        if digest((root / "out/current/index.json").read_bytes()) != index_hash:
            raise ShareError("baseline: selected index changed during packaging")
        db_hash = file_hash(db_copy)
        archive = staging / "db" / "state.sqlite3.gz"
        with db_copy.open("rb") as incoming, archive.open("wb") as outgoing:
            with gzip.GzipFile(filename="", mode="wb", fileobj=outgoing, mtime=0,
                               compresslevel=6) as compressed:
                shutil.copyfileobj(incoming, compressed)
        db_copy.unlink()
        manifest = {"schema_version": 1,
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                    "selected_advertisements": count,
                    "source_index_sha256": index_hash,
                    "review_sha256": review_hash,
                    "removed_unsafe_unselected_captures": len(unsafe),
                    "removed_unsafe_targeted_reprocess_rows": len(unsafe_targeted),
                    "files": files,
                    "database": {"path": db_target.as_posix(),
                                 "archive": "db/state.sqlite3.gz",
                                 "sha256": db_hash, "archive_sha256": file_hash(archive)}}
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                               encoding="utf-8")
        staging.rename(baseline)
        return manifest
    except Exception:
        shutil.rmtree(staging)
        raise


def restore(root=ROOT, baseline=BASELINE, *, validate=True):
    """Populate a fresh checkout; leave an existing local index and DB alone."""
    try:
        manifest_bytes = (baseline / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise ShareError("baseline: manifest is missing or invalid") from None
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
        raise ShareError("baseline: unsupported manifest")
    if digest((root / "reviews/current-v2.json").read_bytes()) != manifest.get("review_sha256"):
        raise ShareError("baseline: review decisions differ from shared data")
    db_info = manifest.get("database")
    if not isinstance(db_info, dict) or db_info.get("archive") != "db/state.sqlite3.gz":
        raise ShareError("baseline: invalid database entry")
    db_path = safe_relative(db_info.get("path"))
    if db_path != DB_TARGET:
        raise ShareError("baseline: unexpected database target")
    index_path = root / "out/current/index.json"
    target_db = root / db_path
    if index_path.is_file() and target_db.is_file():
        state = "existing"
    else:
        if (not manifest["files"] or not all(isinstance(item, dict) for item in manifest["files"])
                or len({item.get("path") for item in manifest["files"]}) != len(manifest["files"])):
            raise ShareError("baseline: invalid file list")
        for item in manifest["files"]:
            relative = safe_relative(item.get("path"))
            if not (relative.as_posix().startswith("out/current/")
                    or relative.as_posix().startswith("out/statistics/")):
                raise ShareError("baseline: unexpected file target")
            source = package_source(baseline, item)
            if not source.is_file() or source.is_symlink() or file_hash(source) != item.get("sha256"):
                raise ShareError("baseline: selected artifact hash mismatch")
            destination = root / relative
            if destination.exists() and file_hash(destination) != item["sha256"]:
                raise ShareError("baseline: existing local file differs; nothing overwritten")
        archive = baseline / db_info["archive"]
        if not archive.is_file() or file_hash(archive) != db_info.get("archive_sha256"):
            raise ShareError("baseline: database archive hash mismatch")
        if target_db.exists() and file_hash(target_db) != db_info.get("sha256"):
            raise ShareError("baseline: existing local database differs; nothing overwritten")
        for item in manifest["files"]:
            destination = root / safe_relative(item["path"])
            if destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".tmp-" + uuid.uuid4().hex[:8])
            try:
                shutil.copyfile(package_source(baseline, item), temporary)
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
        if not target_db.exists():
            target_db.parent.mkdir(parents=True, exist_ok=True)
            temporary = target_db.with_name(target_db.name + ".tmp-" + uuid.uuid4().hex[:8])
            try:
                with gzip.open(archive, "rb") as incoming, temporary.open("wb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing)
                if file_hash(temporary) != db_info["sha256"]:
                    raise ShareError("baseline: restored database hash mismatch")
                os.replace(temporary, target_db)
            finally:
                temporary.unlink(missing_ok=True)
        state = "restored"
    if validate:
        records, _ = statistics.load_current_records(index_path, root / "out/current")
        statistics.apply_selected_review(records)
        if state == "restored" and len(records) != manifest.get("selected_advertisements"):
            raise ShareError("baseline: restored advertisement count differs")
        connection = sqlite3.connect(f"file:{target_db.as_posix()}?mode=ro", uri=True)
        try:
            if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ShareError("baseline: runtime database integrity check failed")
        finally:
            connection.close()
        return state, len(records)
    return state, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("package", "check"), required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "package":
            result = package()
            print(f"Shared baseline: {result['selected_advertisements']} selected ads; "
                  f"{result['removed_unsafe_unselected_captures']} unused captures and "
                  f"{result['removed_unsafe_targeted_reprocess_rows']} old targeted rows excluded")
        else:
            state, count = restore()
            print(f"Shared baseline: {state}; {count} selected ads")
    except (ShareError, OSError, sqlite3.Error, ValueError) as exc:
        print(f"Shared baseline failed: {str(exc) if isinstance(exc, ShareError) else type(exc).__name__}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
