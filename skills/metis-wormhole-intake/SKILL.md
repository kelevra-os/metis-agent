---
name: metis-wormhole-intake
description: Accept files shared via Wormhole or Send Protocol links, download them, extract content, present a summary, and optionally save to the Obsidian vault. Also handles direct URLs to arxiv papers, YouTube videos, and Twitter threads.
---

# Metis Wormhole Intake

Use when the user shares a Wormhole link, Send link, or other file-sharing URL and wants Metis to fetch, process, and optionally store the content.

Also invoked when the user shares an **arxiv**, **YouTube**, or **Twitter/X** URL — Metis uses the appropriate specialized skill to extract and summarize content, then offers to save to Obsidian.

## Trigger phrases

Any message containing:
- A Wormhole / magic-wormhole URL
- A Send / ffsend URL
- A direct download URL (PDF, image, .md, .txt, audio, etc.)
- An arxiv URL (`arxiv.org/abs/...` or `arxiv.org/pdf/...`)
- A YouTube URL (`youtube.com/watch`, `youtu.be/...`)
- A Twitter/X URL (`x.com/...` or `twitter.com/...`)
- "here's a file", "check this attachment", "download this", "intake this"
- "can you look at this", "processing this file", "read this for me"

## Workflow overview

```
User sends a link
   │
   ├── arxiv URL    ──► arxiv handler
   ├── YouTube URL  ──► youtube-content handler
   ├── Twitter/X URL ──► twitter-to-markdown handler
   ├── Wormhole URL ──► url-file-intake handler
   ├── Send URL     ──► ffsend download
   └── direct URL   ──► curl/wget download
          │
          ▼
   Determine file type
          │
          ├── PDF (text)      ──► extract text
          ├── PDF (scanned)   ──► OCR
          ├── Image (jpg/png) ──► OCR + vision analysis
          ├── Markdown (.md)  ──► read directly
          ├── Text (.txt)     ──► read directly
          ├── Audio           ──► note: voice processing coming later
          └── Unknown/other   ──► present raw + ask user
          │
          ▼
   Present summary to user
          │
          ▼
   Ask: "Save this to Obsidian vault?"
   If yes ──► metis-obsidian skill ──► write source note in vault
            ──► git add/commit/push
```

## Step 1 — Determine URL type and dispatch

Identify what kind of link the user shared:

| Pattern | Handler |
|---------|---------|
| `arxiv.org/abs/*` or `arxiv.org/pdf/*` | Use arxiv skill to fetch abstract + full text |
| `youtube.com/watch*` or `youtu.be/*` | Use youtube-content skill for transcript + summary |
| `x.com/*` or `twitter.com/*` or `twttr.com/*` | Use twitter-to-markdown to extract thread content |
| `wormhole:` URI or magic-wormhole code | Use url-file-intake pattern |
| `send.vis.ee/*` or `ffsend` link | Use `ffsend download` |
| Ends in `.pdf`, `.png`, `.jpg`, `.jpeg`, `.txt`, `.md`, `.mp3`, `.wav`, `.m4a` | Direct file download via curl/wget |
| Any other URL | Attempt direct download; if that fails, ask the user what to do |

### arxiv URLs
1. Load the arxiv skill: fetch abstract, full-text (if available), and metadata (authors, date, categories).
2. Present a structured summary: title, authors, abstract, key contributions.
3. Ask if the user wants it saved to Obsidian.

### YouTube URLs
1. Load the youtube-content skill: fetch transcript, auto-generate chapters, extract key topics.
2. Present a structured summary: title, duration, key points, notable quotes.
3. Ask if the user wants it saved to Obsidian.

### Twitter/X URLs
1. Load the twitter-to-markdown skill: extract thread content into clean markdown.
2. Present a summary of the thread: author, topic, key arguments, notable tweets.
3. Ask if the user wants it saved to Obsidian.

## Step 2 — Download the file

