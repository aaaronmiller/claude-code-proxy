# Input Compression - Roadmap

> **Last Updated:** April 2, 2026  
> **Version:** 1.0.0  
> **Status:** Active Development

---

## Executive Summary

**Current Focus:** Phase 1 - Parallel Installation

**Key Achievements:**
- ✅ 92% GPU VRAM utilization
- ✅ 97% compression rate
- ✅ Multi-CLI support (6 CLIs)
- ✅ Unified control script
- ✅ Real-time visualization

---

## Project Phases

### Phase 1: Parallel Installation ✅ (IN PROGRESS)

**Goal:** Single command installs all three proxies

**Tasks:**
- [ ] Create `install-all.sh` - installs headroom, RTK, claude-code-proxy
- [ ] Create `unified-start.sh` - starts all in correct order
- [ ] Modify `compressctl` for claude-code-proxy awareness
- [ ] Test on fresh machine
- [ ] Document installation process

**Timeline:** April 2026

### Phase 2: Tight Integration ⏳ (PLANNED)

**Goal:** Shared state and unified monitoring

**Tasks:**
- [ ] Shared configuration file
- [ ] Unified health monitoring
- [ ] Log aggregation
- [ ] Cross-proxy event system

**Timeline:** May 2026

### Phase 3: Full Merger 🔮 (FUTURE)

**Goal:** Single unified proxy process

**Tasks:**
- [ ] Headroom as claude-code-proxy middleware
- [ ] RTK as proxy filter
- [ ] Single process, single port

**Timeline:** Q3 2026

---

## Feature Requests

### High Priority

1. **Low-VRAM Mode** (5GB GPU or less)
   - Target: Intel Arc A370M (5GB)
   - Strategy: Smaller models, CPU fallback
   - ETA: April 2026

2. **No-GPU Mode**
   - Target: CPU-only machines
   - Strategy: Quantized models
   - ETA: April 2026

3. **Network Proxy Access**
   - Target: Multiple machines sharing proxy
   - Strategy: SSH tunneling, LAN access
   - ETA: April 2026

### Medium Priority

4. **Auto-Optimization**
5. **Team Dashboard**
6. **Provider Integration**

---

## Technical Debt

### Refactoring Needed

1. **compressctl** - Add claude-code-proxy awareness
2. **State Management** - Shared state file
3. **Error Handling** - Standardize responses

### Documentation Gaps

1. Installation guide
2. Troubleshooting guide
3. Performance tuning guide

---

## Metrics & Goals

### Current Metrics (April 2026)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| GPU VRAM | 92% | 90%+ | ✅ |
| Compression | 97% | 95%+ | ✅ |
| Latency | 50ms | <100ms | ✅ |
| Cost Savings | 95-99% | 90%+ | ✅ |
| CLI Support | 6 | 5+ | ✅ |

### Q2 2026 Goals

- [ ] 10+ CLI integrations
- [ ] <40ms latency overhead
- [ ] 98%+ compression rate
- [ ] Network proxy access
- [ ] Low-VRAM mode

---

## Community

### How to Contribute

1. **Report Issues** - GitHub Issues
2. **Feature Requests** - GitHub Discussions
3. **Code Contributions** - Pull Requests

### Areas Needing Help

- [ ] Windows compatibility
- [ ] macOS testing
- [ ] Additional CLI integrations
- [ ] Translations

---

*This roadmap is a living document. Last updated: April 2, 2026*
