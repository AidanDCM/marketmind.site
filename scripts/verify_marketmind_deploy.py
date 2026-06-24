#!/usr/bin/env python3
"""Post-deploy verification for MarketMind API."""

from __future__ import annotations

import os
import sys

from marketmind.deploy_verify import verify_marketmind_deploy


def main() -> int:
    base = os.environ.get("MARKETMIND_API_BASE", "http://127.0.0.1:8000")
    token = os.environ.get("MARKETMIND_API_TOKEN") or None
    result = verify_marketmind_deploy(base, token)
    for line in result.lines:
        if line.startswith("FAIL"):
            print(line, file=sys.stderr)
        else:
            print(line)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
