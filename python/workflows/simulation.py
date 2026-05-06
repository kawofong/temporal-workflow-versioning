import asyncio
import logging
import os
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client
from temporalio.common import VersioningBehavior

with workflow.unsafe.imports_passed_through():
    from activities.transaction_auth import AuthRequest
    from workflows.card import CardWorkflow
    from workflows.transaction_auth import TransactionAuthWorkflow

NUM_CARD_ACCOUNTS = 3

MERCHANTS: list[tuple[str, str]] = [
    ("Whole Foods", "grocery"),
    ("Delta Airlines", "travel"),
    ("Starbucks", "dining"),
    ("Amazon", "retail"),
    ("Netflix", "entertainment"),
    ("Shell", "gas_station"),
    ("CVS Pharmacy", "pharmacy"),
    ("Best Buy", "electronics"),
    ("Marriott Hotels", "travel"),
    ("Target", "retail"),
]


@workflow.defn(versioning_behavior=VersioningBehavior.AUTO_UPGRADE)
class SimulationWorkflow:
    """Long-running simulation that drives the worker-versioning demo.

    First run: spawns NUM_CARD_ACCOUNTS CardWorkflows (with ABANDON parent close policy)
    as the persistent account entities, then enters a loop that continuously
    generates card transactions by starting TransactionAuthWorkflow child
    workflows (with ABANDON parent close policy) against randomly chosen accounts.

    The list of account IDs is threaded through Continue-as-New so the
    one-time setup is not repeated on subsequent runs.
    """

    @workflow.run
    async def run(self, account_ids: list[str] | None = None) -> None:
        rng = workflow.random()

        # ── One-time setup: spawn the 10 persistent CardWorkflows ─────────
        if not account_ids:
            account_ids = [str(workflow.uuid4()) for i in range(NUM_CARD_ACCOUNTS)]
            for account_id in account_ids:
                await workflow.start_child_workflow(
                    CardWorkflow.run,
                    args=[account_id],
                    id=f"card/{account_id}",
                    parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                )
            workflow.logger.info(
                f"Simulation initialized — spawned {len(account_ids)} CardWorkflows: "
                + ", ".join(account_ids)
            )

        # ── Transaction generation loop ───────────────────────────────────
        tx_counter = 0
        while not workflow.info().is_continue_as_new_suggested():
            # Slowing down the simulation for demo purposes
            if tx_counter % NUM_CARD_ACCOUNTS == 0:
                await workflow.sleep(timedelta(seconds=1))

            account_id = rng.choice(account_ids)
            merchant_name, merchant_category = rng.choice(MERCHANTS)
            amount = round(rng.uniform(10.0, 600.0), 2)
            tx_id = f"transaction/auth/{str(workflow.uuid4())}"

            await workflow.start_child_workflow(
                TransactionAuthWorkflow.run,
                args=[
                    AuthRequest(
                        card_id=account_id,
                        merchant_name=merchant_name,
                        merchant_category=merchant_category,
                        amount=amount,
                    )
                ],
                id=tx_id,
                parent_close_policy=workflow.ParentClosePolicy.ABANDON,
            )

            workflow.logger.info(
                f"Transaction {tx_counter} dispatched — id={tx_id} "
                f"card={account_id} merchant={merchant_name!r} amount=${amount:.2f}"
            )
            tx_counter += 1

        # ── Continue-as-New: preserve account IDs, skip setup ────────────
        workflow.logger.info(
            f"CaN suggested after {tx_counter} transactions — "
            f"continuing with {len(account_ids)} accounts"
        )
        workflow.continue_as_new(args=[account_ids])


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    task_queue = os.environ.get("TASK_QUEUE", "card-task-queue")
    workflow_id = "simulation/started-by-simulation-py"

    client = await Client.connect(address, namespace=namespace)

    _ = await client.start_workflow(
        SimulationWorkflow.run,
        id=workflow_id,
        task_queue=task_queue,
    )

    logging.info(f"Started SimulationWorkflow — workflow_id={workflow_id}")


if __name__ == "__main__":
    asyncio.run(main())
