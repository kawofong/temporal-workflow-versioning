"""Replay tests for TransactionDisputeWorkflow (AUTO_UPGRADE + patching)."""

import pytest
from temporalio.worker import Replayer
from tests.conftest import load_history
from workflows.transaction_dispute import TransactionDisputeWorkflow


@pytest.mark.asyncio
async def test_transaction_dispute_replay():
    """Replay test: customer did not initiate a dispute."""
    history = load_history("transaction-dispute-customer-no-dispute.json")
    replayer = Replayer(workflows=[TransactionDisputeWorkflow])
    await replayer.replay_workflow(history)


@pytest.mark.asyncio
async def test_transaction_dispute_replay_merchant_no_response():
    """Replay test: customer initiated a dispute, and merchant did not respond."""
    history = load_history("transaction-dispute-merchant-no-response.json")
    replayer = Replayer(workflows=[TransactionDisputeWorkflow])
    await replayer.replay_workflow(history)


@pytest.mark.asyncio
async def test_transaction_dispute_replay_unauthorized():
    """Replay test: customer initiated a dispute, won with 'unauthorized' reason."""
    history = load_history("transaction-dispute-unauthorized.json")
    replayer = Replayer(workflows=[TransactionDisputeWorkflow])
    await replayer.replay_workflow(history)
