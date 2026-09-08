#!/usr/bin/env python3
"""Compare JobWatch scan JSON week-over-week.

Prints ONLY new/changed Warsaw + Plymouth people-manager hits vs the previous
snapshot. Exit 10 when there is nothing new to notify about.

Usage:
  python3 jobwatch-diff.py \\
    --current out/scan.json \\
    --previous out/scan-prev.json

  python3 jobwatch-diff.py --current out/scan.json --previous out/scan-prev.json \\
    --json out/diff.json

  # After a Wednesday ping (or a quiet week you still want as baseline):
  python3 jobwatch-diff.py --current out/scan.json --previous out/scan-prev.json \\
    --promote

  # Or point at a dated history file:
  python3 jobwatch-diff.py --current out/scan.json \\
    --previous out/history/2026-09-01.json

Identity key (stable): url if present, else title|employer|location (casefold).
Buckets compared: warsaw + plymouth only (manager lists already filtered by scan.py).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POCKETS = ("warsaw", "plymouth")


def job_key(j: dict[str, Any]) -> str:
    url = (j.get("url") or "").strip()
    if url:
        # strip trailing slash / opportunistic tracking noise
        return url.rstrip("/").lower()
    title = (j.get("title") or "").strip().casefold()
    employer = (j.get("employer") or "").strip().casefold()
    location = (j.get("location") or "").strip().casefold()
    return f"{title}|{employer}|{location}"


def load_scan(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing scan file: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a scan object")
    return data


def pocket_map(scan: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """pocket -> {key: job}"""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for pocket in POCKETS:
        jobs = scan.get(pocket) or []
        m: dict[str, dict[str, Any]] = {}
        for j in jobs:
            if not isinstance(j, dict):
                continue
            m[job_key(j)] = j
        out[pocket] = m
    return out


def fmt_job(j: dict[str, Any]) -> str:
    bits = [f"**{j.get('title') or '?'}** — {j.get('employer') or '?'}"]
    if j.get("location"):
        bits.append(str(j["location"]))
    if j.get("posted"):
        bits.append(f"posted {j['posted']}")
    if j.get("salary"):
        bits.append(str(j["salary"]))
    if j.get("education"):
        bits.append(str(j["education"]))
    if j.get("url"):
        bits.append(str(j["url"]))
    return " | ".join(bits)


def promote(current: Path, previous: Path, history_dir: Path | None) -> None:
    previous.parent.mkdir(parents=True, exist_ok=True)
    if history_dir is not None:
        history_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        hist = history_dir / f"{stamp}.json"
        # don't clobber same-day history if already written
        if not hist.exists():
            shutil.copy2(current, hist)
            print(f"history: {hist}", file=sys.stderr)
        else:
            # still refresh same-day snapshot
            shutil.copy2(current, hist)
            print(f"history refreshed: {hist}", file=sys.stderr)
    shutil.copy2(current, previous)
    print(f"promoted current → {previous}", file=sys.stderr)


def main() -> int:
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="JobWatch week-over-week scan diff")
    ap.add_argument(
        "--current",
        type=Path,
        default=root / "out" / "scan.json",
        help="this week's scan JSON (default: out/scan.json)",
    )
    ap.add_argument(
        "--previous",
        type=Path,
        default=root / "out" / "scan-prev.json",
        help="last baseline scan JSON (default: out/scan-prev.json)",
    )
    ap.add_argument("--json", dest="json_path", type=Path, help="write diff JSON")
    ap.add_argument(
        "--promote",
        action="store_true",
        help="after diff, copy --current over --previous (and dated history)",
    )
    ap.add_argument(
        "--history-dir",
        type=Path,
        default=root / "out" / "history",
        help="with --promote, also save dated copy here (default: out/history)",
    )
    ap.add_argument(
        "--no-history",
        action="store_true",
        help="with --promote, skip dated history file",
    )
    ap.add_argument(
        "--bootstrap",
        action="store_true",
        help="if --previous is missing, treat all current pocket jobs as baseline "
        "(unchanged), write previous=current, exit 10 (quiet). Use on first run.",
    )
    args = ap.parse_args()

    try:
        current = load_scan(args.current)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if not args.previous.exists():
        if args.bootstrap or args.promote:
            args.previous.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.current, args.previous)
            hist_dir = None if args.no_history else args.history_dir
            if hist_dir is not None:
                hist_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                shutil.copy2(args.current, hist_dir / f"{stamp}.json")
            print(
                f"bootstrapped baseline at {args.previous} "
                f"({sum(len(current.get(p) or []) for p in POCKETS)} pocket jobs). Quiet.",
                file=sys.stderr,
            )
            report = {
                "as_of": datetime.now(timezone.utc).isoformat(),
                "current": str(args.current),
                "previous": str(args.previous),
                "bootstrapped": True,
                "new": {"warsaw": [], "plymouth": []},
                "gone": {"warsaw": [], "plymouth": []},
                "unchanged_count": {
                    p: len(current.get(p) or []) for p in POCKETS
                },
            }
            if args.json_path:
                args.json_path.parent.mkdir(parents=True, exist_ok=True)
                args.json_path.write_text(json.dumps(report, indent=2))
                print(f"wrote {args.json_path}", file=sys.stderr)
            print("=== New Warsaw manager hits ===\n(none)")
            print("=== New Plymouth manager hits ===\n(none)")
            return 10
        print(
            f"error: previous scan missing: {args.previous}\n"
            f"hint: pass --bootstrap on first run, or copy a prior out/scan.json there.",
            file=sys.stderr,
        )
        return 2

    try:
        previous = load_scan(args.previous)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    cur_m = pocket_map(current)
    prev_m = pocket_map(previous)

    new: dict[str, list[dict[str, Any]]] = {p: [] for p in POCKETS}
    gone: dict[str, list[dict[str, Any]]] = {p: [] for p in POCKETS}
    unchanged_count: dict[str, int] = {}

    for pocket in POCKETS:
        ck, pk = cur_m[pocket], prev_m[pocket]
        new_keys = set(ck) - set(pk)
        gone_keys = set(pk) - set(ck)
        unchanged_count[pocket] = len(set(ck) & set(pk))
        new[pocket] = [ck[k] for k in sorted(new_keys, key=lambda x: ck[x].get("title") or x)]
        gone[pocket] = [pk[k] for k in sorted(gone_keys, key=lambda x: pk[x].get("title") or x)]

    report = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "current": str(args.current),
        "previous": str(args.previous),
        "current_as_of": current.get("as_of"),
        "previous_as_of": previous.get("as_of"),
        "new": new,
        "gone": gone,
        "unchanged_count": unchanged_count,
        "new_total": sum(len(v) for v in new.values()),
        "gone_total": sum(len(v) for v in gone.values()),
    }

    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(report, indent=2))
        print(f"wrote {args.json_path}", file=sys.stderr)

    print("=== New Warsaw manager hits ===")
    if new["warsaw"]:
        for j in new["warsaw"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    print("=== New Plymouth manager hits ===")
    if new["plymouth"]:
        for j in new["plymouth"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    if report["gone_total"]:
        print("=== Gone since previous (FYI) ===")
        for pocket in POCKETS:
            for j in gone[pocket]:
                print(f"- [{pocket}]", fmt_job(j))

    print(
        f"[summary] new={report['new_total']} gone={report['gone_total']} "
        f"unchanged={sum(unchanged_count.values())}",
        file=sys.stderr,
    )

    if args.promote:
        promote(
            args.current,
            args.previous,
            None if args.no_history else args.history_dir,
        )

    if report["new_total"] == 0:
        return 10
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
