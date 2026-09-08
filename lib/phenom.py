"""Phenom People /widgets refineSearch (Zimmer Biomet)."""
from __future__ import annotations

from typing import Any

from .http import post_json
from .models import Job

SITES = {
    "zimmer": {
        "employer": "Zimmer Biomet",
        "widgets": "https://careers.zimmerbiomet.com/widgets",
        "detail_base": "https://careers.zimmerbiomet.com/us/en/job/",
        "pageId": "page19",
    },
}


def fetch_phenom(
    site_key: str = "zimmer",
    *,
    state: str | None = "Indiana",
    keywords: str = "",
    size: int = 50,
) -> list[Job]:
    cfg = SITES[site_key]
    selected: dict[str, list[str]] = {}
    if state:
        selected["state"] = [state]
    body: dict[str, Any] = {
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
        "pageId": cfg["pageId"],
        "siteType": "external",
        "keywords": keywords,
        "global": True,
        "selected_fields": selected,
        "location": "",
        "refNum": "",
    }
    data = post_json(cfg["widgets"], body)
    block = (data.get("refineSearch") or {}).get("data") or {}
    jobs: list[Job] = []
    for j in block.get("jobs") or []:
        jid = j.get("jobId") or j.get("reqId") or ""
        jobs.append(
            Job(
                source=f"phenom:{site_key}",
                title=j.get("title") or "",
                employer=cfg["employer"],
                location=" ".join(x for x in (j.get("city"), j.get("state")) if x),
                url=f"{cfg['detail_base']}{jid}" if jid else cfg["widgets"],
                req_id=str(j.get("reqId") or jid),
                raw=j,
            )
        )
    return jobs
