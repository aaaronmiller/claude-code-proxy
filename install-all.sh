#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE CODE PROXY - UNIFIED INSTALLER (v2.0)
# ═══════════════════════════════════════════════════════════════════════════════
# Installs Claude Code Proxy with full compression stack integration
# Includes: claude-code-proxy, Headroom, RTK, and all compression tools
# Features: Auto-detects NVIDIA, Intel Arc, or CPU and configures accordingly
#
# Usage: curl -fsSL https://raw.githubusercontent.com/aaaronmiller/claude-code-proxy/main/install-all.sh | bash
# Or:    ./install-all.sh
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Configuration
PROXY_DIR="${HOME}/code/claude-code-proxy"
COMPRESSION_DIR="${PROXY_DIR}/compression"
HEADROOM_PORT="${HEADROOM_PORT:-8787}"
PROXY_PORT="${PROXY_PORT:-8082}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}✗${NC} $1"; }
log_header()  { echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}\n"; }

# ─── GPU Detection ────────────────────────────────────────────────────────────
# Detects all available GPUs and returns a structured list

GPU_MODE="cpu"  # default fallback
GPU_DEVICES=()
GPU_NAMES=()

detect_gpus() {
    log_header "DETECTING GPU HARDWARE"

    local has_nvidia=false has_intel=false has_amd=false
    local nvidia_name="" intel_names=() intel_vrams=()

    # ── NVIDIA detection ──
    if command -v nvidia-smi &>/dev/null; then
        nvidia_name=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)
        if [[ -n "$nvidia_name" ]]; then
            has_nvidia=true
            local nvidia_vram
            nvidia_vram=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1 || echo "?")
            GPU_DEVICES+=("nvidia")
            GPU_NAMES+=("NVIDIA ${nvidia_name} (${nvidia_vram} VRAM)")
            log_success "NVIDIA GPU: ${nvidia_name} (${nvidia_vram} VRAM)"
        fi
    fi

    # ── Intel detection (via clinfo or lspci) ──
    if command -v clinfo &>/dev/null; then
        while IFS= read -r line; do
            local dev_name
            dev_name=$(echo "$line" | sed 's/.*Device Name.*//; s/^[[:space:]]*//')
            if [[ -n "$dev_name" ]]; then
                has_intel=true
                intel_names+=("$dev_name")
            fi
        done < <(clinfo 2>/dev/null | grep "Device Name" | grep -i intel || true)

        # Get VRAM for each Intel device
        if [[ ${#intel_names[@]} -gt 0 ]]; then
            local vrams=()
            while IFS= read -r line; do
                vrams+=("$(echo "$line" | sed 's/.*Global memory size.*//; s/^[[:space:]]*//')")
            done < <(clinfo 2>/dev/null | grep "Global memory size" | head -${#intel_names[@]} || true)

            for i in "${!intel_names[@]}"; do
                local vram="${vrams[$i]:-unknown}"
                GPU_DEVICES+=("intel")
                GPU_NAMES+=("Intel ${intel_names[$i]} (${vram})")
                log_info "Intel GPU #${i}: ${intel_names[$i]} (${vram})"
            done
        fi
    elif command -v lspci &>/dev/null; then
        while IFS= read -r line; do
            has_intel=true
            GPU_DEVICES+=("intel")
            GPU_NAMES+=("Intel $(echo "$line" | sed 's/.*VGA.*//')")
        done < <(lspci 2>/dev/null | grep -i "intel.*vga\|intel.*display\|intel.*graphics" || true)
    fi

    # Check for /dev/dxg (WSL2 GPU passthrough)
    if [[ -e /dev/dxg ]]; then
        log_success "WSL2 GPU passthrough active (/dev/dxg present)"
    fi

    # ── AMD detection ──
    if command -v rocminfo &>/dev/null || command -v clinfo &>/dev/null; then
        local amd_count
        amd_count=$(clinfo 2>/dev/null | grep "Device Name" | grep -ci amd || echo 0)
        if [[ "$amd_count" -gt 0 ]]; then
            has_amd=true
            GPU_DEVICES+=("amd")
            GPU_NAMES+=("AMD GPU (via ROCm/OpenCL)")
            log_success "AMD GPU detected (${amd_count} device(s))"
        fi
    fi

    # ── Summary ──
    echo ""
    if [[ ${#GPU_DEVICES[@]} -eq 0 ]]; then
        log_warn "No GPU detected — falling back to CPU mode"
        GPU_DEVICES=("cpu")
        GPU_NAMES=("CPU-only (no GPU)")
    else
        log_info "Found ${#GPU_DEVICES[@]} GPU(s):"
        for i in "${!GPU_NAMES[@]}"; do
            echo -e "  ${GREEN}$((i+1)).${NC} ${GPU_NAMES[$i]}"
        done
    fi
}

# ── Interactive GPU Selection ─────────────────────────────────────────────────
prompt_gpu_mode() {
    detect_gpus

    echo ""
    log_header "SELECT GPU ACCELERATION"

    echo "Choose your compute backend:"
    echo ""
    echo -e "  ${GREEN}1)${NC} NVIDIA CUDA    (cuBLAS, TensorRT, best performance)"
    echo -e "  ${GREEN}2)${NC} Intel Arc / iGPU (Level Zero, oneAPI, SYCL)"
    echo -e "  ${GREEN}3)${NC} AMD ROCm       (ROCm, OpenCL)"
    echo -e "  ${GREEN}4)${NC} CPU-only       (no GPU, works everywhere)"
    echo ""

    # Auto-select if only one option makes sense
    local default_choice=""
    if [[ " ${GPU_DEVICES[*]} " =~ "nvidia" ]]; then
        default_choice="1"
        echo -e "  ${CYAN}Auto-detected: NVIDIA GPU — defaulting to option 1${NC}"
    elif [[ " ${GPU_DEVICES[*]} " =~ "intel" ]]; then
        default_choice="2"
        echo -e "  ${CYAN}Auto-detected: Intel GPU — defaulting to option 2${NC}"
    elif [[ " ${GPU_DEVICES[*]} " =~ "amd" ]]; then
        default_choice="3"
        echo -e "  ${CYAN}Auto-detected: AMD GPU — defaulting to option 3${NC}"
    fi

    echo ""
    read -rp "Select option [${default_choice:-4}]: " gpu_choice
    gpu_choice="${gpu_choice:-${default_choice:-4}}"

    case "$gpu_choice" in
        1)
            GPU_MODE="nvidia"
            log_info "Selected: NVIDIA CUDA backend"
            ;;
        2)
            GPU_MODE="intel"
            log_info "Selected: Intel Arc / iGPU backend (Level Zero + oneAPI)"
            ;;
        3)
            GPU_MODE="amd"
            log_info "Selected: AMD ROCm backend"
            ;;
        4)
            GPU_MODE="cpu"
            log_info "Selected: CPU-only mode"
            ;;
        *)
            log_error "Invalid choice — falling back to CPU mode"
            GPU_MODE="cpu"
            ;;
    esac
}

# ─── GPU-Specific Setup ───────────────────────────────────────────────────────
setup_gpu_backend() {
    log_header "CONFIGURING GPU BACKEND: $(echo "$GPU_MODE" | tr '[:lower:]' '[:upper:]')"

    case "$GPU_MODE" in
        nvidia)
            _setup_nvidia
            ;;
        intel)
            _setup_intel
            ;;
        amd)
            _setup_amd
            ;;
        cpu)
            _setup_cpu
            ;;
    esac
}

