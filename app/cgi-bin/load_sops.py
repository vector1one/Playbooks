#!/usr/bin/env python3
import sys, json, sqlite3

DB = "/data/playbooks.db"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

try:
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, name, category, filename, size, uploaded_at "
        "FROM sops ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    result = [
        {"id": r[0], "name": r[1], "category": r[2],
         "filename": r[3], "size": r[4], "uploaded_at": r[5]}
        for r in rows
    ]
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e)}))
