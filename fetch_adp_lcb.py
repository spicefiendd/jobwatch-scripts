#!/usr/bin/env python3
"""Lake City Bank via ADP Workforce Now public job-requisitions API."""
from __future__ import annotations
from common import http_json, print_jobs

CID = "4c0f5e63-d8a0-4686-b48c-977660d2dabc"
CCID = "9200753277202_3"
URL = (
    "https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions"
    f"?cid={CID}&ccId={CCID}&lang=en_US&$top=50&$skip=0&locale=en_US"
)
PORTAL = (
    f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html"
    f"?cid={CID}&ccId={CCID}&lang=en_US"
)


def fetch() -> list[dict]:
    data = http_json("GET", URL, headers={"Referer": PORTAL})
    rows = []
    for j in data.get("jobRequisitions") or []:
        title = j.get("requisitionTitle") or ""
        loc = ""
        # title often embeds branch/city; also try nested address
        for key in ("requisitionLocations", "workLocations", "locations"):
            locs = j.get(key) or []
            if locs and isinstance(locs, list):
                addr = (locs[0] or {}).get("address") or locs[0] or {}
                if isinstance(addr, dict):
                    loc = ", ".join(filter(None, [addr.get("cityName"), addr.get("countrySubdivisionLevel1", {}).get("codeValue") if isinstance(addr.get("countrySubdivisionLevel1"), dict) else addr.get("stateCode")]))
                break
        rows.append({
            "title": title,
            "location": loc or title,
            "url": PORTAL,
            "extra": j.get("postDate") or j.get("itemID") or "",
        })
    return rows


def main():
    rows = fetch()
    print(f"# Lake City Bank ADP  n={len(rows)}\n")
    print_jobs(rows)


if __name__ == "__main__":
    main()
