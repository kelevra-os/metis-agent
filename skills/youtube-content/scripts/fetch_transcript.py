#!/usr/bin/env python3
"""
Fetch a YouTube video transcript and output it as structured JSON.

Usage:
    python fetch_transcript.py <url_or_video_id> [--language en,tr] [--timestamps]

Output (JSON):
    {
        "video_id": "...",
        "language": "en",
        "segments": [{"text": "...", "start": 0.0, "duration": 2.5}, ...],
        "full_text": "complete transcript as plain text",
        "timestamped_text": "00:00 first line\n00:05 second line\n..."
    }

Fallback chain:
  1. youtube-transcript-api (primary — uses official subtitles/captions)
  2. yt-dlp --write-auto-sub (downloads auto-generated SRT subtitles)
  3. Whisper (downloads audio, runs openai/whisper transcription)

Install dependencies:
    pip install youtube-transcript-api openai-whisper
  (yt-dlp must also be installed and on PATH for fallback #2 and #3)

NOTE: yt-dlp requires a JS runtime for YouTube. This script passes
  --js-runtimes node --remote-components ejs:github
to yt-dlp to (a) use the node binary already in PATH and (b) download
the EJS challenge solver from GitHub. This unblocks downloads on servers
that would otherwise hit YouTube's "sign in to confirm" bot wall.

PROXY AUTHENTICATION (required for residential proxies):
  Set YOUTUBE_PROXY env var in format: http://user:pass@host:port
  Example: export YOUTUBE_PROXY="http://YzPDFyZm:t6vUfKgPxX@192.46.187.217:6795"
  Note: user:pass must be URL-encoded if they contain special characters.

COOKIES (required for age-restricted / geo-blocked videos):
  Set YOUTUBE_COOKIES env var to path of Netscape-format cookie file.
  Or use --cookies CLI flag.
  Cookie file must NOT have leading dots on domain names (Python http.cookiejar bug).
  Tip: use the Cookie-Editor Chrome extension to export as Netscape format,
  then strip leading dots from domain names if you get format errors.
"""

import argparse
import json
import os
import re
import sys


def extract_video_id(url_or_id: str) -> str:
    """Extract the 11-character video ID from various YouTube URL formats."""
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _build_ytdlp_base_args(proxy: str = None, cookies: str = None) -> list:
    """Build common yt-dlp args for proxy and cookie auth."""
    args = ["--js-runtimes", "node", "--remote-components", "ejs:github"]
    if proxy:
        args.extend(["--proxy", proxy])
    if cookies:
        args.extend(["--cookies", cookies])
    return args


def fetch_transcript_with_ytdlp(video_id: str, languages: list = None,
                                  proxy: str = None, cookies: str = None):
    """Fallback #2: use yt-dlp to download auto-generated SRT subtitles.

    Runs: yt-dlp --write-auto-sub --sub-lang en --skip-download --convert-subs srt <url>
    Then parses the resulting .srt file into segments.
    """
    import subprocess
    import tempfile
    import os

    url = f"https://youtu.be/{video_id}"
    lang = (languages[0] if languages else "en")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "yt-dlp",
            "--write-auto-sub", f"--sub-lang={lang}",
            "--skip-download",
            "--convert-subs", "srt",
            "--output", os.path.join(tmpdir, "subtitle"),
        ] + _build_ytdlp_base_args(proxy, cookies) + [url]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
        except subprocess.TimeoutExpired:
            return None, "yt-dlp timed out"
        except FileNotFoundError:
            return None, "yt-dlp not installed"

        if result.returncode != 0:
            return None, f"yt-dlp failed: {result.stderr.strip()}"

        # Find the generated .srt file
        srt_files = [f for f in os.listdir(tmpdir) if f.endswith(".srt")]
        if not srt_files:
            return None, "No SRT file generated"
        srt_path = os.path.join(tmpdir, srt_files[0])

        return _parse_srt(srt_path), None


