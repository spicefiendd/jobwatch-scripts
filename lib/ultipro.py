"""UKG Ultipro / JobBoard JSON search (no browser)."""
from __future__ import annotations

import json
from typing import Any
from urllib.request import Request

from .http import UA, opener_with_cookies, request
from .models import Job

# 1st Source public board
FIRST_SOURCE = {
    "employer": "1st Source Bank",
    "board_id": "bdcbc22d-c568-4b9f-bc84-421f9522fd47",
    "tenant": "STS1000SCO",
    "base": "https://recruiting.ultipro.com/STS1000SCO/JobBoard/bdcbc22d-c568-4b9f-bc84-421f9522fd47",
}


def fetch_ultipro_board(cfg: dict[str, str] | None = None, *, top: int = 100, query: str = "") -> list[Job]:
    cfg = cfg or FIRST_SOURCE
    base = cfg["base"]
    opener = opener_with_cookies()
    # warm session + anonymous cookie
    request(base + "/", opener=opener)
    try:
        request(
            base + "/AnonymousSessionCheck",
            opener=opener,
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": base + "/"},
        )
    except Exception:
        pass

    payload = {
        "opportunitySearch": {
            "Top": top,
            "Skip": 0,
            "QueryString": query,
            "OrderBy": [
                {"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": False}
            ],
            "Filters": [],
        }
    }
    data = json.dumps(payload).encode("utf-8")
    status, body, _ = request(
        base + "/JobBoardView/LoadSearchResults",
        data=data,
        opener=opener,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": base + "/",
            "Origin": "https://recruiting2.ultipro.com" if "recruiting2" in base else "https://recruiting.ultipro.com",
        },
    )
    if status >= 400:
        raise RuntimeError(f"Ultipro search failed: HTTP {status}")
    parsed: dict[str, Any] = json.loads(body.decode("utf-8"))
    jobs: list[Job] = []
    for opp in parsed.get("opportunities") or []:
        locs = opp.get("Locations") or []
        loc_bits = []
        for loc in locs:
            city = loc.get("City") or ""
            state = (loc.get("State") or {})
            if isinstance(state, dict):
                state = state.get("Code") or state.get("Name") or ""
            bit = ", ".join(x for x in (city, state) if x)
            if not bit:
                bit = loc.get("LocalizedName") or ""
            if bit:
                loc_bits.append(bit)
        # Ultipro often puts city in the title when Locations is empty
        location = "; ".join(loc_bits)
        oid = opp.get("Id") or ""
        jobs.append(
            Job(
                source="ultipro",
                title=opp.get("Title") or "",
                employer=cfg["employer"],
                location=location,
                url=f"{base}/OpportunityDetail?opportunityId={oid}",
                posted=str(opp.get("PostedDate") or ""),
                req_id=opp.get("RequisitionNumber") or "",
                raw=opp,
            )
        )
    return jobs


INTERRA = {
    "employer": "Interra Credit Union",
    "board_id": "5786d0b7-c595-469a-b8c2-56d92566cc7b",
    "tenant": "INT1063INTCU",
    "base": "https://recruiting2.ultipro.com/INT1063INTCU/JobBoard/5786d0b7-c595-469a-b8c2-56d92566cc7b",
}


def fetch_1st_source(**kw) -> list[Job]:
    return fetch_ultipro_board(FIRST_SOURCE, **kw)


def fetch_interra(**kw) -> list[Job]:
    return fetch_ultipro_board(INTERRA, **kw)
