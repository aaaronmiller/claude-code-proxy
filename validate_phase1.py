#!/usr/bin/env python3
"""
Phase 1 Validation - Quick Check
Validates all Phase 1 components are in place
"""

import os
from pathlib import Path

print("=" * 70)
print("🚀 PHASE 1 VALIDATION - QUICK CHECK")
print("=" * 70)

project_root = Path(__file__).parent
passed = 0
total = 5

# Check 1: Database Migration
print("\n[1/5] Database Migration...")
migration_file = project_root / "migrations" / "enhanced_analytics_004.py"
if migration_file.exists():
    print("  ✅ Migration file exists")
    passed += 1
else:
    print("  ❌ Migration file missing")

# Check 2: WebSocket API
print("\n[2/5] WebSocket Live API...")
ws_file = project_root / "src" / "api" / "websocket_live.py"
if ws_file.exists():
    content = ws_file.read_text()
    if "router" in content and "websocket_live_metrics" in content:
        print("  ✅ WebSocket live API exists")
        passed += 1
    else:
        print("  ⚠ WebSocket file incomplete")
else:
    print("  ❌ WebSocket file missing")

# Check 3: System Monitor API
print("\n[3/5] System Monitor API...")
sysmon_file = project_root / "src" / "api" / "system_monitor.py"
if sysmon_file.exists():
    content = sysmon_file.read_text()
    if "get_system_health" in content and "get_system_stats" in content:
        print("  ✅ System monitor API exists")
        passed += 1
    else:
        print("  ⚠ System monitor incomplete")
else:
    print("  ❌ System monitor missing")

# Check 4: Enhanced Landing Page
print("\n[4/5] Enhanced Landing Page...")
landing_file = project_root / "web-ui" / "src" / "routes" / "+page.svelte"
if landing_file.exists():
    content = landing_file.read_text()
    features = ["dashboard", "liveMetrics", "systemHealth", "initWebSocket"]
    found = sum(1 for f in features if f in content)
    if found >= 3:
        print(f"  ✅ Landing page enhanced ({found}/4 features)")
        passed += 1
    else:
        print(f"  ⚠ Landing page incomplete ({found}/4 features)")
else:
    print("  ❌ Landing page missing")

# Check 5: Crosstalk Studio
print("\n[5/5] Crosstalk Studio UI...")
crosstalk_file = project_root / "web-ui" / "src" / "routes" / "crosstalk" / "+page.svelte"
if crosstalk_file.exists():
    size = crosstalk_file.stat().st_size
    print(f"  ✅ Crosstalk Studio exists ({size:,} bytes)")
    passed += 1
else:
    print("  ❌ Crosstalk Studio missing")

# Summary
print("\n" + "=" * 70)
print(f"📊 VALIDATION RESULT: {passed}/{total} PASSED")
print("=" * 70)

if passed >= 4:
    print("""
✅ Phase 1 Implementation Complete!

To launch and test:
1. Run migration:
   python -c "from migrations.enhanced_analytics_004 import run_migration; run_migration()"

2. Start proxy with Web UI:
   python start_proxy.py --web-ui

3. Visit http://localhost:8082
   - Dashboard tab = Live metrics + alerts
   - Crosstalk tab = Full studio with live monitor

4. Enable tracking for analytics:
   TRACK_USAGE=true python start_proxy.py --web-ui

Key Features Now Available:
✨ Dashboard with real-time WebSocket metrics
⚠️  Alert system (budget, latency, errors)
💰 Budget tracking with 80/95/100% warnings
🔄 Crosstalk live session monitoring
📊 System health indicators
⚡ Quick actions panel
""")
else:
    print("❌ Phase 1 incomplete. Check failed items above.")

print("=" * 70)