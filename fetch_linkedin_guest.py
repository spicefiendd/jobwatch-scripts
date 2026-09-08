#!/usr/bin/env python3
"""LinkedIn public guest job cards (no login). Fragile; rate-limits possible."""
from __future__ import annotations
import argparse
import re
from urllib.parse import urlencode
from common import http_text, print_jobs, strip_tags

API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def fetch(keywords: str = "manager", location: str = "Warsaw, Indiana", start: int = 0) -> list[dict]:
    qs = urlencode({"keywords": keywords, "location": location, "start": start})
    html = http_text(f"{API}?{qs}")
    cards = re.findall(
        r'data-entity-urn="urn:li:jobPosting:(\d+)"[\s\S]*?'
        r'class="base-search-card__title"[^>]*>\s*([^<]+)\s*<'
        r'[\s\S]*?class="base-search-card__subtitle"[^>]*>\s*([\s\S]*?)</'
        r'[\s\S]*?class="job-search-card__location"[^>]*>\s*([^<]+)',
        html,
    )
    rows = []
    for jid, title, company, loc in cards:
        rows.append({
            "title": strip_tags(title),
            "location": strip_tags(loc),
            "url": f"https://www.linkedin.com/jobs/view/{jid}/",
            "extra": strip_tags(company),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", default="manager")
    ap.add_argument("--location", default="Warsaw, Indiana")
    args = ap.parse_args()
    rows = fetch(keywords=args.q, location=args.location)
    print(f"# LinkedIn guest q={args.q!r} loc={args.location!r} n={len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
