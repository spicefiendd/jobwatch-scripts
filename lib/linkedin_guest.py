"""LinkedIn public guest job cards → Job objects (no login). Fragile; optional."""
from __future__ import annotations

import re
from urllib.parse import urlencode

from .http import request
from .models import Job

API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def _strip_tags(s: str) -> str:
    from html import unescape

    return unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def fetch_linkedin_guest(
    keywords: str = "systems analyst",
    location: str = "Warsaw, Indiana",
    start: int = 0,
) -> list[Job]:
    qs = urlencode({"keywords": keywords, "location": location, "start": start})
    url = f"{API}?{qs}"
    status, body, _ = request(
        url,
        headers={"Accept": "text/html, application/xhtml+xml, */*"},
        timeout=45,
        retries=2,
    )
    if status != 200:
        raise RuntimeError(f"linkedin guest HTTP {status}")
    html = body.decode("utf-8", errors="replace")
    cards = re.findall(
        r'data-entity-urn="urn:li:jobPosting:(\d+)"[\s\S]*?'
        r'class="base-search-card__title"[^>]*>\s*([^<]+)\s*<'
        r'[\s\S]*?class="base-search-card__subtitle"[^>]*>\s*([\s\S]*?)</'
        r'[\s\S]*?class="job-search-card__location"[^>]*>\s*([^<]+)',
        html,
    )
    jobs: list[Job] = []
    for jid, title, company, loc in cards:
        jobs.append(
            Job(
                source="linkedin:guest",
                title=_strip_tags(title),
                employer=_strip_tags(company),
                location=_strip_tags(loc),
                url=f"https://www.linkedin.com/jobs/view/{jid}/",
            )
        )
    return jobs


def fetch_csa_searches() -> list[Job]:
    """Warsaw + Plymouth CSA keyword sweeps; dedupe by URL."""
    queries = [
        ("systems analyst", "Warsaw, Indiana"),
        ("computer systems analyst", "Warsaw, Indiana"),
        ("systems analyst", "Plymouth, Indiana"),
        ("computer systems analyst", "Plymouth, Indiana"),
    ]
    seen: set[str] = set()
    out: list[Job] = []
    errors: list[str] = []
    for kw, loc in queries:
        try:
            batch = fetch_linkedin_guest(keywords=kw, location=loc)
        except Exception as e:
            errors.append(f"{kw}@{loc}: {e}")
            continue
        for j in batch:
            key = (j.url or "").rstrip("/").lower() or f"{j.title}|{j.employer}|{j.location}"
            if key in seen:
                continue
            seen.add(key)
            out.append(j)
    if errors and not out:
        raise RuntimeError("; ".join(errors))
    return out
