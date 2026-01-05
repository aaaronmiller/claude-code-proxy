"""
Migration 006: Advanced Alert Engine & Notification System
Enhanced alerting with complex conditions and multi-channel notifications

Author: AI Architect
Date: 2026-01-05
Version: 1.0
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = "usage_tracking.db"
MIGRATION_NAME = "006_alert_engine"


def create_notification_channels_table(conn):
    """Create notification channels configuration table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_channels (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            config TEXT NOT NULL,
            is_enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_used TEXT
        )
    """)
    conn.commit()


def create_notification_history_table(conn):
    """Create notification delivery history table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_history (
            id TEXT PRIMARY KEY,
            alert_id TEXT,
            channel_id TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            sent_at TEXT NOT NULL,
            FOREIGN KEY (alert_id) REFERENCES alert_history(id),
            FOREIGN KEY (channel_id) REFERENCES notification_channels(id)
        )
    """)
    conn.commit()


def create_user_preferences_table(conn):
    """Create user preferences table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id TEXT PRIMARY KEY,
            theme TEXT,
            keyboard_shortcuts TEXT,
            notifications_enabled INTEGER DEFAULT 1,
            quiet_hours_start TEXT,
            quiet_hours_end TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def extend_alert_rules_table(conn):
    """Add new columns to alert_rules for advanced features"""
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(alert_rules)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    # Add condition_logic for AND/OR groups
    if 'condition_logic' not in existing_columns:
        cursor.execute("ALTER TABLE alert_rules ADD COLUMN condition_logic TEXT")

    # Add time_window (evaluation frequency in minutes)
    if 'time_window' not in existing_columns:
        cursor.execute("ALTER TABLE alert_rules ADD COLUMN time_window INTEGER DEFAULT 5")

    # Add is_active toggle
    if 'is_active' not in existing_columns:
        cursor.execute("ALTER TABLE alert_rules ADD COLUMN is_active INTEGER DEFAULT 1")

    # Add last_triggered timestamp
    if 'last_triggered' not in existing_columns:
        cursor.execute("ALTER TABLE alert_rules ADD COLUMN last_triggered TEXT")

    # Add trigger_count for statistics
    if 'trigger_count' not in existing_columns:
        cursor.execute("ALTER TABLE alert_rules ADD COLUMN trigger_count INTEGER DEFAULT 0")

    conn.commit()


def extend_report_templates_table(conn):
    """Add branding and content options to report templates"""
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(report_templates)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if 'brand_logo' not in existing_columns:
        cursor.execute("ALTER TABLE report_templates ADD COLUMN brand_logo TEXT")

    if 'brand_color' not in existing_columns:
        cursor.execute("ALTER TABLE report_templates ADD COLUMN brand_color TEXT")

    if 'include_charts' not in existing_columns:
        cursor.execute("ALTER TABLE report_templates ADD COLUMN include_charts INTEGER DEFAULT 1")

    if 'include_tables' not in existing_columns:
        cursor.execute("ALTER TABLE report_templates ADD COLUMN include_tables INTEGER DEFAULT 1")

    conn.commit()


def create_scheduled_reports_table(conn):
    """Create scheduled reports table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_reports (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            frequency TEXT NOT NULL,
            recipients TEXT NOT NULL,
            last_run TEXT,
            next_run TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES report_templates(id)
        )
    """)
    conn.commit()


def create_report_executions_table(conn):
    """Create report execution history table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_executions (
            id TEXT PRIMARY KEY,
            scheduled_report_id TEXT,
            template_id TEXT NOT NULL,
            execution_time TEXT NOT NULL,
            status TEXT NOT NULL,
            file_size INTEGER,
            error_message TEXT,
            FOREIGN KEY (scheduled_report_id) REFERENCES scheduled_reports(id),
            FOREIGN KEY (template_id) REFERENCES report_templates(id)
        )
    """)
    conn.commit()


def create_indexes(conn):
    """Create performance indexes"""
    cursor = conn.cursor()

    # Alert rule indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_priority ON alert_rules(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_rules_last_triggered ON alert_rules(last_triggered)")

    # Notification history indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_sent ON notification_history(sent_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_history_alert ON notification_history(alert_id)")

    # User preferences indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_preferences(user_id)")

    conn.commit()


