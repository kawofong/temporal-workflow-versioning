import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import VersioningBehavior

with workflow.unsafe.imports_passed_through():
    from activities.transaction_dispute import issue_provisional_credit  # TODO (v2)
    from activities.transaction_dispute import (
        DisputeEvaluation,
        DisputeReasonCode,
        DisputeRequest,
        DisputeResult,
        evaluate_dispute,
        finalize_dispute,
        notify_merchant,
    )
    from workflows.card import CardWorkflow

# Compressed for demo purposes (represents 30 days in production).
MERCHANT_RESPONSE_WINDOW = timedelta(seconds=60)

# How long the workflow waits for the cardholder to confirm before cancelling.
SUBMISSION_TIMEOUT = timedelta(seconds=15)


@workflow.defn(versioning_behavior=VersioningBehavior.AUTO_UPGRADE)
class TransactionDisputeWorkflow:
    """Medium-running chargeback dispute workflow — one per disputed transaction.

    Marked AUTO_UPGRADE so in-flight disputes automatically migrate to a newer
    Worker Deployment Version at the next Workflow Task after a deploy.

    Because a version change can happen mid-run, any new command added to the
    sequence MUST be guarded with workflow.patched() to remain replay-safe.
    """

    def __init__(self) -> None:
        self._submitted: bool = False
        self._merchant_responded: bool = False
        self._status: str = "waiting_for_submission"
        self._reason_code: DisputeReasonCode = None

    # ── Signal handlers ───────────────────────────────────────────────────────

    @workflow.signal
    def submit_dispute(self, reason: str) -> None:
        """Cardholder confirms they want to dispute the transaction."""
        if reason not in DisputeReasonCode:
            workflow.logger.error(f"Invalid reason code: {reason}")
            return

        self._reason_code = DisputeReasonCode(reason)
        workflow.logger.info(f"Dispute submission received from cardholder: {reason}")
        self._submitted = True
        self._status = "processing"

    @workflow.signal
    def merchant_responded(self) -> None:
        """Merchant submitted evidence in response to the dispute notice."""
        workflow.logger.info("Merchant response received before deadline")
        self._merchant_responded = True

    # ── Query handlers ────────────────────────────────────────────────────────

    @workflow.query
    def get_status(self) -> str:
        """Return the current processing stage of this dispute."""
        return self._status

    async def _record_dispute_on_card(
        self, card_id: str, dispute_id: str, result: DisputeResult
    ) -> None:
        card_handle = workflow.get_external_workflow_handle_for(
            CardWorkflow.run, f"card/{card_id}"
        )
        await card_handle.signal(CardWorkflow.record_dispute, args=[dispute_id, result])

    # ── Main run ──────────────────────────────────────────────────────────────

    @workflow.run
    async def run(self, request: DisputeRequest) -> DisputeResult:
        workflow.logger.info(
            f"Dispute started — card={request.card_id} "
            f"transaction={request.transaction_id} "
            f"amount=${request.amount:.2f}"
        )

        # ── Step: wait for cardholder to confirm the dispute ────────────
        try:
            await workflow.wait_condition(
                lambda: self._submitted,
                timeout=SUBMISSION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            workflow.logger.info(
                f"Dispute cancelled — cardholder did not submit within timeout "
                f"(transaction={request.transaction_id})"
            )
            self._status = "cancelled"
            result = DisputeResult(outcome="cancelled", credit_amount=0.0)
            await self._record_dispute_on_card(
                request.card_id, workflow.info().workflow_id, result
            )
            return result

        # # TODO (v2): business requested to issue provisional credit for customers
        # if workflow.patched("add-provisional-credit"):
        #     await workflow.execute_activity(
        #         issue_provisional_credit,
        #         args=[request.card_id, request.amount],
        #         start_to_close_timeout=timedelta(seconds=10),
        #     )

        # ── Step: notify the merchant ───────────────────────────────────
        self._status = "waiting_for_merchant_response"
        await workflow.execute_activity(
            notify_merchant,
            args=[request.transaction_id, self._reason_code],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # ── Step: wait for merchant response or let the window expire ───
        try:
            await workflow.wait_condition(
                lambda: self._merchant_responded,
                timeout=MERCHANT_RESPONSE_WINDOW,
            )
            workflow.logger.info("Merchant responded before deadline")
        except asyncio.TimeoutError:
            workflow.logger.info(
                "Merchant response window expired — no response received"
            )

        # ── Step: evaluate the dispute ──────────────────────────────────
        self._status = "evaluating"
        evaluation: DisputeEvaluation = await workflow.execute_activity(
            evaluate_dispute,
            args=[self._reason_code, self._merchant_responded],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # ── Step: finalize ──────────────────────────────────────────────
        await workflow.execute_activity(
            finalize_dispute,
            args=[request.card_id, evaluation.outcome, request.amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        credit_amount = (
            request.amount if evaluation.outcome == "cardholder_wins" else 0.0
        )
        self._status = "resolved"
        workflow.logger.info(
            f"Dispute resolved — card={request.card_id} "
            f"outcome={evaluation.outcome} credit=${credit_amount:.2f}"
        )

        result = DisputeResult(outcome=evaluation.outcome, credit_amount=credit_amount)

        # ── Signal the CardWorkflow with the dispute outcome ────────────
        await self._record_dispute_on_card(
            request.card_id, workflow.info().workflow_id, result
        )

        return result


async def main() -> None:
    import logging
    import os
    from time import sleep

    from temporalio.client import Client

    logging.basicConfig(level=logging.INFO)

    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    task_queue = os.environ.get("TASK_QUEUE", "card-task-queue")
    workflow_id = "transaction/dispute/random-transaction-id"

    client = await Client.connect(address, namespace=namespace)

    handle = await client.start_workflow(
        TransactionDisputeWorkflow.run,
        args=[
            DisputeRequest(
                card_id="card-123",
                transaction_id="random-transaction-id",
                amount=100.0,
            )
        ],
        id=workflow_id,
        task_queue=task_queue,
    )

    await handle.signal(TransactionDisputeWorkflow.submit_dispute, "unauthorized")
    sleep(3)
    await handle.signal(TransactionDisputeWorkflow.merchant_responded)

    logging.info(f"Started TransactionDisputeWorkflow — workflow_id={workflow_id}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
