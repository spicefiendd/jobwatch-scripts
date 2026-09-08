"""ADP Workforce Now public careercenter job-requisitions (Lake City Bank)."""
from __future__ import annotations

from typing import Any

from .http import get_json
from .models import Job

# Lake City Bank widget (from careers page <recruitment-current-openings>)
LCB = {
    "employer": "Lake City Bank",
    "cid": "4c0f5e63-d8a0-4686-b48c-977660d2dabc",
    "ccId": "9200753277202_3",
}


def _loc_from_req(j: dict[str, Any]) -> str:
    for key in ("requisitionLocations", "workLocations", "locations"):
        locs = j.get(key) or []
        if not locs:
            continue
        addr = (locs[0] or {}).get("address") or {}
        if not isinstance(addr, dict):
            continue
        city = addr.get("cityName") or ""
        st = ""
        sub = addr.get("countrySubdivisionLevel1")
        if isinstance(sub, dict):
            st = sub.get("codeValue") or sub.get("shortName") or ""
        st = st or addr.get("stateCode") or ""
        bit = ", ".join(x for x in (city, st) if x)
        if bit:
            return bit
    return ""


def fetch_adp_requisitions(cfg: dict[str, str] | None = None, *, top: int = 50) -> list[Job]:
    cfg = cfg or LCB
    portal = (
        "https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html"
        f"?cid={cfg['cid']}&ccId={cfg['ccId']}&lang=en_US"
    )
    url = (
        "https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions"
        f"?cid={cfg['cid']}&ccId={cfg['ccId']}&lang=en_US&$top={top}&$skip=0&locale=en_US"
    )
    data = get_json(url, headers={"Referer": portal, "Accept": "application/json"})
    jobs: list[Job] = []
    for j in data.get("jobRequisitions") or []:
        title = j.get("requisitionTitle") or ""
        jobs.append(
            Job(
                source="adp:lakecity",
                title=title,
                employer=cfg["employer"],
                location=_loc_from_req(j) or title,
                url=portal,
                posted=str(j.get("postDate") or ""),
                req_id=str(j.get("itemID") or ""),
                raw=j,
            )
        )
    return jobs


def fetch_lake_city_adp(**kw) -> list[Job]:
    return fetch_adp_requisitions(LCB, **kw)
