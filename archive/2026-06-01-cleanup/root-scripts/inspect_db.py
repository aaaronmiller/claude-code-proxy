
import sqlite3
import json

db_path = r"\\wsl.localhost\Ubuntu\home\cheta\code\claude-code-proxy\usage_tracking.db"

try:
    conn = sqlite3.connect(db_path)
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
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    conn.close()

except Exception as e:
    print(f"Database Error: {e}")
