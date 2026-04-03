# Compression Stack Integration Guide

**Version:** 1.0.0  
**Date:** April 2, 2026  
**Strategy:** Tight Integration with Independent Projects

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE PROXY                                 │
│  (Main Application - Port 8082)                                     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │ HTTP :8787
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    HEADROOM PROXY                                    │
│  (External Project - Port 8787)                                     │
│  - Token compression (97% rate)                                     │
│  - GPU-accelerated (92% VRAM)                                       │
│  - Managed via git submodule                                        │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UPSTREAM PROVIDERS                                │
│  (OpenRouter, OpenAI, Anthropic, etc.)                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    RTK (Command Layer)                               │
│  (External Project - Shell Integration)                             │
│  - Command output compression (88.9% rate)                          │
│  - Pre-processing before Headroom                                   │
│  - Managed via git submodule                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Integration Strategy

### 1. Git Submodules (Recommended)

**Keep Headroom and RTK as independent git repositories** but managed within claude-code-proxy:

```bash
# compression/ directory structure
compression/
├── headroom/           # git submodule → github.com/chopratejas/headroom
├── rtk/                # git submodule → github.com/rtk-ai/rtk
├── scripts/            # Our integration scripts
├── lib/                # Adapter layers
└── systemd/            # Service definitions
```

**Benefits:**
- ✅ Independent projects retained
- ✅ Easy updates (`git submodule update --remote`)
- ✅ Version control over integration point
- ✅ Can fork if needed
- ✅ Clear separation of concerns

**Cost:**
- ⚠️ Proxy hop overhead (~50ms)
- ⚠️ Inter-process communication
- ⚠️ Separate version management

---

### 2. Adapter Layers

**Create Python adapters** to isolate breaking changes:

#### Headroom Adapter

```python
# compression/lib/headroom_adapter.py
"""
Adapter layer for Headroom compression proxy.
Isolates breaking changes and provides version compatibility.
"""
import subprocess
import sys
from typing import Optional
from packaging import version

HEADROOM_MIN_VERSION = "1.0.0"
HEADROOM_MAX_VERSION = "2.0.0"

class HeadroomAdapter:
    """Manages Headroom proxy lifecycle and compatibility."""
    
    def __init__(self, port: int = 8787):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self._process: Optional[subprocess.Popen] = None
    
    def get_version(self) -> str:
        """Get installed Headroom version."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'headroom', '--version'],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except Exception as e:
            return f"unknown (error: {e})"
    
    def check_compatibility(self) -> bool:
        """Check if installed version is compatible."""
        current = self.get_version()
        try:
            v_current = version.parse(current.split()[-1])  # Extract version string
            v_min = version.parse(HEADROOM_MIN_VERSION)
            v_max = version.parse(HEADROOM_MAX_VERSION)
            return v_min <= v_current < v_max
        except:
            return False  # Assume incompatible if can't parse
    
    def start(self, mode: str = "token_headroom", backend: str = "openrouter") -> bool:
        """Start Headroom proxy."""
        if self.is_running():
            return True
        
        cmd = [
            sys.executable, '-m', 'headroom', 'proxy',
            '--port', str(self.port),
            '--mode', mode,
            '--openai-api-url', 'https://openrouter.ai/api/v1',
            '--backend', backend,
            '--no-telemetry'
        ]
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            return True
        except Exception as e:
            print(f"Failed to start Headroom: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop Headroom proxy."""
        if self._process:
            self._process.terminate()
            self._process = None
            return True
        
        # Fallback: kill by process name
        subprocess.run(['pkill', '-f', 'headroom proxy'], capture_output=True)
        return True
    
    def is_running(self) -> bool:
        """Check if Headroom is running."""
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.base_url}/health", timeout=2)
            return True
        except:
            return False
    
    def health(self) -> dict:
        """Get Headroom health status."""
        try:
            import urllib.request
            import json
            response = urllib.request.urlopen(f"{self.base_url}/health", timeout=2)
            return json.loads(response.read().decode())
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Singleton instance
_adapter: Optional[HeadroomAdapter] = None

def get_adapter() -> HeadroomAdapter:
    """Get or create Headroom adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = HeadroomAdapter()
    return _adapter
```

