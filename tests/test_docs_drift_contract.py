"""Phase B pass 28 (rotation 4): docs drift contract parity and deeper coverage."""

from __future__ import annotations

import re

import pytest

from marketmind.docs_contract import (
    CURRENT_HARDENING_PASS,
    CURRENT_HARDENING_PHASE_LABEL,
    DOCS_DRIFT_TEST_FILES,
    ENGINEERING_LOG_DIR,
    MIN_PYTEST_CASES,
    MIN_VITEST_FILES,
    OPERATOR_INVENTORY_DOC_PATHS,
    PHASE_B_ROTATION_3_CONTRACTS,
    PHASE_B_ROTATION_3_PASS_END,
    PHASE_B_ROTATION_3_PASS_START,
    PHASE_B_ROTATION_4_CONTRACTS,
    PHASE_B_ROTATION_4_ENGINEERING_LOG_SUFFIX,
    PHASE_B_ROTATION_4_PASS_END,
    PHASE_B_ROTATION_4_PASS_START,
    REPO_ROOT,
    STALE_PYTEST_INVENTORY,
)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("theme", "contract_path", "test_path"),
    PHASE_B_ROTATION_3_CONTRACTS,
    ids=[theme for theme, _, _ in PHASE_B_ROTATION_3_CONTRACTS],
)
def test_rotation_3_contract_files_exist_on_disk(
    theme: str, contract_path: str, test_path: str,
):
    assert (REPO_ROOT / contract_path).is_file(), contract_path
    assert (REPO_ROOT / test_path).is_file(), test_path
    assert theme in contract_path
    assert theme.replace("_", "") in test_path.replace("_", "")


def test_docs_drift_guard_files_exist_on_disk():
    for rel in DOCS_DRIFT_TEST_FILES:
        assert (REPO_ROOT / rel).is_file(), rel


def test_testing_manual_documents_rotation_3_pass_range():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    assert str(PHASE_B_ROTATION_3_PASS_START) in text
    assert str(PHASE_B_ROTATION_3_PASS_END) in text
    assert re.search(
        rf"passes {PHASE_B_ROTATION_3_PASS_START}[–-]{PHASE_B_ROTATION_3_PASS_END}|"
        rf"pass {PHASE_B_ROTATION_3_PASS_START}\+",
        text,
    )


def test_testing_manual_lists_rotation_3_contract_modules():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    for _theme, contract_path, _test_path in PHASE_B_ROTATION_3_CONTRACTS:
        module_name = contract_path.split("/")[-1].replace(".py", "")
        assert module_name in text, f"testing manual missing {module_name}"


def test_testing_manual_lists_rotation_3_contract_tests():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    for _theme, _contract_path, test_path in PHASE_B_ROTATION_3_CONTRACTS:
        test_name = test_path.split("/")[-1].replace(".py", "")
        assert test_name in text, f"testing manual missing {test_name}"


def test_testing_manual_documents_docs_drift_guard_files():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    for rel in DOCS_DRIFT_TEST_FILES:
        name = rel.split("/")[-1].replace(".py", "")
        assert name in text, f"testing manual missing {name}"
    assert "docs_contract.py" in text


def test_agents_and_slice_workflow_reference_docs_drift_guards():
    for rel in ("AGENTS.md", "SLICE_WORKFLOW.md"):
        text = _read(rel)
        assert "docs_contract" in text or "test_docs_drift" in text, rel


def test_operating_index_documents_docs_drift_guard():
    text = _read("OPERATING_INDEX.md")
    assert "test_docs_drift_contract" in text


@pytest.mark.parametrize("rel", OPERATOR_INVENTORY_DOC_PATHS)
def test_operator_inventory_docs_cite_current_pytest_minimum(rel: str):
    text = _read(rel)
    assert (
        str(MIN_PYTEST_CASES) in text
        or f"{MIN_PYTEST_CASES}+" in text
        or f"~{MIN_PYTEST_CASES}" in text
    )


def test_engineering_log_directory_has_readme():
    readme = REPO_ROOT / ENGINEERING_LOG_DIR / "README.md"
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")
    assert "append-only" in text.lower() or "per-entry" in text.lower()


