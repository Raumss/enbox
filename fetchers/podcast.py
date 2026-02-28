"""
Podcast fetcher.

Supports:
  - Direct RSS feed URL (url field)
  - Apple Podcast URL or ID (apple_podcast_url / apple_podcast_id)
    → auto-resolves to the underlying RSS feed via iTunes Lookup API
"""

from __future__ import annotations

import re
import httpx

from fetchers.rss import fetch_rss


async def fetch_podcast(source: dict) -> list[dict]:
    url = source.get("url", "")
    apple_url = source.get("apple_podcast_url", "")
    apple_id = source.get("apple_podcast_id", "")

    # If no direct RSS URL, resolve from Apple Podcast
    if not url:
        pod_id = apple_id or _extract_apple_id(apple_url)
        if pod_id:
            url = await _resolve_apple_feed(str(pod_id))

    if not url:
        return []

    # Delegate to the generic RSS fetcher
    patched = {**source, "url": url}
    patched.setdefault("display", "article")
    return await fetch_rss(patched)


def _extract_apple_id(apple_url: str) -> str:
    """Extract podcast ID from an Apple Podcasts URL like
    https://podcasts.apple.com/.../id1726135306"""
    if not apple_url:
        return ""
    m = re.search(r"/id(\d+)", apple_url)
    return m.group(1) if m else ""


async def _resolve_apple_feed(pod_id: str) -> str:
    """Use iTunes Lookup API to resolve podcast ID → RSS feed URL."""
    lookup_url = f"https://itunes.apple.com/lookup?id={pod_id}&entity=podcast"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(lookup_url)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if results:
                return results[0].get("feedUrl", "")
    except Exception:
        pass
    return ""
