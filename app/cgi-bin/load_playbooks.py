#!/usr/bin/env python3
import sys, sqlite3

DB = "/data/playbooks.db"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

try:
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT content FROM playbooks ORDER BY num ASC, id ASC"
    ).fetchall()
    conn.close()
    sys.stdout.write("[" + ",".join(r[0] for r in rows) + "]")
except Exception as e:
    import json
    sys.stdout.write(json.dumps({"error": str(e)}))
