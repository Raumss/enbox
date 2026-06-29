"""
Twitter / X fetcher.

Three strategies (tried in order):
1. **Authenticated GraphQL** — if `auth_token` is provided in config,
   uses the real Twitter API to get the chronological latest tweets.
2. **Guest GraphQL** — uses a guest token to access the GraphQL API.
   Returns highlighted/popular tweets (not strictly chronological).
3. **Syndication fallback** — parses the embed widget timeline.

Config fields:
  username: elonmusk
  auth_token: "your_auth_token_cookie"   # optional, for latest tweets
"""

from __future__ import annotations

import json
import re
from email.utils import parsedate_tz, mktime_tz

import httpx

LIMIT = 20
BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)
SYNDICATION_URL = (
    "https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
)

# GraphQL feature flags — Twitter checks these rigorously.
_GQL_FEATURES = {
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

_USER_FEATURES = {
    "hidden_profile_subscriptions_enabled": True,
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "highlights_tweets_tab_ui_enabled": True,
    "responsive_web_twitter_article_notes_tab_enabled": True,
    "subscriptions_feature_can_gift_premium": True,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
}

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ── Public entry point ─────────────────────────────────────────────

async def fetch_twitter(source: dict) -> list[dict]:
    username = source.get("username", "")
    limit = source.get("limit", LIMIT)
    auth_token = source.get("auth_token", "")

    if not username:
        return []

    # Strategy 1: Authenticated GraphQL (latest chronological tweets)
    if auth_token:
        items = await _fetch_graphql(username, limit, auth_token=auth_token)
        if items:
            return items

    # Strategy 2: Guest GraphQL (highlighted tweets)
    items = await _fetch_graphql(username, limit)
    if items:
        return items

    # Strategy 3: Syndication fallback
    items = await _fetch_syndication(username, limit)
    if items:
        return items

    return []


# ── GraphQL strategy ───────────────────────────────────────────────

async def _fetch_graphql(
    username: str,
    limit: int,
    auth_token: str = "",
) -> list[dict]:
    """Fetch tweets via Twitter GraphQL API.

    If *auth_token* is provided, uses authenticated access (latest tweets).
    Otherwise, obtains a guest token (highlighted tweets).
    """
    try:
        cookies: dict[str, str] = {}
        if auth_token:
            cookies["auth_token"] = auth_token

        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True, cookies=cookies
        ) as client:
            # Build auth headers
            headers = {
                "Authorization": f"Bearer {BEARER}",
                "User-Agent": _UA,
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "en",
            }

            if auth_token:
                # Authenticated: need a csrf token from cookies
                ct0 = await _get_ct0(client, headers)
                if ct0:
                    headers["x-csrf-token"] = ct0
            else:
                # Guest: get a guest token
                gt = await _get_guest_token(client)
                if not gt:
                    return []
                headers["x-guest-token"] = gt

            # Step 1: Resolve screen_name → user_id
            user_id, display_name = await _resolve_user(client, headers, username)
            if not user_id:
                return []

            # Step 2: Fetch user tweets
            tweet_vars = {
                "userId": user_id,
                "count": 40,
                "includePromotedContent": False,
                "withQuickPromoteEligibilityTweetFields": False,
                "withVoice": False,
                "withV2Timeline": True,
            }
            resp = await client.get(
                "https://x.com/i/api/graphql/E3opETHurmVJflFsUBVuUQ/UserTweets",
                params={
                    "variables": json.dumps(tweet_vars),
                    "features": json.dumps(_GQL_FEATURES),
                },
                headers=headers,
            )
            if resp.status_code != 200:
                return []

            return _parse_graphql_tweets(resp.json(), username, limit)
    except Exception:
        return []


async def _get_guest_token(client: httpx.AsyncClient) -> str:
    """Extract guest token from twitter.com HTML."""
    try:
        resp = await client.get(
            "https://twitter.com/",
            headers={"User-Agent": _UA},
        )
        m = re.search(r"document\.cookie\s*=\s*[\"']gt=(\d+)", resp.text)
        return m.group(1) if m else ""
    except Exception:
        return ""


async def _get_ct0(client: httpx.AsyncClient, headers: dict) -> str:
    """Get ct0 CSRF token for authenticated sessions."""
    try:
        resp = await client.get(
            "https://x.com/",
            headers={k: v for k, v in headers.items() if k != "x-csrf-token"},
        )
        return resp.cookies.get("ct0", "")
    except Exception:
        return ""


