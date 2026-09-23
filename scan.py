#!/usr/bin/env python3
"""JobWatch cheap scan — HTTP/API first, no browser.

Usage:
  python3 scan.py
  python3 scan.py --json out/scan.json
  python3 scan.py --source 1stsource,everwise,slate,lakecity,zimmer,hershey,ats,interra
  python3 scan.py --all
  python3 scan.py --source ...,linkedin   # optional LinkedIn guest CSA sweep

Exit 10 if BOTH manager (warsaw+plymouth) AND CSA (warsaw_csa+plymouth_csa)
notify pockets are empty.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from lib.adp import fetch_lake_city_adp  # noqa: E402
from lib.filters import NOTIFY_POCKETS, classify, has_bachelors_wall  # noqa: E402
from lib.hershey import fetch_hershey  # noqa: E402
from lib.html_careers import fetch_purity_gas  # noqa: E402
from lib.linkedin_guest import fetch_csa_searches  # noqa: E402
from lib.models import Job  # noqa: E402
from lib.phenom import fetch_phenom  # noqa: E402
from lib.talentbrew import fetch_ats  # noqa: E402
from lib.ultipro import fetch_1st_source, fetch_interra  # noqa: E402
from lib.workday import fetch_all_workday_pages  # noqa: E402


SOURCES = {
    "1stsource": "1st Source Ultipro JSON",
    "interra": "Interra CU Ultipro JSON",
    "everwise": "Everwise Workday CXS",
    "slate": "Slate Auto Workday CXS",
    "lakecity": "Lake City Bank ADP JSON",
    "zimmer": "Zimmer Biomet Phenom widgets",
    "hershey": "Hershey SuccessFactors HTML search",
    "ats": "ATS Advanced Technology Services TalentBrew",
    "purity": "Purity Gas HTML careers",
    "linkedin": "LinkedIn guest CSA keyword sweep (optional/fragile)",
}

DEFAULT = "1stsource,everwise,slate,lakecity,zimmer,hershey,ats,interra,purity,linkedin"


def gather(selected: list[str]) -> tuple[list[Job], dict[str, str]]:
    jobs: list[Job] = []
    errors: dict[str, str] = {}

    def run(name: str, fn):
        try:
            batch = fn()
            jobs.extend(batch)
            print(f"[ok] {name}: {len(batch)}", file=sys.stderr)
        except Exception as e:
            errors[name] = str(e)
            print(f"[err] {name}: {e}", file=sys.stderr)

    if "1stsource" in selected:
        run("1stsource", lambda: fetch_1st_source(top=100))
    if "interra" in selected:
        run("interra", lambda: fetch_interra(top=100))
    if "everwise" in selected:
        run("everwise", lambda: fetch_all_workday_pages("everwise", search_text="", page_size=20, max_pages=5))
    if "slate" in selected:
        run("slate", lambda: fetch_all_workday_pages("slate", search_text="Warsaw", page_size=20, max_pages=5))
    if "lakecity" in selected:
        run("lakecity", fetch_lake_city_adp)
    if "zimmer" in selected:
        run("zimmer", lambda: fetch_phenom("zimmer", state="Indiana", size=50))
    if "hershey" in selected:
        run("hershey", lambda: fetch_hershey(location="Plymouth, IN"))
    if "ats" in selected:
        run("ats", lambda: fetch_ats(location="Indiana", per_page=50))
    if "purity" in selected:
        run("purity", fetch_purity_gas)
    if "linkedin" in selected:
        run("linkedin", fetch_csa_searches)
    return jobs, errors


def fmt_job(j: Job) -> str:
    bits = [f"**{j.title}** — {j.employer}"]
    if j.location:
        bits.append(j.location)
    if j.posted:
        bits.append(f"posted {j.posted}")
    if j.salary:
        bits.append(j.salary)
    if j.education:
        bits.append(j.education)
    if has_bachelors_wall(j):
        bits.append("[bachelor wall?]")
    if j.url:
        bits.append(j.url)
    return " | ".join(bits)


def _dump_jobs(jobs: list[Job]) -> list[dict]:
    return [j.to_dict() for j in jobs]


def main() -> int:
    ap = argparse.ArgumentParser(description="JobWatch HTTP job scan")
    ap.add_argument("--source", default=DEFAULT, help="comma list: " + ",".join(SOURCES))
    ap.add_argument("--json", dest="json_path", help="write full JSON report")
    ap.add_argument("--all", action="store_true", help="also print near-miss / out-of-radius + other")
    ap.add_argument("--raw", action="store_true", help="print every fetched job before filtering")
    args = ap.parse_args()
    selected = [s.strip() for s in args.source.split(",") if s.strip()]
    unknown = [s for s in selected if s not in SOURCES]
    if unknown:
        print("unknown sources:", ", ".join(unknown), file=sys.stderr)
        return 2

    jobs, errors = gather(selected)
    buckets = classify(jobs)

    report = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "sources": selected,
        "counts": {k: len(v) for k, v in buckets.items()},
        "fetched": len(jobs),
        "errors": errors,
        "browser_fallback": [],
        "warsaw": _dump_jobs(buckets["warsaw"]),
        "plymouth": _dump_jobs(buckets["plymouth"]),
        "warsaw_csa": _dump_jobs(buckets["warsaw_csa"]),
        "plymouth_csa": _dump_jobs(buckets["plymouth_csa"]),
        "near_miss": _dump_jobs(buckets["near_miss"]),
        "near_miss_csa": _dump_jobs(buckets["near_miss_csa"]),
        "other_in_pocket": _dump_jobs(buckets["other"]),
    }
    # Known browser-only targets (not in this fetch set)
    report["browser_fallback"].extend(
        [
            "walmart: careers.walmart.com SPA + bot wall — browserUse",
            "pregis: Dayforce jobs.dayforcehcm.com/api/geo/.../jobposting/search returns 403 without browser client",
            "wildman: secure*.entertimeonline.com Career Search SPA — no durable public JSON yet",
            "indeed: RSS/search 403",
            "linkedin: guest HTML cards wired as optional --source linkedin (fragile; rate-limits)",
        ]
    )

    if args.json_path:
        path = Path(args.json_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2))
        print(f"wrote {path}", file=sys.stderr)

    if args.raw:
        for j in jobs:
            print("RAW", fmt_job(j))

    print("=== Warsaw (manager-ish, ~10mi) ===")
    if buckets["warsaw"]:
        for j in buckets["warsaw"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    print("=== Plymouth (manager-ish, ~10mi) ===")
    if buckets["plymouth"]:
        for j in buckets["plymouth"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    print("=== Warsaw CSA (entry/mid systems analyst, ~10mi) ===")
    if buckets["warsaw_csa"]:
        for j in buckets["warsaw_csa"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    print("=== Plymouth CSA (entry/mid systems analyst, ~10mi) ===")
    if buckets["plymouth_csa"]:
        for j in buckets["plymouth_csa"]:
            print("-", fmt_job(j))
    else:
        print("(none)")

    if args.all:
        print("=== Near-miss / outside radius managers ===")
        for j in buckets["near_miss"]:
            print("-", fmt_job(j))
        print("=== Near-miss CSA (systems analyst outside radius) ===")
        for j in buckets["near_miss_csa"]:
            print("-", fmt_job(j))
        print("=== Other in-pocket (not manager/CSA notify) ===")
        for j in buckets["other"]:
            print("-", fmt_job(j))

    if report["browser_fallback"]:
        print("=== Browser fallback needed ===", file=sys.stderr)
        for line in report["browser_fallback"]:
            print(line, file=sys.stderr)

    notify_empty = all(not buckets[p] for p in NOTIFY_POCKETS)
    if notify_empty:
        return 10
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
