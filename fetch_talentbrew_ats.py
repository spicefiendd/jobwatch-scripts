#!/usr/bin/env python3
"""Advanced Technology Services — TMP TalentBrew AJAX search-jobs/results."""
from __future__ import annotations
import argparse
import re
from urllib.parse import urlencode
from common import http_json, print_jobs, strip_tags

BASE = "https://jobs.advancedtech.com"


def fetch(location: str = "Indiana", page: int = 1, per_page: int = 50, keywords: str = "") -> list[dict]:
    qs = {
        "ActiveFacetID": 0,
        "CurrentPage": page,
        "RecordsPerPage": per_page,
        "Distance": 50,
        "RadiusUnitType": 0,
        "Keywords": keywords,
        "Location": location,
        "ShowRadius": "False",
        "CustomFacetName": "",
        "FacetTerm": "",
        "FacetType": 0,
        "SearchResultsModuleName": "Search Results",
        "SearchFiltersModuleName": "Search Filters",
        "SortCriteria": 0,
        "SortDirection": 0,
        "SearchType": 5,
        "PostalCode": "",
        "ResultsType": 0,
        "fc": "",
        "fl": "",
        "fcf": "",
        "afc": "",
        "afl": "",
        "afcf": "",
    }
    url = f"{BASE}/en/search-jobs/results?{urlencode(qs)}"
    data = http_json(
        "GET",
        url,
        headers={
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE}/en/search-jobs",
        },
    )
    html = data.get("results") or ""
    total = None
    m = re.search(r'data-total-job-results="(\d+)"', html)
    if m:
        total = int(m.group(1))
    items = re.findall(
        r'<a href="(/en/job/[^"]+)" data-job-id="(\d+)">\s*<h2>(.*?)</h2>\s*'
        r'<span class="job-location">(.*?)</span>',
        html,
        re.S,
    )
    rows = []
    for path, jid, title, loc in items:
        rows.append({
            "title": strip_tags(title),
            "location": strip_tags(loc),
            "url": BASE + path,
            "extra": jid,
        })
    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", default="Indiana")
    ap.add_argument("--q", default="")
    ap.add_argument("--per-page", type=int, default=50)
    args = ap.parse_args()
    rows, total = fetch(location=args.location, per_page=args.per_page, keywords=args.q)
    print(f"# ATS TalentBrew location={args.location!r} total={total} n={len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
