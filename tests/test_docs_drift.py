"""Phase B pass 7: operator docs must match code and suite inventory."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from marketmind.docs_contract import (
    CANONICAL_SHOPIFY_DOMAIN,
    CANONICAL_SHOPIFY_TOKEN_NAMES,
    CANONICAL_STRIPE_ENV_NAMES,
    MIN_PYTEST_CASES,
    MIN_VITEST_FILES,
    REPO_ROOT,
    STALE_ENV_VAR_NAMES,
)
from marketmind.local_ci import FULL_CI_EXTRA

OWNER_MANUAL = REPO_ROOT / "OWNER_MANUAL.md"
OPERATING_INDEX = REPO_ROOT / "OPERATING_INDEX.md"
TESTING_MANUAL = REPO_ROOT / "docs" / "dev_manual" / "MARKETMIND_TESTING_AND_EVIDENCE.md"
AGENTS_MD = REPO_ROOT / "AGENTS.md"
SLICE_WORKFLOW = REPO_ROOT / "SLICE_WORKFLOW.md"
DEPLOYMENT = REPO_ROOT / "docs" / "DEPLOYMENT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _vitest_file_count() -> int:
    src = REPO_ROOT / "desktop" / "src"
    return len(list(src.rglob("*.test.ts"))) + len(list(src.rglob("*.test.tsx")))


def test_owner_manual_uses_canonical_env_names():
    text = _read(OWNER_MANUAL)
    for stale in STALE_ENV_VAR_NAMES:
        assert stale not in text, f"OWNER_MANUAL still references stale env var {stale!r}"
    assert any(name in text for name in CANONICAL_STRIPE_ENV_NAMES)
    assert CANONICAL_SHOPIFY_DOMAIN in text
    assert any(name in text for name in CANONICAL_SHOPIFY_TOKEN_NAMES)


def test_owner_manual_status_is_hardening_not_slice_building():
    text = _read(OWNER_MANUAL)
    assert "Building (active slice development)" not in text
    assert "Hardening" in text


def test_operating_index_test_inventory_matches_contract():
    text = _read(OPERATING_INDEX)
    pytest_match = re.search(r"~(\d+) pytest", text)
    vitest_match = re.search(r"(\d+) desktop Vitest", text)
    assert pytest_match, "OPERATING_INDEX missing ~N pytest inventory line"
    assert vitest_match, "OPERATING_INDEX missing N desktop Vitest inventory line"
    assert int(pytest_match.group(1)) >= MIN_PYTEST_CASES
    assert int(vitest_match.group(1)) >= MIN_VITEST_FILES


def test_agents_and_slice_workflow_test_counts_current():
    for path in (AGENTS_MD, SLICE_WORKFLOW):
        text = _read(path)
        assert "465" not in text, f"{path.name} still cites 465 pytest cases"
        assert str(MIN_PYTEST_CASES) in text or f"{MIN_PYTEST_CASES}+" in text


def test_testing_manual_inventory_current():
    text = _read(TESTING_MANUAL)
    assert str(MIN_PYTEST_CASES) in text
    assert str(MIN_VITEST_FILES) in text
    assert "local_ci.py --full" in text
    assert "check_operator_readiness.py --api" in text


def test_deployment_post_deploy_mentions_both_verifiers():
    text = _read(DEPLOYMENT)
    assert "verify_marketmind_deploy.py" in text
    assert "check_operator_readiness.py --api" in text


def test_local_ci_full_documented_in_testing_manual():
    names = [name for name, _ in FULL_CI_EXTRA]
    assert names == ["deploy_verify", "operator_readiness_api"]
    text = _read(TESTING_MANUAL)
    assert "deploy_verify" in text or "verify_marketmind_deploy" in text
    assert "operator_readiness" in text or "check_operator_readiness" in text


def test_pytest_collection_meets_documented_minimum():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    last = proc.stdout.strip().splitlines()[-1]
    count = int(last.split()[0])
    assert count >= MIN_PYTEST_CASES


def test_vitest_file_count_meets_documented_minimum():
    assert _vitest_file_count() >= MIN_VITEST_FILES
