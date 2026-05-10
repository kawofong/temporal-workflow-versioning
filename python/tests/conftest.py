"""Shared fixtures and helpers for Temporal replay tests."""

import json
import pathlib
import uuid

import pytest
from temporalio.client import WorkflowHistory

HISTORIES_DIR = pathlib.Path(__file__).parent / "histories"


def load_history(filename: str) -> WorkflowHistory:
    """Load a workflow history JSON and return a WorkflowHistory.

    Skips the calling test with a clear message if the file does not exist yet,
    so the suite stays green while history files are being collected.
    """
    path = HISTORIES_DIR / filename
    if not path.exists():
        pytest.skip(
            f"History file not yet captured — save a downloaded history to: "
            f"{path.relative_to(pathlib.Path.cwd(), walk_up=True)}"
        )
    with path.open() as f:
        raw = json.load(f)
    return WorkflowHistory.from_json(str(uuid.uuid4()), raw)


@pytest.fixture
def histories_dir() -> pathlib.Path:
    """Absolute path to the histories directory."""
    return HISTORIES_DIR
