
import sqlite3
import json
import shutil
import os
import sys

db_path = "usage_tracking.db"
copy_path = "usage_tracking_copy.db"

try:
    print(f"Copying {db_path} to {copy_path}...")
    shutil.copy2(db_path, copy_path)
    print("Copy successful.")
    
    conn = sqlite3.connect(copy_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, condition_json FROM alert_rules")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} rules.")
    for row in rows:
        rule_id, condition_json = row
        print("-" * 40)
        print(f"Rule ID: {rule_id}")
        print(f"Condition JSON: {condition_json}")
        try:
            parsed = json.loads(condition_json)
            print(f"Parsed Type: {type(parsed)}")
            if isinstance(parsed, list):
                if len(parsed) > 0:
                    print(f"First element type: {type(parsed[0])}")
                    print(f"First element value: {parsed[0]}")
            elif isinstance(parsed, str):
                print(f"Parsed is a string: {parsed}")
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    conn.close()
    
    # Cleanup
    os.remove(copy_path)
    print("Cleanup successful.")

except Exception as e:
    print(f"Error: {e}")
