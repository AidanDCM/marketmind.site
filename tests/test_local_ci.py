"""Meta-tests: local CI steps stay aligned with GitHub Actions."""

from pathlib import Path

from marketmind.local_ci import (
    CI_DEPLOY_VERIFY_SCRIPTS,
    CI_STEPS,
    FULL_CI_EXTRA,
    StepResult,
    aggregate_ok,
    format_test_log_entry,
    overall_state,
    status_description,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_local_ci_steps_include_ruff_and_pytest():
    names = [name for name, _ in CI_STEPS]
    assert "ruff" in names
    assert "pytest" in names
    assert names.index("ruff") < names.index("pytest")


def test_full_ci_extra_matches_github_deploy_verify_job():
    extra_names = [name for name, _ in FULL_CI_EXTRA]
    assert extra_names == ["deploy_verify", "operator_readiness_api"]
    commands = [" ".join(cmd) for _, cmd in FULL_CI_EXTRA]
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert script in workflow
        assert any(script in cmd for cmd in commands)


def test_deploy_verify_scripts_exist_on_disk():
    for script in CI_DEPLOY_VERIFY_SCRIPTS:
        assert (REPO_ROOT / script).is_file()


def test_aggregate_ok_requires_all_steps_pass():
    ok = StepResult("ruff", ("python", "-m", "ruff"), 0, 0.1)
    bad = StepResult("pytest", ("python", "-m", "pytest"), 1, 1.0)
    assert aggregate_ok([ok, ok]) is True
    assert aggregate_ok([ok, bad]) is False
    assert aggregate_ok([]) is False


def test_overall_state_and_description():
    ok = StepResult("ruff", ("python", "-m", "ruff"), 0, 0.1)
    bad = StepResult("pytest", ("python", "-m", "pytest"), 1, 1.0)
    assert overall_state([ok]) == "success"
    assert overall_state([bad]) == "failure"
    assert "PASS" in status_description([ok])
    assert "pytest" in status_description([ok, bad])


def test_format_test_log_entry_lists_commands_and_failures():
    results = [
        StepResult("ruff", ("python", "-m", "ruff", "check", "."), 0, 0.2),
        StepResult("pytest", ("python", "-m", "pytest", "-q"), 1, 3.5),
    ]
    entry = format_test_log_entry(
        timestamp="2026-06-24T12:00:00Z",
        branch="main",
        commit="abc123",
        python="3.12.0",
        results=results,
        follow_up="fix pytest",
    )
    assert "FAIL" in entry
    assert "pytest" in entry
    assert "fix pytest" in entry
    assert "FAILED (exit 1)" in entry
