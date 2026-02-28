"""
YouTube fetcher.

Strategy:
1. Try the official RSS feed first (fastest, most reliable)
2. If RSS returns 404, fall back to scraping the channel page
"""

from __future__ import annotations

import re
import json
import time
import httpx
import feedparser

LIMIT = 15


async def fetch_youtube(source: dict) -> list[dict]:
    url = source.get("url", "")
    channel_handle = source.get("handle", "")  # e.g. "@tiabtc"
    channel_id = source.get("channel_id", "")
    limit = source.get("limit", LIMIT)

    # Build RSS URL from channel_id if not provided directly
    if not url and channel_id:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    # Strategy 1: Try RSS feed
    if url:
        items = await _try_rss(url, limit)
        if items:
            return items

    # Strategy 2: Scrape channel page
    page_url = ""
    if channel_handle:
        handle = channel_handle if channel_handle.startswith("@") else f"@{channel_handle}"
        page_url = f"https://www.youtube.com/{handle}/videos"
    elif channel_id:
        page_url = f"https://www.youtube.com/channel/{channel_id}/videos"
    elif url:
        # Extract channel_id from RSS URL and build page URL
        m = re.search(r"channel_id=([^&]+)", url)
        if m:
            page_url = f"https://www.youtube.com/channel/{m.group(1)}/videos"

    if page_url:
        return await _scrape_channel(page_url, limit)

    return []


async def _try_rss(url: str, limit: int) -> list[dict]:
    """Try fetching from YouTube's RSS feed."""
    try:
        cookies = {"CONSENT": "PENDING+987"}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, cookies=cookies) as client:
            resp = await client.get(url, headers={"User-Agent": "Enbox/1.0"})
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:limit]:
                pub_time = 0
                for key in ("published_parsed", "updated_parsed"):
                    tp = entry.get(key)
                    if tp:
                        try:
                            pub_time = int(time.mktime(tp))
                        except Exception:
                            pass
                        break

                items.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": _truncate(_strip_html(entry.get("summary", "")), 200),
                    "author": entry.get("author", ""),
                    "time": pub_time,
                    "display": "article",
                })
            return items
    except Exception:
        return []


async def _scrape_channel(page_url: str, limit: int) -> list[dict]:
    """Scrape video list from a YouTube channel page."""
    try:
        # CONSENT cookie to bypass GDPR consent page
        cookies = {"CONSENT": "PENDING+987", "SOCS": "CAISNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwODI5LjA3X3AxGgJlbiACGgYIgJnZpwY"}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, cookies=cookies) as client:
            resp = await client.get(page_url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            })
            if resp.status_code != 200:
                return []
            html = resp.text

        # Extract ytInitialData JSON from the page
        m = re.search(r"var ytInitialData\s*=\s*", html)
        if not m:
            return []

        # Use JSONDecoder to properly extract the JSON object
        start = m.end()
        decoder = json.JSONDecoder()
        try:
            data, _ = decoder.raw_decode(html, start)
        except json.JSONDecodeError:
            return []
        items = []

        # Navigate the deeply nested YouTube data structure
        tabs = (data.get("contents", {})
                .get("twoColumnBrowseResultsRenderer", {})
                .get("tabs", []))

        videos_content = None
        for tab in tabs:
            tab_renderer = tab.get("tabRenderer", {})
            if tab_renderer.get("selected"):
                videos_content = (tab_renderer
                                  .get("content", {})
                                  .get("richGridRenderer", {})
                                  .get("contents", []))
                break

        if not videos_content:
            return []

        for item in videos_content[:limit]:
            video = (item.get("richItemRenderer", {})
                     .get("content", {})
                     .get("videoRenderer", {}))
            if not video:
                continue

            video_id = video.get("videoId", "")
            title = ""
            title_runs = video.get("title", {}).get("runs", [])
            if title_runs:
                title = title_runs[0].get("text", "")

            # Published time text (e.g. "2 days ago")
            pub_text = ""
            pub_snippet = video.get("publishedTimeText", {})
            if pub_snippet:
                pub_text = pub_snippet.get("simpleText", "")

            items.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
                "summary": pub_text,
                "author": "",
                "time": 0,  # Can't get exact timestamp from scrape
                "display": "article",
            })

        return items

    except Exception:
        import traceback
        traceback.print_exc()
        return []


def _extract_json_object(text: str, start: int) -> str | None:
    """Extract a complete JSON object from text starting at position `start`."""
    if start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, min(start + 5_000_000, len(text))):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _truncate(text: str, length: int) -> str:
    if len(text) > length:
        return text[:length] + "…"
    return text
