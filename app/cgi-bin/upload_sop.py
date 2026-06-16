#!/usr/bin/env python3
import sys, os, json, sqlite3, time, secrets, cgi

DB       = "/data/playbooks.db"
SOPS_DIR = "/data/sops"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(0)

if os.environ.get("REQUEST_METHOD") != "POST":
    err("Method not allowed")

os.makedirs(SOPS_DIR, exist_ok=True)

try:
    form = cgi.FieldStorage(
        fp=sys.stdin.buffer,
        environ=os.environ,
        keep_blank_values=True
    )
except Exception as e:
    err(f"Failed to parse upload: {e}")

file_item = form.getvalue("file") or form["file"] if "file" in form else None
if file_item is None or (hasattr(file_item, "filename") and not file_item.filename):
    err("No file provided")

if hasattr(file_item, "file"):
    raw = file_item.file.read()
    original_filename = file_item.filename or "upload.pdf"
else:
    raw = file_item if isinstance(file_item, bytes) else file_item.encode()
    original_filename = "upload.pdf"

if not raw:
    err("Empty file")

name     = (form.getvalue("name") or os.path.splitext(original_filename)[0]).strip()
category = (form.getvalue("category") or "General").strip()

sop_id   = f"sop-{int(time.time()*1000):x}-{secrets.token_hex(4)}"
filename = f"{sop_id}.pdf"
filepath = os.path.join(SOPS_DIR, filename)

try:
    with open(filepath, "wb") as fh:
        fh.write(raw)
except Exception as e:
    err(f"Failed to save file: {e}")

try:
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO sops (id,name,category,filename,size,uploaded_at) "
        "VALUES (?,?,?,?,?,datetime('now'))",
        (sop_id, name, category, filename, len(raw))
    )
    conn.commit()
    conn.close()
    print(json.dumps({"ok": True, "id": sop_id, "name": name, "filename": filename}))
except Exception as e:
    try:
        os.remove(filepath)
    except Exception:
        pass
    err(str(e))
