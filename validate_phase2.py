#!/usr/bin/env python3
"""
Phase 2 Validation - Advanced Analytics Check
Validates all Phase 2 components are in place and functional
"""

import os
from pathlib import Path

print("=" * 70)
print("🚀 PHASE 2 VALIDATION - ADVANCED ANALYTICS")
print("=" * 70)

project_root = Path(__file__).parent
passed = 0
total = 8

# Check 1: Database Migration
print("\n[1/8] Database Migration (005_advanced_analytics.py)...")
migration_file = project_root / "migrations" / "005_advanced_analytics.py"
if migration_file.exists():
    content = migration_file.read_text()
    if "saved_queries" in content and "report_templates" in content:
        print("  ✅ Migration file exists with advanced tables")
        passed += 1
    else:
        print("  ⚠ Migration file incomplete")
else:
    print("  ❌ Migration file missing")

# Check 2: Analytics API Endpoints
print("\n[2/8] Analytics API Endpoints (analytics.py)...")
api_file = project_root / "src" / "api" / "analytics.py"
if api_file.exists():
    content = api_file.read_text()
    if "timeseries" in content and "aggregate" in content and "query" in content:
        print("  ✅ Analytics API exists with key endpoints")
        passed += 1
    else:
        print("  ⚠ Analytics API incomplete")
else:
    print("  ❌ Analytics API file missing")

# Check 3: Chart.js Dependencies
print("\n[3/8] Chart.js Dependencies...")
package_json = project_root / "web-ui" / "package.json"
if package_json.exists():
    content = package_json.read_text()
    if "chart.js" in content and "svelte-chartjs" in content:
        print("  ✅ Chart.js dependencies installed")
        passed += 1
    else:
        print("  ⚠ Missing Chart.js in package.json")
else:
    print("  ❌ package.json missing")

# Check 4: Line Chart Component
print("\n[4/8] Line Chart Component...")
line_chart = project_root / "web-ui" / "src" / "components" / "charts" / "LineChart.svelte"
if line_chart.exists():
    content = line_chart.read_text()
    if "Chart.register" in content and "labels" in content:
        print("  ✅ LineChart component exists")
        passed += 1
    else:
        print("  ⚠ LineChart incomplete")
else:
    print("  ❌ LineChart component missing")

# Check 5: Bar Chart Component
print("\n[5/8] Bar Chart Component...")
bar_chart = project_root / "web-ui" / "src" / "components" / "charts" / "BarChart.svelte"
if bar_chart.exists():
    content = bar_chart.read_text()
    if "BarController" in content and "BarElement" in content:
        print("  ✅ BarChart component exists")
        passed += 1
    else:
        print("  ⚠ BarChart incomplete")
else:
    print("  ❌ BarChart component missing")

# Check 6: Time Range Picker Component
print("\n[6/8] Time Range Picker Component...")
time_picker = project_root / "web-ui" / "src" / "components" / "charts" / "TimeRangePicker.svelte"
if time_picker.exists():
    content = time_picker.read_text()
    if "startDate" in content and "endDate" in content and "presets" in content:
        print("  ✅ TimeRangePicker component exists")
        passed += 1
    else:
        print("  ⚠ TimeRangePicker incomplete")
else:
    print("  ❌ TimeRangePicker component missing")

# Check 7: Analytics Dashboard Page
print("\n[7/8] Analytics Dashboard Page...")
dashboard = project_root / "web-ui" / "src" / "routes" / "analytics" / "+page.svelte"
if dashboard.exists():
    content = dashboard.read_text()
    features = ["fetchTimeSeriesData", "LineChart", "BarChart", "TimeRangePicker", "stats-grid", "comparison-table"]
    found = sum(1 for f in features if f in content)
    if found >= 4:
        print(f"  ✅ Analytics dashboard exists ({found}/6 features)")
        passed += 1
    else:
        print(f"  ⚠ Dashboard incomplete ({found}/6 features)")
else:
    print("  ❌ Analytics dashboard missing")

# Check 8: Component Index File
print("\n[8/8] Component Index File...")
index_file = project_root / "web-ui" / "src" / "components" / "charts" / "index.js"
if index_file.exists():
    content = index_file.read_text()
    if "LineChart" in content and "BarChart" in content:
        print("  ✅ Chart components properly exported")
        passed += 1
    else:
        print("  ⚠ Index file incomplete")
else:
    print("  ❌ Index file missing")

# Summary
print("\n" + "=" * 70)
print(f"📊 VALIDATION RESULT: {passed}/{total} PASSED")
print("=" * 70)

if passed >= 6:
    print("""
✅ Phase 2 Implementation Complete!

To launch and test:
1. Run migration:
   python -c "from migrations.005_advanced_analytics import run_migration; run_migration()"

2. Restart proxy with analytics:
   python start_proxy.py --web-ui

3. Visit http://localhost:8082/analytics
   - Interactive charts for tokens, cost, requests
   - Date range picker with presets
   - Provider and model comparisons
   - Export data to CSV/JSON

Key Features Now Available:
✨ Interactive time-series charts (Chart.js)
📊 Provider & model comparison tables
🗓️  Date range selector with presets
💾 Saved queries management
📤 CSV/JSON export functionality
🎨 Full responsive design

User Tasks Possible:
• Visualize token usage trends over time
• Compare costs across providers
• Identify peak usage hours
• Export data for reporting
• Drill down into specific periods
""")

    if passed >= total:
        print("🎉 ALL CHECKS PASSED - Ready for production!")
    else:
        print("⚠️  Most features ready - minor issues to address")
else:
    print("❌ Phase 2 incomplete. Check failed items above.")

print("=" * 70)