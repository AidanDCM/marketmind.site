#!/usr/bin/env python3
"""
Phase 2 Backtest Runner
-----------------------
Runs internal health probes and prints a JSON summary suitable for CI logs.
This does not require the API server; it executes probe functions in-process.

Outputs:
- overall ok flag
- counts and names of failing checks
- per-check messages (no secrets)

Exit codes:
- 0 if all checks are healthy
- 1 if any check fails or an unexpected error occurs
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        from packages.shared.health.probes import get_all_health_checks
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Failed to import probes: {e}"}), file=sys.stderr)
        return 1

    try:
        result = get_all_health_checks()
        checks = result.get("checks", {})
        failing = [name for name, r in checks.items() if not r.get("status", False)]
        summary = {
            "ok": result.get("ok", False),
            "total_checks": len(checks),
            "failing_count": len(failing),
            "failing": failing,
            "timestamp": result.get("timestamp"),
        }
        print(json.dumps({"summary": summary, "checks": checks}, indent=2))
        return 0 if summary["ok"] else 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Probe execution error: {e}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
