"""Static HTML career pages (no browser)."""
from __future__ import annotations

import html as H
import re

from .http import get_text
from .models import Job


def fetch_purity_gas() -> list[Job]:
    url = "https://www.puritygas.com/careers/"
    text = get_text(url)
    jobs: list[Job] = []
    # Warsaw Branch Manager block observed in prior scan
    for m in re.finditer(
        r"(?is)(Branch Manager[^<]{0,80}|[^.]{0,40}Manager)[^.]{0,20}Warsaw[^.]{0,200}",
        text,
    ):
        chunk = re.sub(r"<[^>]+>", " ", m.group(0))
        chunk = re.sub(r"\s+", " ", H.unescape(chunk)).strip()
        title = "Branch Manager"
        tm = re.search(r"(Branch Manager[^–\-|]{0,40})", chunk, re.I)
        if tm:
            title = tm.group(1).strip(" –-|")
        jobs.append(
            Job(
                source="html:puritygas",
                title=title,
                employer="Purity Cylinder Gases, Inc.",
                location="Warsaw, IN",
                url=url,
                education="no degree listed (verify)",
                raw={"snippet": chunk[:400]},
            )
        )
    # de-dupe by title
    seen = set()
    uniq = []
    for j in jobs:
        if j.title in seen:
            continue
        seen.add(j.title)
        uniq.append(j)
    if not uniq and re.search(r"Warsaw.*Branch Manager|Branch Manager.*Warsaw", text, re.I | re.S):
        uniq.append(
            Job(
                source="html:puritygas",
                title="Branch Manager",
                employer="Purity Cylinder Gases, Inc.",
                location="Warsaw, IN",
                url=url,
            )
        )
    return uniq


def fetch_lake_city_job_openings() -> list[Job]:
    """Best-effort HTML scrape. Lake City often JS-hydrates listings — may return empty.

    Returns whatever static markup contains; caller should fall back to browser if empty.
    """
    url = "https://www.lakecitybank.com/about-us/careers/job-openings/"
    text = get_text(url)
    jobs: list[Job] = []
    # Prefer structured blocks if present
    for m in re.finditer(
        r'(?is)<(?:div|li|article)[^>]*class="[^"]*job[^"]*"[^>]*>(.*?)</(?:div|li|article)>',
        text,
    ):
        block = m.group(1)
        title_m = re.search(r"(?is)<h[1-4][^>]*>(.*?)</h[1-4]>", block)
        if not title_m:
            continue
        title = re.sub(r"<[^>]+>", "", H.unescape(title_m.group(1))).strip()
        if len(title) < 4:
            continue
        loc_m = re.search(r"(?i)\b(Warsaw|Plymouth|Ligonier|Fort Wayne|Rochester|Warsaw HQ)[^<\n]{0,40}", block)
        location = loc_m.group(0).strip() if loc_m else ""
        link_m = re.search(r'href="(https?://[^"]+)"', block)
        jobs.append(
            Job(
                source="html:lakecity",
                title=title,
                employer="Lake City Bank",
                location=location,
                url=link_m.group(1) if link_m else url,
            )
        )
    return jobs
