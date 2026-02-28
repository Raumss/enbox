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
from fetchers.youtube import fetch_youtube
from fetchers.podcast import fetch_podcast
from fetchers.twitter import fetch_twitter
from fetchers.xueqiu import fetch_xueqiu

FETCHER_MAP = {
    "hackernews": fetch_hackernews,
    "v2ex": fetch_v2ex,
    "rss": fetch_rss,
    "youtube": fetch_youtube,
    "podcast": fetch_podcast,
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
        # Stamp each item with source metadata for frontend grouping
        src_name = source.get("name", stype)
        src_icon = source.get("icon", "")

        # For multi-user platforms, ensure author is set on every item
        # so the frontend can distinguish content from different creators.
        _MULTI_USER_TYPES = {"youtube", "podcast", "twitter", "xueqiu"}
        fallback_author = ""
        if stype in _MULTI_USER_TYPES:
            fallback_author = src_name
            # Strip platform prefix if present, e.g. "YouTube - tiabtc" → "tiabtc"
            if " - " in fallback_author:
                fallback_author = fallback_author.split(" - ", 1)[1]

        for item in items:
            item["source_name"] = src_name
            item["source_type"] = stype
            item["source_icon"] = src_icon
            # Populate author from fetcher data or fallback to source name
            if not item.get("author") and fallback_author:
                item["author"] = fallback_author
        return {
            "name": src_name,
            "type": stype,
            "icon": src_icon,
            "items": items,
        }

    tasks = [_fetch_one(s) for s in sources]
    return await asyncio.gather(*tasks)
