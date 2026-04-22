"""
Forensic analysis for RAG V2 PDF ingestion:
- SQLite index_store: exact entry for rollooff.pdf
- ChromaDB: chunks for rollooff.pdf
- FTS5: chunks for rollooff.pdf
"""
import sys
import os
import sqlite3
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.paths import get_app_data_dir

app_data = get_app_data_dir()
index_db = os.path.join(app_data, "knowledge_index_v2.db")
fts_db = os.path.join(app_data, "knowledge_fts_v2.db")
chroma_path = os.path.join(app_data, "rag_chroma_db_v2")

print("=" * 80)
print("FORENSIC ANALYSIS — RAG V2 PDF INGESTION")
print("=" * 80)

# 1) SQLite index_store
print("\n[1] SQLite index_store — knowledge_index_v2.db")
print(f"    Path: {index_db}")
print(f"    Exists: {os.path.exists(index_db)}")

conn = sqlite3.connect(index_db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Schema
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"    Tables: {[t['name'] for t in tables]}")

# All PDF entries
print("\n    All PDF entries (LIKE '%.pdf'):")
rows = cur.execute("SELECT path, sha256, format, chunk_ids FROM indexed_files WHERE path LIKE '%.pdf'").fetchall()
for r in rows:
    chunks = json.loads(r["chunk_ids"])
    print(f"      path={r['path']}")
    print(f"        format={r['format']}  sha={r['sha256'][:12]}  #chunks={len(chunks)}")
    if chunks:
        print(f"        first_chunk_id={chunks[0]}")

# rollooff.pdf specifically
print("\n    Direct lookup rollooff.pdf:")
for pattern in ["%rollooff.pdf", "%rollooff%", "%ROLLOOFF%"]:
    rows = cur.execute("SELECT path, format, chunk_ids FROM indexed_files WHERE path LIKE ?", (pattern,)).fetchall()
    print(f"      LIKE '{pattern}' -> {len(rows)} rows")
    for r in rows:
        print(f"        {r['path']}  format={r['format']}  chunks={len(json.loads(r['chunk_ids']))}")

# All entries overview
total = cur.execute("SELECT COUNT(*) FROM indexed_files").fetchone()[0]
print(f"\n    Total indexed_files: {total}")
format_counts = cur.execute("SELECT format, COUNT(*) as c FROM indexed_files GROUP BY format").fetchall()
for fc in format_counts:
    print(f"      format={fc['format']}: {fc['c']}")

conn.close()

# 2) ChromaDB check
print("\n[2] ChromaDB — rag_chroma_db_v2")
print(f"    Path: {chroma_path}")
print(f"    Exists: {os.path.exists(chroma_path)}")

try:
    import chromadb
    client = chromadb.PersistentClient(path=chroma_path)
    cols = client.list_collections()
    print(f"    Collections: {[c.name for c in cols]}")
    for col in cols:
        c = client.get_collection(col.name)
        cnt = c.count()
        print(f"      {col.name}: count={cnt}")
        # Query by source_path metadata for rollooff
        try:
            got = c.get(where={"source_path": {"$eq": r"C:\Users\pruve\Desktop\JanusPDFs\rollooff.pdf"}})
            print(f"        rollooff.pdf chunks: {len(got['ids'])}")
            if got["ids"]:
                print(f"          first_id={got['ids'][0]}")
                print(f"          first_metadata={got['metadatas'][0]}")
                txt = got["documents"][0] if got.get("documents") else ""
                print(f"          first_text[:200]={txt[:200]!r}")
        except Exception as e:
            print(f"        metadata query failed: {e}")
        # Fallback: list all unique source_paths
        try:
            all_docs = c.get(limit=2000)
            unique = set()
            for m in all_docs.get("metadatas", []):
                if m and m.get("source_path"):
                    unique.add(m["source_path"])
            print(f"        unique source_paths in collection: {len(unique)}")
            for sp in list(unique)[:10]:
                print(f"          - {sp}")
        except Exception as e:
            print(f"        full list failed: {e}")
except Exception as e:
    print(f"    ChromaDB check failed: {e}")

# 3) FTS5 check
print("\n[3] FTS5 — knowledge_fts_v2.db")
print(f"    Path: {fts_db}")
print(f"    Exists: {os.path.exists(fts_db)}")
try:
    fts = sqlite3.connect(fts_db)
    fts.row_factory = sqlite3.Row
    cur = fts.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"    Tables: {[t['name'] for t in tables]}")
    # Try common FTS5 table names
    for tbl in ["chunks_fts", "chunks", "fts_chunks"]:
        try:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            print(f"    {tbl}: count={cnt}")
            # Try to find rollooff
            sample = cur.execute(f"SELECT * FROM {tbl} LIMIT 1").fetchall()
            if sample:
                print(f"      sample row keys: {sample[0].keys()}")
        except Exception:
            pass
    fts.close()
except Exception as e:
    print(f"    FTS check failed: {e}")

print("\n" + "=" * 80)
