"""Replay tests for CardWorkflow (PINNED + CaN upgrade)."""

import pytest
from temporalio.worker import Replayer
from tests.conftest import load_history
from workflows.card import CardWorkflow


@pytest.mark.asyncio
async def test_card_workflow_replay_before_can():
    """Card Workflow before Continue-as-New."""
    history = load_history("card-workflow-before-can.json")
    replayer = Replayer(workflows=[CardWorkflow])
    await replayer.replay_workflow(history)


@pytest.mark.asyncio
async def test_card_workflow_replay_after_can():
    """Card Workflow after Continue-as-New."""
    history = load_history("card-workflow-can.json")
    replayer = Replayer(workflows=[CardWorkflow])
    await replayer.replay_workflow(history)