def insert_sample_notification_channels(conn):
    """Insert sample notification channel configurations"""
    cursor = conn.cursor()

    # Check if already exists
    cursor.execute("SELECT COUNT(*) FROM notification_channels")
    if cursor.fetchone()[0] > 0:
        return

    channels = [
        {
            "id": "email_primary",
            "name": "Primary Email",
            "type": "email",
            "config": '{"to": "admin@example.com", "subject_prefix": "[Alert]"}',
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "slack_webhook",
            "name": "Team Slack",
            "type": "slack",
            "config": '{"webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK", "channel": "#alerts"}',
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "in_app",
            "name": "In-App Notifications",
            "type": "in_app",
            "config": '{"sound": true, "badge": true}',
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    for channel in channels:
        cursor.execute("""
            INSERT INTO notification_channels (id, name, type, config, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (channel["id"], channel["name"], channel["type"], channel["config"], channel["created_at"]))

    conn.commit()


def insert_enhanced_alert_rules(conn):
    """Insert advanced sample alert rules"""
    cursor = conn.cursor()

    # Check if enhanced rules exist
    cursor.execute("SELECT COUNT(*) FROM alert_rules WHERE id LIKE 'advanced_%'")
    if cursor.fetchone()[0] > 0:
        return

    rules = [
        {
            "id": "advanced_cost_spike",
            "name": "Cost Spike Detection",
            "description": "Alert when daily cost increases 20% vs yesterday",
            "condition_json": '{"metric": "cost_change_percent", "operator": ">", "threshold": 20}',
            "condition_logic": '{"type": "AND", "conditions": [{"metric": "daily_cost", "operator": ">", "threshold": 500}, {"metric": "cost_change_percent", "operator": ">", "threshold": 20}]}',
            "actions_json": '{"channels": ["in_app", "email"], "priority": "high"}',
            "cooldown_minutes": 60,
            "priority": 1,
            "time_window": 30,
            "is_active": 1,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system"
        },
        {
            "id": "advanced_efficiency",
            "name": "Provider Efficiency Monitor",
            "description": "Alert when cost per token exceeds threshold",
            "condition_json": '{"metric": "cost_per_token", "operator": ">", "threshold": 0.01, "provider": "OpenAI"}',
            "condition_logic": '{"type": "AND", "conditions": [{"metric": "cost_per_token", "operator": ">", "threshold": 0.01}, {"field": "provider", "operator": "=", "value": "OpenAI"}]}',
            "actions_json": '{"channels": ["slack_webhook", "email"], "priority": "medium"}',
            "cooldown_minutes": 120,
            "priority": 2,
            "time_window": 60,
            "is_active": 1,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system"
        },
        {
            "id": "advanced_error_surge",
            "name": "Error Rate Surge",
            "description": "Alert when error rate > 10% in 5 minute window",
            "condition_json": '{"metric": "error_rate", "operator": ">", "threshold": 10, "window": 5}',
            "condition_logic": '{"type": "AND", "conditions": [{"metric": "error_rate", "operator": ">", "threshold": 10}, {"metric": "time_window", "operator": "=", "value": 5}]}',
            "actions_json": '{"channels": ["in_app", "slack_webhook"], "priority": "critical"}',
            "cooldown_minutes": 15,
            "priority": 0,
            "time_window": 5,
            "is_active": 1,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "system"
        }
    ]

    for rule in rules:
        cursor.execute("""
            INSERT INTO alert_rules (
                id, name, description, condition_json, condition_logic,
                actions_json, cooldown_minutes, priority, time_window,
                is_active, created_at, created_by, trigger_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule["id"], rule["name"], rule["description"], rule["condition_json"],
            rule["condition_logic"], rule["actions_json"], rule["cooldown_minutes"],
            rule["priority"], rule["time_window"], rule["is_active"],
            rule["created_at"], rule["created_by"], 0
        ))

    conn.commit()


def insert_user_preferences_template(conn):
    """Insert default user preferences"""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM user_preferences WHERE user_id = 'default'")
    if cursor.fetchone()[0] > 0:
        return

    cursor.execute("""
        INSERT INTO user_preferences
        (user_id, theme, keyboard_shortcuts, notifications_enabled, quiet_hours_start, quiet_hours_end, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "default",
        "light",
        '{"dashboard": "g", "alerts": "a", "reports": "r", "query": "q", "settings": "s"}',
        1,
        "22:00",
        "08:00",
        datetime.utcnow().isoformat()
    ))

    conn.commit()


def insert_sample_report_templates(conn):
    """Insert sample report templates"""
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM report_templates")
    if cursor.fetchone()[0] > 0:
        return

    templates = [
        {
            "id": "tpl_weekly_summary",
            "name": "Weekly Usage Summary",
            "description": "Comprehensive weekly usage report",
            "config": '{"charts": ["token_trend", "cost_over_time"], "tables": ["model_usage", "cost_breakdown"], "date_range": "7d"}',
            "is_default": 1
        },
        {
            "id": "tpl_cost_analysis",
            "name": "Cost Analysis Report",
            "description": "Detailed cost breakdown by provider",
            "config": '{"charts": ["cost_breakdown"], "tables": ["cost_breakdown"], "date_range": "30d"}',
            "is_default": 1
        },
        {
            "id": "tpl_model_performance",
            "name": "Model Performance Comparison",
            "description": "Compare model efficiency and costs",
            "config": '{"charts": ["token_trend"], "tables": ["model_comparison"], "date_range": "30d"}',
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
            template["config"],
            datetime.utcnow().isoformat(),
            "system",
            template["is_default"]
        ))

    conn.commit()


def run_migration():
    """Execute the migration"""
    print(f"🔍 Running Migration: {MIGRATION_NAME}")
    print("   Creating advanced alert engine tables...")

    if not os.path.exists(DB_PATH):
        print("⚠️  Database file not found. Run Phase 1 & 2 migrations first!")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Create new tables
        print("   🔔 Creating notification_channels table...")
        create_notification_channels_table(conn)

        print("   📧 Creating notification_history table...")
        create_notification_history_table(conn)

        print("   👤 Creating user_preferences table...")
        create_user_preferences_table(conn)

        # Extend existing tables
        print("   🔄 Extending alert_rules table...")
        extend_alert_rules_table(conn)

        print("   📊 Extending report_templates table...")
        extend_report_templates_table(conn)

        # New tables for scheduling
        print("   📅 Creating scheduled_reports table...")
        create_scheduled_reports_table(conn)

        print("   📈 Creating report_executions table...")
        create_report_executions_table(conn)

        # Create indexes
        print("   🔗 Creating performance indexes...")
        create_indexes(conn)

        # Insert sample data
        print("   🎯 Inserting sample notification channels...")
        insert_sample_notification_channels(conn)

        print("   🔔 Inserting enhanced sample alert rules...")
        insert_enhanced_alert_rules(conn)

        print("   👤 Inserting default user preferences...")
        insert_user_preferences_template(conn)

        print("   📊 Inserting sample report templates...")
        insert_sample_report_templates(conn)

        # Verify
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN
            ('notification_channels', 'notification_history', 'user_preferences')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print(f"   ✅ Migration complete! New tables: {len(tables)}")
        print(f"   📋 Tables: {', '.join(tables)}")

        # Add to migration log
        cursor.execute("""
            INSERT INTO migration_log (migration_name, executed_at, status)
            VALUES (?, ?, ?)
        """, (MIGRATION_NAME, datetime.utcnow().isoformat(), "success"))

        conn.commit()

        print("\n🎉 Migration successful!")
        print("   ✨ Enhanced alert engine ready!")
        print("   🚀 Multi-channel notifications configured!")
        print("   👤 User preferences initialized!")

        print("\n📋 Next steps:")
        print("   1. Implement AlertEngine service (src/services/alert_engine.py)")
        print("   2. Create notification service (src/services/notifications.py)")
        print("   3. Build alert rule builder UI (web-ui/src/routes/alerts/builder)")
        print("   4. Start notification task scheduler")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()