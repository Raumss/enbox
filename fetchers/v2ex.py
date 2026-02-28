"""
V2EX fetcher – uses the public API.
"""

from __future__ import annotations

import httpx

V2EX_HOT = "https://www.v2ex.com/api/v2/topics/hot"
V2EX_LATEST = "https://www.v2ex.com/api/v2/topics/latest"
LIMIT = 30


async def fetch_v2ex(source: dict) -> list[dict]:
    limit = source.get("limit", LIMIT)
    # V2EX v2 API requires a token for some endpoints; fall back to v1 if needed
    tab = source.get("tab", "hot")

    url = "https://www.v2ex.com/api/topics/hot.json"
    if tab == "latest":
        url = "https://www.v2ex.com/api/topics/latest.json"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    items = []
    for topic in data[:limit]:
        items.append({
            "title": topic.get("title", ""),
            "url": topic.get("url", ""),
            "summary": _truncate(topic.get("content", ""), 200),
            "author": topic.get("member", {}).get("username", ""),
            "node": topic.get("node", {}).get("title", ""),
            "replies": topic.get("replies", 0),
            "time": topic.get("created", 0),
            "display": "article",
        })
    return items


def _truncate(text: str, length: int) -> str:
    text = text.strip().replace("\r\n", " ").replace("\n", " ")
    if len(text) > length:
        return text[:length] + "…"
    return text
