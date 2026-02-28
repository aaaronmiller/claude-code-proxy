
import sqlite3
import json
import shutil
import os
import sys
import time

# Flush stdout
sys.stdout.reconfigure(line_buffering=True)

db_path = "usage_tracking.db"
copy_path = "/tmp/usage_tracking_debug.db"

try:
    abs_db_path = os.path.abspath(db_path)
    print(f"Copying {abs_db_path} to {copy_path}...")
    shutil.copy2(db_path, copy_path)
    time.sleep(1.0) # Wait a bit to ensure FS sync
    print("Copy successful.")
    
    # Check header
    with open(copy_path, 'rb') as f:
        header = f.read(16)
        print(f"Header: {header}")
        if b"SQLite format 3" in header:
             print("Valid SQLite header.")
        else:
             print("Invalid SQLite header.")

    print(f"Connecting to {copy_path}...")
    conn = sqlite3.connect(copy_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute("SELECT id, condition_json FROM alert_rules")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} rules.")
    for row in rows:
        rule_id, condition_json = row
        print("-" * 40)
        print(f"Rule ID: {rule_id}")
        print(f"Condition JSON: {condition_json}")

    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
