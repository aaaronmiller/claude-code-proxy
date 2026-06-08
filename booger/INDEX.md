# Audit Index — Quick Reference

## 📋 Documents Overview

| Document | Size | Lines | Purpose |
|----------|------|-------|---------|
| **[AUDIT.md](AUDIT.md)** | 25K | 570 | Executive summary, risk assessment, top 15 changes |
| **[FEATURES.md](FEATURES.md)** | 18K | 322 | Categorized feature inventory (64 features across 14 categories) |
| **[FILE-CHANGES.md](FILE-CHANGES.md)** | 14K | 347 | File-level diff manifest, new directories, deleted files |
| `file-inventory.txt` | 36K | — | Complete sorted file list for both repos |
| `file-diff-inventory.txt` | 37K | — | New/deleted/modified classification |
| `scratch-1.md` | 338B | 7 | Audit initialization, upstream identification |
| `scratch-2.md` | 22K | 563 | Raw source file diffs (src/) |
| `scratch-3.md` | 32K | 696 | Raw config/infra file diffs |
| `SCRATCH-4-FEATURE-INVENTORY.md` | 9K | 247 | Detailed feature inventory by subsystem |
| **`README.md`** (this file) | — | — | Navigation index |

**Total audit data:** 212 KB, ~2,750 lines of documentation

---

## 🎯 Quick Answers

### Q: What is this fork?
A: aaaronmiller's heavily-modified claude-code-proxy with compression, dashboard, crosstalk, usage tracking.

### Q: How different is it from upstream?
A: 29 files → 618 files. 25× codebase growth. Upstream is simple proxy; fork is enterprise AI gateway platform.

### Q: Is it stable?
A: 62/64 features complete and working. 2 incomplete (VibeProxy token refresh, free model ranking freshness). 1 deprecated. Production-ready for small teams.

### Q: Can I merge upstream changes?
A: No. Architectures incompatible. Fork rewrote everything. Treat as independent project.

### Q: What are the top 5 new features?
1. **Compression Stack** — 97% token savings with Headroom + RTK
2. **Web Dashboard** — Svelte real-time monitoring UI
3. **Crosstalk** — Multi-model conversations (8 models)
4. **Usage Analytics** — SQLite tracking, cost, quotas
5. **Circuit Breakers** — Resilient cascade fallback

### Q: What's broken/incomplete?
- Test coverage near zero (⚠️ CRITICAL)
- Schema migrations missing (usage DB created inline)
- VibeProxy requires manual re-auth on token expiry
- Free model rankings stale without manual refresh
- GPU resident manager experimental (may leak memory)

### Q: Should I use this fork?
**Yes if you need:**
- Token compression (97% savings)
- Realtime dashboard
- Multi-model crosstalk
- Usage tracking + quotas
- Production resilience (circuit breakers)

**No if you need:**
- Minimal simple proxy (upstream is 300 LOC)
- Extensive test coverage (fork has almost none)
- Easy Docker deployment (Dockerfile exists but not published)
- Mergeability with upstream (impossible)

---

## 🔍 File Locations by Topic

### Compression Stack
- Code: `compression/lib/`
- Services: `compression/systemd/`
- Scripts: `compression/scripts/`
- Docs: `compression/docs/`

### Web Dashboard  
- Frontend: `web-ui/src/`
- Backend: `src/dashboard/`
- Static: `web-ui/static/`

### Crosstalk
- Orchestrator: `src/conversation/crosstalk.py`
- Presets: `configs/crosstalk/presets/`
- Prompts: `configs/crosstalk/prompts/`
- Templates: `configs/crosstalk/templates/`

### Usage Tracking
- DB: `data/usage_tracking.db`
- Tracker: `src/services/usage/usage_tracker.py`
- API: `src/api/endpoints.py` (analytics routes)

### CLI Tools
- Main: `start_proxy.py`
- Commands: `src/services/cli/`
- Aliases: `compression/scripts/compression-aliases.zsh`

---

## 📊 Stats at a Glance

```
Files:        29 (upstream) → 618 (fork)  [+589]
Source LOC:   ~3K → ~50K+                  [+47K]
Python files: 12 → 304                      [+292]
New dirs:     0 → 13                        [+13]
CLI cmds:     2 → 20+                       [+18]
API endpoints: 2 → 20+                       [+18]
```

---

## 🚀 Getting Started with Fork

1. **Install:** `./install-all.sh` — auto-detects GPU, installs deps, configures
2. **Start:** `cs-start` (compression) or `python start_proxy.py` (proxy only)
3. **Configure:** `python start_proxy.py --setup` or `--settings` for TUI
4. **Access:**
   - Proxy: http://localhost:8082
   - Dashboard: http://localhost:8899
   - Docs: `docs/` directory
5. **Monitor:** `cs-stats-quick` or web dashboard

---

## 📁 Audit File Structure

```
booger/
├── README.md                    ← You are here (index)
├── AUDIT.md                     ← Executive summary + risk assessment
├── FEATURES.md                  ← Categorized feature inventory (64 features)
├── FILE-CHANGES.md              ← File-by-file change manifest
├── file-inventory.txt           ← Raw file lists for both repos
├── file-diff-inventory.txt      ← New/deleted/modified classification
├── scratch-1.md                 ← Initial findings, upstream ID
├── scratch-2.md                 ← Source code diffs (src/)
├── scratch-3.md                 ← Config/infra diffs
└── SCRATCH-4-FEATURE-INVENTORY.md  ← Detailed feature breakdown
```

---

## 🎓 Understanding the Fork

### Upstream Philosophy (fuergaosi233)
- Minimal single-file proxy (~300 LOC)
- Simple env var config
- No dependencies beyond FastAPI + OpenAI SDK
- Single responsibility: convert Anthropic → OpenAI API

### Fork Philosophy (aaaronmiller)
- Full AI gateway platform
- Enterprise features: compression, analytics, multi-model, dashboard
- Production resilience: circuit breakers, cascade, deduplication
- Developer experience: CLI wizards, TUIs, docs
- GPU-optimized from day one
- Self-hosted with auto-updates

**They are different products sharing a name.**

---

## 🔗 Cross-References

- **Upstream repo:** https://github.com/fuergaosi233/claude-code-proxy
- **Fork repo:** https://github.com/aaaronmiller/claude-code-proxy
- **Compression docs:** `compression/docs/COMPRESSION-STACK.md`
- **Crosstalk guide:** `docs/crosstalk.md`
- **API reference:** `docs/api/reference.md`
- **Troubleshooting:** `docs/troubleshooting/`

---

**Last updated:** 2026-04-21  
**Maintained by:** Kilo (audit) + aaaronmiller (fork)  
**License:** MIT (both upstream and fork)
