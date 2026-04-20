import json

try:
    from backend.data import models
    from backend.data.database import SessionLocal, init_db
except ModuleNotFoundError:
    from data import models
    from data.database import SessionLocal, init_db


def main() -> int:
    init_db()
    db = SessionLocal()

    try:
        test_key = "diagnose|memory|type-check"
        test_hash = "testhash_123"

        # Cleanup stale test row if present
        existing = db.query(models.Memory).filter(models.Memory.normalized_text == test_key).first()
        if existing:
            db.delete(existing)
            db.commit()

        new_memory = models.Memory(
            chat_id=None,
            snippet=json.dumps({"fact": "Type alignment test"}),
            embedding_json=b"[0.1, 0.2, 0.3]",
            normalized_text=test_key,
            text_hash=test_hash,
            category="diagnostic",
        )

        db.add(new_memory)
        db.commit()
        db.refresh(new_memory)

        loaded = db.query(models.Memory).filter(models.Memory.id == new_memory.id).first()
        if not loaded:
            print("[FAIL] Inserted row could not be reloaded.")
            return 1

        if not isinstance(loaded.text_hash, str):
            print(f"[FAIL] text_hash type mismatch: {type(loaded.text_hash)}")
            return 1

        if not isinstance(loaded.embedding_json, (bytes, bytearray)):
            print(f"[FAIL] embedding_json type mismatch: {type(loaded.embedding_json)}")
            return 1

        print("[PASS] Memory insert succeeded.")
        print(f"[INFO] id={loaded.id}")
        print(f"[INFO] text_hash_type={type(loaded.text_hash).__name__}")
        print(f"[INFO] embedding_json_type={type(loaded.embedding_json).__name__}")
        return 0

    except Exception as exc:
        print(f"[FAIL] Exception during insert test: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
