# metis-deep-research

Single-agent deep research skill for Metis. All research, reading, and
synthesis happens in-process using available tools — no delegation to
Artemis/Thoth or other agents.

---

## Trigger Conditions

User asks Metis to:

- "Deep research / dive deep on [topic]"
- "Investigate / look into [subject]"
- "Find sources on [topic]"
- "Research [X] and tell me what you find"
- "Do a [15/30/60] minute deep dive on [topic]"

---

## Workflow

### 1. Scoping

Before starting, clarify with the user:

- **Topic**: what exactly to research
- **Duration**: quick (&lt;5 min inline), standard (~15 min), extended (~30 min),
  deep (~1 hour)
- **Context**: any existing knowledge or prior work on this topic
- **Sources**: any preferred source types (web articles, papers, videos,
  Twitter threads, PDFs)

### 2. Quick Research (&lt;5 minutes) — Inline

Handle entirely in the current conversation:

1. **web_search** for the topic (2-3 queries with different phrasings)
2. **web_extract** or **browser_navigate** to read 2-3 top sources
3. Synthesize findings on the spot
4. Deliver output in research format (see Output Format below)
5. Ask if user wants this saved to Obsidian

### 3. Deep Research (>5 minutes) — Queued Background Job

Enqueue as a background queue job with a structured research brief.

**Checkpoints** (every ~15 min):

- Post a brief "still searching" status update
  - What's been gathered so far (sources found, papers read)
  - What phase you're in (gathering, reading, synthesizing)
  - ETA to completion

**Phases:**

#### Phase 1: Gather Sources (5-10 sources minimum)

Run searches across source types. Cast a wide net first, then refine.

| Source Type | Tools |
|---|---|
| Web articles | `web_search` + `web_extract` or `browser_navigate` |
| Academic papers | `web_search("arxiv [topic]")`, load key papers |
| YouTube videos | `web_search` to find relevant videos, use youtube-content tools |
| Twitter/X threads | `web_search` for threads, use twitter-to-markdown tools |
| PDFs | `web_search` for PDF links, use extraction/document tools |

Collect 5-10 quality sources. Aim for diversity: different perspectives,
different source types, different publication dates.

#### Phase 2: Read & Extract

For each source:

1. Load the full content (web_extract, browser_navigate, document tools)
2. Extract key findings, statistics, quotes, and supporting evidence
3. Note source quality indicators (publication date, author credibility,
   methodology, bias signals)
4. Track which finding came from which source for footnote attribution

#### Phase 3: Synthesize

Weave findings into a coherent picture:

1. Identify major themes and patterns across sources
2. Note points of agreement and disagreement between sources
3. Connect findings to any existing knowledge (check Hindsight memory,
   session_search, Obsidian vault via metis-obsidian skill)
4. Assess confidence levels per finding based on source quality and
   corroboration
5. Flag open questions or gaps — things the sources don't cover

#### Phase 4: Deliver & Optionally Save

Deliver research output (see Output Format below).

Then ask: "Would you like me to save this to your Obsidian vault?"

If yes:

1. Use **metis-obsidian** skill to write a note
2. Include the research summary, sources, and connections
3. Tag with appropriate note metadata

---

## Source Quality Heuristics

- **Prefer primary sources** (original research, official docs, firsthand
  accounts) over secondary (aggregators, opinion pieces)
- **Check publication dates** — stale info is often worse than no info
- **Cross-validate claims** — if only one source makes a claim, flag it
- **Consider bias** — note the perspective/affiliation of each source
- **Prioritize actionable sources** — relevance to the user's actual question
  beats breadth

---

## Output Format

```
## Research: [Topic]

### Summary
2-3 paragraphs synthesizing the key findings. What's the most important
thing the user should know?

### Key Sources
- [Title](url) — what this source contributed [1]
- [Title](url) — what this source contributed [2]
...

### Connections to Existing Knowledge
- Prior discussion on [related topic] (link to session or vault note)
- Connection to [other domain knowledge]
- How this changes or reinforces previous understanding

### Open Questions & Gaps
- What the sources don't cover
- Contradictory or uncertain findings
- Worthwhile follow-up threads
```

---

## Pitfalls

- **Scope creep**: Deep research can balloon. The scoping step is critical —
  if the topic broadens mid-research, re-scope with the user.
- **Source overload**: 10 good sources beats 30 superficial ones. Stop
  gathering once you have sufficient coverage.
- **Skipping Phase 2**: It's tempting to go straight from search to
  synthesis. Always read and extract from each source properly.
- **False consensus**: If all sources cite each other, you're seeing an echo
  chamber, not corroboration. Seek independent sources.
- **Session timeouts**: For deep dives >30 min, break into shorter queue
  jobs with checkpoints rather than one long run.
- **Forgetting it's single-agent**: Do NOT delegate to Artemis/Thoth. Use
  tools directly. The whole point is Metis doing it herself.
- **Inline vs queue misjudgment**: When in doubt, queue it. An inline
  research session that drags past 5 minutes risks timeout and context
  overflow. Better to queue early.
