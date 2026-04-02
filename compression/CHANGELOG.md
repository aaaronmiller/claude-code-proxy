# Input Compression - Changelog

> **Last Updated:** April 2, 2026  
> **Version:** 1.0.0

---

## April 2026 - Compression Stack Integration

### Multi-CLI Compression Support

**Date:** April 2, 2026

**What Changed:**
- Extended compression beyond Claude Code to ALL CLIs
- Created shims for 6 CLIs (Claude, Qwen, Codex, OpenCode, OpenClaw, Hermes)
- Created compressed wrappers for forced compression
- Modified cli-init/resume to ALWAYS enable compression

**Files Added:**
- `scripts/harden-compression-stack.sh`
- `scripts/compression-aliases.zsh`
- `scripts/compression-stack.sh`
- `scripts/compression-dashboard.py`
- `scripts/compression-tracker.py`
- `scripts/gpu-resident-manager.py`
- `docs/DELIBERATIVE-REFINEMENT.md`
- `docs/PERFORMANCE-ANALYSIS.md`

**Key Features:**
1. **30+ new aliases** for quick access
2. **4 compression modes** (max/balanced/speed/free-tier)
3. **Unified control script** (compression-stack.sh)
4. **Visualization dashboard** (terminal + web)
5. **Auto-logging** of compression stats

---

### GPU VRAM Optimization

**Date:** April 2, 2026

**What Changed:**
- GPU utilization increased from 0.2% to 92%
- Multiple models loaded resident in VRAM
- Batch processing enabled (16x parallel chunks)
- GPU cache allocation (1.5GB)

**Results:**
- Before: 11 MiB (0.2%)
- After: 5311 MiB (92%)
- Improvement: 460x increase

**Files Added:**
- `scripts/gpu-resident-manager.py`
- `.config/systemd/user/gpu-resident-manager.service`

---

### Cost Savings Analysis

**Estimated Savings (OpenRouter 2026 Pricing):**

| User | Tokens/Month | Without | With | Savings |
|------|--------------|---------|------|---------|
| Individual | 50M | $75.00 | $2.25 | $72.75 (97%) |
| Team of 10 | 500M | $750.00 | $22.50 | $727.50 (97%) |

**Latency Impact:**
- Headroom: 45-55ms
- RTK: 3-7ms
- Total: 48-62ms (negligible vs 200-2000ms LLM inference)

---

## March 2026 - Initial Release

### RTK Integration

**Date:** March 30, 2026

**What Changed:**
- RTK compression integrated
- Command output compression (88.9% average)
- 15,720 commands processed
- 138 million tokens saved

---

### Headroom Integration

**Date:** March 28, 2026

**What Changed:**
- Headroom proxy integration
- Token compression (97% rate)
- GPU acceleration support

---

## Roadmap

### Phase 1: Parallel Installation (April 2026)
- [ ] Create `install-all.sh` script
- [ ] Create `unified-start.sh` script
- [ ] Modify `compressctl` for claude-code-proxy awareness
- [ ] Test on fresh machine

### Phase 2: Tight Integration (May 2026)
- [ ] Shared state management
- [ ] Unified health monitoring
- [ ] Log aggregation

### Phase 3: Full Merger (Q3 2026)
- [ ] Headroom compression built INTO claude-code-proxy
- [ ] RTK-style compression as proxy middleware
- [ ] Single process, single port

---

*Changelog for input-compression project*
