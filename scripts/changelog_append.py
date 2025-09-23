#!/usr/bin/env python3
"""
Changelog Append Helper
-----------------------
Appends a structured entry to CHANGELOG.md with a title and optional JSON payload.

Usage:
  python scripts/changelog_append.py --title "Phase 2 Backtest" --data '{"ok": true}'
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a structured changelog entry")
    parser.add_argument("--title", required=True, help="Section title")
    parser.add_argument("--data", help="JSON string payload to include as code block")
    args = parser.parse_args()

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append(f"\n## [{now}] {args.title}")
    if args.data:
        try:
            parsed = json.loads(args.data)
            payload = json.dumps(parsed, indent=2, sort_keys=True)
        except Exception:
            payload = args.data
        lines.append("")
        lines.append("```json")
        lines.append(payload)
        lines.append("```")
    with CHANGELOG.open("a", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"[changelog-append] Wrote entry: {args.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
