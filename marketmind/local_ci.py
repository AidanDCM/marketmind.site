"""Offline CI core — pure logic for local verification gate.

Mirrors `.github/workflows/ci.yml` backend steps so agents can record evidence
without relying on hosted minutes. Side-effect free for unit testing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

CI_STEPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pip_upgrade", ("python", "-m", "pip", "install", "--upgrade", "pip")),
    ("install_dependencies", ("python", "-m", "pip", "install", "-e", ".[dev]")),
    ("ruff", ("python", "-m", "ruff", "check", ".")),
    ("pytest", ("python", "-m", "pytest", "-q", "--tb=short")),
)

FULL_CI_EXTRA: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "deploy_verify",
        (
            "python",
            "scripts/verify_marketmind_deploy.py",
        ),
    ),
)

STATUS_CONTEXT = "marketmind-local-ci"


@dataclass(frozen=True)
class StepResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    duration_s: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def aggregate_ok(results: Sequence[StepResult]) -> bool:
    return bool(results) and all(r.ok for r in results)


def overall_state(results: Sequence[StepResult]) -> str:
    return "success" if aggregate_ok(results) else "failure"


def status_description(results: Sequence[StepResult]) -> str:
    if not results:
        return "marketmind-local-ci: no steps ran"
    failed = [r.name for r in results if not r.ok]
    if failed:
        return f"marketmind-local-ci FAIL: {', '.join(failed)}"[:140]
    return f"marketmind-local-ci PASS: {', '.join(r.name for r in results)}"[:140]


def format_test_log_entry(
    *,
    timestamp: str,
    branch: str,
    commit: str,
    python: str,
    results: Sequence[StepResult],
    follow_up: str = "",
) -> str:
    lines = [
        f"## {timestamp}",
        f"- Branch: {branch}",
        f"- Commit: {commit}",
        f"- Environment: marketmind-local-ci, Python {python}",
        f"- Result: {'PASS' if aggregate_ok(results) else 'FAIL'}",
        "- Commands:",
    ]
    for r in results:
        verdict = "ok" if r.ok else f"FAILED (exit {r.returncode})"
        lines.append(f"  - `{' '.join(r.command)}` — {verdict} ({r.duration_s:.1f}s)")
    failed = [r.name for r in results if not r.ok]
    failure_note = "none" if not failed else f"see {', '.join(failed)} above"
    lines.append(f"- Failure output: {failure_note}")
    lines.append(f"- Follow-up: {follow_up or 'none'}")
    return "\n".join(lines) + "\n"
