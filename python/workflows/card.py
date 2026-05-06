"""Start a CardWorkflow and send sample transactions via signals.

To start a CardWorkflow, run:
    uv run -m workflows.card

Environment variables:
    TEMPORAL_ADDRESS    Temporal server address (default: localhost:7233)
    TEMPORAL_NAMESPACE  Temporal namespace (default: default)
    TASK_QUEUE          Task queue name (default: card-task-queue)
    ACCOUNT_ID          Card account ID (default: ACC-001)
"""

import asyncio
import logging
import os
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client
from temporalio.common import VersioningBehavior
from temporalio.workflow import ContinueAsNewVersioningBehavior

with workflow.unsafe.imports_passed_through():
    from activities.card import (
        Statement,
        Transaction,
        generate_statement,
        persist_statement,
        send_statement_notification,
    )

# Compressed to 30 seconds for demo purposes (represents one monthly billing cycle).
BILLING_CYCLE_DURATION = timedelta(seconds=30)

# CaN threshold kept low for demo purposes; production would use the Temporal
# default (~10 000 events) or workflow.info().is_continue_as_new_suggested().
MAX_HISTORY_EVENTS = 50


@workflow.defn(versioning_behavior=VersioningBehavior.PINNED)
class CardWorkflow:
    """Long-running entity workflow — one instance per card account.

    Each run covers one billing cycle. Continue-as-New resets the history at
    the end of each run once the event threshold is reached.  When a new Worker
    Deployment Version is available, the workflow upgrades to it at the
    Continue-as-New boundary without patching.
    """

    def __init__(self) -> None:
        self._pending_transactions: list[Transaction] = []
        self.rewards_points: int = 0

    # -------------------------------------------------------------------------
    # Signal handler
    # -------------------------------------------------------------------------

    @workflow.signal
    def record_transaction(self, transaction: Transaction) -> None:
        """Record a card transaction to be included in the current billing cycle."""
        workflow.logger.info(
            f"Transaction received: ${transaction.amount:.2f} at {transaction.merchant}"
        )
        self._pending_transactions.append(transaction)

    # -------------------------------------------------------------------------
    # Query handlers
    # -------------------------------------------------------------------------

    @workflow.query
    def get_rewards_points(self) -> int:
        """Return rewards points accumulated so far."""
        return self.rewards_points

    # -------------------------------------------------------------------------
    # Main run loop
    # -------------------------------------------------------------------------

    @workflow.run
    async def run(
        self, account_id: str, cycle: int = 1, rewards_points: int = 0
    ) -> None:
        self.rewards_points = rewards_points
        while True:
            workflow.logger.info(
                f"Billing cycle {cycle} started for account {account_id} "
            )

            # Wait for the end of this billing cycle.
            await workflow.sleep(BILLING_CYCLE_DURATION)

            # Snapshot and clear the transaction buffer for this cycle.
            transactions = list(self._pending_transactions)
            self._pending_transactions.clear()

            statement: Statement = await workflow.execute_activity(
                generate_statement,
                args=[account_id, cycle, transactions],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # TODO (v2): store statement in a object storage
            await workflow.execute_activity(
                persist_statement,
                args=[statement],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Calculate rewards points
            self.rewards_points += int(statement.total_spend)

            await workflow.execute_activity(
                send_statement_notification,
                args=[statement, self.rewards_points],
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info(
                f"Billing cycle {cycle} complete — "
                f"spend=${statement.total_spend:.2f}, rewards={self.rewards_points} pts, "
                f"history_length={workflow.info().get_current_history_length()}"
            )

            cycle += 1

            if self._should_continue_as_new():
                self._do_continue_as_new(account_id, cycle)

    def _should_continue_as_new(self) -> bool:
        info = workflow.info()
        return (
            info.get_current_history_length() >= MAX_HISTORY_EVENTS
            or info.is_target_worker_deployment_version_changed()
        )

    def _do_continue_as_new(self, account_id: str, cycle: int) -> None:
        """Raise ContinueAsNew, upgrading to the new deployment version if available."""
        if workflow.info().is_target_worker_deployment_version_changed():
            workflow.logger.info(
                f"New deployment version available — upgrading at cycle {cycle} CaN boundary"
            )
            workflow.continue_as_new(
                args=[account_id, cycle, self.rewards_points],
                initial_versioning_behavior=ContinueAsNewVersioningBehavior.AUTO_UPGRADE,
            )
        else:
            workflow.logger.info(
                f"History threshold reached — resetting history at cycle {cycle} CaN boundary"
            )
            workflow.continue_as_new(args=[account_id, cycle, self.rewards_points])


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    task_queue = os.environ.get("TASK_QUEUE", "card-task-queue")
    account_id = os.environ.get("ACCOUNT_ID", "ACC-001")
    workflow_id = f"card-{account_id}"

    client = await Client.connect(address, namespace=namespace)

    handle = await client.start_workflow(
        CardWorkflow.run,
        args=[account_id],
        id=workflow_id,
        task_queue=task_queue,
    )

    logging.info(f"Started CardWorkflow — workflow_id={workflow_id}")

    # Send sample transactions as signals to simulate card activity.
    SAMPLE_TRANSACTIONS = [
        Transaction(amount=42.50, merchant="Whole Foods"),
        Transaction(amount=15.00, merchant="Netflix"),
        Transaction(amount=120.00, merchant="Delta Airlines"),
        Transaction(amount=8.75, merchant="Starbucks"),
    ]
    for txn in SAMPLE_TRANSACTIONS:
        await handle.signal(CardWorkflow.record_transaction, txn)
        logging.info(f"Signalled transaction: ${txn.amount:.2f} at {txn.merchant}")

    count = await handle.query(CardWorkflow.get_rewards_points)
    logging.info(f"Rewards points accumulated so far: {count}")


if __name__ == "__main__":
    asyncio.run(main())
