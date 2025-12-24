# PRD: Web UI Redesign & Auto-Wizard Fallback

**Version**: 1.0
**Date**: 2025-12-20
**Status**: Draft

---

## Executive Summary

Redesign the existing web configuration UI with a modern "cyberpunk terminal" aesthetic that appeals to developer sensibilities, add comprehensive settings coverage, and implement intelligent auto-wizard fallback when API providers are unreachable.

---

## Problem Statement

### Current State
1. **Existing web UI** at `/static/` is functional but uses a generic dark theme
2. **Missing settings** - many .env options aren't configurable via web UI
3. **No graceful failure** - if API provider is down/misconfigured, proxy starts but fails silently
4. **No visual differentiation** - looks like every other dashboard

### Desired State
1. **Distinctive "leet" aesthetic** - cyberpunk/terminal hybrid that developers love
2. **Complete settings coverage** - all .env options configurable via UI
3. **Intelligent fallback** - auto-launch wizard when provider is unreachable
4. **Enhanced features** - live logs, health checks, usage graphs

---

## Goals & Success Metrics

| Goal | Metric |
|------|--------|
| Developer appeal | Positive feedback on aesthetic |
| Complete configuration | 100% of .env settings available in UI |
| Reduced setup friction | Users can fix config without editing files |
| Enhanced monitoring | Real-time request visibility |

---

## Scope

### Phase 1: Auto-Wizard Fallback (Priority: HIGH)
- On startup, perform health check on configured provider
- If unreachable (404, 401, connection refused), launch interactive wizard
- Allow user to fix configuration
- Resume normal startup after successful config

### Phase 2: UI Redesign (Priority: HIGH)
- Apply cyberpunk/terminal theme to existing UI
- Monospace headers, neon accents (cyan/magenta)
- Subtle glow effects, terminal-style elements
- Keep existing functionality intact

### Phase 3: Missing Settings (Priority: MEDIUM)
Add configuration for:
- Hybrid mode (per-model endpoints)
- Custom system prompts
- Terminal output settings
- Dashboard configuration
- Crosstalk settings
- Custom headers

### Phase 4: Enhanced Features (Priority: LOW)
- Live request log (WebSocket)
- Provider health check panel
- Usage graphs (from SQLite)
- Model playground (test prompts)
- API key validator

### Out of Scope (Future)
- macOS native Go wrapper (separate project)
- Mobile responsive design
- Multi-user authentication

---

## Technical Design

### Theme: Cyberpunk Terminal

**Color Palette:**
```css
--bg-primary: #0a0a0f;        /* Deep black */
--bg-surface: #12121a;        /* Card backgrounds */
--bg-elevated: #1a1a24;       /* Hover states */

--accent-cyan: #00fff2;       /* Primary accent */
--accent-magenta: #ff00ff;    /* Secondary accent */
--accent-green: #00ff88;      /* Success/terminal */
--accent-amber: #ffaa00;      /* Warning */
--accent-red: #ff3366;        /* Error */

--text-primary: #e0e0e0;      /* Main text */
--text-secondary: #808080;    /* Muted text */
--text-glow: #00fff2;         /* Glowing text */

--border-default: #2a2a3a;    /* Subtle borders */
--border-glow: rgba(0,255,242,0.3); /* Glowing borders */
```

**Typography:**
- Headers: `JetBrains Mono` or `Fira Code` (monospace)
- Body: `Inter` or system sans-serif
- Code: `JetBrains Mono`

**Effects:**
- Subtle glow on focus/hover: `box-shadow: 0 0 10px var(--accent-cyan)`
- Terminal cursor blink animation
- Scanline overlay (optional, toggleable)
- Gradient borders on cards

### Auto-Wizard Implementation

```python
# In src/main.py or startup
async def check_provider_health() -> bool:
    """Check if configured provider is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                f"{config.provider_base_url}/models",
                headers={"Authorization": f"Bearer {config.provider_api_key}"}
            )
            return response.status_code in [200, 401]  # 401 = reachable but bad key
    except Exception:
        return False

async def startup():
    if not await check_provider_health():
        logger.warning("Provider unreachable - launching setup wizard")
        from src.cli.wizard import SetupWizard
        wizard = SetupWizard()
        wizard.run()
        # Reload config after wizard
        reload_config()
```

### File Structure

```
src/static/
├── index.html          # Main app (existing, update)
├── dashboard.html      # Dashboard (existing, update)
├── css/
│   ├── style.css       # Base styles (replace)
│   ├── theme-cyber.css # Cyberpunk theme (new)
│   └── animations.css  # Glow/terminal effects (new)
├── js/
│   ├── app.js          # Main app logic (existing, update)
│   ├── websocket.js    # Live updates (new)
│   └── charts.js       # Usage graphs (new)
└── fonts/              # JetBrains Mono (new)
```

---

## UI Sections

### 1. Header
- Glowing logo/title
- Status indicator (pulsing green/red)
- Provider name + model info
- Settings gear icon

### 2. Navigation Tabs
```
[CORE] [MODELS] [ROUTING] [TERMINAL] [MONITOR] [LOGS]
```

### 3. Core Settings Tab
- Provider selection (dropdown with icons)
- API key input (password with toggle)
- Base URL input
- Proxy auth key
- Quick provider presets (VibeProxy, OpenRouter, etc.)

### 4. Models Tab
- BIG/MIDDLE/SMALL model inputs
- Model browser with search
- Reasoning configuration
  - Effort level slider
  - Max tokens input (with 128k max)
  - Per-model overrides

### 5. Routing Tab (Hybrid Mode)
- Enable per-tier routing toggles
- Endpoint + API key for each tier
- Visual routing diagram

### 6. Terminal Tab
- Display mode selector
- Toggle switches for each metric
- Color scheme picker
- Preview panel

### 7. Monitor Tab
- Stats cards (requests, tokens, cost, latency)
- Usage graph (line chart, last 24h)
- Provider health status

### 8. Logs Tab
- Live request stream (WebSocket)
- Filter by model/status
- Click to expand details

---

## Implementation Plan

### Day 1: Auto-Wizard + Theme Foundation
1. Implement provider health check
2. Add wizard fallback logic
3. Create new CSS theme file
4. Apply to existing HTML

### Day 2: Complete UI Redesign
1. Update all HTML elements with new classes
2. Add glow effects and animations
3. Implement tab navigation updates
4. Add missing settings sections

### Day 3: Enhanced Features
1. Add WebSocket live logs
2. Implement usage charts
3. Add provider health panel
4. Testing and polish

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Theme too flashy | Add "subtle" theme toggle |
| Performance (animations) | Use CSS transforms, reduce-motion support |
| Browser compatibility | Test on Chrome, Firefox, Safari |
| Wizard blocks startup | Add `--skip-wizard` flag |

---

## Future Considerations

### macOS Native Wrapper (Go)
- Similar to VibeProxy architecture
- Menu bar icon with status
- Native notifications
- Would be separate project
- Estimate: 1-2 weeks

### Alternative Approaches Considered
1. **Electron app** - Too heavy for a proxy
2. **Tauri app** - Good option for native, but adds complexity
3. **Just CLI** - Current state, works but less accessible

---

## Appendix: Trending UI References

1. **Cyberpunk theme**: https://www.shadcn.io/theme/cyberpunk
2. **Catppuccin**: https://tweakcn.com/ (catppuccin preset)
3. **VS Code theme**: https://www.shadcn.io/theme/vs-code
4. **Terminal aesthetic**: Dribbble neon-ui tag
