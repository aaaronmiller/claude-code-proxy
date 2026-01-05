"""
Migration 005: Advanced Analytics & Reporting
Creates tables for saved queries, alert rule versions, and extended alert history

Author: AI Architect
Date: 2026-01-05
Version: 1.0
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = "usage_tracking.db"
MIGRATION_NAME = "005_advanced_analytics"


def create_saved_queries_table(conn):
    """Create table for saved user queries"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_queries (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            query_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT,
            updated_at TEXT,
            is_public INTEGER DEFAULT 0,
            tags TEXT
        )
    """)
    conn.commit()


def create_alert_rule_versions_table(conn):
    """Create table for tracking alert rule changes"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_rule_versions (
            id TEXT PRIMARY KEY,
            rule_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            changes_json TEXT NOT NULL,
            modified_at TEXT NOT NULL,
            modified_by TEXT,
            reason TEXT,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE
        )
    """)
    conn.commit()


def create_report_templates_table(conn):
    """Create table for custom report templates"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            template_config TEXT NOT NULL,  -- JSON: charts, tables, layout
            created_at TEXT NOT NULL,
            created_by TEXT,
            is_default INTEGER DEFAULT 0
        )
    """)
    conn.commit()


def create_scheduled_reports_table(conn):
    """Create table for scheduled report deliveries"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_reports (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            frequency TEXT NOT NULL,  -- daily, weekly, monthly
            recipients TEXT NOT NULL,  -- JSON array of emails
            last_run TEXT,
            next_run TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            created_by TEXT,
            FOREIGN KEY (template_id) REFERENCES report_templates(id)
        )
    """)
    conn.commit()


def create_report_executions_table(conn):
    """Create table for report execution history"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_executions (
            id TEXT PRIMARY KEY,
            scheduled_report_id TEXT,
            template_id TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            status TEXT NOT NULL,  -- success, failed, pending
            error_message TEXT,
            file_path TEXT,
            file_size INTEGER,
            recipients TEXT,  -- JSON array of emails sent to
            FOREIGN KEY (scheduled_report_id) REFERENCES scheduled_reports(id),
            FOREIGN KEY (template_id) REFERENCES report_templates(id)
        )
    """)
    conn.commit()


def extend_alert_history_table(conn):
    """Extend alert_history table with new columns"""
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(alert_history)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    # Add acknowledged column
    if 'acknowledged' not in existing_columns:
        cursor.execute("ALTER TABLE alert_history ADD COLUMN acknowledged INTEGER DEFAULT 0")

    # Add resolved column
    if 'resolved' not in existing_columns:
        cursor.execute("ALTER TABLE alert_history ADD COLUMN resolved INTEGER DEFAULT 0")

    # Add notes column
    if 'notes' not in existing_columns:
        cursor.execute("ALTER TABLE alert_history ADD COLUMN notes TEXT")

    # Add resolution_time column
    if 'resolution_time' not in existing_columns:
        cursor.execute("ALTER TABLE alert_history ADD COLUMN resolution_time TEXT")

    conn.commit()


def create_indexes(conn):
    """Create performance indexes"""
    cursor = conn.cursor()

    # Saved queries indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_queries_user ON saved_queries(created_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_saved_queries_created ON saved_queries(created_at)")

    # Alert rule versions indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_versions_rule ON alert_rule_versions(rule_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_versions_modified ON alert_rule_versions(modified_at)")

    # Scheduled reports indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_next_run ON scheduled_reports(next_run)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_active ON scheduled_reports(is_active)")

    # Alert history extended indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_status ON alert_history(acknowledged, resolved)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_trigger ON alert_history(triggered_at)")

    conn.commit()


def insert_sample_templates(conn):
    """Insert sample report templates"""
    cursor = conn.cursor()

    # Check if templates already exist
    cursor.execute("SELECT COUNT(*) FROM report_templates")
    if cursor.fetchone()[0] > 0:
        return

    templates = [
        {
            "id": "weekly_summary",
            "name": "Weekly Usage Summary",
            "description": "Summary of usage, costs, and trends for the past week",
            "template_config": '{"charts": ["token_trend", "cost_breakdown"], "tables": ["model_usage"], "date_range": "7d"}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "is_default": 1
        },
        {
            "id": "cost_analysis",
            "name": "Cost Analysis Report",
            "description": "Detailed cost breakdown by provider, model, and time period",
            "template_config": '{"charts": ["cost_by_provider", "cost_over_time"], "tables": ["cost_breakdown"], "date_range": "30d"}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "is_default": 1
        },
        {
            "id": "model_performance",
            "name": "Model Performance Comparison",
            "description": "Compare performance metrics across all models",
            "template_config": '{"charts": ["token_efficiency", "latency_comparison"], "tables": ["model_comparison"], "date_range": "30d"}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "is_default": 1
        }
    ]

    for template in templates:
        cursor.execute("""
            INSERT INTO report_templates (id, name, description, template_config, created_at, created_by, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            template["id"],
            template["name"],
            template["description"],
            template["template_config"],
            template["created_at"],
            template["created_by"],
            template["is_default"]
        ))

    conn.commit()


