"""
Fetchers package – every fetcher returns a list of ``FeedItem`` dicts.
"""

from __future__ import annotations

import asyncio
import traceback
from typing import Any

from fetchers.hackernews import fetch_hackernews
from fetchers.v2ex import fetch_v2ex
from fetchers.rss import fetch_rss
from fetchers.twitter import fetch_twitter
from fetchers.xueqiu import fetch_xueqiu

FETCHER_MAP = {
    "hackernews": fetch_hackernews,
    "v2ex": fetch_v2ex,
    "rss": fetch_rss,
    "youtube": fetch_rss,       # YouTube channels expose RSS
    "podcast": fetch_rss,       # Podcasts are RSS-based
    "coolshell": fetch_rss,     # CoolShell has an RSS feed
    "twitter": fetch_twitter,
    "xueqiu": fetch_xueqiu,
}


async def get_all_feeds(sources: list[dict[str, Any]]) -> list[dict]:
    """Fetch all sources concurrently and return a flat list grouped by source."""

    async def _fetch_one(source: dict) -> dict:
        stype = source.get("type", "rss")
        fetcher = FETCHER_MAP.get(stype, fetch_rss)
        try:
            items = await fetcher(source)
        except Exception as exc:
            traceback.print_exc()
            items = []
        return {
            "name": source.get("name", stype),
            "type": stype,
            "icon": source.get("icon", ""),
            "items": items,
        }

    tasks = [_fetch_one(s) for s in sources]
    return await asyncio.gather(*tasks)
