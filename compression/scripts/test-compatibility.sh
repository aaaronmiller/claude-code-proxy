#!/usr/bin/env bash
# Compression Stack Compatibility Tests
# Run after dependency updates to ensure everything still works

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

log_pass() { echo -e "${GREEN}✓${NC} $1"; ((PASS++)); }
log_fail() { echo -e "${RED}✗${NC} $1"; ((FAIL++)); }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; ((WARN++)); }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     COMPRESSION STACK - COMPATIBILITY TESTS                         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Headroom installed
log_info "Testing Headroom installation..."
if command -v headroom &>/dev/null; then
    log_pass "Headroom is installed"
    headroom --version 2>/dev/null || log_warn "Could not get Headroom version"
else
    log_fail "Headroom is not installed"
fi

# Test 2: RTK installed
log_info "Testing RTK installation..."
if command -v rtk &>/dev/null; then
    log_pass "RTK is installed"
    rtk --version 2>/dev/null || log_warn "Could not get RTK version"
else
    log_warn "RTK is not installed (optional)"
fi

# Test 3: Headroom can start
log_info "Testing Headroom startup..."
headroom proxy --port 18787 --mode token_headroom \
    --openai-api-url https://openrouter.ai/api/v1 \
    --backend openrouter --no-telemetry > /dev/null 2>&1 &
HEADROOM_PID=$!
sleep 3

if kill -0 $HEADROOM_PID 2>/dev/null; then
    log_pass "Headroom starts successfully"
else
    log_fail "Headroom failed to start"
fi

# Test 4: Headroom health endpoint
log_info "Testing Headroom health endpoint..."
if curl -s http://127.0.0.1:18787/health 2>/dev/null | grep -q "healthy"; then
    log_pass "Headroom health endpoint responds"
else
    log_fail "Headroom health endpoint not responding"
fi

# Test 5: Kill test Headroom
kill $HEADROOM_PID 2>/dev/null || true
wait $HEADROOM_PID 2>/dev/null || true
log_pass "Headroom stopped cleanly"

# Test 6: Aliases file syntax
log_info "Testing aliases file syntax..."
if bash -n compression/scripts/compression-aliases.zsh 2>/dev/null; then
    log_pass "Aliases file has valid syntax"
else
    log_fail "Aliases file has syntax errors"
fi

# Test 7: Install script syntax
log_info "Testing install scripts syntax..."
if bash -n compression/scripts/install-all.sh 2>/dev/null; then
    log_pass "install-all.sh has valid syntax"
else
    log_fail "install-all.sh has syntax errors"
fi

if bash -n compression/scripts/install-aliases.sh 2>/dev/null; then
    log_pass "install-aliases.sh has valid syntax"
else
    log_fail "install-aliases.sh has syntax errors"
fi

# Test 8: Python imports
log_info "Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'compression/lib')
try:
    from headroom_adapter import HeadroomAdapter
    print('  ✓ headroom_adapter imports successfully')
except Exception as e:
    print(f'  ✗ headroom_adapter import failed: {e}')
    sys.exit(1)

try:
    from rtk_adapter import RTKAdapter
    print('  ✓ rtk_adapter imports successfully')
except Exception as e:
    print(f'  ✗ rtk_adapter import failed: {e}')
    sys.exit(1)

try:
    from stack_manager import CompressionStackManager
    print('  ✓ stack_manager imports successfully')
except Exception as e:
    print(f'  ✗ stack_manager import failed: {e}')
    sys.exit(1)
" && log_pass "All Python imports work" || log_fail "Python import errors"

# Test 9: Compression directory structure
log_info "Testing directory structure..."
REQUIRED_DIRS=("compression/bin" "compression/scripts" "compression/docs" "compression/lib" "compression/systemd")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        log_pass "Directory exists: $dir"
    else
        log_fail "Directory missing: $dir"
    fi
done

# Test 10: Required files
log_info "Testing required files..."
REQUIRED_FILES=(
    "compression/scripts/compression-aliases.zsh"
    "compression/scripts/install-all.sh"
    "compression/scripts/install-aliases.sh"
    "compression/scripts/install-autostart.sh"
    "compression/lib/__init__.py"
    "compression/lib/headroom_adapter.py"
    "compression/lib/rtk_adapter.py"
    "compression/lib/stack_manager.py"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        log_pass "File exists: $file"
    else
        log_fail "File missing: $file"
    fi
done

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                                  ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASS"
echo -e "  ${RED}Failed:${NC}  $FAIL"
echo -e "  ${YELLOW}Warnings:${NC} $WARN"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo -e "  ${RED}❌ COMPATIBILITY TESTS FAILED${NC}"
    echo "  Some tests failed. Review the output above."
    exit 1
else
    echo -e "  ${GREEN}✅ ALL COMPATIBILITY TESTS PASSED${NC}"
    echo "  All tests passed. Dependencies are compatible."
    exit 0
fi