def test_rotation_3_contract_count_matches_pass_range():
    pass_count = PHASE_B_ROTATION_3_PASS_END - PHASE_B_ROTATION_3_PASS_START + 1
    assert len(PHASE_B_ROTATION_3_CONTRACTS) == pass_count - 1
    # Pass 21 is docs drift (this file); passes 15–20 are the six theme contracts.


def test_owner_manual_documents_docs_drift_regression():
    text = _read("OWNER_MANUAL.md")
    assert "test_docs_drift" in text


@pytest.mark.parametrize(
    ("theme", "contract_path", "test_path"),
    PHASE_B_ROTATION_4_CONTRACTS,
    ids=[theme for theme, _, _ in PHASE_B_ROTATION_4_CONTRACTS],
)
def test_rotation_4_contract_files_exist_on_disk(
    theme: str, contract_path: str, test_path: str,
):
    assert (REPO_ROOT / contract_path).is_file(), contract_path
    assert (REPO_ROOT / test_path).is_file(), test_path
    assert theme in contract_path
    assert theme.replace("_", "") in test_path.replace("_", "")


def test_rotation_4_contract_count_matches_pass_range():
    pass_count = PHASE_B_ROTATION_4_PASS_END - PHASE_B_ROTATION_4_PASS_START + 1
    assert len(PHASE_B_ROTATION_4_CONTRACTS) == pass_count - 1


def test_testing_manual_documents_rotation_4_pass_range():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    assert str(PHASE_B_ROTATION_4_PASS_START) in text
    assert str(PHASE_B_ROTATION_4_PASS_END) in text
    assert re.search(
        rf"passes {PHASE_B_ROTATION_4_PASS_START}[–-]{PHASE_B_ROTATION_4_PASS_END}|"
        rf"pass {PHASE_B_ROTATION_4_PASS_START}\+",
        text,
    )


def test_testing_manual_lists_rotation_4_contract_modules():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    for _theme, contract_path, _test_path in PHASE_B_ROTATION_4_CONTRACTS:
        module_name = contract_path.split("/")[-1].replace(".py", "")
        assert module_name in text, f"testing manual missing {module_name}"


def test_testing_manual_lists_rotation_4_contract_tests():
    text = _read("docs/dev_manual/MARKETMIND_TESTING_AND_EVIDENCE.md")
    for _theme, _contract_path, test_path in PHASE_B_ROTATION_4_CONTRACTS:
        test_name = test_path.split("/")[-1].replace(".py", "")
        assert test_name in text, f"testing manual missing {test_name}"


def test_operating_index_documents_current_hardening_pass():
    text = _read("OPERATING_INDEX.md")
    assert str(CURRENT_HARDENING_PASS) in text
    assert CURRENT_HARDENING_PHASE_LABEL in text


def test_changelog_documents_rotation_4_bookend_passes():
    text = _read("CHANGELOG.md")
    assert f"pass {PHASE_B_ROTATION_4_PASS_START}" in text
    assert f"pass {PHASE_B_ROTATION_4_PASS_END - 1}" in text


@pytest.mark.parametrize("theme", [theme for theme, _, _ in PHASE_B_ROTATION_4_CONTRACTS])
def test_engineering_log_has_rotation_4_entry_per_theme(theme: str):
    log_dir = REPO_ROOT / ENGINEERING_LOG_DIR
    pattern = f"*{theme.replace('_', '-')}*{PHASE_B_ROTATION_4_ENGINEERING_LOG_SUFFIX}"
    matches = [path for path in log_dir.glob(pattern) if path.is_file()]
    assert matches, f"missing engineering log for rotation 4 theme {theme!r}"


def test_current_pytest_minimum_not_listed_as_stale():
    assert str(MIN_PYTEST_CASES) not in STALE_PYTEST_INVENTORY


@pytest.mark.parametrize("rel", OPERATOR_INVENTORY_DOC_PATHS)
def test_operator_inventory_docs_cite_current_vitest_minimum(rel: str):
    text = _read(rel)
    assert (
        str(MIN_VITEST_FILES) in text
        or f"{MIN_VITEST_FILES}+" in text
        or f"~{MIN_VITEST_FILES}" in text
    )
