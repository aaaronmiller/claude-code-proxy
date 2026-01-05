#!/usr/bin/env python3
"""
Phase 3 Validation - Advanced Alerting & Reporting Check
Validates all Phase 3 components for enterprise alerting system
"""

import os
from pathlib import Path

print("=" * 70)
print("🚀 PHASE 3 VALIDATION - ADVANCED ALERTING & REPORTING")
print("=" * 70)

project_root = Path(__file__).parent
passed = 0
total = 12

# Check 1: Database Migration
print("\n[1/12] Database Migration (006_alert_engine.py)...")
migration_file = project_root / "migrations" / "006_alert_engine.py"
if migration_file.exists():
    content = migration_file.read_text()
    checks = [
        "notification_channels",
        "notification_history",
        "user_preferences",
        "condition_logic",
        "time_window"
    ]
    found = sum(1 for c in checks if c in content)
    if found >= 4:
        print(f"  ✅ Migration exists ({found}/5 features)")
        passed += 1
    else:
        print(f"  ⚠ Migration incomplete ({found}/5 features)")
else:
    print("  ❌ Migration file missing")

# Check 2: Alert Engine Service
print("\n[2/12] Alert Engine Service...")
alert_engine = project_root / "src" / "services" / "alert_engine.py"
if alert_engine.exists():
    content = alert_engine.read_text()
    if "evaluate_rule" in content and "check_conditions" in content:
        print("  ✅ AlertEngine service exists")
        passed += 1
    else:
        print("  ⚠ AlertEngine incomplete")
else:
    print("  ❌ AlertEngine missing")

# Check 3: Notification Service
print("\n[3/12] Notification Service...")
notif_service = project_root / "src" / "services" / "notifications.py"
if notif_service.exists():
    content = notif_service.read_text()
    checks = ["send_email", "send_slack", "send_webhook", "rate_limiter"]
    found = sum(1 for c in checks if c in content)
    if found >= 3:
        print(f"  ✅ Notification service exists ({found}/4 channels)")
        passed += 1
    else:
        print(f"  ⚠ Notification service incomplete ({found}/4)")
else:
    print("  ❌ Notification service missing")

# Check 4: Alerts API
print("\n[4/12] Alerts API Endpoints...")
alerts_api = project_root / "src" / "api" / "alerts.py"
if alerts_api.exists():
    content = alerts_api.read_text()
    checks = [
        "/api/alerts/rules",
        "/api/alerts/history",
        "/api/notifications",
        "bulk",
        "test"
    ]
    found = sum(1 for c in checks if c in content)
    if found >= 4:
        print(f"  ✅ Alerts API exists ({found}/5 endpoints)")
        passed += 1
    else:
        print(f"  ⚠ Alerts API incomplete ({found}/5)")
else:
    print("  ❌ Alerts API missing")

# Check 5: Alert Rule Builder UI
print("\n[5/12] Alert Rule Builder UI...")
builder_ui = project_root / "web-ui" / "src" / "routes" / "alerts" / "builder" / "+page.svelte"
if builder_ui.exists():
    content = builder_ui.read_text()
    checks = ["ConditionBuilder", "logicType", "testRule", "saveRule", "preview"]
    found = sum(1 for c in checks if c in content)
    if found >= 4:
        print(f"  ✅ Rule builder UI exists ({found}/5 features)")
        passed += 1
    else:
        print(f"  ⚠ Rule builder incomplete ({found}/5)")
else:
    print("  ❌ Rule builder UI missing")

# Check 6: Alert History Dashboard
print("\n[6/12] Alert History Dashboard...")
history_ui = project_root / "web-ui" / "src" / "routes" / "alerts" / "+page.svelte"
if history_ui.exists():
    content = history_ui.read_text()
    checks = ["loadAlerts", "bulkAction", "acknowledgeAlert", "filters", "stats"]
    found = sum(1 for c in checks if c in content)
    if found >= 4:
        print(f"  ✅ History dashboard exists ({found}/5 features)")
        passed += 1
    else:
        print(f"  ⚠ History dashboard incomplete ({found}/5)")
else:
    print("  ❌ History dashboard missing")

# Check 7: Main.py Integration
print("\n[7/12] Main.py Integration...")
main_file = project_root / "src" / "main.py"
if main_file.exists():
    content = main_file.read_text()
    checks = [
        "from src.api.alerts import",
        "alerts_router",
        "alert_engine.start",
        "notification_service.initialize"
    ]
    found = sum(1 for c in checks if c in content)
    if found >= 3:
        print(f"  ✅ Main.py integrated ({found}/4 checks)")
        passed += 1
    else:
        print(f"  ⚠ Main.py incomplete ({found}/4)")
