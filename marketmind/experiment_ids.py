"""Experiment ID naming and validation."""

from __future__ import annotations

import re

# exp_<slug>: lowercase letters, digits, underscores, hyphens; 3–64 chars after prefix.
_EXPERIMENT_ID_RE = re.compile(r"^exp_[a-z0-9][a-z0-9_-]{1,62}$")


def validate_experiment_id(experiment_id: str) -> str:
    """Return a normalized experiment_id or raise ValueError."""
    value = experiment_id.strip()
    if not value:
        raise ValueError("experiment_id must not be empty")
    if not _EXPERIMENT_ID_RE.match(value):
        raise ValueError(
            "experiment_id must match exp_<slug> "
            "(lowercase letters, digits, underscores, hyphens; e.g. exp_interior_kit)"
        )
    return value
