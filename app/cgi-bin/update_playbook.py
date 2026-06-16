#!/usr/bin/env python3
import sys, os, json, sqlite3

DB = "/data/playbooks.db"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(0)

if os.environ.get("REQUEST_METHOD") != "POST":
    err("Method not allowed")

length = int(os.environ.get("CONTENT_LENGTH", 0) or 0)
if length <= 0:
    err("Empty body")

try:
    body = sys.stdin.buffer.read(length)
    data = json.loads(body)
except Exception as e:
    err(f"Invalid JSON: {e}")

pb_id = str(data.get("id", "")).strip()
if not pb_id:
    err("Missing required field: id")

try:
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT source FROM playbooks WHERE id=?", (pb_id,)).fetchone()
    if row:
        old_source = row[0]
        new_source = "library-override" if old_source == "library" else old_source
    else:
        new_source = "library-override"

    data["source"] = new_source
    content = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    conn.execute(
        "INSERT INTO playbooks (id,num,name,cat,sev,source,content,updated_at) "
        "VALUES (?,?,?,?,?,?,?,datetime('now')) "
        "ON CONFLICT(id) DO UPDATE SET "
        "name=excluded.name, cat=excluded.cat, sev=excluded.sev, "
        "source=excluded.source, content=excluded.content, updated_at=excluded.updated_at",
        (pb_id, data.get("num",0), data.get("name",""), data.get("cat","Other"),
         data.get("sev","medium"), new_source, content)
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "id": pb_id, "source": new_source}))
except Exception as e:
    err(str(e))