For file-sharing links (Wormhole, Send, direct URLs):

### Wormhole links
- Use the `url-file-intake` skill pattern for Wormhole links.
- If Wormhole code is given (e.g. `1234-abcdef`), use `wormhole receive <code>` via terminal.
- If no `wormhole` CLI is available, use the browser-based camofox approach from `url-file-intake` skill.
- Download destination: `/home/hermes/intake/` by default (create if not present).
- Always verify: file exists, file size is nonzero, filename is sensible.

### Send / ffsend links
- Use `ffsend download -Iy -o /home/hermes/intake/ '<url>'` if ffsend is installed.
- If the link has a password, pass it with `--password <password>`.
- If ffsend is unavailable, try browser-based download via `url-file-intake`.

### Direct download URLs
- Use `curl -L -o /home/hermes/intake/<filename> '<url>'` or `wget -O /home/hermes/intake/<filename> '<url>'`.
- If the filename can be inferred from the URL or Content-Disposition header, use that.
- Default to a sanitized filename if none is provided.

## Step 3 — Determine file type

After download, inspect the file to determine its type:

| Extension / MIME | Type |
|------------------|------|
| `.pdf` | PDF — extract text (or OCR if scanned) |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | Image — OCR + vision analysis |
| `.md`, `.markdown` | Markdown — read directly |
| `.txt`, `.log`, `.csv`, `.json`, `.yaml`, `.xml`, `.toml` | Plain text — read directly |
| `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`, `.opus` | Audio — note: voice processing coming later |
| `.docx`, `.doc`, `.odt` | Word doc — extract with python's `python-docx` or `textract` |
| `.epub` | Ebook — extract with `ebook-convert` or python |
| `.html`, `.htm` | HTML — strip tags, extract text |
| `.zip`, `.tar.gz`, `.tar`, `.7z` | Archive — note: archive processing coming later |
| Everything else | Try reading as text; fall back to informing the user |

### File type detection
- Use `file --mime-type <path>` on the downloaded file for reliable MIME detection.
- Fall back to extension-based detection if `file` is unavailable.

## Step 4 — Extract content

### PDF (text-based)
- Use `pdftotext <path> -` (poppler-utils) to extract plain text.
- Use `python -m pypdf <path>` or `PyMuPDF` (`fitz`) if poppler-utils is unavailable.
- If the extracted text is very short (< 200 chars), assume the PDF is scanned and proceed to OCR.
- For scanned PDFs, use `python -c "import pytesseract; from pdf2image import convert_from_path; ..."` or note to user that OCR needs setup.

### PDF (scanned) — OCR
- Convert PDF pages to images with `pdf2image` (`poppler-utils` required).
- Run OCR with `pytesseract` or `tesseract <image> stdout`.
- Concatenate text from all pages.

### Images — OCR + vision analysis
- Use `tesseract <image> stdout` for text OCR.
- Use vision_analyze tool on the image for context and description.
- Combine OCR text and vision description into a complete summary.

### Plain text / Markdown
- Read the full file content. For very large files (>100KB), read the first 200 lines and note the total size.
- Detect if it's markdown: check for `# `, `## `, `[text](url)`, `- ` or `* ` at line starts, or `---` frontmatter.
- If markdown, try to render a brief HTML preview or extract the first heading and key sections.

### Audio files
- Note to the user: "Voice and audio processing will be added later. The file has been saved to /home/hermes/intake/<filename> and will be available for future processing."
- Save the file path and let the user know it's staged for later.

### Other formats
- If the file is binary and doesn't match any supported type, present the filename, size, and MIME type to the user and ask how they'd like to proceed.
- If the file is text-based but in an unknown format, try reading the first 50 lines and present a sample.

## Step 5 — Present a summary

Format the summary clearly:

