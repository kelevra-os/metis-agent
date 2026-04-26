#!/usr/bin/env python3
"""
Twitter/X to Markdown converter.
Tries multiple backends in order:
1. api.fxtwitter.com (works for older/cached tweets)
2. syndication.twitter.com profile timeline (fallback, extracts recent tweets)
"""

import sys
import json
import re
import html
import urllib.request
import urllib.error


def fetch_fxtwitter(username: str, tweet_id: str) -> dict | None:
    """Try fxtwitter API for a specific tweet."""
    url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            if data.get("tweet"):
                return data
    except Exception as e:
        print(f"[fxtwitter] Failed: {e}", file=sys.stderr)
    return None


def fetch_syndication_timeline(username: str, count: int = 10) -> list[dict]:
    """Get recent tweets from a user via syndication timeline."""
    url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}?count={count}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            decoded = html.unescape(raw)
            tweets = extract_tweets_from_html(decoded)
            return tweets
    except Exception as e:
        print(f"[syndication] Failed: {e}", file=sys.stderr)
    return []


def extract_tweets_from_html(html_content: str) -> list[dict]:
    """Parse tweets from syndication HTML page."""
    tweets = []
    # Try to find tweet objects in the page
    # Look for tweetId patterns
    id_pattern = re.compile(r'"tweetId"\s*:\s*"(\d+)"')
    text_pattern = re.compile(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"')

    # Find all tweet ID matches with their approximate position
    ids = id_pattern.findall(html_content)
    texts = text_pattern.findall(html_content)

    # Also try full_text
    full_text_pattern = re.compile(r'"full_text"\s*:\s*"((?:[^"\\]|\\.)*)"')
    full_texts = full_text_pattern.findall(html_content)

    # Combine texts (prefer full_text over text)
    all_texts = full_texts if full_texts else texts

    for i, tweet_id in enumerate(ids):
        text = all_texts[i] if i < len(all_texts) else ""
        # Unescape common HTML entities
        text = text.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
        tweets.append({"id": tweet_id, "text": text})

    return tweets


def extract_article_text(tweet: dict) -> str:
    """Extract text from tweet article (long-form tweet/note)."""
    article = tweet.get("article", {})
    if not article:
        return tweet.get("text", "") or tweet.get("raw_text", {}).get("text", "")

    blocks = article.get("content", {}).get("blocks", [])
    parts = []
    for block in blocks:
        block_type = block.get("type", "")
        block_text = block.get("text", "")
        if block_type == "unstyled" and block_text:
            parts.append(block_text)
        elif block_type in ("header-two", "header-one"):
            parts.append(f"### {block_text}")
        elif block_type == "ordered-list-item":
            parts.append(f"1. {block_text}")
        elif block_type == "unordered-list-item":
            parts.append(f"- {block_text}")
    return "\n\n".join(parts)


def tweet_to_markdown(username: str, tweet_id: str, tweet: dict, is_thread: bool = False, index: int = 0) -> str:
    """Convert a single tweet to markdown."""
    prefix = f"## Tweet {index + 1}" if is_thread else "## Tweet"
    text = extract_article_text(tweet)

    # Media
    media = tweet.get("media_entities", [])
    media_links = []
    for m in media:
        url = m.get("media_info", {}).get("original_img_url", "")
        if url:
            media_links.append(f"<!-- media: {url} -->")

    media_md = "\n".join(media_links) if media_links else ""

    author = tweet.get("author", {})
    author_name = author.get("name", username)

    return f"""{prefix}

**Author:** {author_name} (@{username})
**Tweet ID:** {tweet_id}
**Source:** [Original Tweet](https://x.com/{username}/status/{tweet_id})
**Likes:** {tweet.get("likes", 0)} | **Retweets:** {tweet.get("retweets", 0)} | **Views:** {tweet.get("views", "N/A")}

{text}

{media_md}
---
"""


def convert_thread(tweets: list[dict], username: str) -> str:
    """Convert a list of tweets to a thread markdown."""
    if not tweets:
        return "No tweets found."

    md = f"""# Tweet Thread: @{username}

**Source:** [Profile Timeline](https://x.com/{username})

---

"""

    for i, tweet in enumerate(tweets):
        md += tweet_to_markdown(username, tweet["id"], tweet["text"], is_thread=True, index=i)

    return md


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert.py <tweet_url_or_username> [tweet_id]")
        print("Examples:")
        print("  python convert.py OpenAI 1885117291586695342")
        print("  python convert.py OpenAI")
        sys.exit(1)

    username = sys.argv[1]
    tweet_id = sys.argv[2] if len(sys.argv) > 2 else None

    if tweet_id:
        # Try specific tweet first
        result = fetch_fxtwitter(username, tweet_id)
        if result:
            tweet = result["tweet"]
            md = tweet_to_markdown(username, tweet.get("id", tweet_id), tweet)
            print(md)
            return

        # Fallback: get timeline and find the tweet
        print("# Falling back to timeline extraction...", file=sys.stderr)
        tweets = fetch_syndication_timeline(username, count=20)
        matching = [t for t in tweets if t["id"] == tweet_id]
        if matching:
            print(tweet_to_markdown(username, tweet_id, {"id": tweet_id, "text": matching[0]["text"]}))
            return
        print(f"# Tweet {tweet_id} not found in recent timeline", file=sys.stderr)
    else:
        # Get timeline
        tweets = fetch_syndication_timeline(username, count=10)
        print(convert_thread(tweets, username))


if __name__ == "__main__":
    main()
