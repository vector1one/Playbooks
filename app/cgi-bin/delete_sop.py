#!/usr/bin/env python3
import sys, os, json, sqlite3

DB       = "/data/playbooks.db"
DOCS_DIR = "/data/docs"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(0)

method = os.environ.get("REQUEST_METHOD","")
if method not in ("DELETE","POST"):
    err("Method not allowed")

qs     = os.environ.get("QUERY_STRING","")
doc_id = next((p.split("=",1)[1] for p in qs.split("&") if p.startswith("id=")), "")
doc_id = "".join(c for c in doc_id if c.isalnum() or c in "._-")
if not doc_id:
    err("Missing id")

try:
    conn = sqlite3.connect(DB)
    row  = conn.execute("SELECT filename FROM documents WHERE id=?", (doc_id,)).fetchone()
    if not row:
        err("Document not found")
    filename = row[0]
    conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()
    try: os.remove(os.path.join(DOCS_DIR, filename))
    except FileNotFoundError: pass
    print(json.dumps({"ok":True,"deleted":doc_id}))
except Exception as e:
    err(str(e))
