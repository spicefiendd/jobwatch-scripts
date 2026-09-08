"""Workday CXS public job search (no browser)."""
from __future__ import annotations

from typing import Any

from .http import post_json
from .models import Job

# tenant, site path segment, public careers host prefix
WORKDAY_SITES = {
    "everwise": {
        "employer": "Everwise Credit Union",
        "cxs": "https://ecu.wd12.myworkdayjobs.com/wday/cxs/ecu/Everwise_Careers/jobs",
        "detail_base": "https://ecu.wd12.myworkdayjobs.com/en-US/Everwise_Careers",
    },
    "slate": {
        "employer": "Slate Auto",
        "cxs": "https://recar.wd108.myworkdayjobs.com/wday/cxs/recar/SLATEcareers/jobs",
        "detail_base": "https://recar.wd108.myworkdayjobs.com/en-US/SLATEcareers",
    },
}


def fetch_workday(site_key: str, *, search_text: str = "", limit: int = 50, offset: int = 0) -> list[Job]:
    cfg = WORKDAY_SITES[site_key]
    payload = {
        "appliedFacets": {},
        "limit": limit,
        "offset": offset,
        "searchText": search_text,
    }
    data: dict[str, Any] = post_json(cfg["cxs"], payload)
    jobs: list[Job] = []
    for post in data.get("jobPostings") or []:
        path = post.get("externalPath") or ""
        jobs.append(
            Job(
                source=f"workday:{site_key}",
                title=post.get("title") or "",
                employer=cfg["employer"],
                location=post.get("locationsText") or "",
                url=f"{cfg['detail_base']}{path}" if path else cfg["detail_base"],
                posted=post.get("postedOn") or post.get("bulletFields", [""])[0] if post.get("bulletFields") else "",
                raw=post,
            )
        )
    return jobs


def fetch_all_workday_pages(site_key: str, *, search_text: str = "", page_size: int = 20, max_pages: int = 10) -> list[Job]:
    out: list[Job] = []
    for page in range(max_pages):
        batch = fetch_workday(site_key, search_text=search_text, limit=page_size, offset=page * page_size)
        out.extend(batch)
        if len(batch) < page_size:
            break
    return out
