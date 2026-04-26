#!/usr/bin/env bash
set -euo pipefail

# Metis Agent — One-curl Installer
# Run: curl -fsSL https://raw.githubusercontent.com/kelevra-os/metis-agent/main/install.sh | bash
# Or:  bash <(curl -fsSL https://raw.githubusercontent.com/kelevra-os/metis-agent/main/install.sh)

REPO="kelevra-os/metis-agent"
BRANCH="main"
REPO_URL="https://github.com/$REPO"
RAW_BASE="https://raw.githubusercontent.com/$REPO/$BRANCH"

# ─── Colors ─────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}➜${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }

# ─── 1. Install Hermes (if not present) ──────────────────────────────
if ! command -v hermes &>/dev/null; then
  info "Hermes Agent not found. Installing..."
  curl -fsSL https://hermes-agent.io/install.sh | bash
  echo
  ok "Hermes Agent installed."
else
  ok "Hermes Agent already installed ($(hermes --version 2>/dev/null || echo 'unknown version'))."
fi

# ─── 2. Create Metis profile directory ──────────────────────────────
METIS_DIR="$HOME/.hermes/profiles/metis"
METIS_SKILLS_DIR="$METIS_DIR/skills"
mkdir -p "$METIS_SKILLS_DIR"
ok "Created profile directory: $METIS_DIR"

# ─── 3. Download core files ─────────────────────────────────────────
info "Downloading Metis profile files..."
for f in config.yaml SOUL.md agents.md; do
  curl -fsSL -o "$METIS_DIR/$f" "$RAW_BASE/$f"
  ok "  $f"
done

# ─── 4. Download & install skills ───────────────────────────────────
info "Downloading Metis skills..."
SKILLS=(
  metis-obsidian
  metis-deep-research
  metis-connection-map
  metis-idea-to-plan
  metis-wormhole-intake
)
for skill in "${SKILLS[@]}"; do
  SKILL_DIR="$METIS_SKILLS_DIR/$skill"
  mkdir -p "$SKILL_DIR"
  curl -fsSL -o "$SKILL_DIR/SKILL.md" "$RAW_BASE/skills/$skill/SKILL.md" 2>/dev/null || true
  if [ -f "$SKILL_DIR/SKILL.md" ]; then
    ok "  $skill"
  else
    warn "  $skill (stub — will be filled in a future release)"
  fi
done

# ─── 5. Prompt for .env vars ────────────────────────────────────────
ENV_FILE="$METIS_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo
  info "Setting up Metis environment variables..."
  echo "Leave blank to skip any variable (you can edit $ENV_FILE later)."

  read -r -p "  Discord Bot Token (required for gateway): " DISCORD_TOKEN
  read -r -p "  Obsidian Vault Path (e.g. /home/user/obsidian): " OBSIDIAN_PATH
  read -r -p "  Obsidian Git Remote URL: " OBSIDIAN_REPO
  read -r -p "  Wormhole API Key (optional): " WORMHOLE_KEY

  cat > "$ENV_FILE" <<ENVEOF
DISCORD_BOT_TOKEN=${DISCORD_TOKEN:-}
OBSIDIAN_VAULT_PATH=${OBSIDIAN_PATH:-}
OBSIDIAN_REPO_URL=${OBSIDIAN_REPO:-}
WORMHOLE_API_KEY=${WORMHOLE_KEY:-}
ENVEOF
  ok "Created $ENV_FILE"
else
  warn "$ENV_FILE already exists — skipping .env setup"
fi

# ─── 6. Set up Discord gateway ──────────────────────────────────────
info "Configuring Discord gateway for Metis..."
if hermes -p metis gateway setup 2>&1; then
  ok "Discord gateway configured."
else
  warn "Gateway setup skipped or failed — run 'hermes -p metis gateway setup' manually."
fi

# ─── 7. Welcome ─────────────────────────────────────────────────────
echo
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║     Metis Agent — installed successfully!       ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo
echo -e "  ${BOLD}Profile:${NC}  metis"
echo -e "  ${BOLD}Config:${NC}   $METIS_DIR/config.yaml"
echo -e "  ${BOLD}Skills:${NC}   $METIS_SKILLS_DIR"
echo -e "  ${BOLD}Repo:${NC}     $REPO_URL"
echo
echo -e "  ${BOLD}Next Steps:${NC}"
echo -e "  1. Edit ${CYAN}$METIS_DIR/.env${NC} if you skipped any values"
echo -e "  2. Start chatting: ${CYAN}hermes -p metis${NC}"
echo -e "  3. Or start the Discord gateway: ${CYAN}hermes -p metis gateway run${NC}"
echo
echo -e "  ${BOLD}Need help?${NC}  $REPO_URL/issues"
echo