_setup_nvidia() {
    log_info "Configuring NVIDIA CUDA backend..."

    # Install CUDA runtime if not present
    if ! command -v nvidia-smi &>/dev/null; then
        log_warn "nvidia-smi not found — installing NVIDIA drivers"
        local os="$(uname -s)"
        if [[ "$os" == "Linux" ]]; then
            log_info "Run: sudo apt install nvidia-driver-550 nvidia-cuda-toolkit"
        fi
    else
        log_success "NVIDIA driver active"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | while read -r line; do
            echo -e "  ${GREEN}✓${NC} $line"
        done
    fi

    # Set NVIDIA env vars for Headroom
    echo "" >> ~/.zshrc
    echo '# NVIDIA GPU backend' >> ~/.zshrc
    echo 'export CUDA_VISIBLE_DEVICES=0' >> ~/.zshrc
    echo 'export HEADROOM_DEVICE=cuda' >> ~/.zshrc

    log_success "NVIDIA CUDA backend configured"
}

_setup_intel() {
    log_info "Configuring Intel Arc / iGPU backend (Level Zero + oneAPI)..."

    local distro
    distro=$(lsb_release -cs 2>/dev/null || echo "unknown")
    log_info "Detected Ubuntu: $distro"

    # Check /dev/dxg for WSL2
    if [[ -e /dev/dxg ]]; then
        log_success "WSL2 GPU passthrough active (/dev/dxg)"
    else
        log_warn "/dev/dxg not found — ensure Windows Intel Arc driver is installed"
    fi

    # Step 1: Intel graphics repo
    if [[ ! -f /usr/share/keyrings/intel-graphics.gpg ]]; then
        log_info "Adding Intel graphics repository..."
        wget -qO - https://repositories.intel.com/graphics/intel-graphics.key | \
            sudo gpg --dearmor --output /usr/share/keyrings/intel-graphics.gpg
    fi

    # Step 2: Add repo for distro
    local repo_file="/etc/apt/sources.list.d/intel.gpu.${distro}.list"
    if [[ ! -f "$repo_file" ]]; then
        case "$distro" in
            jammy|noble)
                echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu ${distro} arc" | \
                    sudo tee "$repo_file" > /dev/null
                ;;
            focal)
                echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/graphics/ubuntu focal-devel main" | \
                    sudo tee "$repo_file" > /dev/null
                ;;
            *)
                log_warn "Unsupported distro ($distro) — you may need to add the Intel repo manually"
                ;;
        esac
    fi

    # Step 3: Install runtimes
    log_info "Installing Intel compute stack..."
    sudo apt-get update -qq 2>/dev/null || true
    sudo apt-get install -y -qq \
        intel-opencl-icd \
        intel-level-zero-gpu \
        libze-intel-gpu1 \
        intel-media-va-driver-non-free \
        libmfx1 libmfxgen1 libvpl2 \
        libigc2 libigdgmm12 \
        mesa-vulkan-drivers va-driver-all \
        clinfo 2>/dev/null || true

    # Step 4: Add user to render/video groups
    sudo usermod -a -G render,video "$USER" 2>/dev/null || true

    # Step 5: Detect Arc A370M vs iGPU and set ONEAPI_DEVICE_SELECTOR
    local arc_pci_id=""
    if command -v clinfo &>/dev/null; then
        arc_pci_id=$(clinfo 2>/dev/null | grep -oP '0x569[0-9a-f]' | head -1 || true)
    fi

    local selector_line='export ONEAPI_DEVICE_SELECTOR=level_zero:0'
    local va_line='export LIBVA_DRIVER_NAME=iHD'

    if [[ -n "$arc_pci_id" ]]; then
        log_success "Intel Arc detected (PCI ID: $arc_pci_id)"
        echo -e "  ${CYAN}→ Setting ONEAPI_DEVICE_SELECTOR=level_zero:0 to prefer Arc over iGPU${NC}"
    else
        log_info "No Arc detected — using Level Zero with first available Intel GPU"
    fi

    grep -qxF "$selector_line" ~/.zshrc || echo "$selector_line" >> ~/.zshrc
    grep -qxF "$va_line"    ~/.zshrc || echo "$va_line"    >> ~/.zshrc

    log_success "Intel Level Zero + OpenCL stack installed"
}

