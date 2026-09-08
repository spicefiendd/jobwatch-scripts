"""JobWatch filters (Warsaw / Plymouth, people-manager, pay band heuristics)."""
from __future__ import annotations

import re
from typing import Iterable

from .models import Job

MANAGER_RE = re.compile(
    r"\b(manager|supervisor|director|AVP|assistant vice president|"
    r"vice president|general manager|\bGM\b|coach|team lead|group leader|"
    r"department lead|operations lead)\b",
    re.I,
)
NON_MANAGER_RE = re.compile(
    r"\b(teller|universal banker|personal banker|CSR|cashier|"
    r"associate\b|coordinator|specialist|processor|technician|"
    r"operator|baker|RN\b|nurse|pharmacist|PharmD)\b",
    re.I,
)
WARSAW_RE = re.compile(
    r"\b(Warsaw|Winona Lake|Leesburg|Pierceton|Claypool|Mentone)\b", re.I
)
PLYMOUTH_RE = re.compile(
    r"\b(Plymouth|Argos|Bourbon)\b", re.I
)
NEAR_BUT_OUT_RE = re.compile(
    r"\b(Goshen|South Bend|Bremen|Ligonier|LaPorte|La Porte|"
    r"Middlebury|Shipshewana|Elkhart|Mishawaka|Granger|Fort Wayne)\b",
    re.I,
)


def pocket(job: Job) -> str | None:
    blob = f"{job.title} {job.location} {job.url}"
    if WARSAW_RE.search(blob):
        return "warsaw"
    if PLYMOUTH_RE.search(blob):
        return "plymouth"
    return None


def looks_like_people_manager(job: Job) -> bool:
    t = job.title
    if not MANAGER_RE.search(t):
        return False
    # teller supervisor is management-ish but usually below band; still keep and flag later
    if NON_MANAGER_RE.search(t) and not re.search(r"manager|supervisor|coach|lead", t, re.I):
        return False
    return True


def classify(jobs: Iterable[Job]) -> dict[str, list[Job]]:
    out = {"warsaw": [], "plymouth": [], "near_miss": [], "other": []}
    for j in jobs:
        p = pocket(j)
        mgr = looks_like_people_manager(j)
        blob = f"{j.title} {j.location}"
        if p and mgr:
            out[p].append(j)
        elif mgr and NEAR_BUT_OUT_RE.search(blob):
            out["near_miss"].append(j)
        elif p:
            out["other"].append(j)
        elif mgr:
            out["near_miss"].append(j)
    return out
