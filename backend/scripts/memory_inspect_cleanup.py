"""
Memory Inspect & Cleanup Utility

Usage:
  python backend/scripts/memory_inspect_cleanup.py --search "<term>"
  python backend/scripts/memory_inspect_cleanup.py --search "<term>" --delete

Inspects and optionally deletes Memory rows whose normalized_text or snippet
contains a given search term (case-insensitive LIKE). Use to remove hallucinated
memory entries (e.g. "Skandinavien"-Fakten) that conflict with real PDF content.
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data.database import SessionLocal
from backend.data import models


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", required=True, help="Case-insensitive substring to search.")
    parser.add_argument("--delete", action="store_true", help="Delete matching rows.")
    parser.add_argument("--category", default=None, help="Optional category filter.")
    args = parser.parse_args()

    pattern = f"%{args.search}%"
    db = SessionLocal()
    try:
        q = db.query(models.Memory).filter(
            (models.Memory.normalized_text.ilike(pattern))
            | (models.Memory.snippet.ilike(pattern))
        )
        if args.category:
            q = q.filter(models.Memory.category == args.category)

        rows = q.all()
        print(f"Found {len(rows)} Memory rows matching '{args.search}'")
        for m in rows:
            snippet = (m.snippet or "")[:120].replace("\n", " ")
            print(
                f"  id={m.id}  chat_id={m.chat_id}  cat={m.category}  core={m.is_core_fact}  "
                f"created={m.created_at}\n    snippet: {snippet!r}"
            )

        if args.delete and rows:
            confirm = input(f"\nDelete all {len(rows)} rows? Type 'YES' to confirm: ")
            if confirm == "YES":
                for m in rows:
                    db.delete(m)
                db.commit()
                print(f"Deleted {len(rows)} rows.")
            else:
                print("Aborted.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