_setup_amd() {
    log_info "Configuring AMD ROCm backend..."

    # Install ROCm runtime
    if command -v rocminfo &>/dev/null; then
        log_success "ROCm already installed"
        rocminfo 2>/dev/null | grep -E "^Name:.*gfx" | head -5 | while read -r line; do
            echo -e "  ${GREEN}✓${NC} $line"
        done
    else
        log_warn "ROCm not installed — install from https://rocm.docs.amd.com"
    fi

    echo "" >> ~/.zshrc
    echo '# AMD ROCm backend' >> ~/.zshrc
    echo 'export HSA_OVERRIDE_GFX_VERSION=10.3.0' >> ~/.zshrc
    echo 'export HEADROOM_DEVICE=rocm' >> ~/.zshrc

    log_success "AMD ROCm backend configured"
}

_setup_cpu() {
    log_info "Configuring CPU-only mode..."

    echo "" >> ~/.zshrc
    echo '# CPU-only mode (no GPU)' >> ~/.zshrc
    echo 'export HEADROOM_DEVICE=cpu' >> ~/.zshrc

    log_success "CPU-only mode configured"
}

# ─── Rest of Installer Functions ──────────────────────────────────────────────

check_prereqs() {
    log_header "CHECKING PREREQUISITES"

    local missing=()

    # Python 3.9+
    if command -v python3 &>/dev/null; then
        local pyver
        pyver=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
            log_success "Python 3.9+ detected ($pyver)"
        else
            log_error "Python 3.9+ required (found $pyver)"
            missing+=("python3.9+")
        fi
    else
        missing+=("python3")
    fi

    # Git
    if command -v git &>/dev/null; then
        log_success "Git detected"
    else
        missing+=("git")
    fi

    # pip
    if command -v pip3 &>/dev/null || command -v pip &>/dev/null; then
        log_success "pip detected"
    else
        missing+=("pip")
    fi

    local os
    os="$(uname -s)"
    log_info "Detected OS: $os"

    # Optional
    command -v node &>/dev/null && log_success "Node.js detected (web UI)" || log_warn "Node.js not found"
    command -v cargo &>/dev/null && log_success "Cargo detected (RTK)" || log_warn "Cargo not found — using pip for RTK"
    command -v wget &>/dev/null || missing+=("wget")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing prerequisites: ${missing[*]}"
        if [[ "$os" == "Linux" ]]; then
            log_info "Install with: sudo apt install ${missing[*]}"
        elif [[ "$os" == "Darwin" ]]; then
            log_info "Install with: brew install ${missing[*]}"
        fi
        return 1
    fi

    log_success "All prerequisites met"
}

