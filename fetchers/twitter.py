"""
Twitter / X fetcher.

Since the official X API requires paid access, we support two approaches:
1. RSSHub instance (self-hosted or public) – recommended
2. Nitter RSS (if a public Nitter instance is available)

Configure via `rsshub_base` in source config:
  rsshub_base: https://rsshub.app          # or your own instance
  username: elonmusk
"""

from __future__ import annotations

from fetchers.rss import fetch_rss


async def fetch_twitter(source: dict) -> list[dict]:
    username = source.get("username", "")
    rsshub = source.get("rsshub_base", "https://rsshub.app").rstrip("/")

    if not source.get("url"):
        if not username:
            return []
        source = {**source, "url": f"{rsshub}/twitter/user/{username}"}

    source.setdefault("display", "post")
    items = await fetch_rss(source)

    # Mark as tweet-style posts for collapsible display
    for item in items:
        item["display"] = "post"

    return items
