---
name: metis-wormhole-intake
description: Accept files shared via Wormhole or Send links, download them, process the content (PDF, image, text, audio), summarize it for the user, and optionally save structured notes to the Obsidian vault.
---

# Metis Wormhole / Send File Intake

## Purpose

Securely accept files sent via Wormhole or Send Protocol links, process them into usable content, and optionally save summaries and key points to the Obsidian vault. Designed for Metis's role as a warm, Socratic thinking partner — the goal is understanding what the file contains and connecting it to your thinking, not just storing bytes.

## When to Use

- Ru or someone shares a Wormhole link like `https://wormhole.app/XXXX#YYYY`
- Someone shares a Send / ffsend link
- A direct file URL arrives in chat and needs local capture
- The file needs processing: PDF extraction, image OCR, text analysis

**Do NOT rely on this skill for:** voice memos or audio transcription (tagged as future capability), or for files that can simply be fetched with `curl` / `wget` (use `url-file-intake` for those).

## Metis Personality for This Skill

When processing files, speak in your warm, conversational voice:

- **After download**: "I've got the file — let me take a look inside."
- **After processing**: "Here's what I found... Does any of this feel worth saving?"
- **When saving**: "Let me tuck this into your vault so you can find it later."
- **For known domains**: "Ah, this looks like a paper from your research queue — I'll handle it the same way I've done before."

Avoid dry, technical play-by-play of the pipeline. The user sees the result, not the gears.

## Workflow

### Step 1: Identify the link type

When the user shares a URL, quickly classify it:

| Pattern | Provider | Strategy |
|---------|----------|----------|
| `wormhole.app/...` or `wormhole.com/...` | Wormhole | Camofox browser download |
| Contains `send.vis.ee`, `send` in host | Send / ffsend | `ffsend` CLI (preferred) or Camofox fallback |
| `arxiv.org/abs/...` or `arxiv.org/pdf/...` | arXiv | Use arxiv skill for metadata + PDF |
| `youtube.com/...`, `youtu.be/...` | YouTube | Use youtube-content skill |
| `twitter.com/...`, `x.com/...` | Twitter/X | Use twitter-to-markdown skill |
| Any other direct file URL | Direct | Use url-file-intake or curl/wget |

### Step 2: Download the file

**For Wormhole links:**
Use the Camofox browser pipeline. The intake script lives at `~/.hermes/scripts/wormhole-intake.py` within the Hermes agent environment (not Metis-specific). Metis can invoke it from the system Hermes install:

```bash
# Ensure Camofox is running
docker ps | grep camofox

# Run the intake script from the Hermes agent venv
~/.hermes/hermes-agent/venv/bin/python ~/.hermes/scripts/wormhole-intake.py \
  "https://wormhole.app/XXXX#YYYY" \
  --intake-dir /home/hermes/intake
```

If Camofox is unavailable or fails, fall back to Hermes browser tools (`browser_navigate`, `browser_snapshot`, `browser_click`) to navigate the Wormhole page and trigger the download.

**For Send / ffsend links:**
Prefer the CLI:

```bash
ffsend download -I -o /home/hermes/intake/ '<share-url>'
```

If `ffsend` is not installed, try a Camofox browser approach as fallback.

**For direct file URLs:**
Use `url-file-intake` approach — download with curl/wget to `/home/hermes/intake/`.

**For arXiv, YouTube, Twitter:**
Use the respective integration skills to fetch content directly, bypassing the file-download pipeline.

### Step 3: Verify the download

Confirm the file exists, is non-zero, and is readable:

```bash
ls -lh /home/hermes/intake/
file /home/hermes/intake/<filename>
```

If the download failed, report the error conversationally and suggest retrying or using an alternative share method.

### Step 4: Determine file type and process content

Classify by MIME type or extension:

#### PDF files
Extract text with pdfplumber (from the Hermes agent venv):

```python
import pdfplumber, json
with pdfplumber.open("/home/hermes/intake/<file>.pdf") as pdf:
    pages = len(pdf.pages)
    # Extract first few pages for summary
    text = "\n".join(
        pdf.pages[i].extract_text() or ""
        for i in range(min(5, pages))
    )
```

Present: document title (from first content page), page count, first few lines of content, key themes you can detect.

#### Images (PNG, JPG, JPEG, WEBP, GIF)
Use OCR to extract text. The agent has vision tools available — use `vision_analyze` on the image file to get a description and extract any visible text.

If tesseract is available on the system:

```bash
tesseract /home/hermes/intake/<image>.png /home/hermes/intake/<image>-ocr-output 2>/dev/null
cat /home/hermes/intake/<image>-ocr-output.txt
```

Present: what the image shows, extracted text if any, notable visual elements.

#### Text files (TXT, MD, CSV, JSON, LOG)
Read directly with `read_file`. For long files, read the first 100-200 lines and summarize.

Present: file type, line count, first few lines, key topics detected, any patterns or data worth noting.

#### Markdown files
Read and render the content. If it appears to be a structured document (meeting notes, research notes, etc.), note the structure (headings, lists, links).

#### Audio files (MP3, WAV, OGG, M4A, FLAC)
Note to the user: "I've received the audio file, but voice transcription isn't wired up yet. I've saved it to your intake folder — when audio processing arrives, I can transcribe and summarize it." Save the file path for future processing.

#### Archives (ZIP, TAR, GZ)
List contents:

