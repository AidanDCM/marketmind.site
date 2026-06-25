"""Phase B pass 14 (rotation 2): docs drift hardening — deploy verify + inventory parity."""

from __future__ import annotations

import re
from pathlib import Path

from marketmind.deploy_ci_contract import (
    CI_DEPLOY_VERIFY_ENDPOINTS,
    CI_DEPLOY_VERIFY_SCRIPTS,
    INTEGRATIONS_SECRET_LEAK_MARKERS,
)
from marketmind.docs_contract import (
    DEPLOYMENT_DOC_PATH,
    OPERATOR_DOC_PATHS,
    REPO_ROOT,
    STALE_PYTEST_INVENTORY,
    STALE_VITEST_INVENTORY,
)

DEPLOYMENT = REPO_ROOT / DEPLOYMENT_DOC_PATH
TESTING_MANUAL = REPO_ROOT / "docs" / "dev_manual" / "MARKETMIND_TESTING_AND_EVIDENCE.md"
OWNER_MANUAL = REPO_ROOT / "OWNER_MANUAL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _operator_doc_texts() -> list[tuple[str, str]]:
    return [(rel, _read(REPO_ROOT / rel)) for rel in OPERATOR_DOC_PATHS]


def test_active_operator_docs_have_no_stale_pytest_inventory():
    for rel, text in _operator_doc_texts():
        for stale in STALE_PYTEST_INVENTORY:
            assert stale not in text, f"{rel} still cites stale pytest inventory {stale!r}"


def test_active_operator_docs_have_no_stale_vitest_inventory():
    for rel, text in _operator_doc_texts():
        for stale in STALE_VITEST_INVENTORY:
            assert stale not in text, f"{rel} still cites stale Vitest inventory {stale!r}"


def test_deployment_documents_all_verify_endpoints():
    text = _read(DEPLOYMENT)
    for endpoint in CI_DEPLOY_VERIFY_ENDPOINTS:
        assert endpoint in text, f"DEPLOYMENT.md missing deploy-verify endpoint {endpoint!r}"


def test_deployment_documents_integrations_secret_leak_check():
    text = _read(DEPLOYMENT)
    assert "/operator/integrations" in text
    assert "secret" in text.lower() or "forbidden" in text.lower()
    assert any(marker in text for marker in INTEGRATIONS_SECRET_LEAK_MARKERS[:2])


def test_owner_manual_verify_deploy_documents_integrations():
    text = _read(OWNER_MANUAL)
    assert "verify_marketmind_deploy.py" in text
    assert "integrations" in text.lower()


def test_testing_manual_documents_deploy_ci_contract():
    text = _read(TESTING_MANUAL)
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert script.replace("scripts/", "") in text or script in text
    for endpoint in CI_DEPLOY_VERIFY_ENDPOINTS:
        assert endpoint in text, f"testing manual missing {endpoint!r}"
    assert "deploy_ci_contract" in text
    assert "test_docs_drift_hardening.py" in text


def test_testing_manual_phase_b_rotation_2_contract_modules():
    text = _read(TESTING_MANUAL)
    assert "Rotation 2" in text
    assert "deploy_ci_contract" in text
    assert re.search(r"passes 8.14|passes 8–14", text), (
        "testing manual missing Phase B rotation 2 pass range"
    )
