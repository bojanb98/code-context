from pathlib import Path

from .scanner import _sha256_of_file
from .types import DetectedChanges, FileRecord


async def compare_snapshot_to_current(
    root: Path,
    old_files: dict[str, FileRecord],
    current_meta: dict[str, tuple[int, float, int | None]],
) -> DetectedChanges:
    """Compare old snapshot vs current metadata. Conservative: never miss a modification.

    Returns DetectedChanges with lists of relative paths.
    """
    old_paths: set[str] = set(old_files.keys())
    new_paths: set[str] = set(current_meta.keys())

    added = sorted(list(new_paths - old_paths))
    removed = sorted(list(old_paths - new_paths))
    common = sorted(list(old_paths & new_paths))

    modified: list[str] = []

    # For common paths: if metadata changed -> compute hash and compare
    for p in common:
        size, mtime, inode = current_meta[p]
        old = old_files[p]
        if old.size == size and old.mtime == mtime and old.inode == inode:
            continue
        # metadata changed; compute current hash and compare
        curr_hash = _sha256_of_file(root / p)
        if curr_hash != old.hash:
            modified.append(p)
        # else: metadata changed but content same -> treat as unchanged

    # Attempt rename/move detection for added/removed pairs
    added_set: set[str] = set(added)
    removed_set: set[str] = set(removed)

    # Build old inode -> path and old hash -> path maps
    old_inode_map: dict[int, str] = {}
    old_hash_map: dict[str, str] = {}
    for path, rec in old_files.items():
        if rec.inode is not None:
            old_inode_map[rec.inode] = path
        old_hash_map[rec.hash] = path

    # 1) inode-based detection (verify content if metadata differs)
    to_remove_added: set[str] = set()
    to_remove_removed: set[str] = set()

    for new_p in list(added_set):
        _, _, new_inode = current_meta[new_p]
        if new_inode is None:
            continue
        old_p = old_inode_map.get(new_inode)
        if not old_p:
            continue
        # we found a candidate; must ensure content same to avoid missing modifications
        old_rec = old_files[old_p]
        curr_hash = _sha256_of_file(root / new_p)
        if curr_hash == old_rec.hash:
            to_remove_added.add(new_p)
            to_remove_removed.add(old_p)
        else:
            # inode same but content changed -> treat as modification of old path if the path still present?
            # Conservative approach: mark new_p as modified (appeared changed) and keep removed old_p as removed
            modified.append(new_p)

    added_set -= to_remove_added
    removed_set -= to_remove_removed

    # 2) hash-based detection (for remaining added)
    removed_hashes = {old_files[p].hash: p for p in removed_set}
    to_remove_added = set()
    to_remove_removed = set()
    for new_p in list(added_set):
        curr_hash = _sha256_of_file(root / new_p)
        old_p = removed_hashes.get(curr_hash)
        if old_p:
            to_remove_added.add(new_p)
            to_remove_removed.add(old_p)

    added_set -= to_remove_added
    removed_set -= to_remove_removed

    # Final lists
    final_added = sorted(list(added_set))
    final_removed = sorted(list(removed_set))
    # deduplicate modified
    modified = sorted(list(dict.fromkeys(modified)))

    return DetectedChanges(added=final_added, modified=modified, removed=final_removed)
