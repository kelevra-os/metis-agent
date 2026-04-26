---
name: youtube-content
description: >
  Fetch YouTube video transcripts and transform them into structured content
  (chapters, summaries, threads, blog posts). Use when the user shares a YouTube
  URL or video link, asks to summarize a video, requests a transcript, or wants
  to extract and reformat content from any YouTube video.
version: 1.0.1
author: Metis Agent (adapted from Hermes Agent)
license: MIT

---

> **Adapted for Metis (single-agent profile).** All YouTube processing happens
> in-process using available tools — no delegation to Artemis/Thoth or other
> agents. Cookie paths use `~/.hermes/profiles/metis/` instead of pantheon paths.

# YouTube Content Tool

Fetch YouTube video transcripts and transform them into structured content:
chapters, summaries, threads, blog posts.

## When to Use

- User shares a YouTube URL: "summarize this video", "get the transcript"
- User asks about a YouTube channel or specific video content
- Background research involving video lectures, talks, or tutorials
- Extracting quotes, data points, or arguments from video content

## Trigger Conditions

User mentions:
- "summarize [YouTube URL]"
- "transcript of [YouTube URL]"
- "get the content from [YouTube URL]"
- "what does [video title] say about [topic]"
- Any YouTube link in the conversation

## Two Approaches

### Approach 1: youtube-transcript-api (Recommended, No Cookies)

Uses the unofficial `youtube-transcript-api` (PyPI). Fastest, no browser needed.

```python
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "dQw4w9WgXcQ"  # Extract from URL
transcript = YouTubeTranscriptApi.get_transcript(video_id)

# Format as plain text
text = " ".join([seg["text"] for seg in transcript])
```

### Approach 2: yt-dlp (For age-restricted videos)

```python
import subprocess, json

def fetch_yt_transcript(video_url):
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-subs", "--sub-lang", "en",
        "--convert-subs", "srt",
        "-o", "/tmp/%(id)s.%(ext)s",
        video_url
    ]
    subprocess.run(cmd, check=True, timeout=60)
    # Read the SRT file
```

## Video ID Extraction

Extract video ID from various YouTube URL formats:

```python
import re

def extract_video_id(url):
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[?&]|$)",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
```

## Transcript Formatting

### Plain Text (for summarization)

```python
text = " ".join([seg["text"] for seg in transcript])
```

### Timestamped (for chapter extraction)

```python
def format_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

lines = [f"[{format_timestamp(seg['start'])}] {seg['text']}"
         for seg in transcript]
```

## Cookie-Based Extraction (Critical for Age-Restricted Content)

When youtube-transcript-api and yt-dlp both fail with `LOGIN_REQUIRED`, use Playwright with YouTube session cookies.

### Cookie File Location
- **JSON format**: `~/.hermes/profiles/metis/cookies/youtube_session.json`
- **Netscape format** (for yt-dlp): `/tmp/yt_cookies.txt`

### Cookie Requirements for Playwright — Critical Details

**Cookie file preparation** — strip these fields from each cookie: `partitionKey`, `storeId`, `firstPartyDomain`, `session`, `expirationDate`.

**`sameSite` normalization**: Playwright requires the **string** `'None'`, not Python's `None` object:
- If `sameSite` is Python `None` or `"no_restriction"` → set to **string** `'None'`
- If `sameSite` is `"lax"` (lowercase) → set to `'Lax'` (capitalized)
- Valid values: exactly `'Strict'`, `'Lax'`, `'None'` (strings)

**⚠️ Critical — Auth cookie dropping**: `ctx.add_cookies()` **silently drops** auth cookies (HSID, SSID, APISID, SAPISID, SID, LOGIN_INFO, SIDCC) even when `secure=True` is set in the dict. Chromium enforces the Secure flag at the browser level and rejects non-Secure cookies from `add_cookies()`. **Use the JavaScript injection method below instead.**

### JavaScript Cookie Injection (Required for Auth Cookies)

```python
from playwright.sync_api import sync_playwright

def inject_youtube_cookies(cookies_list):
    """Inject YouTube session cookies into the browser via JavaScript."""
    script = ""
    for c in cookies_list:
        name = c["name"]
        value = c["value"]
        domain = c.get("domain", ".youtube.com")
        path = c.get("path", "/")
        secure = "true" if c.get("secure", False) else "false"
        same_site = c.get("sameSite", "Lax")
        script += f'document.cookie = "{name}={value};domain={domain};path={path};secure={secure};sameSite={same_site}";\n'
    page.evaluate(script)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
    )
    page = context.new_page()
    page.goto("https://www.youtube.com", wait_until="networkidle")
    inject_youtube_cookies(cookies)
    page.goto(video_url, wait_until="networkidle")
    # Proceed with scraping
```

### Cookie Preparation Script

A full script lives at `scripts/fetch_transcript.py` in this skill directory.

## Output Formats

### Summary Format

```
## [Video Title]

**Channel:** [Channel Name]  **Duration:** [MM:SS]
**Link:** [YouTube URL]

**TL;DR:** 2-3 sentence summary of the video's core message.

### Key Points
1. First key point from the video
2. Second key point
3. Third key point

### Notable Quotes
> "[Exact quote from video]"

### Related Topics
- Links to wiki pages or relevant background
```

### Chaptered Summary

```
## [Video Title]

**0:00 - [Chapter 1 Title]**
Summary of chapter 1 content.

**[MM:SS] - [Chapter 2 Title]**
Summary of chapter 2 content.
```

## Installation Dependencies

```bash
pip install youtube-transcript-api yt-dlp
# For cookie-based extraction
pip install playwright
playwright install chromium
```

## Pitfalls

- **Age-restricted videos**: Require cookie-based auth. Use Playwright + session cookies.
- **Language codes**: Some videos only have `a.en` (auto-generated English) or localized subs. Try `["en", "a.en", "en-US"]`.
- **Long videos (3h+)**: Transcripts can be 30K+ words. Use chunking for summaries.
- **Rate limiting**: YouTube may throttle rapid requests. Add 2-3s delays between extraction attempts.
- **Deleted/unavailable videos**: yt-dlp returns exit code 1; catch and report clearly.

## Related Skills

- `ocr-and-documents` — extract text from slides or papers referenced in a video
- `arxiv` — find academic papers mentioned or related to video content
