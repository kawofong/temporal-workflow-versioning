"""Replay tests for TransactionAuthWorkflow (PINNED)."""

import pytest
from temporalio.worker import Replayer
from tests.conftest import load_history
from workflows.transaction_auth import TransactionAuthWorkflow


@pytest.mark.asyncio
async def test_transaction_auth_replay():
    """Transaction Authorization Workflow replay tests."""
    history = load_history("transaction-auth.json")
    replayer = Replayer(workflows=[TransactionAuthWorkflow])
    await replayer.replay_workflow(history)
