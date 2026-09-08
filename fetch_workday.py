#!/usr/bin/env python3
"""Workday CXS jobs search (POST /wday/cxs/{tenant}/{site}/jobs)."""
from __future__ import annotations
import argparse
from common import http_json, print_jobs

SITES = {
    "everwise": {
        "cxs": "https://ecu.wd12.myworkdayjobs.com/wday/cxs/ecu/Everwise_Careers/jobs",
        "base": "https://ecu.wd12.myworkdayjobs.com/Everwise_Careers",
    },
    "slate": {
        "cxs": "https://recar.wd108.myworkdayjobs.com/wday/cxs/recar/SLATEcareers/jobs",
        "base": "https://recar.wd108.myworkdayjobs.com/SLATEcareers",
    },
}


def fetch(cxs_url: str, base: str, search: str = "", limit: int = 50, location_hint: str = "") -> list[dict]:
    body = {"appliedFacets": {}, "limit": limit, "offset": 0, "searchText": search or location_hint}
    data = http_json("POST", cxs_url, body, headers={"Referer": base})
    rows = []
    for j in data.get("jobPostings") or []:
        path = j.get("externalPath") or ""
        rows.append({
            "title": j.get("title") or "",
            "location": j.get("locationsText") or "",
            "url": base.rstrip("/") + path if path else base,
            "extra": j.get("postedOn") or "",
        })
    return rows, data.get("total")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=list(SITES), default="everwise")
    ap.add_argument("--q", default="")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--filter-loc", default="", help="Client-side substring filter on locationsText")
    args = ap.parse_args()
    meta = SITES[args.site]
    rows, total = fetch(meta["cxs"], meta["base"], search=args.q, limit=args.limit)
    if args.filter_loc:
        fl = args.filter_loc.lower()
        rows = [r for r in rows if fl in (r["location"] or "").lower() or fl in (r["title"] or "").lower()]
    print(f"# Workday {args.site} total={total} shown={len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
