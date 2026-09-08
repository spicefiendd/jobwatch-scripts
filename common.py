#!/usr/bin/env python3
"""Shared helpers for jobwatch fetchers."""
from __future__ import annotations
import json
import re
import sys
from html import unescape
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def http_json(method: str, url: str, body: dict | None = None, headers: dict | None = None, timeout: int = 45) -> Any:
    h = {"User-Agent": UA, "Accept": "application/json, text/html, */*"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    req = Request(url, data=data, headers=h, method=method.upper())
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        ctype = resp.headers.get("Content-Type", "")
        text = raw.decode("utf-8", errors="replace")
        if "json" in ctype or text[:1] in "{[":
            return json.loads(text)
        return text


def http_text(url: str, headers: dict | None = None, timeout: int = 45) -> str:
    h = {"User-Agent": UA, "Accept": "text/html, application/xhtml+xml, */*"}
    if headers:
        h.update(headers)
    req = Request(url, headers=h, method="GET")
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def print_jobs(rows: list[dict], limit: int = 50) -> None:
    for i, row in enumerate(rows[:limit], 1):
        title = row.get("title") or ""
        loc = row.get("location") or ""
        link = row.get("url") or ""
        extra = row.get("extra") or ""
        line = f"{i:3}. {title}"
        if loc:
            line += f"  |  {loc}"
        if extra:
            line += f"  |  {extra}"
        if link:
            line += f"\n     {link}"
        print(line)
    print(f"\n({min(limit, len(rows))} of {len(rows)} shown)")


def strip_tags(s: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
