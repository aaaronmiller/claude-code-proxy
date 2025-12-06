#!/bin/bash

# API Key Wizard for Claude Code Proxy
# Fixes API keys in your global profile (zshrc/bash_profile)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧙 API Key Wizard for Claude Code Proxy${NC}"
echo "This wizard will help you fix your API keys in your shell profile."
echo ""

# 1. Detect Profile
PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.bashrc" ]; then
    PROFILE="$HOME/.bashrc"
elif [ -f "$HOME/.profile" ]; then
    PROFILE="$HOME/.profile"
else
    echo -e "${RED}Could not detect shell profile. Please enter path manually:${NC}"
    read -p "> " PROFILE
fi

echo -e "Detected profile: ${YELLOW}$PROFILE${NC}"
echo ""

# 2. Select Provider
echo "Select your provider:"
echo "1) Anthropic (Claude)"
echo "2) OpenRouter"
echo "3) OpenAI"
echo "4) Google Gemini"
echo "5) Perplexity"
read -p "Enter number (1-5): " PROVIDER_CHOICE

PROVIDER_NAME=""
PROVIDER_VAR=""
PROVIDER_URL_VAR=""
DEFAULT_URL=""

case $PROVIDER_CHOICE in
    1)
        PROVIDER_NAME="Anthropic"
        PROVIDER_VAR="ANTHROPIC_API_KEY"
        PROVIDER_URL_VAR="ANTHROPIC_BASE_URL"
        DEFAULT_URL="https://api.anthropic.com"
        ;;
    2)
        PROVIDER_NAME="OpenRouter"
        PROVIDER_VAR="OPENROUTER_API_KEY"
        PROVIDER_URL_VAR="OPENROUTER_BASE_URL"
        DEFAULT_URL="https://openrouter.ai/api/v1"
        ;;
    3)
        PROVIDER_NAME="OpenAI"
        PROVIDER_VAR="OPENAI_API_KEY"
        PROVIDER_URL_VAR="OPENAI_BASE_URL"
        DEFAULT_URL="https://api.openai.com/v1"
        ;;
    4)
        PROVIDER_NAME="Google Gemini"
        PROVIDER_VAR="GOOGLE_API_KEY"
        PROVIDER_URL_VAR="GOOGLE_BASE_URL"
        DEFAULT_URL="https://generativelanguage.googleapis.com/v1beta/openai"
        ;;
    5)
        PROVIDER_NAME="Perplexity"
        PROVIDER_VAR="PERPLEXITY_API_KEY"
        PROVIDER_URL_VAR="PERPLEXITY_BASE_URL"
        DEFAULT_URL="https://api.perplexity.ai"
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "Selected Provider: ${GREEN}$PROVIDER_NAME${NC}"

# 3. Input Key
echo -e "Enter your REAL ${PROVIDER_NAME} API Key:"
read -s -p "> " API_KEY
echo ""

if [ -z "$API_KEY" ]; then
    echo -e "${RED}API Key cannot be empty. Exiting.${NC}"
    exit 1
fi

# Basic validation
if [[ "$PROVIDER_NAME" == "Anthropic" && ! "$API_KEY" =~ ^sk-ant- ]]; then
    echo -e "${YELLOW}Warning: Anthropic keys usually start with 'sk-ant-'${NC}"
    read -p "Continue anyway? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then exit 1; fi
fi
if [[ "$PROVIDER_NAME" == "OpenRouter" && ! "$API_KEY" =~ ^sk-or- ]]; then
    echo -e "${YELLOW}Warning: OpenRouter keys usually start with 'sk-or-'${NC}"
    read -p "Continue anyway? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then exit 1; fi
fi

# 4. Write to Profile
echo ""
echo "Writing to $PROFILE..."

# Backup profile
cp "$PROFILE" "${PROFILE}.bak.$(date +%s)"
echo "Backed up profile to ${PROFILE}.bak.$(date +%s)"

# Function to update or append a variable
update_var() {
    local var_name="$1"
    local new_value="$2"
    local file="$3"
    
    # Check if var exists (commented or not)
    if grep -q "export ${var_name}=" "$file"; then
        # Replace existing line
        # Use a temporary file to avoid sed compatibility issues between macOS/Linux
        sed "s|^export ${var_name}=.*|export ${var_name}=\"${new_value}\"|" "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
        echo "Updated existing ${var_name}"
    else
        # Append new line
        echo "export ${var_name}=\"${new_value}\"" >> "$file"
        echo "Added new ${var_name}"
    fi
}

update_var "${PROVIDER_VAR}" "${API_KEY}" "$PROFILE"
update_var "${PROVIDER_URL_VAR}" "${DEFAULT_URL}" "$PROFILE"
update_var "PROVIDER_API_KEY" "\$${PROVIDER_VAR}" "$PROFILE"
update_var "PROVIDER_BASE_URL" "\$${PROVIDER_URL_VAR}" "$PROFILE"

echo "" >> "$PROFILE"
echo "# Updated by Claude Code Proxy Wizard $(date)" >> "$PROFILE"

echo -e "${GREEN}✅ Successfully updated $PROFILE${NC}"
echo ""
echo "Added:"
echo "  export ${PROVIDER_VAR}=..."
echo "  export ${PROVIDER_URL_VAR}=${DEFAULT_URL}"
echo "  export PROVIDER_API_KEY=\$${PROVIDER_VAR}"
echo "  export PROVIDER_BASE_URL=\$${PROVIDER_URL_VAR}"
echo ""
echo -e "${YELLOW}IMPORTANT: You must source your profile for changes to take effect in THIS terminal.${NC}"
echo "Run: source $PROFILE"
echo ""
