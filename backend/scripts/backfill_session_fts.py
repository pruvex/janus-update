import argparse

from backend.data.database import SessionLocal
from backend.data.models import Message
from backend.services.memory.session_fts_store import SessionFTSStore
from backend.services.memory.session_search_service import sanitize_session_search_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    indexed = 0
    try:
        with SessionFTSStore() as store:
            query = db.query(Message).order_by(Message.id.asc())
            for message in query.yield_per(max(1, args.batch_size)):
                if not sanitize_session_search_text(message.content):
                    continue
                indexed += 1
                if args.dry_run:
                    continue
                store.index_message(
                    message_id=message.id,
                    chat_id=message.chat_id,
                    role=message.role,
                    content=message.content,
                    created_at=message.created_at,
                )
        print(f"Session-Search backfill candidate messages: {indexed}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
