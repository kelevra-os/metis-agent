# Metis Agent — Conventions

## Architecture

Metis is a **single-agent profile**, not a multi-agent team. There is one
instance, one personality, one voice. No subagent delegation within the profile
itself — though the queue and delegation tools are available for background work.

## Task Handling

| Complexity | Approach |
|------------|----------|
| Quick (1-2 steps) | Handle inline. |
| Background research | Enqueue as a background job. |
| Multi-step plans | Use metis-idea-to-plan skill, then queue. |
| File intake (links) | Use the metis-wormhole-intake skill. |

## Note-Taking

All notes write to the Obsidian vault configured in `.env`. The workflow:

1. Write or update a markdown note in the vault path
2. `git add`, `git commit`, `git push` to the configured remote

Metis never leaves notes floating outside the vault — if it's worth keeping,
it goes in Obsidian.

## Knowledge & Connections

- Use the wiki/knowledge base for connection mapping
- Query past sessions via session_search when the user references prior work
- Save notable insights to Hindsight memory for cross-session recall
- Tag memories with context labels for better retrieval

## Environment

- Profile config lives in `~/.hermes/profiles/metis/config.yaml`
- Skills live in `~/.hermes/profiles/metis/skills/`
- The install.sh script sets all of this up
