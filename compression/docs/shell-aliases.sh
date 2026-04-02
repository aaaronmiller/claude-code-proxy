# Headroom + RTK token compression stack (off by default, use `compress-on`)
# Source: ~/.zshrc lines 13-39
# Copy this block into any machine's shell rc file, or use deploy-compression-stack.sh

export RTK_TELEMETRY_DISABLED=1
export HEADROOM_TELEMETRY=off

compress-on() { # route all LLM API traffic through headroom proxy (:8787)
  export ANTHROPIC_BASE_URL=http://127.0.0.1:8787
  export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
  export GEMINI_API_BASE=http://127.0.0.1:8787/v1
  systemctl --user start headroom-proxy.service 2>/dev/null
  echo "compression ON  →  :8787"
}

compress-off() { # restore direct API access, unset proxy routing
  unset ANTHROPIC_BASE_URL
  unset OPENAI_BASE_URL
  unset GEMINI_API_BASE
  echo "compression OFF →  direct API"
}

compress-status() { # show current compression routing state and live stats
  local proxy_state=$(systemctl --user is-active headroom-proxy.service 2>/dev/null)
  echo "headroom service: $proxy_state"
  echo "ANTHROPIC_BASE_URL: ${ANTHROPIC_BASE_URL:-(unset, direct)}"
  echo "OPENAI_BASE_URL:    ${OPENAI_BASE_URL:-(unset, direct)}"
  echo "RTK hook:           always-on (shell output layer, harmless)"
  [[ "$proxy_state" == "active" ]] && curl -sf http://127.0.0.1:8787/stats 2>/dev/null | python3 -m json.tool 2>/dev/null || true
}