def insert_sample_saved_queries(conn):
    """Insert sample saved queries"""
    cursor = conn.cursor()

    # Check if queries already exist
    cursor.execute("SELECT COUNT(*) FROM saved_queries")
    if cursor.fetchone()[0] > 0:
        return

    queries = [
        {
            "id": "high_cost_requests",
            "name": "High Cost Requests",
            "description": "All requests costing more than $0.10",
            "query_json": '{"filters": [{"field": "estimated_cost", "operator": ">", "value": 0.1}], "sort": {"field": "estimated_cost", "order": "DESC"}, "limit": 100}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "tags": "cost,high-priority"
        },
        {
            "id": "error_analysis",
            "name": "Error Analysis",
            "description": "All failed requests from last 24 hours",
            "query_json": '{"filters": [{"field": "status", "operator": "=", "value": "error"}, {"field": "timestamp", "operator": ">", "value": "now-24h"}], "sort": {"field": "timestamp", "order": "DESC"}, "limit": 200}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "tags": "errors,debugging"
        },
        {
            "id": "model_efficiency",
            "name": "Model Efficiency",
            "description": "Token efficiency by model (tokens per dollar)",
            "query_json": '{"group_by": ["routed_model"], "aggregates": [{"field": "total_tokens", "func": "SUM"}, {"field": "estimated_cost", "func": "SUM"}], "sort": {"field": "efficiency", "order": "DESC"}}',
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system",
            "tags": "optimization,models"
        }
    ]

    for query in queries:
        cursor.execute("""
            INSERT INTO saved_queries (id, name, description, query_json, created_at, created_by, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            query["id"],
            query["name"],
            query["description"],
            query["query_json"],
            query["created_at"],
            query["created_by"],
            query["tags"]
        ))

    conn.commit()


def insert_default_alert_rules(conn):
    """Insert enhanced default alert rules"""
    cursor = conn.cursor()

    # Add some intelligent defaults for Phase 2
    new_rules = [
        {
            "id": "rule_high_token_usage",
            "name": "High Token Usage",
            "description": "Alert when daily tokens exceed 1M",
            "condition_json": '{"metric": "daily_tokens", "operator": ">", "threshold": 1000000}',
            "actions_json": '{"in_app": true, "email": false, "priority": "medium"}',
            "cooldown_minutes": 60,
            "priority": 2,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system"
        },
        {
            "id": "rule_cost_efficiency",
            "name": "Cost Efficiency Alert",
            "description": "Alert when average cost per token > $0.01",
            "condition_json": '{"metric": "cost_per_token", "operator": ">", "threshold": 0.01}',
            "actions_json": '{"in_app": true, "email": true, "priority": "high"}',
            "cooldown_minutes": 120,
            "priority": 1,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system"
        }
    ]

    for rule in new_rules:
        # Check if rule already exists
        cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE id = ?", (rule["id"],))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO alert_rules (id, name, description, condition_json, actions_json, cooldown_minutes, priority, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule["id"],
                rule["name"],
                rule["description"],
                rule["condition_json"],
                rule["actions_json"],
                rule["cooldown_minutes"],
                rule["priority"],
                rule["created_at"],
                rule["created_by"]
            ))

    conn.commit()


def run_migration():
    """Execute the migration"""
    print(f"🔍 Running Migration: {MIGRATION_NAME}")
    print("   Creating advanced analytics tables...")

    if not os.path.exists(DB_PATH):
        print("⚠️  Database file not found. Run Phase 1 migration first!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Create new tables
        print("   📝 Creating saved_queries table...")
        create_saved_queries_table(conn)

        print("   📋 Creating alert_rule_versions table...")
        create_alert_rule_versions_table(conn)

        print("   📊 Creating report_templates table...")
        create_report_templates_table(conn)

        print("   ⏰ Creating scheduled_reports table...")
        create_scheduled_reports_table(conn)

        print("   📤 Creating report_executions table...")
        create_report_executions_table(conn)

        # Extend existing table
        print("   🔄 Extending alert_history table...")
        extend_alert_history_table(conn)

        # Create indexes
        print("   🔗 Creating performance indexes...")
        create_indexes(conn)

        # Insert sample data
        print("   🎯 Inserting sample templates...")
        insert_sample_templates(conn)

        print("   💾 Inserting sample saved queries...")
        insert_sample_saved_queries(conn)

        print("   🔔 Adding enhanced alert rules...")
        insert_default_alert_rules(conn)

        # Verify
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN
            ('saved_queries', 'alert_rule_versions', 'report_templates',
             'scheduled_reports', 'report_executions')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print(f"   ✅ Migration complete! Tables created: {len(tables)}")
        print(f"   📋 New tables: {', '.join(tables)}")

        # Migration log
        cursor.execute("""
            INSERT INTO migration_log (migration_name, executed_at, status)
            VALUES (?, ?, ?)
        """, (MIGRATION_NAME, datetime.utcnow().isoformat(), "success"))

        conn.commit()

        print("\n🎉 Migration successful!")
        print("   Phase 2 foundations ready!")
        print("   Next: Implement chart components and API endpoints")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()