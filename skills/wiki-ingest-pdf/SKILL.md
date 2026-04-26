---
name: wiki-ingest-pdf
description: Extract text from PDFs and synthesize structured wiki pages with proper frontmatter, sources, and stack connections.
version: 1.0.1
author: Metis Agent (adapted from Hermes Agent)
license: MIT

---

> **Adapted for Metis (single-agent profile).** All PDF processing and wiki
> writing happens in-process using available tools — no delegation to
> Artemis/Thoth subagents. Use `ocr-and-documents` skill for text extraction,
> then Metis's own wiki-writing abilities for the final page.

# Wiki PDF Ingestion

Extract text from PDF documents (books, papers, reports) and synthesize durable wiki pages with YAML frontmatter, structured content, and connections to the existing knowledge stack.

## When to Use

- User shares a PDF link or file: "ingest this into the wiki"
- User asks to save key information from a PDF document
- Reference material (manuals, guides, papers) that should be searchable
- Books or long-form content that needs structured extraction

## Trigger Conditions

User mentions:
- "ingest [PDF link] into the wiki"
- "save this paper to the wiki"
- "add [document] to the knowledge base"
- "wiki this PDF"
- Any PDF link in the conversation

## Overview

```
User shares PDF link → Extract text → Analyze content → Write wiki page
```

Each phase runs in sequence, all handled by Metis directly:

1. **Download & Extract** — Get the PDF and extract text
2. **Analyze & Synthesize** — Process content, extract key information
3. **Write Wiki Page** — Create structured wiki entry with frontmatter

## Phase 1: Download & Extract

### Text Extraction Methods (in priority order)

#### Method A: Direct text via PyMuPDF (pymupdf) — Fastest

```python
import fitz  # pip install pymupdf

doc = fitz.open("/tmp/paper.pdf")
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

#### Method B: OCR via marker_pdf — For scanned/image-only PDFs

```bash
pip install marker-pdf
```

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

converter = PdfConverter(
    artifact_dict=create_model_dict(),
)
rendered = converter("/tmp/scanned.pdf")
text = rendered.text
```

#### Method C: OCR via pymupdf4llm — Good balance of speed and quality

```bash
pip install pymupdf4llm
```

```python
import pymupdf4llm

text = pymupdf4llm.to_markdown("/tmp/paper.pdf")
```

### Full Extract Script

See `scripts/extract_marker.py` and `scripts/extract_pymupdf.py` in the `ocr-and-documents` skill for complete extraction workflows with error handling.

### PDF Download

```python
import requests

def download_pdf(url, output_path="/tmp/paper.pdf"):
    resp = requests.get(url, timeout=30, stream=True)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path
```

## Phase 2: Analyze & Synthesize

After extracting text, Metis analyzes the content to extract:

### Content Structure

1. **Core Topic** — What is this document about?
2. **Key Claims** — Main arguments, findings, or ideas
3. **Supporting Evidence** — Data, citations, examples
4. **Related Concepts** — How this connects to existing wiki content
5. **Actionable Insights** — What can be applied or used
6. **Contradictions or Gaps** — What's missing or debatable

### Synthesis Prompt

Process the extracted text with a structured synthesis:

```
You are synthesizing a PDF document into wiki knowledge.
Given the extracted text below, produce:

1. **Title**: A concise, descriptive title for the wiki page
2. **Summary**: 3-5 sentences covering the core contribution
3. **Key Points**: 5-10 bullet points of main takeaways
4. **Connections**: How this relates to existing topics in the wiki
5. **Tags**: 3-8 tags for discoverability

Extracted text: [first 15000 chars]
```

**Note:** For very long documents (100K+ chars), chunk and process section by section, then aggregate.

## Phase 3: Write Wiki Page

### Wiki Page Location

Wiki pages are written to the user's configured wiki path. The default location follows the convention:

```
~/wiki/topics/<topic-slug>.md
```

### Wiki Page Template

```yaml
---
title: "Paper/Document Title"
tags:
  - source-type: paper/report/book
  - author: "Author Name(s)"
  - year: 2024
  - topic-category
  - ingested: YYYY-MM-DD
sources:
  - type: pdf
    url: "https://..."
    title: "Original Document Title"
    accessed: YYYY-MM-DD
connections:
  - topic: RelatedWikiTopic
    relation: extends / references / contrasts_with
---

# Paper/Document Title

## Summary

3-5 sentences covering the core contribution and relevance.

## Key Points

- Major finding or argument 1
- Major finding or argument 2
- Major finding or argument 3

## Supporting Details

Deeper explanation of methodology, evidence, or reasoning.

## Connections

- **RelatedWikiTopic**: How this relates — expands on concept X, provides evidence for Y
- **ExistingProject**: Relevance to active projects or decisions

## Source

[Original PDF](source-url) — accessed YYYY-MM-DD
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Human-readable page title |
| `tags` | Yes | Discovery and categorization tags |
| `sources` | Conditional | For externally-sourced content |
| `connections` | No | Links to existing wiki pages |
| `date` | Yes | Ingestion date |
| `status` | No | `draft`, `needs-review`, `complete` |

## Complete Workflow Summary

| Step | What Metis does | Est. Time |
|------|-----------------|-----------|
| 1. Download PDF | Fetch from URL, save to temp location | ~10s |
| 2. Extract text | PyMuPDF or marker_pdf for OCR | ~30s-3m |
| 3. Analyze | Synthesize content into key points | ~30s |
| 4. Write wiki | Create structured page with frontmatter | ~20s |
| 5. (Optional) Review | Ask user to verify before saving | ~10s |

## Pitfalls

- **Scanned PDFs**: Must use OCR (marker_pdf). PyMuPDF returns empty text.
- **Very long PDFs**: 500+ page documents may need section-by-section processing.
- **Malformed PDFs**: Some PDFs fail to download or parse. Always validate extraction.
- **Language**: Non-English PDFs may need language detection and translation.
- **Tables/Figures**: Extracted as raw text; structured table formatting is lost.
- **File size**: Large PDFs (50MB+) may need timeout adjustments or streaming download.

## Related Skills

- `ocr-and-documents` — text extraction scripts (marker_pdf, pymupdf4llm)
- `youtube-content` — video summaries alongside document ingestion
- `arxiv` — academic paper search for related sources
