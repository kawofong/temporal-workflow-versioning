from dataclasses import dataclass
from enum import StrEnum
from time import sleep

from temporalio import activity


class DisputeReasonCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    NOT_RECEIVED = "not_received"
    DUPLICATE = "duplicate"
    QUALITY = "quality"


@dataclass
class DisputeRequest:
    card_id: str
    transaction_id: str
    amount: float
    # reason_code: str  # "unauthorized" | "not_received" | "duplicate" | "quality"


@dataclass
class DisputeResult:
    outcome: str  # "cardholder_wins" | "merchant_wins" | "cancelled"
    credit_amount: float


@dataclass
class DisputeEvaluation:
    outcome: str
    reasoning: str
    merchant_responded: bool


@activity.defn
def issue_provisional_credit(card_id: str, amount: float) -> str:
    """v2: issue provisional credit to the cardholder while the dispute is in progress."""
    confirmation_id = f"PROV-{card_id[:6].upper()}-{int(amount * 100):08d}"
    activity.logger.info(
        f"Provisional credit issued — card={card_id} amount=${amount:.2f} "
        f"confirmation={confirmation_id}"
    )
    sleep(1)
    return confirmation_id


@activity.defn
def notify_merchant(transaction_id: str, reason_code: str) -> str:
    """Notify the merchant of the dispute and request evidence."""
    notification_id = f"NOTIF-{transaction_id[:8].upper()}"
    activity.logger.info(
        f"Merchant notified — transaction={transaction_id} "
        f"reason={reason_code} notification_id={notification_id}"
    )
    sleep(1)
    return notification_id


@activity.defn
def evaluate_dispute(
    reason_code: DisputeReasonCode, merchant_responded: bool
) -> DisputeEvaluation:
    """v1: no merchant response incorrectly defaults to merchant_wins."""
    if merchant_responded:
        outcome = (
            "customer_wins"
            if reason_code == DisputeReasonCode.UNAUTHORIZED
            else "merchant_wins"
        )
        reasoning = (
            f"Merchant responded; outcome determined by reason_code={str(reason_code)}"
        )
    else:
        outcome = "customer_wins"
        reasoning = (
            "Merchant did not respond within deadline (defaults to customer_wins)"
        )

    activity.logger.info(
        f"Dispute evaluated — reason={str(reason_code)} "
        f"merchant_responded={merchant_responded} outcome={outcome}"
    )
    sleep(1)
    return DisputeEvaluation(
        outcome=outcome,
        reasoning=reasoning,
        merchant_responded=merchant_responded,
    )


@activity.defn
def finalize_dispute(card_id: str, outcome: str, amount: float) -> str:
    """Post the final dispute outcome and settle any credit adjustments."""
    credit_amount = amount if outcome == "cardholder_wins" else 0.0
    confirmation_id = f"DISP-{card_id[:6].upper()}-{outcome[:3].upper()}"
    activity.logger.info(
        f"Dispute finalized — card={card_id} outcome={outcome} "
        f"credit_amount=${credit_amount:.2f} confirmation={confirmation_id}"
    )
    sleep(1)
    return confirmation_id
