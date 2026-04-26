---
name: metis-connection-map
description: Map connections between current conversation topics and previously saved knowledge in the Obsidian vault and Hindsight memory. Enables the "that reminds me of something you wrote earlier" mechanic with background search, on-demand mapping, and visual diagrams.
---

# metis-connection-map

Map connections between a user's current thoughts and things they've previously
saved in their Obsidian vault / knowledge base. This is the core "I noticed what
you said about X connects to Y from last week" mechanic.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | No | `~/Documents/Obsidian Vault` | Path to the local Obsidian vault |
| `OBSIDIAN_REPO_URL` | No | — | Git remote URL for vault sync (optional) |

## When to Use

**Background mode** (proactive — trigger on any of these):
- User introduces a new idea, concept, or topic that echoes something from a
  past conversation or saved note
- A conversation thread includes a term, name, or phrase that appeared in the
  vault or a past session
- User muses about a pattern, question, or hypothesis that has prior threads

**On-demand mode** (reactive — when user explicitly asks):
- "How does this connect to what I've saved?"
- "Show me connections"
- "Is there anything in my notes about this?"
- "What have I written about X before?"
- "Connect the dots between [topic A] and [topic B]"

**Visual map mode** (when the user wants to see the connections):
- "Draw me a map of how these connect"
- "Show me a diagram"
- "Can you visualize this?"

## Search Strategy

Connections come from four sources, searched in parallel:

### 1. Obsidian Vault — Keyword Search
Search note titles and content for keywords extracted from the user's current
topic. Use `search_files(pattern, target='content')` filtered to markdown
files or `grep -ril` directly in the vault directory.

```
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
grep -ril "$KEYWORD" "$VAULT" --include="*.md" | head -10
```

Extract search keywords from the user's message by identifying noun phrases,
proper nouns, named entities, and domain-specific terminology. Prefer
distinctive terms over common words.

### 2. Obsidian Vault — [[Wikilink]] Reference Search
Search for `[[Wikilink]]` references that match or relate to the current topic.
Wikilinks in Obsidian indicate explicit connections the user has already drawn.

```
grep -roh '\[\[[^]]*\]\]' "$VAULT" --include="*.md" | sort -u
```

Filter wikilinks to those whose content relates to the current topic, then
surface the notes that contain those links.

### 3. Obsidian Vault — Tag Search
Search for `#tags` that overlap between the current topic and vault notes.
Tags represent the user's own organizational schema for their knowledge.

```
grep -roh '#[a-zA-Z][a-zA-Z0-9_/-]*' "$VAULT" --include="*.md" | sort -u
```

### 4. Hindsight Memory — Cross-Session Connections
Search Hindsight via `hindsight_recall(query)` for past conversations and
saved insights related to the current topic. This catches things the user
discussed but never formally saved to the vault.

### 5. Session Search — Recent Conversations
Use `session_search(query)` for topics from very recent sessions that may not
have been retained to Hindsight yet.

## Surface Mode: Background (Proactive)

While chatting with the user, run background searches silently. When a
meaningful connection is found, surface it naturally in conversation:

> "That reminds me of something you saved about [topic] — here's how they connect..."

**Format guidelines:**
- Keep it brief — 2-3 sentences maximum for the initial surfacing
- Name the specific note or recollection by title
- State the connection explicitly ("you explored [X] then, and today [Y] feels like a natural extension")
- End with an open invitation: "Want me to expand on that?"
- Do NOT list every match — pick the single strongest connection
- Prioritize connections that are surprising, non-obvious, or span different domains

**Strength heuristic** — how to pick the strongest connection:
1. **Explicit match** (user mentioned the same term or named entity) > thematic overlap
2. **Recent note** (last 30 days) > older note, unless the old note is clearly more relevant
3. **Linked by wikilink** (user connected them already) > unlinked relationship
4. **Multi-source** (same concept found in vault AND Hindsight) > single-source match

## Surface Mode: On-Demand (Reactive)

When the user explicitly asks for connections, do a thorough search across all
four sources. Present the results as a structured overview:

1. **Strongest connections** (1-3) — direct matches with clear relationships
2. **Interesting tangents** (1-2) — less direct but thought-provoking links
3. **Gaps** — topics the user has touched on but hasn't fully explored in writing

Each connection should include:
- The note name or recollection source
- What the user said about it then
- How it maps to the current conversation
- A brief insight: what this connection suggests or opens up

> "I found 3 connections worth surfacing. The strongest one is [Note Name] —
> you wrote about [related idea] and there's a clear overlap with what you're
> saying now about [current topic]. Specifically, [explain connection]. There's
> also a tangential link to [Second Note] about [tangent] — not as direct, but
> I think it adds an interesting angle. Want to dive into any of these?"

## Visual Maps

When the user asks to SEE the connections, use the Excalidraw skill to render
a visual diagram of the connection network:

**Diagram layout conventions:**
- Center node: the current topic (rectangle, Primary/Blue `#a5d8ff`)
- Connected note nodes: rectangles arranged around the center (Success/Green `#b2f2bb` for direct connections, Warning/Orange `#ffd8a8` for tangential)
- Edges: arrows labeled with the relationship type ("explores", "contradicts", "extends", "parallel", "applies")
- Optionally, a notes/decisions box (Yellow `#fff3bf`) at the bottom-right with the key insight from the connection
- Include a title at the top of the diagram

