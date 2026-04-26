#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# Metis Agent — Install Script
# ═══════════════════════════════════════════════════════════════
# One-curl install. Run:
#
#   curl -fsSL https://raw.githubusercontent.com/kelevra-os/metis-agent/main/install.sh | bash
#
# This script:
#   1. Installs Hermes Agent if not already present
#   2. Creates ~/.hermes/profiles/metis/ directory structure
#   3. Drops in config.yaml, SOUL.md, agents.md
#   4. Installs skills from the skills/ directory
#   5. Prompts for required .env variables
#   6. Runs hermes -p metis gateway setup
#   7. Prints a welcome message
# ═══════════════════════════════════════════════════════════════

REPO_URL="https://raw.githubusercontent.com/kelevra-os/metis-agent/main"
HERMES_HOME="${HOME}/.hermes"
METIS_HOME="${HERMES_HOME}/profiles/metis"
METIS_SKILLS="${METIS_HOME}/skills"
METIS_ENV="${METIS_HOME}/.env"

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { printf "${CYAN}ℹ %s${NC}\n" "$*"; }
ok()    { printf "${GREEN}✓ %s${NC}\n" "$*"; }
warn()  { printf "${YELLOW}⚠ %s${NC}\n" "$*"; }
error() { printf "${RED}✗ %s${NC}\n" "$*"; }
header(){ printf "\n${BOLD}══ %s ══${NC}\n\n" "$*"; }

# ── Step 1: Ensure Hermes Agent is installed ─────────────────
header "Step 1: Hermes Agent"

if command -v hermes &>/dev/null; then
    HERMES_VERSION=$(hermes --version 2>/dev/null || echo "installed")
    ok "Hermes Agent found: ${HERMES_VERSION}"
else
    info "Hermes Agent not found. Installing..."
    curl -fsSL https://hermes-agent.sh/install.sh | bash
    
    if ! command -v hermes &>/dev/null; then
        # Try adding to PATH
        export PATH="${HOME}/.local/bin:${PATH}"
    fi
    
    if command -v hermes &>/dev/null; then
        ok "Hermes Agent installed successfully"
    else
        error "Hermes Agent installation failed."
        error "Please install manually: curl -fsSL https://hermes-agent.sh/install.sh | bash"
        exit 1
    fi
fi

# ── Step 2: Create Metis profile directory structure ─────────
header "Step 2: Metis Profile Directory"

mkdir -p "${METIS_HOME}"
mkdir -p "${METIS_SKILLS}"
ok "Created ${METIS_HOME}/"

# ── Step 3: Download configuration files ─────────────────────
header "Step 3: Configuration Files"

download_file() {
    local url="${REPO_URL}/$1"
    local dest="$2"
    
    if curl -fsSL "${url}" -o "${dest}" 2>/dev/null; then
        ok "Downloaded $1"
    else
        error "Failed to download $1 from ${url}"
        return 1
    fi
}

download_file "config.yaml" "${METIS_HOME}/config.yaml"
download_file "SOUL.md" "${METIS_HOME}/SOUL.md"
download_file "agents.md" "${METIS_HOME}/agents.md"

# ── Step 4: Install skills ───────────────────────────────────
header "Step 4: Skills"

SKILLS=(
    "metis-obsidian"
    "metis-deep-research"
    "metis-connection-map"
    "metis-idea-to-plan"
    "metis-wormhole-intake"
)

for skill in "${SKILLS[@]}"; do
    SKILL_DIR="${METIS_SKILLS}/${skill}"
    SKILL_FILE="${SKILL_DIR}/SKILL.md"
    
    mkdir -p "${SKILL_DIR}"
    
    if curl -fsSL "${REPO_URL}/skills/${skill}/SKILL.md" -o "${SKILL_FILE}" 2>/dev/null; then
        ok "Installed skill: ${skill}"
    else
        # Create a stub if the skill file doesn't exist on remote yet
        cat > "${SKILL_FILE}" <<-STUB
# ${skill}

<!-- Scaffold — content coming in a future phase. -->

## Purpose

*Describe what this skill does.*

## When to Use

*When should Metis load this skill?*

## Steps

*Step-by-step workflow.*

## Pitfalls

*Common mistakes and how to avoid them.*

## Related

*Links to other skills or references.*
STUB
        warn "Created stub for skill: ${skill} (not yet on remote)"
    fi
done

ok "Skills installed to ${METIS_SKILLS}/"

# ── Step 5: Environment variables ────────────────────────────
header "Step 5: Environment Variables"

if [ -f "${METIS_ENV}" ]; then
    warn ".env file already exists at ${METIS_ENV}"
    echo ""
    printf "Do you want to overwrite it? [y/N] "
    read -r OVERWRITE
    if [ "${OVERWRITE}" != "y" ] && [ "${OVERWRITE}" != "Y" ]; then
        info "Keeping existing .env file"
    else
        rm "${METIS_ENV}"
    fi
fi

