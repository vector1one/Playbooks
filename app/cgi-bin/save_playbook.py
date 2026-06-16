#!/usr/bin/env python3
import sys, os, json, sqlite3, time, secrets

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

if not data.get("name"):
    err("Missing required field: name")

pb_id = f"custom-{int(time.time()*1000):x}-{secrets.token_hex(4)}"

try:
    conn = sqlite3.connect(DB)
    max_num = conn.execute(
        "SELECT COALESCE(MAX(num),0) FROM playbooks WHERE source='custom'"
    ).fetchone()[0]
    num = max_num + 1

    data["id"]        = pb_id
    data["num"]       = num
    data["source"]    = "custom"
    data["createdAt"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    content = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    conn.execute(
        "INSERT INTO playbooks (id,num,name,cat,sev,source,content,updated_at) "
        "VALUES (?,?,?,?,?,'custom',?,datetime('now'))",
        (pb_id, num, data.get("name",""), data.get("cat","Other"),
         data.get("sev","medium"), content)
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "id": pb_id, "num": num}))
except Exception as e:
    err(str(e))
