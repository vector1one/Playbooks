#!/usr/bin/env python3
import sys, os, json, sqlite3

DB = "/data/playbooks.db"

print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()

qs   = os.environ.get("QUERY_STRING","")
dtype = next((p.split("=",1)[1] for p in qs.split("&") if p.startswith("type=")), "sop")
dtype = dtype if dtype in ("sop","doc") else "sop"

try:
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id,name,category,type,filename,size,uploaded_at "
        "FROM documents WHERE type=? ORDER BY uploaded_at DESC",
        (dtype,)
    ).fetchall()
    conn.close()
    result = [
        {"id":r[0],"name":r[1],"category":r[2],"type":r[3],
         "filename":r[4],"size":r[5],"uploaded_at":r[6]}
        for r in rows
    ]
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e)}))
