---
name: ocr-and-documents
description: Extract text from PDFs and scanned documents using marker-pdf (high-quality OCR), pymupdf4llm, or PyMuPDF. Includes scripts for marker extraction and pymupdf conversion.
version: 1.0.1
author: Metis Agent (adapted from Hermes Agent)
license: MIT

---

> **Adapted for Metis (single-agent profile).** All document processing happens
> in-process using available tools — no delegation to subagents.

# OCR and Document Extraction

Extract text from PDFs and scanned documents using marker-pdf (high-quality OCR for complex/scanned PDFs), pymupdf4llm (markdown conversion), or PyMuPDF (fast direct extraction).

## When to Use

- User shares a PDF and asks to extract its text
- User provides a scanned document that needs OCR
- Background step for wiki ingestion, analysis, or quote extraction
- Fallback when direct PDF text extraction produces empty results

## Trigger Conditions

- "extract text from [PDF]"
- "OCR this document"
- "read this PDF for me"
- "what does this document say?"
- Any PDF or document link where Metis needs to read the content
- Direct text extraction returns empty or garbled results

## Available Methods (in priority order)

### Method 1: PyMuPDF (fitz) — Fast Direct Text

For digital-born PDFs (not scanned). Returns text directly from the PDF structure.

```python
import fitz

doc = fitz.open("document.pdf")
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

**Install:** `pip install pymupdf` (or `fitz`)

### Method 2: pymupdf4llm — Markdown Conversion

Extracts text and converts to structured markdown with headers preserved.

```bash
pip install pymupdf4llm
```

```python
import pymupdf4llm

text = pymupdf4llm.to_markdown("document.pdf")
```

Good for PDFs with chapters, sections, and hierarchical structure.

### Method 3: marker-pdf — Full OCR (Scanned PDFs)

For scanned documents, image-heavy PDFs, or when PyMuPDF returns no text.

```bash
pip install marker-pdf
```

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

converter = PdfConverter(
    artifact_dict=create_model_dict(),
)
rendered = converter("scanned_document.pdf")
text = rendered.text
```

**First run:** Downloads models (~2GB). Runs cached afterward.
**Accuracy:** Excellent for complex layouts, tables, multi-column.

## Scripts

This skill directory includes:

- `scripts/extract_marker.py` — Full marker-pdf extraction with error handling and progress feedback
- `scripts/extract_pymupdf.py` — PyMuPDF extraction with fallback to pymupdf4llm

## Workflow for Wiki Ingestion

When combined with `wiki-ingest-pdf`:

1. Download PDF to temp location
2. Try Method 1 (PyMuPDF) — fast path
3. If empty or garbled, try Method 2 (pymupdf4llm)
4. If still poor, try Method 3 (marker-pdf OCR)
5. Pass extracted text to wiki page synthesis

## Pitfalls

- **First run of marker-pdf:** Downloads models (~2GB). Ensure sufficient disk space and network.
- **GPU vs CPU:** marker-pdf runs on CPU by default. GPU support requires additional config.
- **Very large PDFs (500+ pages):** marker-pdf is memory-intensive. Consider chunking.
- **Form-fillable PDFs:** May appear blank in PyMuPDF — use marker-pdf.
- **Encrypted PDFs:** Most tools fail. May need decryption first.
- **Language support:** marker-pdf supports 100+ languages; pymupdf4llm is Latin-script focused.

## Installation

```bash
# Core: PyMuPDF (fast direct extraction)
pip install pymupdf

# Markdown output (optional)
pip install pymupdf4llm

# OCR for scanned PDFs (optional, ~2GB model download on first run)
pip install marker-pdf
```

## Related Skills

- `wiki-ingest-pdf` — full PDF-to-wiki ingestion workflow
- `arxiv` — academic paper search (papers are usually PDFs)
- `youtube-content` — process video alongside document content
