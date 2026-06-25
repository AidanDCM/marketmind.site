"""Offline CI gate — run backend checks and append evidence to TEST_LOG.md.

Usage:
  python scripts/local_ci.py
  python scripts/local_ci.py --full   # deploy verify + operator readiness (API must be running)
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from marketmind.local_ci import (  # noqa: E402
    CI_STEPS,
    FULL_CI_EXTRA,
    StepResult,
    aggregate_ok,
    format_test_log_entry,
)

TEST_LOG_PATH = REPO_ROOT / "reports" / "local_ci" / "TEST_LOG.md"


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ("git", *args), cwd=REPO_ROOT, text=True, capture_output=True, check=False
        )
        return out.stdout.strip()
    except OSError:
        return ""


def _run_steps(steps: tuple[tuple[str, tuple[str, ...]], ...]) -> list[StepResult]:
    results: list[StepResult] = []
    for name, command in steps:
        argv = (sys.executable, *command[1:]) if command[0] == "python" else command
        print(f"\n==> {name}: {' '.join(argv)}", flush=True)
        started = monotonic()
        completed = subprocess.run(argv, cwd=REPO_ROOT, check=False)
        duration = monotonic() - started
        results.append(StepResult(name, tuple(argv), completed.returncode, duration))
        print(f"   {name}: exit {completed.returncode} ({duration:.1f}s)", flush=True)
    return results


def _write_test_log(results: list[StepResult], *, branch: str, commit: str) -> None:
    entry = format_test_log_entry(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        branch=branch or "unknown",
        commit=commit or "unknown",
        python=platform.python_version(),
        results=results,
    )
    TEST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not TEST_LOG_PATH.exists():
        TEST_LOG_PATH.write_text(
            "# MarketMind local CI test log\n\nAppend-only evidence. Do not edit past entries.\n\n",
            encoding="utf-8",
        )
    with TEST_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MarketMind local CI gate")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also run deploy verify (requires API at MARKETMIND_API_BASE)",
    )
    args = parser.parse_args()
    steps = CI_STEPS + (FULL_CI_EXTRA if args.full else ())
    results = _run_steps(steps)
    branch = _git("branch", "--show-current")
    commit = _git("rev-parse", "HEAD")
    _write_test_log(results, branch=branch, commit=commit)
    ok = aggregate_ok(results)
    print("\n" + ("PASS" if ok else "FAIL"), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