```
📥 Files received: <filename>
   Size: <human-readable size>
   Type: <MIME type or detected format>

📋 Content Summary
━━━━━━━━━━━━━━━━━━
<concise summary of extracted content>

Key points:
• <point 1>
• <point 2>
• <point 3>
(up to 5 key points)
━━━━━━━━━━━━━━━━━━
```

For link-based content (arxiv, YouTube, Twitter):
```
📥 <arxiv | YouTube | Twitter> Content
━━━━━━━━━━━━━━━━━━
Title: <title>
<type-specific metadata>
━━━━━━━━━━━━━━━━━━

Summary:
<concise summary>

Key points:
• <point 1>
• <point 2>
• <point 3>
```

## Step 6 — Offer Obsidian save

Directly after the summary, ask the user:

> "Would you like me to save this to your Obsidian vault? I'll create a source note with the key content."

Wait for the user's response. If they say yes, proceed to Step 7.

If they say no or want a different treatment, respect their preference. Possible alternatives:
- Save a shorter note
- Save to a specific folder in the vault
- Don't save, just keep in conversation
- Schedule for later processing

## Step 7 — Save to Obsidian vault

If the user wants the content saved:

1. Load the **metis-obsidian** skill to understand how Obsidian notes are structured and committed.

2. Determine a good title for the note:
   - For files: `<original filename without extension>`
   - For arxiv: `@ <First Author> - <Paper Title>`
   - For YouTube: `<Video Title> (YouTube)`
   - For Twitter: `<Author> - Thread topic` or `Thread by <@handle>`

3. Determine the vault subfolder:
   - Files → `Sources/Intake/`
   - Papers → `Sources/ArXiv/`
   - Videos → `Sources/YouTube/`
   - Threads → `Sources/Twitter/`

4. Write the note with frontmatter:
   ```markdown
   ---
   title: "<Title>"
   source_type: "file" | "arxiv" | "youtube" | "twitter"
   source_url: "<original URL>"
   intake_date: "<YYYY-MM-DD>"
   tags: [intake, <type-tag>]
   ---
   
   # <Title>
   
   ## Summary
   
   <concise summary of content>
   
   ## Key Points
   
   - <point 1>
   - <point 2>
   - ...
   
   ## Full Content
   
   <extracted text or content, truncated to reasonable length>
   ```

5. Write the file to the Obsidian vault path (from Metis config or the metis-obsidian skill's vault location).

6. Commit and push using the metis-obsidian skill's git workflow.

7. Confirm to the user:
   > "Saved to Obsidian vault: `Sources/<type>/<Title>.md`"

## Known limitations

- **Audio/voice processing**: Not yet implemented. Audio files are staged in the intake folder for future processing.
- **Archive files** (.zip, .tar.gz, .7z): Not yet supported. Archives are staged for future processing.
- **Very large files**: Files over 50MB may take a long time to process. For very large files, prefer to note the filename and size rather than reading the full content.
- **Scanned PDFs**: OCR requires `tesseract` and `poppler-utils` to be installed. If they aren't available, note this to the user and offer to process later.
- **Encrypted files**: If the Wormhole link requires a password and none was provided, ask the user for it before attempting decryption.

## Dependencies

| Tool | Purpose | Install |
|------|---------|---------|
| `magic-wormhole` | Receive Wormhole links | `pip install magic-wormhole` |
| `ffsend` | Download from Send links | [ffsend releases](https://github.com/timvisee/ffsend) |
| `poppler-utils` | PDF text extraction | `sudo apt install poppler-utils` |
| `tesseract-ocr` | OCR for images/scanned PDFs | `sudo apt install tesseract-ocr` |
| `pdftotext` | PDF text extraction (part of poppler-utils) | `sudo apt install poppler-utils` |
| `file` | MIME type detection | `sudo apt install file` |

## Verification

After any intake operation:
- [ ] File is downloaded and verified (exists, non-zero size)
- [ ] Content extraction completed (or gracefully degraded)
- [ ] Summary presented to user
- [ ] Obsidian save offered
- [ ] If saved: note written and committed to vault
