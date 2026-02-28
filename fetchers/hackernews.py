"""
Hacker News fetcher – uses the official Firebase API.

https://github.com/HackerNews/API
"""

from __future__ import annotations

import httpx

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
LIMIT = 30


async def fetch_hackernews(source: dict) -> list[dict]:
    limit = source.get("limit", LIMIT)
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(HN_TOP)
        resp.raise_for_status()
        ids = resp.json()[:limit]

        items: list[dict] = []
        # Fetch items in batches of 10 to avoid overwhelming the API
        for i in range(0, len(ids), 10):
            batch = ids[i : i + 10]
            import asyncio

            async def _get(item_id: int) -> dict | None:
                r = await client.get(HN_ITEM.format(item_id))
                if r.status_code == 200:
                    return r.json()
                return None

            results = await asyncio.gather(*[_get(iid) for iid in batch])
            for data in results:
                if data is None:
                    continue
                items.append({
                    "title": data.get("title", ""),
                    "url": data.get("url", f"https://news.ycombinator.com/item?id={data['id']}"),
                    "summary": "",
                    "score": data.get("score", 0),
                    "comments": data.get("descendants", 0),
                    "author": data.get("by", ""),
                    "time": data.get("time", 0),
                    "display": "article",
                    "hn_id": data.get("id"),
                })
    return items
