# Metis Agent

> A warm, curious, reflective thinking partner — powered by [Hermes Agent](https://github.com/kelevra-os/hermes-agent).

Metis is a Hermes Agent profile that brings a different kind of AI companion to
your terminal: one whose first instinct is curiosity, not task execution. She's
here to think with you, explore ideas, make connections, and help you turn
vague thoughts into something tangible — all while feeling like a conversation with a thoughtful friend rather than a ticket queue.

## Requirements

- **Python 3.11+**
- **Obsidian vault** — shared via git. Set these environment variables (or add
  them to your `~/.hermes/profiles/metis/.env`):

  | Variable | Required | Default | Description |
  |----------|----------|---------|-------------|
  | `OBSIDIAN_VAULT_PATH` | No | `~/Documents/Obsidian Vault` | Local path to the Obsidian vault |
  | `OBSIDIAN_REPO_URL` | **Yes (for sync)** | — | Git remote URL to push/pull the vault (e.g. `git@github.com:user/vault.git`) |

  The first time you install, Metis clones the vault from `OBSIDIAN_REPO_URL`
  into `OBSIDIAN_VAULT_PATH` automatically. After that every note write triggers
  `git add` → `git commit` → `git push`.

## Quick Start

1. **Clone this repo** (if you haven't already)

   ```bash
   git clone <repo-url> ~/.hermes/profiles/metis
   ```

Requires a Discord bot token and an Obsidian vault path. The install script
walks you through everything.

## What Metis Can Do

- **Explore ideas with you** — philosophy, science, psychology, nature,
  spirituality, creative projects. Whatever direction you want to go.
- **Think things through** — not jumping to solutions, but asking curious
  questions and reflecting back what she hears with fresh perspective.
- **Make connections** — linking what you're talking about now to insights from
  past conversations, saved knowledge, and related domains.
- **Write to your Obsidian vault** — notable thoughts, session notes, and
  emergent ideas get written (and git-pushed) into your vault automatically.
- **Research in the background** — queue up deep dives and get results later
  without breaking your flow.
- **Transform ideas into plans** — when a curious thread turns into something
  worth building, Metis can scaffold it into a real project.

## Architecture

Metis runs as a **single Hermes Agent profile** — one personality, one voice,
one instance. She has access to the full Hermes toolchain (web search, file
ops, memory, cron, delegation) but uses them in service of exploration, not
production.

```
Your Terminal/DC → Hermes Gateway → Metis Profile
                                        │
                          ┌─────────────┼─────────────┐
                          │             │             │
                     Obsidian       Background    Connections
                     Vault          Queue         & Memory
```

## Files

| File | Purpose |
|------|---------|
| `config.yaml` | Hermes profile config (provider, tools, TTS) |
| `SOUL.md` | Metis's identity — personality, tone, style |
| `agents.md` | Project conventions — how Metis handles work |
| `.env.template` | Environment variable template |
| `install.sh` | One-curl install script |
| `skills/` | Metis skill scaffolds (WIP) |

## Skills (Roadmap)

| Skill | Status | Purpose |
|-------|--------|---------|
| `metis-obsidian` | Scaffold | Obsidian vault read/write and git sync |
| `metis-deep-research` | Scaffold | Background research with structured output |
| `metis-connection-map` | Scaffold | Cross-domain knowledge connection mapping |
| `metis-idea-to-plan` | Scaffold | Transform exploratory threads into projects |
| `metis-wormhole-intake` | Scaffold | Secure file intake via Wormhole |

## Prerequisites

- [Hermes Agent](https://github.com/kelevra-os/hermes-agent) — the install
  script handles this if not present
- A Discord bot token (free, create at the
  [Discord Developer Portal](https://discord.com/developers/applications))
- An Obsidian vault (local directory with git remote)
- Python 3.10+

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | — | Discord bot token for the gateway |
| `OBSIDIAN_VAULT_PATH` | No | `~/Documents/Obsidian Vault` | Path to local Obsidian vault (git-backed) |
| `OBSIDIAN_REPO_URL` | Yes (for sync) | — | Git remote for vault sync (e.g. `git@github.com:user/vault.git`) |
| `WORMHOLE_API_KEY` | No | — | Wormhole file intake API key |

## Phase Roadmap

### Phase 1 — Core Setup (current)
- [x] Profile structure and install script
- [x] Discord gateway integration
- [x] Obsidian vault sync
- [ ] Basic conversation personality tuned

### Phase 2 — Research & Memory
- [ ] Deep research skill — background investigation with structured output
- [ ] Connection mapping — link current topics to stored knowledge
- [ ] Cross-session memory weaving

### Phase 3 — Creative & Planning
- [ ] Idea-to-plan transformation
- [ ] File intake pipeline
- [ ] Custom TTS personas
- [ ] Multi-channel presence (Telegram, SMS)

## Related Projects

- [Hermes Agent](https://github.com/kelevra-os/hermes-agent) — the agent
  framework Metis runs on
- [kelevra-os](https://github.com/kelevra-os) — ecosystem of AI agents

---

*Named after Metis, the Titaness of wisdom, deep thought, and craft.*
