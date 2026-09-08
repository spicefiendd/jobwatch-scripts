#!/usr/bin/env python3
"""UKG Ultipro / recruiting.ultipro.com JobBoardView/LoadSearchResults"""
from __future__ import annotations
import argparse
import http.cookiejar
from urllib.request import build_opener, HTTPCookieProcessor, Request
from common import UA, print_jobs
import json

BOARDS = {
    "1stsource": "https://recruiting.ultipro.com/STS1000SCO/JobBoard/bdcbc22d-c568-4b9f-bc84-421f9522fd47/",
    "interra": "https://recruiting2.ultipro.com/INT1063INTCU/JobBoard/5786d0b7-c595-469a-b8c2-56d92566cc7b/",
}


def fetch(board_url: str, query: str = "", top: int = 50) -> list[dict]:
    board_url = board_url if board_url.endswith("/") else board_url + "/"
    cj = http.cookiejar.CookieJar()
    opener = build_opener(HTTPCookieProcessor(cj))
    opener.open(Request(board_url, headers={"User-Agent": UA}))
    payload = {
        "opportunitySearch": {
            "Top": top,
            "Skip": 0,
            "QueryString": query,
            "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": False}],
            "Filters": [],
        }
    }
    api = board_url.rstrip("/") + "/JobBoardView/LoadSearchResults"
    req = Request(
        api,
        data=json.dumps(payload).encode(),
        headers={"User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json", "Referer": board_url},
        method="POST",
    )
    with opener.open(req, timeout=45) as resp:
        data = json.loads(resp.read().decode())
    rows = []
    for o in data.get("opportunities") or []:
        bits = []
        for x in (o.get("Locations") or []):
            name = x.get("LocalizedName") or ""
            if not name:
                city = x.get("City") or ""
                st = x.get("State") or {}
                if isinstance(st, dict):
                    st = st.get("Code") or ""
                name = ", ".join(p for p in (city, st) if p)
            if name:
                bits.append(str(name))
        locs = ", ".join(bits)
        oid = o.get("Id") or ""
        rows.append({
            "title": o.get("Title") or "",
            "location": locs,
            "url": f"{board_url}OpportunityDetail?opportunityId={oid}" if oid else board_url,
            "extra": o.get("JobCategoryName") or o.get("RequisitionNumber") or "",
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", choices=list(BOARDS), default="1stsource")
    ap.add_argument("--url", help="Full Ultipro job board URL")
    ap.add_argument("--q", default="", help="Search text")
    ap.add_argument("--top", type=int, default=50)
    args = ap.parse_args()
    url = args.url or BOARDS[args.board]
    rows = fetch(url, query=args.q, top=args.top)
    # soft location hint for Wednesday scan
    print(f"# Ultipro {url}\n# total fetched: {len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