clone_proxy() {
    log_header "CLONING CLAUDE CODE PROXY"

    if [[ -d "$PROXY_DIR" ]]; then
        log_warn "Claude Code Proxy already exists at $PROXY_DIR"
        read -rp "Update existing installation? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd "$PROXY_DIR" && git pull && log_success "Claude Code Proxy updated"
        fi
    else
        log_info "Cloning claude-code-proxy..."
        git clone https://github.com/aaaronmiller/claude-code-proxy.git "$PROXY_DIR" && \
            log_success "Claude Code Proxy installed" || {
            log_error "Failed to clone claude-code-proxy"
            return 1
        }
    fi
}

install_headroom() {
    log_header "INSTALLING HEADROOM"

    local headroom_dir="${COMPRESSION_DIR}/headroom"
    if [[ ! -d "$headroom_dir" ]]; then
        log_info "Cloning headroom..."
        git clone https://github.com/chopratejas/headroom.git "$headroom_dir" 2>/dev/null && \
            log_success "Headroom cloned" || log_warn "Headroom clone failed — installing via pip"
    fi

    if command -v headroom &>/dev/null; then
        local hv
        hv=$(headroom --version 2>/dev/null || echo "unknown")
        log_warn "Headroom already installed ($hv)"
    else
        log_info "Installing headroom-ai[ml]..."
        pip install --user "headroom-ai[ml]" && log_success "Headroom installed" || {
            log_error "Headroom installation failed"
            return 1
        }
    fi
}

