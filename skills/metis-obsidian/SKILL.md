---
name: metis-obsidian
description: Read, write, search, and sync notes from the configured Obsidian vault. Handles git commit+push for every change.
---

# metis-obsidian

Read, write, search, and sync notes from Metis's configured Obsidian vault.
Every write or update triggers an automatic `git add` → `git commit` → `git push`
cycle so the vault stays in sync with the shared remote.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | No | `~/Documents/Obsidian Vault` | Path to the local Obsidian vault |
| `OBSIDIAN_REPO_URL` | **Yes (for sync)** | — | Git remote URL for the vault (SSH or HTTPS) |

## When to Use

- Saving a thread of thought as a permanent note
- Retrieving past notes during a conversation
- Documenting a decision, idea, or reference
- Syncing vault state after writing

## Commands

All commands assume the vault path is loaded at the top:

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
```

### sync-init

Clone the shared vault repository to the local machine. Only needed on first
setup or after a clean checkout. After cloning, `OBSIDIAN_VAULT_PATH` will point
to the cloned repo.

```bash
if [ ! -d "$VAULT" ]; then
  git clone "$OBSIDIAN_REPO_URL" "$VAULT"
  echo "Vault cloned to $VAULT"
else
  echo "Vault already exists at $VAULT"
fi
```

If `OBSIDIAN_REPO_URL` is unset or empty, print a warning and skip cloning.

### create-note

Create a new note at `$VAULT/<path>/<name>.md`. Nested folder paths are
supported — intermediate directories are created automatically.

```bash
NOTE_PATH="$VAULT/${1}"  # e.g. "Projects/My Idea.md"
mkdir -p "$(dirname "$NOTE_PATH")"
cat > "$NOTE_PATH" << 'ENDNOTE'
# Title

Body text with [[Wikilinks]] to other notes.
ENDNOTE
```

After creating, run the **git-sync** workflow.

### read-note

Print the full content of a note to stdout.

```bash
NOTE_PATH="$VAULT/${1}"
cat "$NOTE_PATH"
```

### search-notes

Search by filename or content within the vault.

```bash
# By filename
find "$VAULT" -name "*.md" -iname "*${1}*" -type f

# By content
grep -rli "${1}" "$VAULT" --include="*.md"
```

### append-note

Append content to an existing note. Creates the note first if it doesn't exist.

```bash
NOTE_PATH="$VAULT/${1}"
mkdir -p "$(dirname "$NOTE_PATH")"
echo -e "\n${2}" >> "$NOTE_PATH"
```

After appending, run the **git-sync** workflow.

### list-notes

List all markdown notes in a directory within the vault.

```bash
DIR="$VAULT/${1:-.}"
ls "$DIR"*.md 2>/dev/null
```

### git-sync

Commit and push any local changes to the vault.

```bash
cd "$VAULT"

# Check if there's anything to commit
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "metis: ${1:-update notes}"
  git push
else
  echo "Nothing to commit — vault is clean."
fi
```

The commit message should be concise and descriptive of what changed. Good
examples:

- `metis: add research note on transformer architectures`
- `metis: update daily note with meeting summary`
- `metis: capture design decision on queue model`

## Workflow

Every note operation that writes to disk follows this pattern:

1. Write/append the file to the vault path
2. `git-sync` with a descriptive commit message

Use `read-note` before `append-note` if you need to see the current content to
avoid duplication.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use
wikilinks to connect related content. Examples:

- `See [[Daily Notes/2026-04-26]] for context.`
- `This builds on the [[queue-model]] design doc.`
- `The [[metis-obsidian]] skill handles this.`

## Pitfalls

- **Vault path with spaces**: Always quote `$VAULT` in shell commands.
- **OBSIDIAN_REPO_URL unset**: The git-sync step will fail silently if the
  remote URL is not configured. Check the environment before relying on sync.
- **SSH key access**: If using SSH (`git@github.com:...`), ensure the SSH agent
  has the correct key loaded. HTTPS with a PAT is a simpler alternative.
- **Large commits**: Commit after each note change rather than batching. Small
  commits are easier to review and conflict-resolve in Obsidian.
- **Race conditions**: Metis is the only writer to this vault. If other agents
  or the user write simultaneously, `git push` may fail with a non-fast-forward
  error. In that case, `git pull --rebase` then `git push`.
- **Nested folders**: Create intermediate directories with `mkdir -p` before
  writing. The vault may not have all subdirectories pre-created.
