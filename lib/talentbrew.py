"""TMP TalentBrew AJAX search-jobs/results (Advanced Technology Services)."""
from __future__ import annotations

import html as H
import re
from urllib.parse import urlencode

from .http import request
from .models import Job

BASE = "https://jobs.advancedtech.com"


def fetch_ats(
    *,
    location: str = "Indiana",
    keywords: str = "",
    per_page: int = 50,
    page: int = 1,
) -> list[Job]:
    qs = urlencode(
        {
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
    )
    url = f"{BASE}/en/search-jobs/results?{qs}"
    status, body, _ = request(
        url,
        headers={
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE}/en/search-jobs",
        },
    )
    if status >= 400:
        raise RuntimeError(f"TalentBrew HTTP {status}")
    import json

    data = json.loads(body.decode("utf-8"))
    html = data.get("results") or ""
    items = re.findall(
        r'<a href="(/en/job/[^"]+)" data-job-id="(\d+)">\s*<h2>(.*?)</h2>\s*'
        r'<span class="job-location">(.*?)</span>',
        html,
        re.S,
    )
    jobs: list[Job] = []
    for path, jid, title, loc in items:
        jobs.append(
            Job(
                source="talentbrew:ats",
                title=H.unescape(re.sub(r"<[^>]+>", "", title)).strip(),
                employer="Advanced Technology Services",
                location=H.unescape(re.sub(r"<[^>]+>", "", loc)).strip(),
                url=BASE + path,
                req_id=jid,
            )
        )
    return jobs