install_rtk() {
    log_header "INSTALLING RTK"

    local rtk_dir="${COMPRESSION_DIR}/rtk"
    if [[ ! -d "$rtk_dir" ]]; then
        log_info "Cloning rtk..."
        git clone https://github.com/rtk-ai/rtk.git "$rtk_dir" 2>/dev/null && \
            log_success "RTK cloned" || log_warn "RTK clone failed — installing via package manager"
    fi

    if command -v rtk &>/dev/null; then
        local rv
        rv=$(rtk --version 2>/dev/null || echo "unknown")
        log_warn "RTK already installed ($rv)"
    elif command -v cargo &>/dev/null; then
        log_info "Installing RTK via cargo..."
        cargo install rtk 2>/dev/null && log_success "RTK installed" || {
            log_warn "Cargo install failed — trying pip"
            pip install --user rtk 2>/dev/null && log_success "RTK installed" || log_warn "RTK not available — skipping"
        }
    else
        log_info "Installing RTK via pip..."
        pip install --user rtk 2>/dev/null && log_success "RTK installed" || log_warn "RTK installation failed"
    fi
}

install_dependencies() {
    log_header "INSTALLING DEPENDENCIES"

    cd "$PROXY_DIR"

    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv .venv && log_success "Virtual environment created"
    else
        log_warn "Virtual environment already exists"
    fi

    source .venv/bin/activate
    log_info "Installing Python dependencies..."

    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt && log_success "Dependencies installed" || {
            log_error "Dependency installation failed"
            return 1
        }
    else
        log_warn "requirements.txt not found"
    fi
}

configure_integration() {
    log_header "CONFIGURING INTEGRATION"

    local envrc="${PROXY_DIR}/.envrc"
    if [[ -f "$envrc" ]]; then
        if ! grep -q "HEADROOM_PORT" "$envrc" 2>/dev/null; then
            log_info "Configuring compression integration..."
            cat >> "$envrc" << EOF

# Compression stack integration
export PROVIDER_BASE_URL="http://127.0.0.1:${HEADROOM_PORT}/v1"
export HEADROOM_PORT="${HEADROOM_PORT}"
# Headroom configuration (all settings in one place)
export HEADROOM_BACKEND="${HEADROOM_BACKEND:-openrouter}"
export HEADROOM_API_URL="${HEADROOM_API_URL:-https://openrouter.ai/api/v1}"
export HEADROOM_MODE="${HEADROOM_MODE:-token_headroom}"
EOF
            log_success "Environment configured"
        else
            log_warn "Environment already configured"
        fi
    fi

    # Add aliases with GPU info
    local alias_section="# ═══════════════════════════════════════════════════════════════════
# COMPRESSION STACK — Headroom + RTK + ${GPU_MODE^^} GPU
# ═══════════════════════════════════════════════════════════════════

# Daily use — point tools at Headroom compression proxy (:8787)
alias cc='ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude' # Claude Code via Headroom compression
alias qw='OPENAI_BASE_URL=http://127.0.0.1:8787/v1 qwen' # Qwen Code via Headroom compression
alias qw-resume='OPENAI_BASE_URL=http://127.0.0.1:8787/v1 qwen --continue' # Qwen resume session via Headroom
"

    if [[ -n "$GPU_MODE" ]]; then
        alias_section+="
# GPU backend: ${GPU_MODE}
"
    fi

    if ! grep -q "COMPRESSION STACK" ~/.zshrc 2>/dev/null; then
        echo "" >> ~/.zshrc
        echo "$alias_section" >> ~/.zshrc
        log_success "Compression aliases added to ~/.zshrc"
    else
        log_warn "Compression aliases already in ~/.zshrc"
    fi

    # Configure proxy_chain.json with correct Headroom args
    local chain_file="${PROXY_DIR}/config/proxy_chain.json"
    if [[ -f "$chain_file" ]]; then
        local headroom_backend="${HEADROOM_BACKEND:-openrouter}"
        local headroom_api_url="${HEADROOM_API_URL:-https://openrouter.ai/api/v1}"
        _python -c "
import json
data = json.load(open('$chain_file'))
for e in data.get('entries', []):
    if e.get('id') == 'headroom':
        e['service_cmd'] = (
            'headroom proxy --port $HEADROOM_PORT --mode token_headroom'
            ' --openai-api-url $headroom_api_url'
            ' --backend $headroom_backend --no-telemetry'
        )
json.dump(data, open('$chain_file', 'w'), indent=2)
print('Updated proxy_chain.json')
" 2>/dev/null && log_success "proxy_chain.json configured" || log_warn "proxy_chain.json update failed"
    fi

    # Set up RTK instructions in CLAUDE.md if not already present
    if command -v rtk &>/dev/null; then
        if [[ -f "${PROXY_DIR}/CLAUDE.md" ]]; then
            if ! grep -q "RTK" "${PROXY_DIR}/CLAUDE.md" 2>/dev/null; then
                rtk init 2>/dev/null && log_success "RTK instructions added to CLAUDE.md" || log_warn "RTK init failed"
            else
                log_warn "RTK already configured in CLAUDE.md"
            fi
        fi
    fi

    # Install systemd services
    if command -v systemctl &>/dev/null; then
        log_info "Installing systemd services..."
        local services_dir="$HOME/.config/systemd/user"
        mkdir -p "$services_dir"

        if [[ -d "${COMPRESSION_DIR}/systemd" ]]; then
            for service in "${COMPRESSION_DIR}/systemd/"*.service; do
                [[ -f "$service" ]] && cp "$service" "$services_dir/" && \
                    log_success "Installed $(basename "$service")"
            done
            systemctl --user daemon-reload 2>/dev/null && log_success "Systemd reloaded" || true
        fi
    else
        log_warn "systemctl not available — skipping systemd"
    fi
}

