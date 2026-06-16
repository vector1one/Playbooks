#!/usr/bin/env python3
"""
init_db.py — run from entrypoint.sh (not a CGI script).
Creates the SQLite schema and seeds library playbooks on first boot.
"""
import os, sys, json, sqlite3, glob

DB_PATH   = "/data/playbooks.db"
SEED_DIR  = "/var/www/localhost/htdocs/playbooks"
DOCS_DIR  = "/data/docs"

SCHEMA = """
CREATE TABLE IF NOT EXISTS playbooks (
  id         TEXT PRIMARY KEY,
  num        INTEGER DEFAULT 0,
  name       TEXT NOT NULL,
  cat        TEXT DEFAULT 'Other',
  sev        TEXT DEFAULT 'medium',
  source     TEXT DEFAULT 'library',
  content    TEXT NOT NULL,
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS documents (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  category    TEXT DEFAULT 'General',
  type        TEXT DEFAULT 'sop',
  filename    TEXT NOT NULL,
  size        INTEGER DEFAULT 0,
  uploaded_at TEXT DEFAULT (datetime('now'))
);
"""

MIGRATION = """
-- migrate legacy sops table if it exists (no-op if already done)
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT DEFAULT 'General',
  type TEXT DEFAULT 'sop', filename TEXT NOT NULL,
  size INTEGER DEFAULT 0, uploaded_at TEXT DEFAULT (datetime('now'))
);
"""

def main():
    os.makedirs("/data", exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    first_run = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    # Migrate from legacy sops table if present
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "sops" in tables and "documents" in tables:
        conn.execute(
            "INSERT OR IGNORE INTO documents (id,name,category,type,filename,size,uploaded_at) "
            "SELECT id,name,category,'sop',filename,size,uploaded_at FROM sops"
        )
        conn.execute("DROP TABLE sops")
    elif "sops" in tables:
        conn.execute("ALTER TABLE sops RENAME TO documents")
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN type TEXT DEFAULT 'sop'")
        except Exception:
            pass

    conn.commit()

    if not first_run:
        count = conn.execute("SELECT COUNT(*) FROM playbooks").fetchone()[0]
        if count > 0:
            print(f"[init_db] DB already seeded ({count} playbooks). Skipping.", flush=True)
            conn.close()
            return

    print("[init_db] Seeding playbooks from JSON files...", flush=True)
    files = glob.glob(os.path.join(SEED_DIR, "**", "*.json"), recursive=True)
    seeded = 0
    for f in sorted(files):
        base = os.path.basename(f)
        if base in ("manifest.json", "mitre-techniques.json"):
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            print(f"[init_db] Skipping {f}: {e}", flush=True)
            continue
        pb_id = data.get("id")
        if not pb_id:
            continue
        content = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        conn.execute(
            "INSERT OR IGNORE INTO playbooks (id,num,name,cat,sev,source,content,updated_at) "
            "VALUES (?,?,?,?,?,'library',?,datetime('now'))",
            (pb_id, data.get("num", 0), data.get("name",""), data.get("cat","Other"),
             data.get("sev","medium"), content)
        )
        seeded += 1

    conn.commit()
    conn.close()
    print(f"[init_db] Done. Seeded {seeded} playbooks.", flush=True)

if __name__ == "__main__":
    main()
