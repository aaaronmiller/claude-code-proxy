# Claude Code Proxy - Roadmap

> **Last Updated:** April 2, 2026
> **Version:** 2.2.0
> **Status:** Active Development

---

## Executive Summary

**Current Focus:** Phase 2 - Tight Integration

**Key Achievements (Phase 1):**
- ✅ 92% GPU VRAM utilization (up from 0.2%)
- ✅ 97% compression rate (900→26 tokens)
- ✅ 95-99% cost savings
- ✅ Multi-CLI support (6 CLIs)
- ✅ Unified control script & 30+ aliases
- ✅ Real-time visualization dashboard
- ✅ Unified installation script (install-all.sh)
- ✅ input-compression migrated and deprecated
- ✅ Low-VRAM/No-GPU support documented

---

## Project Phases

### Phase 1: Parallel Installation ✅ (COMPLETE - April 2026)

**Goal:** Single command installs all three proxies (claude-code-proxy, headroom, RTK)

**Completed Tasks:**
- [x] Create `install-all.sh` script
- [x] Create `unified-start.sh` script
- [x] Modify `compressctl` for claude-code-proxy awareness
- [x] Test on fresh machine
- [x] Document installation process
- [x] Migrate input-compression to compression/ directory
- [x] Deprecate input-compression repository
- [x] Add Low-VRAM mode (5GB GPU)
- [x] Add No-GPU mode (CPU-only)
- [x] Add Network proxy access (SSH/LAN)

**Files Created:**
- `install-all.sh` - Unified installer
- `compression/` directory with all compression code
- `compression/PHASE-1-FINAL.md` - Completion report

**Timeline:** April 2026 ✅

### Phase 2: Tight Integration ⏳ (IN PROGRESS - May 2026)

**Goal:** Shared state management and unified monitoring

**Tasks:**
- [ ] Shared configuration file
- [ ] Unified health monitoring
- [ ] Log aggregation
- [ ] Cross-proxy event system
- [ ] Unified systemd service
- [ ] Auto-optimization per content type
- [ ] Team dashboard with multi-user stats
- [ ] Direct OpenRouter API integration for actual costs

**Timeline:** May 2026

### Phase 3: Full Merger 🔮 (FUTURE - Q3 2026)

**Goal:** Single unified proxy process

**Tasks:**
- [ ] Headroom compression as claude-code-proxy middleware
- [ ] RTK-style compression as proxy filter
- [ ] Single process, single port
- [ ] No inter-proxy communication needed
- [ ] Resource optimization

**Timeline:** Q3 2026

---

## Feature Requests

### High Priority

1. **Low-VRAM Mode** (5GB GPU or less)
   - Target: Intel Arc A370M (5GB), integrated GPUs
   - Strategy: Smaller models, CPU fallback
   - ETA: April 2026

2. **No-GPU Mode**
   - Target: CPU-only machines
   - Strategy: Quantized models, efficient batching
   - ETA: April 2026

3. **Network Proxy Access**
   - Target: Multiple machines sharing single proxy
   - Strategy: SSH tunneling, cleartext LAN access
   - ETA: April 2026

### Medium Priority

4. **Auto-Optimization**
   - Learn optimal compression per content type
   - Adjust thresholds based on success

5. **Team Dashboard**
   - Multi-user stats aggregation
   - Per-user breakdown
   - Cost allocation

6. **Provider Integration**
   - Direct OpenRouter API integration
   - Fetch actual costs
   - Compare with estimates

### Low Priority

7. **Desktop GUI (Tauri)**
8. **Multi-instance analytics**
9. **MCP Server integration**
10. **Multi-agent orchestration ("Swarm Mode")**

---

## Technical Debt

### Refactoring Needed

1. **Model Detection**
   - Remove remaining hardcoded model names
   - Migrate to dynamic family detection
   - Priority: High

2. **Error Handling**
   - Standardize error responses
   - Add retry logic
   - Priority: Medium

3. **Logging**
   - Consolidate logging modules
   - Add structured logging
   - Priority: Medium

### Documentation Gaps

1. **API Documentation** - In progress
2. **Usage Examples** - In progress
3. **Troubleshooting Guide** - Needed
4. **Performance Tuning Guide** - Needed

---

## Known Issues

### Current Bugs

| Issue | Severity | Status | Workaround |
|-------|----------|--------|------------|
| Headroom JSONL logs not writing | Medium | Investigating | Use stdout logs |
| Compression stats not persistent | Low | Known | Manual export |

### Performance Issues

| Issue | Impact | Status |
|-------|--------|--------|
| GPU VRAM fragmentation | Moderate | Mitigated |
| Model load time (cold start) | Low | Accepted |

---

## Metrics & Goals

### Current Metrics (April 2026)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| GPU VRAM Utilization | 92% | 90%+ | ✅ Exceeded |
| Compression Rate | 97% | 95%+ | ✅ Exceeded |
| Latency Overhead | 50ms | <100ms | ✅ Exceeded |
| Cost Savings | 95-99% | 90%+ | ✅ Exceeded |
| CLI Integrations | 6 | 5+ | ✅ Exceeded |

### Q2 2026 Goals

- [ ] 10+ CLI integrations
- [ ] <40ms latency overhead
- [ ] 98%+ compression rate
- [ ] Network proxy access
- [ ] Low-VRAM mode

---

## Community Contributions

### How to Contribute

1. **Report Issues** - GitHub Issues
2. **Feature Requests** - GitHub Discussions
3. **Code Contributions** - Pull Requests
4. **Documentation** - Edit docs/ folder

### Areas Needing Help

- [ ] Windows compatibility
- [ ] macOS testing
- [ ] Additional CLI integrations
- [ ] Translations
- [ ] Performance benchmarks

---

## Version History

- **v2.1.0** (April 2026) - Compression Stack Integration
- **v2.0.0** (March 2026) - Multi-Provider Support
- **v1.0.0** (February 2026) - Initial Release

---

## Contact & Support

- **GitHub:** https://github.com/aaaronmiller/claude-code-proxy
- **Discussions:** https://github.com/aaaronmiller/claude-code-proxy/discussions
- **Issues:** https://github.com/aaaronmiller/claude-code-proxy/issues

---

*This roadmap is a living document. Last updated: April 2, 2026*
