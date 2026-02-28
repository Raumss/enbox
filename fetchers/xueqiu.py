"""
雪球 (Xueqiu) fetcher.

Uses RSSHub to get user timeline:
  rsshub_base: https://rsshub.app
  user_id: 1234567890
"""

from __future__ import annotations

from fetchers.rss import fetch_rss


async def fetch_xueqiu(source: dict) -> list[dict]:
    user_id = source.get("user_id", "")
    rsshub = source.get("rsshub_base", "https://rsshub.app").rstrip("/")

    if not source.get("url"):
        if not user_id:
            return []
        source = {**source, "url": f"{rsshub}/xueqiu/user/{user_id}"}

    source.setdefault("display", "post")
    items = await fetch_rss(source)

    for item in items:
        item["display"] = "post"

    return items
