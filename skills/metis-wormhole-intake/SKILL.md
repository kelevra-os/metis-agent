---
name: metis-wormhole-intake
description: Accept Wormhole, Send, or direct file links, download, process content, present summary, and optionally save to the Obsidian vault as a source note.
tags: ['intake', 'wormhole', 'send', 'file-ingestion', 'obsidian']
---

# metis-wormhole-intake

Accept a Wormhole (`wormhole://`), Send (`send://` / `send.vis.ee`), or direct
file URL, download the file, determine the type, extract the content, present a
readable summary to the user, and optionally write a source note to the Obsidian
vault.

## When to Use

- The user shares a Wormhole link (`wormhole://...` or `https://wormhole.app/...`)
- The user shares a Send link (`https://send.vis.ee/...` or similar ffsend/Send URL)
- The user shares a direct file URL (`https://example.com/file.pdf`)
- The user says "I have a file for you" or "I sent you a file" with a link
- The user asks you to process a shared document, image, or archive

## Prerequisites

- **ffsend** — for Send/ffsend links. Install if missing:

  ```bash
  # cargo
  cargo install ffsend
  # or using the static binary
  curl -sL https://github.com/timvisee/ffsend/releases/latest/download/ffsend-x86_64-unknown-linux-gnu -o ~/.local/bin/ffsend && chmod +x ~/.local/bin/ffsend
  ```

- **pdftotext** (poppler-utils) — for PDF text extraction: `sudo apt install poppler-utils`
- **tesseract-ocr** — for OCR on images: `sudo apt install tesseract-ocr`
- **pandoc** — for document format conversion: `sudo apt install pandoc`
- **OBSIDIAN_VAULT_PATH** — only needed when saving to vault (set in `.env` or `config.yaml`)

The skill itself handles fallbacks gracefully — if a tool is unavailable, report
what content you could extract and note the limitation.

## Workflow

### Step 1 — Identify the provider

| Pattern | Provider | Tool |
|---------|----------|------|
| `wormhole://`, `https://wormhole.app/` | Wormhole | Browser download or wget/curl |
| `send://`, `https://send.vis.ee/`, `https://send.vis.ee/#` | Send / ffsend | `ffsend download` |
| `https://` direct file URL | Direct URL | `curl -LO` or `wget` |
| Other share link | Inspect and ask | — |

### Step 2 — Download to a known location

