"""JobWatch filters (Warsaw / Plymouth, people-manager + CSA tracks)."""
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

# Tight CSA / systems-analyst title match (Strong Interest: Computer Systems Analyst).
# Avoid flooding Help Desk / generic IT Support / pure Finance-Data analysts.
CSA_TITLE_RE = re.compile(
    r"(?i)\b("
    r"computer\s+systems?\s+analyst|"
    r"it\s+systems?\s+analyst|"
    r"(?:jr\.?|junior)\s+(?:computer\s+|it\s+)?systems?\s+analyst|"
    r"(?:business\s+|application\s+|applications?\s+)?systems?\s+analyst|"
    r"it\s+analyst"
    r")\b"
)
# Senior / lead titles stay visible as market signal but are not entry CSA notify.
CSA_SENIOR_RE = re.compile(
    r"(?i)\b(senior|sr\.?|lead|principal|staff|architect|iii\b|iv\b)\b"
)
HELP_DESK_RE = re.compile(
    r"(?i)\b(help\s*desk|service\s*desk|desktop\s+support|it\s+support)\b"
)
# Soft education preference: HS / associate / equivalent OK; bachelor wall flagged.
BACHELORS_WALL_RE = re.compile(
    r"(?i)\b(bachelor'?s?|b\.?s\.?\b|b\.?a\.?\b|4[- ]?year\s+degree|"
    r"four[- ]year\s+degree|undergraduate\s+degree)\b"
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


def looks_like_csa_title(job: Job) -> bool:
    """True if title is tightly systems-analyst / CSA (not Help Desk flood)."""
    t = (job.title or "").strip()
    if not t:
        return False
    if HELP_DESK_RE.search(t) and not CSA_TITLE_RE.search(t):
        return False
    return bool(CSA_TITLE_RE.search(t))


def looks_like_entry_csa(job: Job) -> bool:
    """Entry/mid CSA notify track — prefer no Senior/Lead/Principal in title."""
    if not looks_like_csa_title(job):
        return False
    if CSA_SENIOR_RE.search(job.title or ""):
        return False
    return True


def has_bachelors_wall(job: Job) -> bool:
    blob = f"{job.education or ''} {job.title or ''}"
    return bool(BACHELORS_WALL_RE.search(blob))


def classify(jobs: Iterable[Job]) -> dict[str, list[Job]]:
    """Bucket jobs into manager + CSA notify tracks.

    Notify pockets (first-class):
      warsaw, plymouth           — people-managers in-radius
      warsaw_csa, plymouth_csa   — entry/mid CSA titles in-radius

    Signal / FYI:
      near_miss      — managers outside radius (or manager far afield)
      near_miss_csa  — CSA titles (entry or senior) in near-miss geography
      other          — in-pocket non-notify (ICs, senior CSA, etc.)
    """
    out: dict[str, list[Job]] = {
        "warsaw": [],
        "plymouth": [],
        "warsaw_csa": [],
        "plymouth_csa": [],
        "near_miss": [],
        "near_miss_csa": [],
        "other": [],
    }
    for j in jobs:
        p = pocket(j)
        mgr = looks_like_people_manager(j)
        csa_entry = looks_like_entry_csa(j)
        csa_any = looks_like_csa_title(j)
        blob = f"{j.title} {j.location}"
        near = bool(NEAR_BUT_OUT_RE.search(blob))

        # CSA track first for dual-match edge cases (rare "Systems Analyst Manager")
        # — people-manager still wins if clearly a manager title and not CSA-shaped.
        if p and csa_entry and not mgr:
            out[f"{p}_csa"].append(j)
        elif p and mgr:
            out[p].append(j)
        elif p and csa_any:
            # senior CSA / CSA+manager hybrid in-pocket → other (visible via --all)
            out["other"].append(j)
        elif csa_any and near:
            out["near_miss_csa"].append(j)
        elif mgr and near:
            out["near_miss"].append(j)
        elif p:
            out["other"].append(j)
        elif mgr:
            out["near_miss"].append(j)
        elif csa_any:
            out["near_miss_csa"].append(j)
    return out


# Pockets that trigger notify / exit-code logic
NOTIFY_POCKETS = ("warsaw", "plymouth", "warsaw_csa", "plymouth_csa")
