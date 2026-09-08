from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Job:
    source: str
    title: str
    employer: str
    location: str = ""
    url: str = ""
    posted: str = ""
    salary: str = ""
    education: str = ""
    req_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)
        return d
