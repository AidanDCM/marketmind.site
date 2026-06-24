"""Meta-tests: local CI steps stay aligned with GitHub Actions."""

from marketmind.local_ci import CI_STEPS


def test_local_ci_steps_include_ruff_and_pytest():
    names = [name for name, _ in CI_STEPS]
    assert "ruff" in names
    assert "pytest" in names
    assert names.index("ruff") < names.index("pytest")
