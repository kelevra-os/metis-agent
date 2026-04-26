---
name: twitter-to-markdown
description: Convert Twitter/X threads to clean markdown using vxTwitter/fxtwitter or the vxtwitter-api Python library.
version: 1.0.1
author: Metis Agent (adapted from Hermes Agent)
license: MIT

---

> **Adapted for Metis (single-agent profile).** All Twitter/X processing happens
> in-process using available tools — no delegation to subagents.

# Twitter/X to Markdown

Convert Twitter/X threads to clean markdown documents.

## When to Use

- User shares a Twitter/X link: "convert this thread to markdown"
- User asks to save a thread for later reference
- Background research involving Twitter/X discussions
- Extracting quotes, data points, or arguments from threads

## Trigger Conditions

User mentions:
- "convert [Twitter URL] to markdown"
- "save this thread"
- "extract this thread"
- Any Twitter/X URL in the conversation

## Two Approaches

### Approach 1: vxTwitter (Recommended, No API Key)

Replace `twitter.com` or `x.com` with `vxtwitter.com` in the URL, then fetch JSON:

```python
import requests

def fetch_tweet_json(url):
    """Replace twitter.com/x.com with vxtwitter.com and fetch JSON."""
    api_url = url.replace("twitter.com", "vxtwitter.com")\
                 .replace("x.com", "vxtwitter.com")
    resp = requests.get(api_url, headers={"User-Agent": "Metis/1.0"})
    return resp.json()

data = fetch_tweet_json("https://x.com/user/status/123456789")
```

The JSON response includes:
- `text` — tweet text with URLs, mentions, hashtags
- `url` — original tweet URL
- `author_name` — display name
- `author_screen_name` — @handle
- `date` — ISO date string
- `media_urls` — array of media URLs (images, video thumbnails)
- `tweets` — for threads: array of tweet objects in order

### Approach 2: vxtwitter-api Library

```bash
pip install vxtwitter-api
```

```python
from vxtwitter_api import TweetsAPI

api = TweetsAPI()
tweet = api.get_tweet("https://x.com/user/status/123456789")
```

## Script Reference

The `scripts/convert.py` file in this skill directory contains the full tweet-to-markdown converter with:
- Thread detection (auto-fetches entire thread)
- Media attachment linking
- Timestamp formatting
- Markdown output with author attribution

## Output Format

```markdown
# [Thread Title / Topic]

**Author:** @screen_name — Display Name
**Date:** March 15, 2025
**Link:** https://x.com/user/status/123456789

---

**1/** First tweet text with [links](url) and mentions.

> Key quote if applicable.

**2/** Second tweet text.

![alt text](media_url)

---

*Thread converted from Twitter/X via vxTwitter*
```

## Rate Limits

- vxTwitter is a free proxy service. No documented rate limits, but be respectful.
- Add 1-2s delays between requests when processing multiple tweets.
- For bulk processing, use Approach 2 (vxtwitter-api library).

## Pitfalls

- **Deleted tweets**: vxTwitter returns a `tombstone` or error response. Handle gracefully.
- **Private accounts**: Cannot fetch tweets from protected accounts.
- **Long threads (50+ tweets)**: vxTwitter may truncate. Fetch the first tweet and let the API resolve the thread.
- **Media**: Video thumbnails are static images; actual video URLs may expire.
- **Rate limiting**: vxTwitter has no official rate limits, but excessive requests may trigger blocks.

## Related Skills

- `youtube-content` — process video content alongside thread analysis
- `arxiv` — find academic papers referenced in a thread
- `ocr-and-documents` — extract text from screenshots in threads
