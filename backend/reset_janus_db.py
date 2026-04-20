import os
from urllib.parse import urlparse

try:
    from backend.data.database import SQLALCHEMY_DATABASE_URL, engine
except ModuleNotFoundError:
    from data.database import SQLALCHEMY_DATABASE_URL, engine


def _sqlite_path_from_url(db_url: str) -> str:
    parsed = urlparse(db_url)
    if parsed.scheme != "sqlite":
        raise ValueError(f"Unsupported DB scheme for reset script: {parsed.scheme}")

    # sqlite:///C:/path/to/file.db OR sqlite:////abs/path
    raw_path = parsed.path
    if os.name == "nt" and raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return os.path.abspath(raw_path)


def main() -> int:
    db_path = _sqlite_path_from_url(SQLALCHEMY_DATABASE_URL)
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"

    print(f"[INFO] Target DB: {db_path}")

    # Ensure no active pooled connections hold file handles
    engine.dispose()

    removed_any = False
    for path in (db_path, wal_path, shm_path):
        if os.path.exists(path):
            os.remove(path)
            removed_any = True
            print(f"[OK] Deleted: {path}")

    if not removed_any:
        print("[INFO] No DB files found. Nothing to delete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
