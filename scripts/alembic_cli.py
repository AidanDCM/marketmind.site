#!/usr/bin/env python3
"""
Alembic CLI wrapper to avoid local 'alembic/' package shadowing.

It temporarily removes the project root and empty path ('') from sys.path so the
site-packages Alembic package can be imported, then restores sys.path and
delegates to Alembic's CLI entrypoint.

Usage: python scripts/alembic_cli.py -c alembic.ini <command> [options]
"""

import os
import sys


def _pop_local_paths(paths):
    removed = []
    new_paths = []
    for p in paths:
        # Remove empty/current-dir and the project root to avoid shadowing package 'alembic'
        if p in ("", ".", os.getcwd()):
            removed.append(p)
            continue
        # Heuristic: if path ends with our project name and contains '/alembic.ini'
        # nearby, it's probably the project root. We remove it to avoid shadowing.
        new_paths.append(p)
    return new_paths, removed


# Remove '' and '.' to prevent importing local 'alembic' package
orig_sys_path = list(sys.path)
sys.path, _removed = _pop_local_paths(orig_sys_path)

from alembic.config import main  # type: ignore  # noqa: E402

# Restore sys.path (local imports needed by env.py should be resolved via prepend_sys_path=. in alembic.ini)
sys.path = orig_sys_path

if __name__ == "__main__":
    sys.exit(main())
