---
name: arxiv
description: Search and retrieve academic papers from arXiv using their free REST API. No API key needed. Search by keyword, author, category, or ID. Combine with web_extract or the ocr-and-documents skill to read full paper content.
version: 1.0.1
author: Metis Agent (adapted from Hermes Agent)
license: MIT
metadata:
  hermes:
    tags: [Research, Arxiv, Papers, Academic, Science, API]
    related_skills: [ocr-and-documents]

---

> **Adapted for Metis (single-agent profile).** All research happens in-process
> using available tools — no delegation to Artemis/Thoth or other agents.
> Cookie/credential paths use `~/.hermes/profiles/metis/` instead of
> pantheon-agent paths.

# Arxiv Tool — Academic Paper Search

Search arXiv's REST API programmatically. No authentication required.

## When to Use

- User asks "find papers on [topic]"
- User gives you an arXiv ID and asks for details
- Background research step in a deep-dive task
- Literature review or related-work scanning

## Trigger Conditions

User mentions:
- "search arxiv for [topic]"
- "find papers about [subject]"
- "arXiv ID [number]"
- "recent papers in [category]"
- "latest research on [topic]"

## Quick Reference

**API Base URL:** `http://export.arxiv.org/api/query`

### Search by Keyword

```
http://export.arxiv.org/api/query?search_query=all:quantum+AND+all:computing&start=0&max_results=10
```

### Search by Author

```
http://export.arxiv.org/api/query?search_query=au:Karpathy&start=0&max_results=5
```

### Search by Category + Keyword

```
http://export.arxiv.org/api/query?search_query=cat:cs.AI+AND+ti:reasoning&start=0&max_results=10
```

### Fetch by ID

```
http://export.arxiv.org/api/query?id_list=2303.08774
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `search_query` | Boolean query (all, ti, au, abs, cat, and/or/andnot) | — |
| `id_list` | Comma-separated arXiv IDs | — |
| `start` | Result offset | 0 |
| `max_results` | Max results to return | 10 (max 3000) |
| `sortBy` | `relevance`, `lastUpdatedDate`, `submittedDate` | `relevance` |
| `sortOrder` | `ascending`, `descending` | `descending` |

## Query Prefix Reference

| Prefix | Field |
|--------|-------|
| `ti` | Title |
| `au` | Author |
| `abs` | Abstract |
| `co` | Comment |
| `jr` | Journal Reference |
| `cat` | Subject Category |
| `rn` | Report Number |
| `all` | All fields |

Use `AND`, `OR`, `ANDNOT` between prefixes. Parentheses for grouping:
```
search_query=(cat:cs.AI+OR+cat:cs.LG)+AND+abs:transformer
```

## Response Format

arXiv returns Atom XML. Parse with standard XML tools:

```python
import xml.etree.ElementTree as ET
import requests

url = "http://export.arxiv.org/api/query?search_query=all:quantum&max_results=3"
resp = requests.get(url, headers={"User-Agent": "Metis/1.0"})
root = ET.fromstring(resp.content)
ns = {"a": "http://www.w3.org/2005/Atom"}

for entry in root.findall("a:entry", ns):
    paper_id = entry.find("a:id", ns).text.split("/")[-1]
    title = entry.find("a:title", ns).text.strip().replace("\n", " ")
    summary = entry.find("a:summary", ns).text.strip()[:300]
    authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns)]
    published = entry.find("a:published", ns).text[:10]
    link = entry.find("a:link", ns).attrib.get("href", "")
    print(f"{paper_id} | {title[:80]} | {', '.join(authors[:3])} | {published}")
```

### Full Python Helper

```python
def search_arxiv(query, max_results=10, sort_by="relevance"):
    import requests, xml.etree.ElementTree as ET
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending"
    }
    resp = requests.get(url, params=params,
                        headers={"User-Agent": "Metis/1.0"})
    root = ET.fromstring(resp.content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []
    for entry in root.findall("a:entry", ns):
        pid = entry.find("a:id", ns).text.rsplit("/", 1)[-1]
        title = entry.find("a:title", ns).text.strip().replace("\n", " ")
        summary = entry.find("a:summary", ns).text.strip()
        authors = [a.find("a:name", ns).text
                   for a in entry.findall("a:author", ns)]
        published = entry.find("a:published", ns).text[:10]
        link = entry.find("a:id", ns).text
        results.append({
            "id": pid, "title": title,
            "summary": summary, "authors": authors,
            "published": published, "link": link
        })
    return results
```

## PDF Access

- Append `.pdf` to any arXiv ID URL: `https://arxiv.org/pdf/2303.08774.pdf`
- Use `web_extract(pdf_url)` or the `ocr-and-documents` skill to read PDF content
- Combine with `youtube-content` / `wiki-ingest-pdf` for full paper ingestion

## Rate Limits & Ethics

- **Rate limit:** ~1 request per 3 seconds. Be a good citizen.
- **No API key needed.** This is a free public API.
- **User-Agent:** Always set a descriptive `User-Agent` header.
- **Respect robots.txt:** arXiv asks for no more than 1 request per 3 seconds.
- **Terms:** https://info.arxiv.org/help/api/tou.html

## Related Skills

- `ocr-and-documents` — read PDF content when direct text extraction is needed
- `youtube-content` — fetch video/lecture transcripts alongside papers
