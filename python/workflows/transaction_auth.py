from datetime import timedelta

from temporalio import workflow
from temporalio.common import VersioningBehavior

with workflow.unsafe.imports_passed_through():
    from activities.card import Transaction
    from activities.transaction_auth import (
        AuthRequest,
        AuthResult,
        FraudResult,
        check_credit_limit,
        check_fraud,
    )
    from activities.transaction_dispute import DisputeRequest
    from workflows.card import CardWorkflow
    from workflows.transaction_dispute import TransactionDisputeWorkflow

# Demo: pause between the credit check and fraud screen so the workflow
# remains open long enough to demonstrate PINNED behaviour during a v2 deploy.
FRAUD_SCREEN_DELAY = timedelta(seconds=15)


@workflow.defn(versioning_behavior=VersioningBehavior.PINNED)
class TransactionAuthWorkflow:
    """Short-lived authorization workflow — one execution per card swipe."""

    @workflow.run
    async def run(self, request: AuthRequest) -> AuthResult:
        workflow.logger.info(
            f"Authorization started — card={request.card_id} "
            f"merchant={request.merchant_name!r} amount=${request.amount:.2f}"
        )

        # TODO (v1): comment out the fraud screening and credit limit check
        # ── Fraud screening ───────────────────────────────────────────
        fraud_result: FraudResult = await workflow.execute_activity(
            check_fraud,
            args=[
                request.card_id,
                request.merchant_name,
                request.merchant_category,
                request.amount,
            ],
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not fraud_result.approved:
            workflow.logger.info(
                f"Authorization declined (fraud risk) — card={request.card_id}"
            )
            return AuthResult(
                approved=False,
                decline_reason=f"fraud_risk:{','.join(fraud_result.flags)}",
            )

        # ── Credit limit check ────────────────────────────────────────
        has_credit: bool = await workflow.execute_activity(
            check_credit_limit,
            args=[request.card_id, request.amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not has_credit:
            workflow.logger.info(
                f"Authorization declined (insufficient credit) — card={request.card_id}"
            )
            return AuthResult(
                approved=False,
                decline_reason="insufficient_credit",
            )

        # # TODO (v2): uncomment the check_credit_limit and fraud_screening activities
        # # ── Credit limit check ────────────────────────────────────────
        # has_credit: bool = await workflow.execute_activity(
        #     check_credit_limit,
        #     args=[request.card_id, request.amount],
        #     start_to_close_timeout=timedelta(seconds=10),
        # )

        # if not has_credit:
        #     workflow.logger.info(
        #         f"Authorization declined (insufficient credit) — card={request.card_id}"
        #     )
        #     return AuthResult(
        #         approved=False,
        #         decline_reason="insufficient_credit",
        #     )

        # # ── Fraud screening ───────────────────────────────────────────
        # fraud_result: FraudResult = await workflow.execute_activity(
        #     check_fraud,
        #     args=[
        #         request.card_id,
        #         request.merchant_name,
        #         request.merchant_category,
        #         request.amount,
        #     ],
        #     start_to_close_timeout=timedelta(seconds=10),
        # )

        # if not fraud_result.approved:
        #     workflow.logger.info(
        #         f"Authorization declined (fraud risk) — card={request.card_id}"
        #     )
        #     return AuthResult(
        #         approved=False,
        #         decline_reason=f"fraud_risk:{','.join(fraud_result.flags)}",
        #     )

        # ── Signal the CardWorkflow with the approved transaction ─────────
        card_handle = workflow.get_external_workflow_handle_for(
            CardWorkflow.run, f"card/{request.card_id}"
        )
        await card_handle.signal(
            CardWorkflow.record_transaction,
            Transaction(amount=request.amount, merchant=request.merchant_name),
        )

        # After each transaction authorization, start a transaction dispute workflow
        # to track potential transaction disputes.
        dispute_workflow_id = f"{workflow.info().workflow_id}/dispute"
        _ = await workflow.start_child_workflow(
            TransactionDisputeWorkflow.run,
            args=[
                DisputeRequest(
                    card_id=request.card_id,
                    transaction_id=request.transaction_id,
                    amount=request.amount,
                ),
            ],
            id=dispute_workflow_id,
            parent_close_policy=workflow.ParentClosePolicy.ABANDON,
        )

        result = AuthResult(
            approved=True,
            decline_reason=None,
        )

        workflow.logger.info(
            f"Authorization complete — card={request.card_id} "
            f"approved={result.approved}"
        )

        return result