start_services() {
    log_header "STARTING SERVICES"

    # Set GPU env vars
    case "$GPU_MODE" in
        intel)
            export ONEAPI_DEVICE_SELECTOR=level_zero:0
            export LIBVA_DRIVER_NAME=iHD
            ;;
        nvidia)
            export CUDA_VISIBLE_DEVICES=0
            ;;
    esac

    if command -v headroom &>/dev/null; then
        if ! pgrep -f "headroom proxy" &>/dev/null; then
            log_info "Starting headroom proxy on :$HEADROOM_PORT..."
            local headroom_backend="${HEADROOM_BACKEND:-openrouter}"
            local headroom_api_url="${HEADROOM_API_URL:-https://openrouter.ai/api/v1}"
            headroom proxy \
                --port "$HEADROOM_PORT" \
                --mode token_headroom \
                --openai-api-url "$headroom_api_url" \
                --backend "$headroom_backend" \
                --no-telemetry &
            sleep 3

            if pgrep -f "headroom proxy" &>/dev/null; then
                log_success "Headroom started on :$HEADROOM_PORT"
            else
                log_error "Failed to start headroom"
                return 1
            fi
        else
            log_warn "Headroom already running"
        fi
    fi

    cd "$PROXY_DIR"
    if ! pgrep -f "start_proxy.py" &>/dev/null; then
        log_info "Starting claude-code-proxy on :$PROXY_PORT..."

        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
        fi

        export OPENAI_BASE_URL="http://127.0.0.1:$HEADROOM_PORT/v1"
        export PROVIDER_BASE_URL="http://127.0.0.1:$HEADROOM_PORT/v1"

        nohup python -u start_proxy.py --skip-validation > proxy.log 2>&1 &
        sleep 3

        if pgrep -f "start_proxy.py" &>/dev/null; then
            log_success "Claude Code Proxy started on :$PROXY_PORT"
        else
            log_error "Failed to start claude-code-proxy"
            return 1
        fi
    else
        log_warn "Claude Code Proxy already running"
    fi
}

