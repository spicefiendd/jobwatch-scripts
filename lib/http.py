"""Tiny HTTP helpers (stdlib only)."""
from __future__ import annotations

import http.client
import http.cookiejar
import json
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 JobWatch/1.0"
CTX = ssl.create_default_context()


def opener_with_cookies() -> urllib.request.OpenerDirector:
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=CTX),
        urllib.request.HTTPCookieProcessor(cj),
    )


def request(
    url: str,
    *,
    method: str | None = None,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    opener: urllib.request.OpenerDirector | None = None,
    timeout: float = 30,
    retries: int = 3,
) -> tuple[int, bytes, dict[str, str]]:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    last_err: Exception | None = None
    for attempt in range(max(1, retries)):
        req = urllib.request.Request(
            url, data=data, headers=h, method=method or ("POST" if data is not None else "GET")
        )
        open_fn = opener.open if opener else (
            lambda r, timeout=timeout: urllib.request.urlopen(r, context=CTX, timeout=timeout)
        )
        try:
            with open_fn(req, timeout=timeout) as resp:
                return resp.status, resp.read(), {k.lower(): v for k, v in resp.headers.items()}
        except urllib.error.HTTPError as e:
            body = e.read() if hasattr(e, "read") else b""
            raise RuntimeError(f"HTTP {e.code} for {url}: {body[:200]!r}") from e
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt + 1 >= retries:
                break
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"HTTP failed for {url} after {retries} tries: {last_err}") from last_err


def get_json(url: str, **kw: Any) -> Any:
    status, body, _ = request(url, headers={"Accept": "application/json", **(kw.pop("headers", {}) or {})}, **kw)
    if status >= 400:
        raise RuntimeError(f"HTTP {status} for {url}")
    return json.loads(body.decode("utf-8"))


def post_json(url: str, payload: dict[str, Any], **kw: Any) -> Any:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    headers.update(kw.pop("headers", {}) or {})
    status, body, _ = request(url, data=data, headers=headers, **kw)
    if status >= 400:
        raise RuntimeError(f"HTTP {status} for {url}")
    return json.loads(body.decode("utf-8"))


def get_text(url: str, **kw: Any) -> str:
    status, body, _ = request(url, **kw)
    if status >= 400:
        raise RuntimeError(f"HTTP {status} for {url}")
    return body.decode("utf-8", "replace")
