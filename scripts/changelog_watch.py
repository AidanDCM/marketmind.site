#!/usr/bin/env python3
"""
Changelog Watcher
-----------------
Polls the repository every few seconds and appends verbose, labeled entries to
CHANGELOG.md when file changes are detected.

Usage:
    python scripts/changelog_watch.py --interval 5

Notes for future developers:
- Purpose: automate continuous documentation during active development.
- Entry points: Makefile target `changelog-watch`.
- Config: interval via --interval; excludes common transient dirs.
- Dependencies: standard library only (no extra installs).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
EXCLUDES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "dev.db",
    "htmlcov",
    ".coverage",
    "coverage.xml",
    "alembic/versions",
}

# File globs to ignore by suffix
IGNORE_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".log",
    ".sqlite3",
)


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        # Skip excluded directories
        parts = set(Path(rel_dir).parts)
        if any(ex in parts for ex in EXCLUDES if ex):
            # Prune traversal by clearing dirnames
            dirnames[:] = []
            continue
        for fname in filenames:
            if fname.endswith(IGNORE_SUFFIXES):
                continue
            fpath = Path(dirpath) / fname
            yield fpath


def snapshot_hash(root: Path) -> str:
    """Create a lightweight hash snapshot of file mtimes and sizes."""
    h = hashlib.sha256()
    for f in sorted(iter_files(root)):
        try:
            st = f.stat()
        except FileNotFoundError:
            continue
        h.update(str(f.relative_to(root)).encode())
        h.update(str(st.st_mtime_ns).encode())
        h.update(str(st.st_size).encode())
    return h.hexdigest()


def list_changed_files(prev_map: dict[str, float] | None, root: Path) -> list[Path]:
    """Return files that changed mtime since last map."""
    changed: list[Path] = []
    new_map: dict[str, float] = {}
    for f in iter_files(root):
        try:
            mt = f.stat().st_mtime
        except FileNotFoundError:
            continue
        rel = str(f.relative_to(root))
        new_map[rel] = mt
        if not prev_map or prev_map.get(rel) != mt:
            changed.append(f)
    return changed


def append_changelog(changed: list[Path]):
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = []
    lines.append(f"\n## [{now}] Automated update by changelog_watch.py")
    lines.append("")
    lines.append("### Labeled Components")
    for f in sorted(changed):
        rel = f.relative_to(REPO_ROOT)
        # Basic heuristic labels
        if "apps/hive_api/routers" in str(rel):
            comp = "API Router"
        elif "packages/shared" in str(rel):
            comp = "Shared Library"
        elif "packages/database/models" in str(rel):
            comp = "Database Model"
        elif "scripts/" in str(rel):
            comp = "Developer Script"
        elif "infra/" in str(rel):
            comp = "Infrastructure"
        elif rel.name == "Makefile":
            comp = "Build/Tasks"
        else:
            comp = "General"
        lines.append(f"- {comp}: `{rel}`")

    lines.append("")
    lines.append("### Changes Detected")
    lines.append("- Files modified since last check:")
    for f in sorted(changed):
        rel = f.relative_to(REPO_ROOT)
        try:
            st = f.stat()
            size = st.st_size
        except FileNotFoundError:
            size = -1
        lines.append(f"  - `{rel}` (size={size} bytes)")

    lines.append("")
    lines.append("### Notes for Future Developers")
    lines.append("- Purpose: Continuous documentation of active edits.")
    lines.append("- Entry points: `Makefile` target `changelog-watch`.")
    lines.append(
        "- If this section is too noisy, increase the interval or limit directories in EXCLUDES."
    )

    with CHANGELOG.open("a", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Append verbose changelog entries on file changes")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    args = parser.parse_args()

    print(f"[changelog-watch] Watching {REPO_ROOT} every {args.interval}s. Writing to {CHANGELOG}.")

    prev_map: dict[str, float] | None = None
    prev_hash = None
    try:
        while True:
            # Compare snapshot
            cur_hash = snapshot_hash(REPO_ROOT)
            if prev_hash is None:
                prev_hash = cur_hash
                prev_map = {
                    str(p.relative_to(REPO_ROOT)): p.stat().st_mtime for p in iter_files(REPO_ROOT)
                }
                time.sleep(args.interval)
                continue
            if cur_hash != prev_hash:
                changed = list_changed_files(prev_map, REPO_ROOT)
                if changed:
                    append_changelog(changed)
                    # Refresh map
                    prev_map = {
                        str(p.relative_to(REPO_ROOT)): p.stat().st_mtime
                        for p in iter_files(REPO_ROOT)
                    }
                    prev_hash = cur_hash
                    print(f"[changelog-watch] Appended entry for {len(changed)} changed files.")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[changelog-watch] Stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
