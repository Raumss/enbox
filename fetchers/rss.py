"""
Generic RSS / Atom fetcher.

Works for: CoolShell, YouTube channels, Apple Podcasts, blogs, etc.
"""

from __future__ import annotations

import time
import httpx
import feedparser
from email.utils import parsedate_to_datetime

LIMIT = 30


async def fetch_rss(source: dict) -> list[dict]:
    url = source.get("url", "")
    if not url:
        return []

    limit = source.get("limit", LIMIT)
    display = source.get("display", "article")  # article | post

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Enbox/1.0"})
        resp.raise_for_status()
        raw = resp.text

    feed = feedparser.parse(raw)
    items: list[dict] = []

    for entry in feed.entries[:limit]:
        summary = entry.get("summary", "") or entry.get("description", "")
        summary = _strip_html(summary)
        summary = _truncate(summary, 300)

        pub_time = _parse_time(entry)

        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "summary": summary,
            "author": entry.get("author", ""),
            "time": pub_time,
            "display": display,
        })

    return items


def _strip_html(text: str) -> str:
    """Naively remove HTML tags."""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _truncate(text: str, length: int) -> str:
    if len(text) > length:
        return text[:length] + "…"
    return text


def _parse_time(entry) -> int:
    """Try to extract a Unix timestamp from a feed entry."""
    for key in ("published_parsed", "updated_parsed"):
        tp = entry.get(key)
        if tp:
            try:
                return int(time.mktime(tp))
            except Exception:
                pass
    for key in ("published", "updated"):
        raw = entry.get(key, "")
        if raw:
            try:
                return int(parsedate_to_datetime(raw).timestamp())
            except Exception:
                pass
    return 0
