# Metis Agent — Your Thinking Partner

**Metis** is a Hermes Agent profile designed to be a warm, curious, reflective
thinking partner — not just another task-execution bot. Named for the Titaness
of wisdom, deep thought, and craft, Metis helps you think more clearly by asking
the right questions before jumping to solutions.

## What Makes Metis Different

Most AI agents optimize for *speed to output*. Metis optimizes for *depth of
understanding*. Before solving a problem, Metis wants to understand it — the
context, the connections, the things you haven't said yet.

- **Socratic with warmth** — questions that illuminate, not interrogate
- **Full embrace** — explore any topic: science, philosophy, nature, psychology,
  spirituality, engineering, art
- **Connection-finder** — links your current thoughts to past conversations and
  stored knowledge
- **Obsidian-native** — all notes go into your vault, versioned with git

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/kelevra-os/metis-agent/main/install.sh | bash
```

The installer:

1. Installs Hermes Agent if not present
2. Creates the `metis` profile directory
3. Downloads config.yaml, SOUL.md, agents.md
4. Installs skill scaffolds
5. Prompts for Discord & Obsidian config
6. Sets up the Discord gateway
7. Prints next steps

## What Metis Can Do

| Capability | How |
|------------|-----|
| Think through ideas | Inline conversation — Socratic exploration |
| Background research | Queued deep-dive jobs |
| Save notes to Obsidian | Git-committed markdown in your vault |
| Connect past to present | Session search + Hindsight memory + wiki queries |
| Transform ideas into plans | Idea-to-plan pipeline (skill scaffold) |
| Cross-device file intake | Wormhole link support (skill scaffold) |
| Discord gateway | Chat with Metis from any Discord server |

## Roadmap

### Phase 1 — Foundation (this release)
- ✅ Profile config and soul
- ✅ Installer with Discord gateway setup
- ✅ Obsidian vault integration scaffold

### Phase 2 — Deep Research
- Multi-source research skill (web, arxiv, academic)
- Summarization and cross-referencing
- Automatic Obsidian ingestion of findings

### Phase 3 — Connection Mapping
- Graph-based knowledge linking across vault notes
- Wiki query integration for cross-reference discovery
- Pattern recognition across disparate topics

### Phase 4 — Idea Transformation
- Structured ideation → plan → execution pipeline
- Queue integration for complex multi-step work
- Reflection loops for quality assurance

## Requirements

- Linux or macOS
- Bash 4+
- Git
- Hermes Agent (installed automatically if missing)

## Configuration

Metis uses environment variables stored in `~/.hermes/profiles/metis/.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot token for gateway |
| `OBSIDIAN_VAULT_PATH` | Yes | Local path to your Obsidian vault |
| `OBSIDIAN_REPO_URL` | Yes | Git remote for vault sync |
| `WORMHOLE_API_KEY` | No | For cross-device file transfer |

## Running Metis

```bash
# CLI mode (chat in terminal)
hermes -p metis

# Discord gateway (chat from Discord)
hermes -p metis gateway run
```

## Project Structure

```
~/.hermes/profiles/metis/
├── config.yaml          # Profile configuration
├── SOUL.md              # Personality & behavior
├── agents.md            # Operational conventions
├── .env                 # Environment variables
└── skills/
    ├── metis-obsidian/       # Obsidian note-taking
    ├── metis-deep-research/  # Multi-source research
    ├── metis-connection-map/ # Knowledge graph connections
    ├── metis-idea-to-plan/   # Idea → structured plan
    └── metis-wormhole-intake/ # Cross-device file intake
```

## License

MIT
