"""
Regression Gate: SHA-Check for Legacy ChromaDB Isolation

Ensures that V2 code never modifies the legacy rag_chroma_db/ directory.
This test computes a SHA-256 hash tree of the legacy directory before and after V2 runs.
If the hash changes, the test fails - indicating V2 touched the legacy index.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.paths import get_app_data_dir

logger = logging.getLogger("janus_backend")

LEGACY_CHROMA_PATH = os.path.join(get_app_data_dir(), "rag_chroma_db")


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_directory_hash_tree(dirpath: Path) -> Dict[str, str]:
    """
    Compute a hash tree for a directory.
    Returns a dict mapping relative file paths to their SHA-256 hashes.
    """
    hash_tree = {}
    
    if not dirpath.exists():
        logger.warning(f"Directory does not exist: {dirpath}")
        return hash_tree
    
    for root, dirs, files in os.walk(dirpath):
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            relative_path = file_path.relative_to(dirpath)
            try:
                file_hash = compute_file_hash(file_path)
                hash_tree[str(relative_path)] = file_hash
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
    
    return hash_tree


def compute_tree_hash(hash_tree: Dict[str, str]) -> str:
    """
    Compute a single hash from the hash tree.
    Sorts the paths and hashes them together to get a deterministic result.
    """
    if not hash_tree:
        return hashlib.sha256(b"").hexdigest()
    
    # Sort paths for deterministic ordering
    sorted_items = sorted(hash_tree.items())
    
    # Concatenate path + hash for each file
    combined = ""
    for path, file_hash in sorted_items:
        combined += f"{path}:{file_hash}\n"
    
    return hashlib.sha256(combined.encode()).hexdigest()


def save_hash_snapshot(hash_tree: Dict[str, str], snapshot_path: Path):
    """Save hash tree snapshot to a file."""
    os.makedirs(snapshot_path.parent, exist_ok=True)
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        for path, file_hash in sorted(hash_tree.items()):
            f.write(f"{file_hash}  {path}\n")
    logger.info(f"Hash snapshot saved to {snapshot_path}")


def load_hash_snapshot(snapshot_path: Path) -> Dict[str, str]:
    """Load hash tree snapshot from a file."""
    hash_tree = {}
    if not snapshot_path.exists():
        logger.warning(f"Snapshot file does not exist: {snapshot_path}")
        return hash_tree
    
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('  ', 1)
                if len(parts) == 2:
                    file_hash, path = parts
                    hash_tree[path] = file_hash
    
    return hash_tree


def compare_hash_trees(before: Dict[str, str], after: Dict[str, str]) -> Dict[str, any]:
    """Compare two hash trees and return differences."""
    before_paths = set(before.keys())
    after_paths = set(after.keys())
    
    added = after_paths - before_paths
    removed = before_paths - after_paths
    modified = []
    
    for path in before_paths & after_paths:
        if before[path] != after[path]:
            modified.append(path)
    
    return {
        "added": sorted(list(added)),
        "removed": sorted(list(removed)),
        "modified": sorted(modified),
        "unchanged": len(before_paths & after_paths),
    }


def test_legacy_chroma_isolation():
    """
    Test that the legacy ChromaDB directory is not modified.
    
    This test should be run before and after any V2 code execution.
    If the hash tree changes, it indicates V2 touched the legacy index.
    """
    logger.info(f"Checking legacy ChromaDB isolation: {LEGACY_CHROMA_PATH}")
    
    # Compute current hash tree
    hash_tree = compute_directory_hash_tree(Path(LEGACY_CHROMA_PATH))
    tree_hash = compute_tree_hash(hash_tree)
    
    logger.info(f"Legacy directory hash tree: {tree_hash}")
    logger.info(f"Files in legacy directory: {len(hash_tree)}")
    
    # Save snapshot for comparison
    snapshot_dir = Path(__file__).parent / "snapshots"
    snapshot_path = snapshot_dir / "legacy_chroma_hash.txt"
    save_hash_snapshot(hash_tree, snapshot_path)
    
    # Load previous snapshot if exists
    previous_snapshot = snapshot_dir / "legacy_chroma_hash_previous.txt"
    if previous_snapshot.exists():
        previous_hash_tree = load_hash_snapshot(previous_snapshot)
        differences = compare_hash_trees(previous_hash_tree, hash_tree)
        
        if differences["added"] or differences["removed"] or differences["modified"]:
            logger.error("Legacy ChromaDB directory has been modified!")
            logger.error(f"Added files: {differences['added']}")
            logger.error(f"Removed files: {differences['removed']}")
            logger.error(f"Modified files: {differences['modified']}")
            raise AssertionError(
                f"Legacy ChromaDB isolation violated: "
                f"{len(differences['added'])} added, "
                f"{len(differences['removed'])} removed, "
                f"{len(differences['modified'])} modified"
            )
        else:
            logger.info("Legacy ChromaDB directory unchanged - isolation verified")
    else:
        logger.info("No previous snapshot found - creating baseline")
    
    # Rename current snapshot to previous for next run
    if snapshot_path.exists():
        if previous_snapshot.exists():
            previous_snapshot.unlink()
        snapshot_path.rename(previous_snapshot)
    
    assert True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    test_legacy_chroma_isolation()
