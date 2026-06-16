#!/usr/bin/env python3
import sys, os, json, sqlite3

DB       = "/data/playbooks.db"
SOPS_DIR = "/data/sops"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(0)

method = os.environ.get("REQUEST_METHOD","")
if method not in ("DELETE","POST"):
    err("Method not allowed")

qs    = os.environ.get("QUERY_STRING","")
sop_id = next((p.split("=",1)[1] for p in qs.split("&") if p.startswith("id=")), "")
sop_id = "".join(c for c in sop_id if c.isalnum() or c in "._-")
if not sop_id:
    err("Missing id")

try:
    conn = sqlite3.connect(DB)
    row  = conn.execute("SELECT filename FROM sops WHERE id=?", (sop_id,)).fetchone()
    if not row:
        err("SOP not found")
    filename = row[0]
    conn.execute("DELETE FROM sops WHERE id=?", (sop_id,))
    conn.commit()
    conn.close()

    filepath = os.path.join(SOPS_DIR, filename)
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass

    print(json.dumps({"ok": True, "deleted": sop_id}))
except Exception as e:
    err(str(e))
