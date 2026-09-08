"""Hershey SuccessFactors RMK HTML search (careers.thehersheycompany.com/search/)."""
from __future__ import annotations

import html as H
import re
from urllib.parse import urlencode

from .http import get_text
from .models import Job

BASE = "https://careers.thehersheycompany.com"


def fetch_hershey(*, location: str = "Plymouth, IN", keywords: str = "", startrow: int = 0) -> list[Job]:
    qs = urlencode(
        {
            "createNewAlert": "false",
            "q": keywords,
            "locationsearch": location,
            "startrow": startrow,
        }
    )
    text = get_text(f"{BASE}/search/?{qs}")
    pairs = re.findall(
        r'<a href="(/job/[^"]+)"[^>]*class="jobTitle-link"[^>]*>(.*?)</a>',
        text,
        re.S,
    )
    if not pairs:
        pairs = re.findall(r'<a href="(/job/[^"]+)"[^>]*>([^<]{3,120})</a>', text)
    jobs: list[Job] = []
    seen: set[str] = set()
    # Prefer rows whose path/title mention the requested place (SF locationsearch is fuzzy)
    needle = re.sub(r",\s*[A-Z]{2}\s*$", "", location).strip()
    for path, title in pairs:
        if path in seen:
            continue
        seen.add(path)
        title_clean = H.unescape(re.sub(r"<[^>]+>", "", title)).strip()
        url = BASE + path.replace("&amp;", "&")
        if needle and needle.lower() not in (path + " " + title_clean).lower():
            # keep only if no needle filter requested city token
            continue
        jobs.append(
            Job(
                source="hershey:sf",
                title=title_clean,
                employer="The Hershey Company",
                location=location,
                url=url,
            )
        )
    return jobs
