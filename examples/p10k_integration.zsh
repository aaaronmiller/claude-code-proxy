# Powerlevel10k Integration for Claude Code Proxy
# Add this to your ~/.p10k.zsh file for prompt integration

# Custom segment for proxy status
function prompt_custom_proxy_status() {
  # Check if proxy is configured
  if [[ -z "$PROMPT_INJECTION_MODULES" ]]; then
    return
  fi

  # Get compact status from proxy
  local status_header=""

  # Use dashboard hooks to get live data
  # This requires the proxy to be running
  if command -v curl &> /dev/null && nc -z localhost 8082 2>/dev/null; then
    # Proxy is running - could fetch live stats
    # For now, show configured modules
    status_header=$(python3 -c "
import os
import sys
sys.path.insert(0, '$(pwd)')
try:
    from src.dashboard.prompt_modules import prompt_dashboard_renderer
    from src.dashboard.dashboard_hooks import dashboard_hooks

    modules = os.getenv('PROMPT_INJECTION_MODULES', '').split(',')
    modules = [m.strip() for m in modules if m.strip()]

    if modules:
        stats = dashboard_hooks.get_stats()
        header = prompt_dashboard_renderer.render_header(modules, 'small', stats)
        print(header)
except:
    pass
" 2>/dev/null)
  fi

  # Fallback to configured icon if proxy not running
  if [[ -z "$status_header" ]]; then
    case "$PROMPT_INJECTION_SIZE" in
      large)
        status_header="🔧📊"
        ;;
      medium)
        status_header="🔧⚡"
        ;;
      small)
        status_header="🔧"
        ;;
      *)
        status_header="🔧"
        ;;
    esac
  fi

  # Display with p10k styling
  p10k segment -f 208 -i '🔧' -t "$status_header"
}

# Alternative: Simpler static version
function prompt_custom_proxy_status_simple() {
  # Only show if configured
  [[ -z "$PROMPT_INJECTION_MODULES" ]] && return

  # Parse modules and show icons
  local icons=""
  for module in ${(s:,:)PROMPT_INJECTION_MODULES}; do
    case "$module" in
      status)
        icons+="🔧"
        ;;
      performance)
        icons+="⚡"
        ;;
      errors)
        icons+="⚠️"
        ;;
      models)
        icons+="🤖"
        ;;
    esac
  done

  p10k segment -f 208 -t "$icons"
}

# Installation Instructions:
# 1. Copy this entire section to your ~/.p10k.zsh
# 2. Add 'custom_proxy_status' to POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS
#    Example:
#      typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
#        status
#        command_execution_time
#        background_jobs
#        direnv
#        custom_proxy_status      # <-- Add here
#        context
#        nordvpn
#        time
#      )
# 3. Reload your shell: source ~/.zshrc

# Advanced: Show detailed status on hover (requires terminal support)
# function prompt_custom_proxy_status_detailed() {
#   [[ -z "$PROMPT_INJECTION_MODULES" ]] && return
#
#   # Get full medium-sized output
#   local detailed=$(python3 -c "...")
#
#   # Set tooltip (some terminals support this)
#   p10k segment -f 208 -i '🔧' -t "📊" -v "$detailed"
# }
