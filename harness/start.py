"""Open the local NAV dashboard, restoring shared data on a fresh checkout."""

import argparse
import sqlite3

import nav_dashboard
from share_data import ShareError, restore


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--check-only", action="store_true",
                        help="restore and verify saved data without starting the server")
    args = parser.parse_args(argv)
    try:
        state, count = restore()
    except (ShareError, OSError, sqlite3.Error, ValueError) as exc:
        print(f"Startup failed: {str(exc) if isinstance(exc, ShareError) else type(exc).__name__}")
        return 1
    print(f"Saved data: {state}; selected advertisements: {count}", flush=True)
    if args.check_only:
        return 0
    return nav_dashboard.main(["--port", str(args.port)])


if __name__ == "__main__":
    raise SystemExit(main())