#### RTK Adapter

```python
# compression/lib/rtk_adapter.py
"""
Adapter layer for RTK command compression.
Isolates breaking changes and provides version compatibility.
"""
import subprocess
from typing import Optional
from packaging import version

RTK_MIN_VERSION = "0.34.0"
RTK_MAX_VERSION = "1.0.0"

class RTKAdapter:
    """Manages RTK installation and compatibility."""
    
    def get_version(self) -> str:
        """Get installed RTK version."""
        try:
            result = subprocess.run(['rtk', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def check_compatibility(self) -> bool:
        """Check if installed version is compatible."""
        current = self.get_version()
        try:
            v_current = version.parse(current.replace('v', ''))
            v_min = version.parse(RTK_MIN_VERSION)
            v_max = version.parse(RTK_MAX_VERSION)
            return v_min <= v_current < v_max
        except:
            return False
    
    def is_installed(self) -> bool:
        """Check if RTK is installed."""
        try:
            subprocess.run(['rtk', '--version'], 
                         capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def init(self, global_mode: bool = True) -> bool:
        """Initialize RTK."""
        cmd = ['rtk', 'init']
        if global_mode:
            cmd.append('--global')
        
        try:
            subprocess.run(cmd, timeout=30, check=True)
            return True
        except Exception as e:
            print(f"RTK init failed: {e}")
            return False
    
    def gain(self) -> dict:
        """Get RTK compression stats."""
        try:
            result = subprocess.run(['rtk', 'gain'], 
                                  capture_output=True, text=True, timeout=10)
            # Parse output (format varies by version)
            return {"output": result.stdout, "success": result.returncode == 0}
        except Exception as e:
            return {"error": str(e), "success": False}

# Singleton instance
_adapter: Optional[RTKAdapter] = None

def get_adapter() -> RTKAdapter:
    """Get or create RTK adapter singleton."""
    global _adapter
    if _adapter is None:
        _adapter = RTKAdapter()
    return _adapter
```

---

### 3. Unified Management

**Single command to manage all components:**

```python
# compression/lib/stack_manager.py
"""
Unified management for compression stack.
Controls Headroom, RTK, and integration.
"""
from typing import Dict, List
from .headroom_adapter import get_adapter as get_headroom
from .rtk_adapter import get_adapter as get_rtk

class CompressionStackManager:
    """Manages entire compression stack."""
    
    def __init__(self):
        self.headroom = get_headroom()
        self.rtk = get_rtk()
    
    def start_all(self) -> Dict[str, bool]:
        """Start all compression services."""
        results = {}
        
        # Start RTK first (command layer)
        results['rtk'] = self.rtk.is_installed()
        
        # Start Headroom (proxy layer)
        results['headroom'] = self.headroom.start()
        
        # Verify health
        results['healthy'] = self.headroom.is_running()
        
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        """Stop all compression services."""
        results = {}
        results['headroom'] = self.headroom.stop()
        results['rtk'] = True  # RTK doesn't have daemon mode
        return results
    
    def status(self) -> Dict:
        """Get comprehensive status."""
        return {
            'headroom': {
                'running': self.headroom.is_running(),
                'version': self.headroom.get_version(),
                'compatible': self.headroom.check_compatibility(),
                'health': self.headroom.health()
            },
            'rtk': {
                'installed': self.rtk.is_installed(),
                'version': self.rtk.get_version(),
                'compatible': self.rtk.check_compatibility()
            }
        }
    
    def update_all(self) -> Dict[str, bool]:
        """Update all components to latest compatible versions."""
        results = {}
        
        # Update Headroom (git submodule)
        import subprocess
        result = subprocess.run(
            ['git', 'submodule', 'update', '--remote', 'headroom'],
            capture_output=True, text=True, cwd='compression'
        )
        results['headroom'] = result.returncode == 0
        
        # Update RTK (git submodule)
        result = subprocess.run(
            ['git', 'submodule', 'update', '--remote', 'rtk'],
            capture_output=True, text=True, cwd='compression'
        )
        results['rtk'] = result.returncode == 0
        
        return results

# Singleton
_manager = None

def get_manager() -> CompressionStackManager:
    """Get compression stack manager."""
    global _manager
    if _manager is None:
        _manager = CompressionStackManager()
    return _manager
```

