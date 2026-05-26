"""
Partial scan for JanusPDFs directory
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from backend.utils.paths import get_app_data_dir
from backend.services.rag.ingestion import IngestionRun

# Target directory
target_dir = r"C:\Users\pruve\Desktop\JanusPDFs"

# Paths
chroma_path = str(Path(get_app_data_dir()) / "rag_chroma_db_v2")
db_path = str(Path(get_app_data_dir()) / "knowledge_index_v2.db")

print(f"Running partial scan for: {target_dir}")
print(f"ChromaDB path: {chroma_path}")
print(f"Index DB path: {db_path}")

ingest = IngestionRun(
    root_dir=Path(target_dir),
    chroma_path=chroma_path,
    db_path=db_path,
    enable_path_policy=True,
)

stats = ingest.run()
print(f"\nScan completed: {stats}")
