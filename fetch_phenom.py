#!/usr/bin/env python3
"""Phenom People careers widgets API (Zimmer Biomet)."""
from __future__ import annotations
import argparse
from common import http_json, print_jobs

SITES = {
    "zimmer": {
        "widgets": "https://careers.zimmerbiomet.com/widgets",
        "base": "https://careers.zimmerbiomet.com/us/en/job/",
        "pageId": "page19",
    },
}


def fetch(site: str = "zimmer", state: str | None = "Indiana", keywords: str = "", size: int = 50) -> list[dict]:
    meta = SITES[site]
    selected = {}
    if state:
        selected["state"] = [state]
    body = {
        "lang": "en_us",
        "deviceType": "desktop",
        "country": "us",
        "pageName": "search-results",
        "ddoKey": "refineSearch",
        "sortBy": "",
        "subsearch": "",
        "from": 0,
        "jobs": True,
        "counts": True,
        "all_fields": ["category", "country", "state", "city", "type"],
        "size": size,
        "clearAll": False,
        "jdsource": "facets",
        "isSliderEnable": False,
        "pageId": meta["pageId"],
        "siteType": "external",
        "keywords": keywords,
        "global": True,
        "selected_fields": selected,
        "location": "",
        "refNum": "",
    }
    data = http_json("POST", meta["widgets"], body)
    block = (data.get("refineSearch") or {}).get("data") or {}
    rows = []
    for j in block.get("jobs") or []:
        jid = j.get("jobId") or j.get("reqId") or ""
        rows.append({
            "title": j.get("title") or "",
            "location": " ".join(filter(None, [j.get("city"), j.get("state")])),
            "url": (meta["base"] + str(jid)) if jid else meta["widgets"],
            "extra": j.get("category") or j.get("type") or "",
        })
    return rows, (data.get("refineSearch") or {}).get("hits")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", choices=list(SITES), default="zimmer")
    ap.add_argument("--state", default="Indiana")
    ap.add_argument("--q", default="")
    ap.add_argument("--size", type=int, default=50)
    args = ap.parse_args()
    rows, hits = fetch(args.site, state=args.state or None, keywords=args.q, size=args.size)
    print(f"# Phenom {args.site} hits={hits} n={len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