```bash
unzip -l /home/hermes/intake/<file>.zip 2>/dev/null | head -30
# or
tar tf /home/hermes/intake/<file>.tar.gz 2>/dev/null | head -30
```

Present: archive contents, number of files, notable filenames. Ask if they want it extracted.

#### Other / unknown
Report the file type from `file` command and size. Ask what they'd like to do.

### Step 5: Present a summary to the user

In your warm Metis voice, share:

- **What it is**: filename, type, size
- **What's inside**: a concise, readable summary of the content
- **Key takeaways**: 2-4 bullet points of the most important or interesting content
- **Connections**: if the content relates to anything in their Obsidian vault or past conversations, mention it

Example:

> I've pulled down that paper you shared — *"Building Agentic AI Systems"* by Biswas (2025, Packt). It's 380 pages covering agent architectures, tool-use patterns, and multi-agent coordination. The opening chapters lay out a nice taxonomy of agent autonomy levels that feels relevant to your Metis work. Want me to save the key frameworks to your vault?

### Step 6: Ask about saving to Obsidian

Always offer to save. Phrase it naturally:

- "Would you like me to save a summary of this to your vault?"
- "Want me to capture the key points in Obsidian?"
- "I can write a source note for this — shall I?"

If they say yes, proceed to Step 7. If no, acknowledge and move on.

### Step 7: Save to Obsidian (using metis-obsidian skill)

Use the `metis-obsidian` skill to write a structured source note. Follow the `source-note.md` template:

```
---
created: {{date}}
tags: [source, reference, ingested]
source_url: {{url}}
source_type: pdf|image|text|audio|archive|other
---

# {{title}}

**Source:** {{url}}
**Author:** {{author if known}}
**File:** {{path to file in intake}}

## Summary

{{concise summary of the content}}

## Key Points

- {{point 1}}
- {{point 2}}
- {{point 3}}
...

## Notable Quotes

> {{quote 1}}

> {{quote 2}}

## Connections

- Relates to [[{{related_topic}}]]
- Relevant to [[{{project}}]]
```

The note goes into the vault configured in Metis's `.env` file.

After writing:
1. Save the markdown file to the vault path
2. `git add`, `git commit`, `git push` to the vault's remote
3. Confirm to the user: "Saved to your vault as **[Title]**. You can find it linked from your daily note."

### Step 8: Cleanup

After processing, clean up the intake file only if the user confirms it's no longer needed. Optionally move to a permanent archive directory if they want to keep the original.

## Integration with Other Link Types

### arXiv papers
Use the arxiv skill to:
1. Fetch the abstract and metadata
2. Download the PDF
3. Extract and summarize
4. Offer to save as a source note with arXiv metadata (authors, published date, categories)

### YouTube videos
Use the youtube-content skill to:
1. Fetch the transcript
2. Summarize the video content
3. Offer to save as a source note

### Twitter/X threads
Use the twitter-to-markdown skill to:
1. Convert the thread to clean markdown
2. Summarize the thread's argument or narrative
3. Offer to save as a source note

## Pitfalls

### Camofox availability
The Wormhole download pipeline requires the Camofox browser Docker container running on `localhost:9377`. If it's not running, the intake script will fail with a connection error. Check with `docker ps | grep camofox` and start it if needed.

### Camofox port conflicts
Only ONE Camofox instance should run. If a local Node process is also on port 9377, kill it:
```bash
lsof -ti:9377 | xargs kill -9 2>/dev/null; docker restart camofox
```

### Large files (>50MB)
The intake script handles inline data up to 50MB natively, and falls back to temp files for larger downloads. Very large files (200MB+) may cause memory pressure on a 4GB server.

### Long filenames
Wormhole files can have extremely long filenames that truncate awkwardly. The intake script preserves file extensions when truncating, but double-check if the saved filename looks odd.

### No ffsend installed
If `ffsend` is not on the system, Send links fall back to browser download. Let the user know the file landed but the CLI would be faster if installed.

### Audio transcription not yet available
Clearly flag to the user that audio files are received and saved but not yet transcribed. Don't leave them wondering.

### OCR quality
For scanned PDFs and images, OCR quality varies significantly. Flag "OCR-extracted text, may contain errors" in the summary.

## Prerequisites

- Camofox browser container (for Wormhole downloads)
- pdfplumber (in Hermes agent venv)
- tesseract-ocr (optional, for image OCR)
- ffsend (optional, for Send Protocol CLI)
- Hermes browser tools (fallback for failed automated downloads)
- Metis Obsidian skill (for vault saves)

## Verification

After running the intake pipeline, verify:

- [ ] File downloaded and saved to `/home/hermes/intake/`
- [ ] File type correctly identified
- [ ] Content extracted and summarized
- [ ] Summary presented to user in warm Metis voice
- [ ] User asked about saving to vault
- [ ] If yes: source note written, committed, and pushed
- [ ] Cleanup confirmed or file archived

## Related

- `url-file-intake` — direct URL download when possible
- `link-based-file-intake` — general link intake orchestration
- `camofox-sharing-link-intake` — Camofox-specific browser download pipeline
- `wiki-ingest-pdf` — PDF extraction and wiki page synthesis (Hermes-level, deeper than Metis source notes)
- `metis-obsidian` — vault note writing, source note templates
- `arxiv` — arXiv paper metadata and PDF fetching
- `youtube-content` — YouTube transcript and summary
- `twitter-to-markdown` — Twitter/X thread ingestion
- `ocr-and-documents` — OCR for scanned/image PDFs
