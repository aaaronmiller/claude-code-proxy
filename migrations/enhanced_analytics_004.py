"""
Migration 004: Enhanced Analytics & Monitoring
Creates tables for alerts, budget tracking, and real-time monitoring

Author: AI Architect
Date: 2026-01-04
Version: 1.0
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = "usage_tracking.db"
MIGRATION_NAME = "004_enhanced_analytics"


def create_alert_rules_table(conn):
    """Create alert rules configuration table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            condition_json TEXT NOT NULL,
            actions_json TEXT NOT NULL,
            cooldown_minutes INTEGER DEFAULT 5,
            last_triggered TIMESTAMP,
            trigger_count INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TIMESTAMP,
            enabled BOOLEAN DEFAULT 1,
            muted_until TIMESTAMP,
            priority TEXT DEFAULT 'medium'
        )
    """)
    conn.commit()


def create_alert_history_table(conn):
    """Create alert history/audit table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id TEXT PRIMARY KEY,
            rule_id TEXT,
            rule_name TEXT,
            triggered_at TIMESTAMP,
            resolved_at TIMESTAMP,
            alert_data_json TEXT,
            resolved BOOLEAN DEFAULT 0,
            severity TEXT,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        )
    """)
    conn.commit()


def create_budget_tracking_table(conn):
    """Create budget tracking table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_tracking (
            date TEXT PRIMARY KEY,  -- YYYY-MM-DD format
            daily_limit REAL,
            monthly_limit REAL,
            current_daily REAL DEFAULT 0,
            current_monthly REAL DEFAULT 0,
            auto_disable_at_limit BOOLEAN DEFAULT 0,
            alert_sent_80 BOOLEAN DEFAULT 0,
            alert_sent_95 BOOLEAN DEFAULT 0,
            alert_sent_100 BOOLEAN DEFAULT 0,
            updated_at TIMESTAMP
        )
    """)
    conn.commit()


def create_crosstalk_events_table(conn):
    """Create real-time crosstalk session events table"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crosstalk_events (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            round INTEGER NOT NULL,
            model_from TEXT,
            model_to TEXT,
            model_from_id TEXT,
            model_to_id TEXT,
            tokens INTEGER,
            cost REAL,
            duration_ms INTEGER,
            topology_type TEXT,
            paradigm TEXT,
            message_preview TEXT,
            timestamp TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.commit()


def create_live_metrics_cache(conn):
    """Create live metrics cache for real-time dashboard"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_metrics_cache (
            metric_name TEXT PRIMARY KEY,
            metric_value TEXT,
            updated_at TIMESTAMP,
            metadata_json TEXT
        )
    """)
    conn.commit()


def create_indexes(conn):
    """Create performance indexes"""
    cursor = conn.cursor()

    # Alert history indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_rule_id ON alert_history(rule_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_history_triggered ON alert_history(triggered_at)")

    # Crosstalk events indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crosstalk_session ON crosstalk_events(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crosstalk_timestamp ON crosstalk_events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_crosstalk_models ON crosstalk_events(model_from, model_to)")

    # Budget tracking indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_date ON budget_tracking(date)")

    conn.commit()


def insert_sample_alert_rules(conn):
    """Insert sample alert rules for demonstration"""
    cursor = conn.cursor()

    sample_rules = [
        {
            "id": "sample_cost_limit",
            "name": "Daily Budget Warning",
            "description": "Alert when daily cost reaches 80% of budget",
            "condition_json": '{"metric": "cost", "operator": ">", "threshold": 80, "window_minutes": 1440}',
            "actions_json": '{"email": "admin@example.com", "in_app": true}',
            "cooldown_minutes": 60,
            "priority": "high"
        },
        {
            "id": "sample_high_latency",
            "name": "High Latency Alert",
            "description": "Alert when average latency exceeds 2 seconds",
            "condition_json": '{"metric": "latency", "operator": ">", "threshold": 2000, "window_minutes": 5}',
            "actions_json": '{"in_app": true}',
            "cooldown_minutes": 10,
            "priority": "medium"
        },
        {
            "id": "sample_error_spike",
            "name": "Error Rate Spike",
            "description": "Alert when error rate exceeds 10%",
            "condition_json": '{"metric": "error_rate", "operator": ">", "threshold": 10, "window_minutes": 15}',
            "actions_json": '{"in_app": true, "webhook": "https://hooks.example.com/alerts"}',
            "cooldown_minutes": 5,
            "priority": "critical"
        }
    ]

    for rule in sample_rules:
        cursor.execute("""
            INSERT OR IGNORE INTO alert_rules
            (id, name, description, condition_json, actions_json, cooldown_minutes, priority, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rule["id"],
            rule["name"],
            rule["description"],
            rule["condition_json"],
            rule["actions_json"],
            rule["cooldown_minutes"],
            rule["priority"],
            datetime.utcnow().isoformat(),
            "system"
        ))

    conn.commit()


def run_migration():
    """Execute the migration"""
    print(f"🔍 Running Migration: {MIGRATION_NAME}")
    print("   Creating enhanced analytics tables...")

    if not os.path.exists(DB_PATH):
        print("⚠️  Database file not found. Creating new database...")
        # Create initial tables from previous migrations
        from src.services.usage.usage_tracker import usage_tracker
        usage_tracker.initialize_database()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        # Create tables
        print("   📊 Creating alert_rules table...")
        create_alert_rules_table(conn)

        print("   📝 Creating alert_history table...")
        create_alert_history_table(conn)

        print("   💰 Creating budget_tracking table...")
        create_budget_tracking_table(conn)

        print("   🔄 Creating crosstalk_events table...")
        create_crosstalk_events_table(conn)

        print("   📈 Creating live_metrics_cache table...")
        create_live_metrics_cache(conn)

        # Create indexes
        print("   🔗 Creating performance indexes...")
        create_indexes(conn)

        # Insert sample data
        print("   🎯 Inserting sample alert rules...")
        insert_sample_alert_rules(conn)

        # Verify
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%alert%' OR name LIKE '%budget%' OR name LIKE '%crosstalk%' OR name LIKE '%live%'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"   ✅ Migration complete! Tables created: {len(tables)}")
        print(f"   📋 Tables: {', '.join(tables)}")

        # Migration log
        cursor.execute("""
            INSERT INTO migration_log (migration_name, executed_at, status)
            VALUES (?, ?, ?)
        """, (MIGRATION_NAME, datetime.utcnow().isoformat(), "success"))

        conn.commit()

        print("\n🎉 Migration successful!")
        print("   Next: Run 005_websocket_endpoints.py")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()