show_health() {
    log_header "HEALTH CHECK"

    local healthy=true

    # Headroom
    echo -n "Headroom (:$HEADROOM_PORT): "
    if curl -s "http://127.0.0.1:$HEADROOM_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi

    # Proxy
    echo -n "Claude Code Proxy (:$PROXY_PORT): "
    if curl -s "http://127.0.0.1:$PROXY_PORT/health" 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        healthy=false
    fi

    # GPU status
    echo -n "GPU (${GPU_MODE^^}): "
    case "$GPU_MODE" in
        nvidia)
            if command -v nvidia-smi &>/dev/null; then
                local vram
                vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader 2>/dev/null | head -1)
                if [[ -n "$vram" ]]; then
                    echo -e "${GREEN}✓ Active ($vram)${NC}"
                else
                    echo -e "${YELLOW}○ Idle${NC}"
                fi
            else
                echo -e "${RED}✗ nvidia-smi not found${NC}"
            fi
            ;;
        intel)
            if command -v clinfo &>/dev/null; then
                local dev
                dev=$(clinfo 2>/dev/null | grep "Device Name" | grep -i intel | head -1 | sed 's/.*Device Name//; s/^[[:space:]]*//')
                if [[ -n "$dev" ]]; then
                    echo -e "${GREEN}✓ $dev${NC}"
                else
                    echo -e "${YELLOW}○ No Intel devices found${NC}"
                fi
            else
                echo -e "${YELLOW}○ clinfo not installed${NC}"
            fi
            ;;
        amd)
            if command -v rocminfo &>/dev/null; then
                echo -e "${GREEN}✓ ROCm active${NC}"
            else
                echo -e "${YELLOW}○ ROCm not installed${NC}"
            fi
            ;;
        cpu)
            echo -e "${YELLOW}○ CPU-only (no GPU)${NC}"
            ;;
    esac

    echo ""
    if $healthy; then
        log_success "All systems healthy"
    else
        log_error "Some systems unhealthy"
        return 1
    fi
}

show_completion() {
    log_header "INSTALLATION COMPLETE"

    local gpu_label
    case "$GPU_MODE" in
        nvidia) gpu_label="NVIDIA CUDA" ;;
        intel)  gpu_label="Intel Arc / iGPU (Level Zero)" ;;
        amd)    gpu_label="AMD ROCm" ;;
        cpu)    gpu_label="CPU-only" ;;
    esac

    cat << EOF
╔══════════════════════════════════════════════════════════════════════╗
║                    INSTALLATION SUCCESSFUL                           ║
╠══════════════════════════════════════════════════════════════════════╣
║  GPU Backend: ${gpu_label}
╚══════════════════════════════════════════════════════════════════════╝

Quick Start:
  source ~/.zshrc
  cc             # Claude Code via Headroom compression
  qw             # Qwen Code via Headroom compression
  qw-resume      # Resume Qwen session via Headroom

Services:
  Headroom:  http://127.0.0.1:${HEADROOM_PORT}/health
  Proxy:     http://127.0.0.1:${PROXY_PORT}/health
  Dashboard: python3 ~/code/claude-code-proxy/compress-monitor-web.py

Modes (save with headroom proxy --mode):
  token_headroom  — Compress context to extend session length
  cost_savings    — Preserve prefix cache for lower costs

GPU-Specific:
EOF

    case "$GPU_MODE" in
        intel)
            cat << 'INTEL_EOF'
  ONEAPI_DEVICE_SELECTOR=level_zero:0  # Arc A370M (0x5693) preferred
  LIBVA_DRIVER_NAME=iHD                 # Intel media driver
  Verify: clinfo | grep "Device Name"
INTEL_EOF
            ;;
        nvidia)
            cat << 'NVIDIA_EOF'
  CUDA_VISIBLE_DEVICES=0  # First NVIDIA GPU
  Verify: nvidia-smi
NVIDIA_EOF
            ;;
        amd)
            cat << 'AMD_EOF'
  HSA_OVERRIDE_GFX_VERSION=10.3.0  # ROCm compatibility
  Verify: rocminfo
AMD_EOF
            ;;
        cpu)
            cat << 'CPU_EOF'
  No GPU acceleration — using CPU for all compute
  For better performance, install a GPU backend
CPU_EOF
            ;;
    esac

    echo ""
    echo "══════════════════════════════════════════════════════════════════════"
}

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║         CLAUDE CODE PROXY - UNIFIED INSTALLER v2.0                   ║"
    echo "║         Compression Stack + Headroom + RTK + GPU Auto-Detect         ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""

    prompt_gpu_mode
    check_prereqs || exit 1
    clone_proxy
    install_headroom
    install_rtk
    install_dependencies
    setup_gpu_backend
    configure_integration
    start_services
    show_health
    show_completion
}

main "$@"