Use `/home/hermes/intake/` as the download target (create if it doesn't exist):

```bash
mkdir -p /home/hermes/intake
```

**For Send/ffsend links:**
```bash
ffsend -Iy download -o /home/hermes/intake/ '<share-url>'
```
If the URL includes a password fragment, pass `--password <fragment>` or let
ffsend handle it automatically when the fragment is in the URL.

**For Wormhole links:**
- Open in browser via `browser_navigate` and click the download button
- The download typically lands in `/tmp/camofox-download-*` or can be captured
  via the browser's download API
- Fallback: `curl -L -o /home/hermes/intake/ '<wormhole-url>'` for direct
  download links

**For direct file URLs:**
```bash
curl -L -o /home/hermes/intake/<filename> '<url>'
```

After download, verify:
- File exists at the target path
- File size is nonzero
- Record the filename, size, and MIME type

```bash
file --mime-type -b /home/hermes/intake/<filename>
stat --format='%s' /home/hermes/intake/<filename>
```

### Step 3 — Determine file type

Use the `file` command to get the MIME type, then map to a handler:

```bash
MIME=$(file --mime-type -b /home/hermes/intake/<filename>)
```

### Step 4 — Process content

Dispatch based on MIME type:

#### PDF (`application/pdf`)
```bash
# Extract text
pdftotext /home/hermes/intake/<filename> - | head -500
# Also report page count
pdfinfo /home/hermes/intake/<filename> | grep Pages
```
Present: first ~500 lines of extracted text, page count, and a brief summary
of what the document appears to cover.

#### Image (`image/png`, `image/jpeg`, `image/webp`, `image/gif`, etc.)
Use `vision_analyze` on the local file path to get OCR/description:
```
vision_analyze(image_url='/home/hermes/intake/<filename>',
               question='Extract all visible text and describe the content.')
```
Present: extracted text (if any), a visual description, and key objects/people
identified. For screenshots or diagrams, include the structural layout.

#### Plain text (`text/plain`)
Read the file directly with `read_file`:
```
read_file(path='/home/hermes/intake/<filename>', limit=200)
```
Present: first 200 lines (or full file if shorter), character encoding, and a
brief content summary.

#### Markdown (`text/markdown`)
Read and optionally render as formatted output. Present the content with
headings, links, and structure preserved.

#### HTML (`text/html`)
Extract readable text with `pandoc`:
```bash
pandoc /home/hermes/intake/<filename> -t plain | head -500
```

#### Office documents (docx, xlsx, pptx) — `application/vnd.*`
```bash
# docx → plain text
pandoc /home/hermes/intake/<filename> -t plain | head -500
```
For spreadsheets, note that full extraction may be limited; present the
first few rows conceptually.

#### Archives (zip, tar, gz)
List contents but do not auto-extract:
```bash
unzip -l /home/hermes/intake/<filename>   # for zip
tar tf /home/hermes/intake/<filename>      # for tar.*
```
Ask the user if they want extraction before proceeding.

#### Audio / Video
Note that audio and video processing is not yet fully supported in this skill.
Present basic metadata:
```bash
file /home/hermes/intake/<filename>
ffprobe -v quiet -print_format json -show_format /home/hermes/intake/<filename> 2>/dev/null | head -30
```
Tell the user: *"Audio/video content processing is planned but not yet
implemented. The file is saved at <path> for later use."*

#### Unknown / binary
Report the MIME type and file size. Ask the user how they'd like to proceed.

### Step 5 — Present a summary to the user

Format the summary clearly. Include:

```
📄 **File:** <filename>
📏 **Size:** <human-readable size>
🏷️ **Type:** <MIME type>
📝 **Content summary:** <2-3 sentence overview>

<extracted content preview>

**Key items of interest:**
- Point 1
- Point 2
...
```

### Step 6 — Ask about saving to Obsidian

After presenting the summary, ask:

> "Would you like me to save a source note for this in your Obsidian vault?"

If yes, proceed to Step 7.
If no, note that the file remains at `/home/hermes/intake/<filename>` if they
want to reference it later. (Cleanup is automatic — the intake folder is
ephemeral by design.)

### Step 7 — Save to Obsidian (via metis-obsidian)

Use the `metis-obsidian` skill to create a source note. The template is at
`metis-obsidian/templates/source-note.md` — render it with the extracted
content:

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
NOTES_DIR="$VAULT/sources/Intake"
mkdir -p "$NOTES_DIR"

# Derive a clean title from the filename
TITLE="<Clean Filename Without Extension>"
DATE=$(date +%Y-%m-%d)
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
FILEPATH="$NOTES_DIR/$DATE-$SLUG.md"
```

Write the note with frontmatter and content:

```markdown
---
created: {{date}}
tags: [source, reference, intake]
source_url: {{original_url}}
file_path: /home/hermes/intake/{{filename}}
file_type: {{MIME type}}
---

# {{title}}

**Source:** {{url}}
**Intake date:** {{date}}
**Type:** {{MIME type}}
**Size:** {{human_size}}

## Summary

{{2-3 sentence content summary}}

## Key Content

{{extracted key points, structured}}

## Raw Preview

```
{{first 100 lines or key excerpts}}
```

## Connections

- Intake source note
- Add related tags or links to existing notes if relevant
```

Then commit and push via the metis-obsidian workflow:

```bash
cd "$VAULT"
git add "$FILEPATH"
git commit -m "Intake: $TITLE"
git push
```

Report the saved path to the user.

## Integration with Link-Based Content

When the shared link is not a direct file but a content link (e.g., an arXiv
paper, YouTube video, or Twitter thread):

| Link Type | Recommended Skill |
|-----------|-------------------|
| `arxiv.org/abs/...` | Use the arxiv skill to fetch abstract + PDF |
| `youtube.com/watch?...` | Use youtube-content to fetch transcript |
| `twitter.com/...` / `x.com/...` | Use twitter-to-markdown to convert to markdown |
| General blog/article | Use crawl4ai or direct browser to extract content |

In these cases, treat the result as the "extracted content" and proceed to
Step 5 (present summary) and Step 6 (offer to save to Obsidian).

## Pitfalls

- **ffsend may be missing** — On fresh installs, `cargo install ffsend` needs
  Rust toolchain. Fall back to browser-based download.
- **Large files** — Files over 50MB may take time to download. Set a longer
  timeout on terminal commands. Consider background download with
  `notify_on_complete`.
- **Password-protected Send links** — The fragment `#...` in a Send URL is the
  decryption key. `ffsend` handles this automatically if the URL includes it,
  but if downloading via browser, the key must be entered in the web form.
- **Wormhole link expiry** — Wormhole links typically expire after 24 hours or
  one download. If the link has expired, inform the user and ask them to re-share.
- **OCR quality varies** — Tesseract works well for printed text but struggles
  with handwriting, low-resolution images, or heavy compression.
- **PDFs with embedded images only** — If `pdftotext` returns empty or
  gibberish, the PDF may be scanned images. Try OCR with `tesseract` on
  rendered pages, or use `pypdf` to attempt text extraction.
- **Cleanup** — Downloaded files in `/home/hermes/intake/` are not
  automatically deleted. Periodically clean them up, or delete after successful
  vault save.
- **Metis doesn't have a browser** — Metis runs as a CLI/Discord agent. For
  Wormhole links that require browser interaction, use `browser_navigate` and
  `browser_click` available through Hermes tools. If the Wormhole link
  provides a direct download URL (most do), prefer `curl`/`wget` instead.
- **Git push on vault** — If `OBSIDIAN_REPO_URL` is not configured, skip the
  push step and report that the note was saved locally without remote sync.

## Verification Checklist

After intake:

- [ ] File downloaded successfully to `/home/hermes/intake/`
- [ ] File size is nonzero
- [ ] MIME type identified correctly
- [ ] Content extracted (or limitation noted)
- [ ] Summary presented to user
- [ ] User asked about saving to Obsidian
- [ ] (If saved) Source note written, committed, and pushed
- [ ] Downloaded file path reported for future reference

## Example Flow

User: "I sent you a PDF via Wormhole: https://wormhole.app/abc123"

1. Download: browser_navigate → click download → file lands in `/tmp/`.
2. Verify: file exists, size=2.3MB, MIME=application/pdf.
3. Extract: `pdftotext /tmp/... - | head -500`.
4. Present: "Received 'Research Paper.pdf' (2.3MB, 12 pages). It covers
   transformer attention mechanisms... Key points: [3 items]."
5. Ask: "Would you like me to save this as a source note in Obsidian?"
6. If yes: write note to `$VAULT/sources/Intake/`, commit, push.
7. Report: "Saved to vault at sources/Intake/research-paper.md"