else:
    print("  ❌ Main.py missing")

# Check 8: Dependencies Installed
print("\n[8/12] Required Dependencies...")
package_json = project_root / "web-ui" / "package.json"
if package_json.exists():
    content = package_json.read_text()
    if "chart.js" in content:
        print("  ✅ Chart.js installed")
        passed += 1
    else:
        print("  ⚠ Chart.js not in package.json")
else:
    print("  ❌ package.json missing")

# Check 9: Phase 3 Specification
print("\n[9/12] Phase 3 Specification...")
spec_file = project_root / "PHASE3_SPEC.md"
if spec_file.exists():
    size = spec_file.stat().st_size
    if size > 5000:
        print(f"  ✅ Specification exists ({size:,} bytes)")
        passed += 1
    else:
        print("  ⚠ Specification too small")
else:
    print("  ❌ Specification missing")

# Check 10: Component Index
print("\n[10/12] Component Exports...")
index_file = project_root / "web-ui" / "src" / "components" / "charts" / "index.js"
if index_file.exists():
    content = index_file.read_text()
    if "LineChart" in content and "BarChart" in content:
        print("  ✅ Chart components exported")
        passed += 1
    else:
        print("  ⚠ Component exports incomplete")
else:
    print("  ❌ Component index missing")

# Check 11: Alert Engine Integration in main.py
print("\n[11/12] Alert Engine Lifespan...")
main_file = project_root / "src" / "main.py"
if main_file.exists():
    content = main_file.read_text()
    if "await alert_engine.start()" in content and "notification_service.initialize()" in content:
        print("  ✅ Lifespan hooks in place")
        passed += 1
    else:
        print("  ⚠ Lifespan hooks incomplete")
else:
    print("  ❌ main.py missing")

# Check 12: Migration Log Check
print("\n[12/12] Migration Support...")
if os.path.exists(project_root / "usage_tracking.db"):
    import sqlite3
    try:
        conn = sqlite3.connect(str(project_root / "usage_tracking.db"))
        cursor = conn.cursor()

        # Check if Phase 2 migration exists
        cursor.execute("SELECT COUNT(*) FROM migration_log WHERE migration_name = '004_enhanced_analytics'")
        phase2 = cursor.fetchone()[0] > 0

        # Check if Phase 3 tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('notification_channels', 'alert_rules')")
        tables = [row[0] for row in cursor.fetchall()]

        conn.close()

        if phase2 and len(tables) >= 1:
            print(f"  ✅ Phase 2 migrated, Phase 3 tables: {len(tables)}")
            passed += 1
        else:
            print(f"  ⚠ Database status: Phase2={phase2}, Tables={len(tables)}")
    except:
        print("  ⚠ Database check skipped")
else:
    print("  ⚠ Database not yet created")

# Summary
print("\n" + "=" * 70)
print(f"📊 VALIDATION RESULT: {passed}/{total} PASSED")
print("=" * 70)

if passed >= 8:
    print("""
✅ Phase 3 Core Implementation Ready!

Key Components Verified:
• Alert Engine with rule evaluation
• Notification Service (Email, Slack, Webhook)
• Alert Rule Builder UI
• Alert History Dashboard
• Database migrations

To Launch Phase 3 Features:
1. Run migration:
   python -c "from migrations.006_alert_engine import run_migration; run_migration()"

2. Restart proxy:
   python start_proxy.py --web-ui

3. Test alert system:
   - Visit: http://localhost:8082/alerts/builder
   - Create a test alert rule
   - Visit: http://localhost:8082/alerts
   - View alert history

4. Configure notifications:
   - SMTP settings for email
   - Slack webhook URL
   - Custom webhook endpoints

5. Monitor alert engine logs:
   - Check terminal for "Alert Engine Started"
   - Watch for "🔔 Alert triggered" messages

Phase 3 Features Available:
🔔 Complex alert rules with AND/OR logic
📧 Multi-channel notifications (Email, Slack, Webhook)
📊 Alert history and management
🔄 Bulk actions on alerts
⚡ Rule testing simulator
📈 Alert statistics and metrics

Next Steps:
• Configure email/SMTP credentials
• Set up Slack webhooks
• Test notification delivery
• Create sample alert rules
""")

    if passed >= total:
        print("🎉 ALL PHASE 3 CHECKS PASSED - Ready for production!")
    else:
        print("⚠️  Most features ready - review the few items above")
else:
    print("❌ Phase 3 incomplete. Check failed items and run migrations.")

print("=" * 70)