if [ ! -f "${METIS_ENV}" ]; then
    echo ""
    info "Let's configure your Metis environment."
    echo "You can also edit ${METIS_ENV} later."
    echo ""
    
    # Download template
    TEMPLATE=$(curl -fsSL "${REPO_URL}/.env.template" 2>/dev/null || cat)
    
    # Prompt for required values
    printf "${BOLD}Discord Bot Token${NC} (create one at https://discord.com/developers/applications): "
    read -r DISCORD_TOKEN
    
    DEFAULT_VAULT="${HOME}/Documents/Obsidian Vault"
    printf "${BOLD}Obsidian Vault Path${NC} (default: ${DEFAULT_VAULT}): "
    read -r VAULT_PATH
    if [ -z "${VAULT_PATH}" ]; then
        VAULT_PATH="${DEFAULT_VAULT}"
    fi
    
    printf "${BOLD}Obsidian Repo URL${NC} (git remote for vault sync, e.g., git@github.com:you/vault.git): "
    read -r VAULT_REPO
    
    printf "${BOLD}Wormhole API Key${NC} (optional, press Enter to skip): "
    read -r WORMHOLE_KEY
    
    # Write .env file
    cat > "${METIS_ENV}" <<ENVFILE
# Metis Agent — Environment Configuration
# Generated by install.sh on $(date)

DISCORD_BOT_TOKEN=${DISCORD_TOKEN}
OBSIDIAN_VAULT_PATH=${VAULT_PATH}
OBSIDIAN_REPO_URL=${VAULT_REPO}
WORMHOLE_API_KEY=${WORMHOLE_KEY:-}
ENVFILE
    
    chmod 600 "${METIS_ENV}"
    ok "Written to ${METIS_ENV}"
fi

# ── Step 6: Obsidian vault setup ─────────────────────────────
header "Step 6: Obsidian Vault"

if [ -n "${VAULT_REPO}" ] && [ -n "${VAULT_PATH}" ]; then
    if [ -d "${VAULT_PATH}/.git" ]; then
        info "Vault already cloned at ${VAULT_PATH} — pulling latest"
        (cd "${VAULT_PATH}" && git pull) || warn "git pull failed — check your SSH keys and remote URL"
    elif [ -d "${VAULT_PATH}" ]; then
        warn "Directory exists at ${VAULT_PATH} but is not a git repo."
        info "Run this manually to clone: git clone ${VAULT_REPO} \"${VAULT_PATH}\""
    else
        info "Cloning vault from ${VAULT_REPO} → ${VAULT_PATH}"
        mkdir -p "$(dirname "${VAULT_PATH}")"
        git clone "${VAULT_REPO}" "${VAULT_PATH}" && ok "Vault cloned" || error "git clone failed — check the URL and your SSH/HTTPS access"
    fi
else
    warn "OBSIDIAN_REPO_URL or OBSIDIAN_VAULT_PATH not set — skipping vault setup"
    info "You can set these later in ${METIS_ENV} and run:"
    info "  git clone <repo-url> \"\${OBSIDIAN_VAULT_PATH}\""
fi

# ── Step 7: Gateway setup ────────────────────────────────────
header "Step 7: Discord Gateway"

if [ -n "${DISCORD_TOKEN:-}" ]; then
    info "Running: hermes -p metis gateway setup"
    echo ""
    hermes -p metis gateway setup 2>&1 || warn "Gateway setup had issues — you can re-run: hermes -p metis gateway setup"
    ok "Gateway configured"
else
    warn "No DISCORD_BOT_TOKEN provided — skipping gateway setup."
    warn "Run later: hermes -p metis gateway setup"
    warn "Or edit ${METIS_ENV} and re-run this script."
fi

# ── Done ──────────────────────────────────────────────────────
header "Metis Agent — Installed!"

echo ""
echo "  ${BOLD}Next steps:${NC}"
echo ""
echo "  1. Start Metis in Discord:"
echo "       hermes -p metis gateway run"
echo ""
echo "  2. Or chat in the terminal:"
echo "       hermes -p metis"
echo ""
echo "  3. Edit your environment:"
echo "       \$EDITOR ${METIS_ENV}"
echo ""
echo "  4. Explore Metis's personality:"
echo "       cat ${METIS_HOME}/SOUL.md"
echo ""
echo "  5. Set up Obsidian git sync on your other devices:"
echo "       git clone ${VAULT_REPO:-<OBSIDIAN_REPO_URL>} ~/Documents/Obsidian\\ Vault"
echo "       # Then use the Obsidian git plugin or a cron job to pull regularly"
echo ""
echo "  ${BOLD}Links:${NC}"
echo "    Repository:  https://github.com/kelevra-os/metis-agent"
echo "    Hermes:      https://github.com/kelevra-os/hermes-agent"
echo ""

# ── Post-install check ───────────────────────────────────────
printf "Would you like to start Metis now? [y/N] "
read -r START_NOW
if [ "${START_NOW}" = "y" ] || [ "${START_NOW}" = "Y" ]; then
    echo ""
    info "Starting Metis... (press Ctrl+C to exit)"
    echo ""
    hermes -p metis
fi

ok "Install complete. Welcome to Metis 🦉"
