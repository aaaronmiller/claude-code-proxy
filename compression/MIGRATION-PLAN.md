# Migration Plan: input-compression → claude-code-proxy

**Date:** April 2, 2026  
**Phase:** 1 - Unified Installation  
**Goal:** Deprecate input-compression by migrating all content to claude-code-proxy

---

## Migration Strategy

### 1. Directory Structure

**Target Structure (claude-code-proxy):**
```
claude-code-proxy/
├── compression/              # NEW - All compression-related code
│   ├── bin/                  # compressctl, shims
│   ├── scripts/              # install-all.sh, unified-start.sh, etc.
│   ├── rtk/                  # RTK assets (git submodule)
│   ├── headroom/             # Headroom assets (git submodule)
│   ├── docs/                 # Compression documentation
│   └── systemd/              # Systemd service files
├── src/                      # Existing proxy code
├── docs/                     # Existing docs
├── scripts/                  # Existing scripts
└── ...                       # Existing files
```

### 2. Files to Migrate

#### From input-compression/scripts/
- [x] install-all.sh → compression/scripts/
- [x] unified-start.sh → compression/scripts/
- [x] compression-stack.sh → compression/scripts/
- [x] compression-aliases.zsh → compression/scripts/
- [x] compression-dashboard.py → compression/scripts/
- [x] compression-tracker.py → compression/scripts/
- [x] gpu-resident-manager.py → compression/scripts/
- [x] harden-compression-stack.sh → compression/scripts/
- [x] compress-monitor-web.py → compression/scripts/
- [x] quickstart.sh → compression/scripts/ (merge with existing)

#### From input-compression/bin/
- [x] compressctl → compression/bin/
- [x] All shims → compression/bin/shims/

#### From input-compression/docs/
- [x] SUPPORT-MATRIX.md → compression/docs/
- [x] DELIBERATIVE-REVIEW.md → compression/docs/
- [x] SHELL-ALIASES.md → compression/docs/

#### From input-compression/ (root)
- [x] CHANGELOG.md → compression/CHANGELOG.md (merge)
- [x] ROADMAP.md → compression/ROADMAP.md (merge)
- [x] PHASE-1-COMPLETE.md → compression/PHASE-1-COMPLETE.md
- [x] README.md → Merge relevant sections into main README

#### From input-compression/rtk/ and headroom/
- [ ] Convert to git submodules in compression/

### 3. Installation Script

**New install-all.sh will:**
1. Clone claude-code-proxy
2. Clone RTK as submodule
3. Clone Headroom as submodule
4. Install Python dependencies
5. Install RTK (cargo or pip)
6. Install Headroom (pip)
7. Configure systemd services
8. Add aliases to ~/.zshrc
9. Start all services
10. Show health status

### 4. Deprecation Plan

**After migration:**
1. Update input-compression README with deprecation notice
2. Point all links to claude-code-proxy
3. Archive input-compression (read-only)
4. Update documentation links

---

## Implementation Checklist

### Phase 1a: File Migration
- [ ] Create compression/ directory structure
- [ ] Copy all scripts
- [ ] Copy all docs
- [ ] Copy bin/ files
- [ ] Update paths in scripts

### Phase 1b: Installation Script
- [ ] Create unified install-all.sh
- [ ] Add git clone for submodules
- [ ] Test on fresh machine

### Phase 1c: Documentation
- [ ] Merge CHANGELOGs
- [ ] Merge ROADMAPs
- [ ] Update main README
- [ ] Create migration guide

### Phase 1d: Deprecation
- [ ] Add deprecation notice to input-compression
- [ ] Update all links
- [ ] Archive repository

---

## Timeline

- **Phase 1a:** April 2, 2026 (Today)
- **Phase 1b:** April 3, 2026
- **Phase 1c:** April 3, 2026
- **Phase 1d:** April 4, 2026

---

*Migration plan created April 2, 2026*
