#!/usr/bin/env python3
import sys, os, json, sqlite3, glob

DB       = "/data/playbooks.db"
SEED_DIR = "/var/www/localhost/htdocs/playbooks"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(0)

method = os.environ.get("REQUEST_METHOD","")
if method not in ("DELETE", "POST"):
    err("Method not allowed")

if method == "POST":
    length = int(os.environ.get("CONTENT_LENGTH", 0) or 0)
    body   = sys.stdin.buffer.read(length) if length > 0 else b""
    try:
        pb_id = json.loads(body).get("id","")
    except Exception:
        pb_id = ""
else:
    qs    = os.environ.get("QUERY_STRING","")
    pb_id = next((p.split("=",1)[1] for p in qs.split("&") if p.startswith("id=")), "")

pb_id = "".join(c for c in pb_id if c.isalnum() or c in "._-")
if not pb_id:
    err("Missing id")

try:
    conn = sqlite3.connect(DB)
    row  = conn.execute("SELECT source FROM playbooks WHERE id=?", (pb_id,)).fetchone()
    if not row:
        err("Playbook not found")

    source = row[0]
    conn.execute("DELETE FROM playbooks WHERE id=?", (pb_id,))

    reverted = False
    if source in ("custom", "library-override"):
        # Try to restore the original library version
        for f in glob.glob(os.path.join(SEED_DIR,"**","*.json"), recursive=True):
            if os.path.basename(f) in ("manifest.json","mitre-techniques.json"):
                continue
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                if data.get("id") == pb_id:
                    content = json.dumps(data, ensure_ascii=False, separators=(",",":"))
                    conn.execute(
                        "INSERT OR REPLACE INTO playbooks (id,num,name,cat,sev,source,content,updated_at) "
                        "VALUES (?,?,?,?,?,'library',?,datetime('now'))",
                        (pb_id, data.get("num",0), data.get("name",""),
                         data.get("cat","Other"), data.get("sev","medium"), content)
                    )
                    reverted = True
                    break
            except Exception:
                pass

    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "deleted": pb_id, "reverted": reverted}))
except Exception as e:
    err(str(e))