def _parse_srt(srt_path: str) -> list:
    """Parse an SRT file into segments with text, start, duration."""
    import re

    segments = []
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # SRT block pattern: index, timestamp, text, blank line
    pattern = re.compile(
        r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n([\s\S]*?)(?=\n\n\d+\s*\n|$)",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        start_str = match.group(2).replace(",", ".")
        end_str = match.group(3).replace(",", ".")
        text = match.group(4).strip()

        def to_seconds(ts):
            parts = ts.split(":")
            h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s

        start = to_seconds(start_str)
        end = to_seconds(end_str)
        segments.append({"text": text, "start": start, "duration": end - start})

    return segments


def fetch_transcript(video_id: str, languages: list = None,
                     proxy: str = None, cookies: str = None):
    """Fetch transcript segments from YouTube.

    Fallback chain:
      1. youtube-transcript-api (primary)
      2. yt-dlp --write-auto-sub (fallback #2)
      3. Whisper — download audio + openai/whisper transcription (fallback #3)

    Returns a list of dicts with 'text', 'start', and 'duration' keys.
    Compatible with youtube-transcript-api v1.x.

    Args:
        proxy: HTTP proxy with embedded auth, e.g. "http://user:pass@host:port"
        cookies: Path to Netscape-format cookie file for authenticated requests
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        pass  # fall through to yt-dlp
    else:
        api = YouTubeTranscriptApi()
        try:
            if languages:
                result = api.fetch(video_id, languages=languages)
            else:
                result = api.fetch(video_id)
            # v1.x returns FetchedTranscriptSnippet objects; normalize to dicts
            return [
                {"text": seg.text, "start": seg.start, "duration": seg.duration}
                for seg in result
            ]
        except Exception:
            pass  # fall through to yt-dlp fallback

    # Fallback #2: yt-dlp auto-subs
    segments, err = fetch_transcript_with_ytdlp(video_id, languages, proxy, cookies)
    if segments is not None:
        return segments

    # Fallback #3: Whisper audio transcription
    segments, err = fetch_transcript_with_whisper(video_id, languages, proxy, cookies)
    if segments is not None:
        return segments

    # All three methods failed — raise with combined context
    raise RuntimeError(
        f"youtube-transcript-api failed, yt-dlp fallback also failed, "
        f"and Whisper fallback also failed: {err}"
    )


def fetch_transcript_with_whisper(video_id: str, languages: list = None,
                                    proxy: str = None, cookies: str = None):
    """Fallback #3: download audio with yt-dlp and transcribe with Whisper.

    Downloads the audio via yt-dlp, then runs openai/whisper (CPU inference).
    Cleans up the audio file automatically on success or failure.
    Returns (segments, None) on success, (None, error_string) on failure.

    Args:
        proxy: HTTP proxy with embedded auth, e.g. "http://user:pass@host:port"
        cookies: Path to Netscape-format cookie file for authenticated requests
    """
    import subprocess
    import tempfile
    import os

    url = f"https://youtu.be/{video_id}"
    # Prefer small model for speed; base is a good balance of speed/accuracy.
    # Model selection: tiny|base|small|medium|large
    whisper_model = os.environ.get("WHISPER_MODEL", "base")
    lang_code = languages[0] if languages else None

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")

        # Download audio only — best audio format yt-dlp can get
        dl_cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--output", audio_path.replace(".mp3", ""),
        ] + _build_ytdlp_base_args(proxy, cookies) + [url]
        try:
            result = subprocess.run(
                dl_cmd, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            return None, "yt-dlp audio download timed out"
        except FileNotFoundError:
            return None, "yt-dlp not installed"

        if result.returncode != 0:
            return None, f"yt-dlp audio download failed: {result.stderr.strip()}"

        # Find the file yt-dlp actually created (extension may differ)
        audio_files = [
            f for f in os.listdir(tmpdir)
            if os.path.isfile(os.path.join(tmpdir, f))
        ]
        if not audio_files:
            return None, "No audio file downloaded"
        audio_path = os.path.join(tmpdir, audio_files[0])

        # Run Whisper transcription
        try:
            import whisper
        except ImportError:
            return None, "openai-whisper not installed"

        model = whisper.load_model(whisper_model)
        lang_arg = {"language": lang_code} if lang_code else {}
        result = model.transcribe(audio_path, **lang_arg)

        # Whisper returns flat text + segments with start/duration
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "text": seg["text"].strip(),
                "start": seg["start"],
                "duration": seg["end"] - seg["start"],
            })

        # Audio file is cleaned up automatically when tmpdir exits
        return segments, None


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript as JSON")
    parser.add_argument("url", help="YouTube URL or video ID")
    parser.add_argument("--language", "-l", default=None,
                        help="Comma-separated language codes (e.g. en,tr). Default: auto")
    parser.add_argument("--timestamps", "-t", action="store_true",
                        help="Include timestamped text in output")
    parser.add_argument("--text-only", action="store_true",
                        help="Output plain text instead of JSON")
    parser.add_argument("--list-subs", action="store_true",
                        help="List available subtitle languages and exit (yt-dlp --list-subs)")
    # Hetzner server defaults: use proxy + merged cookie file unless overridden
    default_proxy = os.environ.get("YOUTUBE_PROXY") or "http://yzpdfyzm:t6vufkgppxim@130.180.231.182:8324"
    default_cookies = os.environ.get("YOUTUBE_COOKIES") or "/tmp/yt_cookies_with_auth.txt"
    parser.add_argument("--proxy", default=default_proxy,
                        help="HTTP/SOCKS5 proxy with auth (default: 130.180.231.182:8324 via YOUTUBE_PROXY env or hardcoded)")
    parser.add_argument("--cookies", default=default_cookies,
                        help="Path to Netscape-format cookie file (default: /tmp/yt_cookies_with_auth.txt)")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    languages = [l.strip() for l in args.language.split(",")] if args.language else None

    # --list-subs: check available subtitle languages without downloading
    if args.list_subs:
        import subprocess
        url = f"https://youtu.be/{video_id}"
        list_cmd = [
            "yt-dlp",
            "--list-subs",
        ] + _build_ytdlp_base_args(args.proxy, args.cookies) + [url]
        try:
            result = subprocess.run(
                list_cmd, capture_output=True, text=True, timeout=60
            )
        except subprocess.TimeoutExpired:
            print(json.dumps({"error": "--list-subs timed out"}))
            sys.exit(1)
        except FileNotFoundError:
            print(json.dumps({"error": "yt-dlp not installed"}))
            sys.exit(1)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(json.dumps({"error": result.stderr.strip()}))
            sys.exit(1)
        sys.exit(0)

    try:
        segments = fetch_transcript(video_id, languages, proxy=args.proxy, cookies=args.cookies)
    except Exception as e:
        error_msg = str(e)
        if "disabled" in error_msg.lower():
            print(json.dumps({"error": "Transcripts are disabled for this video."}))
        elif "no transcript" in error_msg.lower():
            print(json.dumps({"error": f"No transcript found. Try specifying a language with --language."}))
        else:
            print(json.dumps({"error": error_msg}))
        sys.exit(1)

    full_text = " ".join(seg["text"] for seg in segments)
    timestamped = "\n".join(
        f"{format_timestamp(seg['start'])} {seg['text']}" for seg in segments
    )

    if args.text_only:
        print(timestamped if args.timestamps else full_text)
        return

    result = {
        "video_id": video_id,
        "segment_count": len(segments),
        "duration": format_timestamp(segments[-1]["start"] + segments[-1]["duration"]) if segments else "0:00",
        "full_text": full_text,
    }
    if args.timestamps:
        result["timestamped_text"] = timestamped

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