---

### 4. Installation Script

**Updated install-all.sh with submodule support:**

```bash
#!/usr/bin/env bash
# install-all.sh - Unified Installer with Submodules

# ... (previous installation code) ...

# Clone submodules
clone_submodules() {
    log_header "CLONING SUBMODULES"
    
    cd "$COMPRESSION_DIR"
    
    # Initialize submodules
    if [[ ! -d "headroom/.git" ]]; then
        log_info "Initializing Headroom submodule..."
        git submodule init headroom
        git submodule update --checkout headroom
        log_success "Headroom submodule initialized"
    else
        log_warn "Headroom submodule already exists"
    fi
    
    if [[ ! -d "rtk/.git" ]]; then
        log_info "Initializing RTK submodule..."
        git submodule init rtk
        git submodule update --checkout rtk
        log_success "RTK submodule initialized"
    else
        log_warn "RTK submodule already exists"
    fi
}

# Update submodules (for future updates)
update_submodules() {
    log_info "Updating submodules..."
    cd "$COMPRESSION_DIR"
    git submodule update --remote --merge
    log_success "Submodules updated"
}

# Main installation
main() {
    check_prereqs
    clone_proxy
    clone_submodules      # NEW: Clone submodules
    install_headroom      # Falls back to pip if submodule fails
    install_rtk           # Falls back to cargo/pip if submodule fails
    install_dependencies
    configure_integration
    start_services
    show_health
    show_completion
}

main "$@"
```

---

### 5. Performance Characteristics

**Proxy Hop Overhead:**

| Layer | Latency | Notes |
|-------|---------|-------|
| Claude Code → Proxy | <1ms | Local HTTP |
| Proxy → Headroom | ~50ms | Compression inference |
| Headroom → Upstream | ~100-500ms | Network + LLM |
| **Total Overhead** | **~50-100ms** | Acceptable for 97% savings |

**Optimization Opportunities:**

1. **Connection Pooling:** Reuse HTTP connections between proxy and Headroom
2. **Batching:** Process multiple requests through Headroom together
3. **Caching:** Cache compression results for repeated content
4. **GPU Residency:** Keep models loaded (already implemented)

---

### 6. Update Strategy

**Weekly Auto-Update Workflow:**

```yaml
# .github/workflows/update-compression-deps.yml
name: Update Compression Dependencies

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight
  workflow_dispatch:      # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Update Submodules
        run: |
          git submodule update --remote --merge
      
      - name: Run Compatibility Tests
        run: |
          ./compression/scripts/test-compatibility.sh
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'chore: update Headroom & RTK submodules'
          branch: auto-update-compression-deps
          commit-message: 'chore: update compression submodules'
          body: |
            Automated weekly update of compression dependencies:
            - Headroom: latest from main
            - RTK: latest from main
            
            Compatibility tests: PASSED
```

---

### 7. Rollback Strategy

**If update breaks compatibility:**

```bash
# Quick rollback to known-good versions
cd compression
git submodule update --checkout <known-good-commit>
systemctl --user restart compression-stack
```

**Or via adapter version check:**

```python
# In adapter, check and rollback automatically
if not adapter.check_compatibility():
    print("Incompatible version detected, rolling back...")
    subprocess.run(['git', 'submodule', 'update', '--checkout', '<known-good>'])
```

---

## Conclusion

**This strategy provides:**
- ✅ Tight integration (single management, unified commands)
- ✅ Independent projects retained (git submodules)
- ✅ Easy updates (weekly auto-update workflow)
- ✅ Version compatibility (adapter layers)
- ✅ Rollback capability (git submodule checkout)
- ✅ Acceptable performance (~50ms proxy hop overhead)

**Trade-offs accepted:**
- ⚠️ Proxy hop latency (~50ms)
- ⚠️ Inter-process communication complexity
- ⚠️ Separate version management

**Benefits gained:**
- ✅ Access to latest features immediately
- ✅ Security patches applied weekly
- ✅ Community support maintained
- ✅ Clear separation of concerns
- ✅ Can fork/modify independently if needed

---

*Integration Guide v1.0.0 - April 2, 2026*