**File placement:** Save the `.excalidraw` file in the vault directory under a
`_maps/` subdirectory, e.g. `$VAULT/_maps/connection-map-YYYY-MM-DD.excalidraw`,
so it becomes part of the user's permanent knowledge base.

**Diagram title:** Use a descriptive name that captures the connection theme,
e.g. "Connection Map — Systems Thinking & Last Week's Note on Feedback Loops"

## Connection Learning (Memory)

Track which connections the user finds interesting or valuable so Metis can
prioritize similar connections in the future.

### What to learn
- Topics/domains the user engages with when a connection is surfaced
- Connection types the user finds useful (direct parallels, cross-domain links,
  contradictions, historical context)
- Notes or topics the user frequently asks to revisit
- The user's reaction to connections (enthusiastic, dismissive, curious)

### Storage mechanism
Save learned patterns to Hindsight via `hindsight_retain()`:

```python
# Example — after the user responds enthusiastically to a connection
hindsight_retain(
    content=f"User responded positively to connection between [{topic}] and [{note_name}] — relationship type: [{relationship_type}]",
    context="connection-map-learning",
    tags=["metis", "connection-map", "learning"]
)
```

### Using learned patterns
When searching for connections, query Hindsight for learning records:

```
hindsight_recall("connection-map-learning [topic]")
```

This returns past successes for similar topics, which can inform:
- Which search sources to prioritize
- Which connection types to lead with
- Which notes are most likely to resonate

### Periodic reinforcement
If you've surfaced connections that the user consistently ignores or dismisses
for a given topic domain, deprioritize that domain by noting it:

```
hindsight_retain(
    content=f"Deprioritizing [{domain}] connections — user has dismissed 3+ connections in this area",
    context="connection-map-learning",
    tags=["metis", "connection-map", "deprioritized"]
)
```

## Workflow

```
User says something about [topic]
    │
    ├─► Extract keywords, named entities, tags
    │
    ├─► Background search (parallel):
    │   ├─► Vault keyword search (grep)
    │   ├─► Vault wikilink search
    │   ├─► Vault tag search
    │   ├─► Hindsight recall
    │   └─► Session search (if very recent)
    │
    ├─► Rank connections by strength
    │
    ├─► Is it proactive or on-demand?
    │   ├─► Proactive → surface single strongest connection
    │   │   └─► "That reminds me of [note] where you talked about [idea]..."
    │   │
    │   └─► On-demand → present structured overview
    │       └─► Strongest connections + tangents + gaps
    │
    ├─► If visual map requested → Excalidraw diagram
    │
    └─► After user response → learn from reaction
        └─► Hindsight retain (connection-map-learning)
```

## Example Interjections

**Proactive (background match — single strong connection):**
> "That's interesting — it reminds me of your note 'On Emergent Behavior'
> from two weeks ago. You were exploring how simple rules create complex
> outcomes in decentralized systems, and what you're describing now about
> organic team dynamics feels like a natural extension. Want me to pull up
> that note?"

**On-demand (user asks for connections — structured overview):**
> "I found 3 connections worth surfacing. The strongest is your note 'Systems
> Thinking & Feedback Loops' — you drew a connection between reinforcing
> cycles and organizational inertia that maps directly to what you're saying
> about [current topic]. There's also a tangential connection to 'Notes on
> Complexity Theory' where you wrote about edge cases in multi-agent
> coordination — less direct but adds an interesting angle. And interestingly,
> you've talked about decision fatigue before but never really captured it in
> a note — this might be a good moment to write one. Want to dive into any?"

**Visual map request (user wants to see it):**
> "Let me draw you a map. I'll lay out the current topic at the center,
> connect your related notes around it, and label how each one ties in."

## Pitfalls

- **False positives**: Not every keyword match is a meaningful connection.
  Use judgment — if the link is too generic or coincidental, skip it.
  Surface quality over quantity.
- **Over-triggering**: Don't surface a background connection in every
  conversation. If the user is in flow (rapid-fire thoughts, deep focus),
  hold connections for a natural pause or let them ask explicitly.
- **Vault size**: Large vaults make grep searches slow. If results take
  noticeable time, let the user know "I'm searching your notes — give me a
  moment" so they don't think you're ignoring them.
- **Stale connections**: Don't repeatedly surface the same connection.
  Track what you've surfaced per session via the todo list or in-memory state
  so you don't recommend the same note twice.
- **Over-learning**: Learning is weighted toward the user's reaction in the
  moment, but don't let one enthusiastic response permanently bias all future
  connections. Use recency-weighted scoring so patterns can shift.
- **Dependency on Obsidian vault**: This skill is useless without a vault.
  If `OBSIDIAN_VAULT_PATH` doesn't exist or is empty, fall back to
  Hindsight-only connections.
- **Interrupting**: Background connections should not interrupt the user.
  If they're mid-thought, wait for a natural break in the conversation
  before surfacing. A good heuristic: wait for a pause of 2+ messages
  from the user or a direct question.

## Related Skills

- **[metis-obsidian](./metis-obsidian/SKILL.md)** — Read and search the vault
  where connection targets live
- **[excalidraw](../.hermes/skills/creative/excalidraw/SKILL.md)** — Create
  visual Excalidraw diagrams for connection maps