async def _resolve_user(
    client: httpx.AsyncClient,
    headers: dict,
    screen_name: str,
) -> tuple[str, str]:
    """Resolve screen_name to (user_id, display_name)."""
    try:
        resp = await client.get(
            "https://x.com/i/api/graphql/xmU6X_CKVnQ5lSrCbAmJsg/UserByScreenName",
            params={
                "variables": json.dumps(
                    {"screen_name": screen_name, "withSafetyModeUserFields": True}
                ),
                "features": json.dumps(_USER_FEATURES),
            },
            headers=headers,
        )
        if resp.status_code != 200:
            return "", ""
        data = resp.json()
        result = data.get("data", {}).get("user", {}).get("result", {})
        return (
            result.get("rest_id", ""),
            result.get("legacy", {}).get("name", ""),
        )
    except Exception:
        return "", ""


def _parse_graphql_tweets(
    data: dict,
    username: str,
    limit: int,
) -> list[dict]:
    """Parse tweets from GraphQL UserTweets response."""
    instructions = (
        data.get("data", {})
        .get("user", {})
        .get("result", {})
        .get("timeline_v2", {})
        .get("timeline", {})
        .get("instructions", [])
    )

    items: list[dict] = []
    for instr in instructions:
        entries = []
        if instr.get("type") == "TimelineAddEntries":
            entries = instr.get("entries", [])

        for entry in entries:
            content = entry.get("content", {})
            entry_type = content.get("entryType", "")

            item_contents: list[dict] = []
            if entry_type == "TimelineTimelineItem":
                item_contents.append(content.get("itemContent", {}))
            elif entry_type == "TimelineTimelineModule":
                for sub in content.get("items", []):
                    item_contents.append(
                        sub.get("item", {}).get("itemContent", {})
                    )

            for ic in item_contents:
                tr = ic.get("tweet_results", {}).get("result", {})
                if tr.get("__typename") == "TweetWithVisibilityResults":
                    tr = tr.get("tweet", {})
                legacy = tr.get("legacy", {})
                if not legacy:
                    continue

                core_legacy = (
                    tr.get("core", {})
                    .get("user_results", {})
                    .get("result", {})
                    .get("legacy", {})
                )

                text = legacy.get("full_text", "")
                tweet_id = legacy.get("id_str", "") or tr.get("rest_id", "")
                screen_name = core_legacy.get("screen_name", username)

                items.append({
                    "title": _make_title(text),
                    "url": f"https://x.com/{screen_name}/status/{tweet_id}"
                    if tweet_id
                    else "",
                    "summary": text,
                    "author": core_legacy.get("name", screen_name),
                    "time": _parse_twitter_time(legacy.get("created_at", "")),
                    "display": "post",
                    "likes": legacy.get("favorite_count", 0),
                    "replies": legacy.get("reply_count", 0),
                    "retweets": legacy.get("retweet_count", 0),
                })

    items.sort(key=lambda x: x.get("time", 0), reverse=True)
    return items[:limit]


# ── Syndication fallback ───────────────────────────────────────────

async def _fetch_syndication(username: str, limit: int) -> list[dict]:
    """Fetch tweets via Twitter's syndication timeline endpoint."""
    url = SYNDICATION_URL.format(username=username)
    try:
        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True
        ) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": _UA,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            if resp.status_code != 200:
                return []
            html = resp.text
    except Exception:
        return []

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">', html
    )
    if not m:
        return []

    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(html, m.end())
    except (json.JSONDecodeError, ValueError):
        return []

    entries = (
        data.get("props", {})
        .get("pageProps", {})
        .get("timeline", {})
        .get("entries", [])
    )

    items: list[dict] = []
    for entry in entries:
        if entry.get("type") != "tweet":
            continue
        tweet = entry.get("content", {}).get("tweet", {})
        if not tweet:
            continue

        text = tweet.get("text", "") or tweet.get("full_text", "")
        tweet_id = tweet.get("id_str", "")
        user = tweet.get("user", {})
        screen_name = user.get("screen_name", username)

        items.append({
            "title": _make_title(text),
            "url": f"https://x.com/{screen_name}/status/{tweet_id}"
            if tweet_id
            else "",
            "summary": text,
            "author": user.get("name", screen_name),
            "time": _parse_twitter_time(tweet.get("created_at", "")),
            "display": "post",
            "likes": tweet.get("favorite_count", 0),
            "replies": tweet.get("reply_count", 0),
            "retweets": tweet.get("retweet_count", 0),
        })

    items.sort(key=lambda x: x.get("time", 0), reverse=True)
    return items[:limit]


# ── Helpers ─────────────────────────────────────────────────────────

def _parse_twitter_time(created_at: str) -> int:
    if not created_at:
        return 0
    try:
        tt = parsedate_tz(created_at)
        return int(mktime_tz(tt)) if tt else 0
    except Exception:
        return 0


def _make_title(text: str) -> str:
    """Create a short title from tweet text."""
    clean = re.sub(r"https?://\S+", "", text).strip()
    if len(clean) > 80:
        return clean[:77] + "..."
    return clean or "(media)"
