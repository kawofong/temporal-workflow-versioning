import uuid
from dataclasses import dataclass, field
from time import sleep

from temporalio import activity


@dataclass
class AuthRequest:
    card_id: str
    merchant_name: str
    merchant_category: str
    amount: float


@dataclass
class FraudResult:
    score: float  # 0.0 (clean) – 1.0 (high risk)
    flags: list[str]  # e.g. ["high_amount", "velocity"]
    approved: bool


@dataclass
class AuthResult:
    approved: bool
    decline_reason: str | None


@activity.defn
def check_credit_limit(card_id: str, amount: float) -> bool:
    """Decline immediately if the transaction exceeds the simulated credit limit."""
    approved = amount < 1_000.0
    activity.logger.info(
        f"Credit limit check — card={card_id} amount=${amount:.2f} "
        f"result={'ok' if approved else 'declined (limit)'}"
    )
    sleep(1)  # Simulate a delay
    return approved


@activity.defn
def check_fraud(
    card_id: str,
    merchant_name: str,
    merchant_category: str,
    amount: float,
) -> FraudResult:
    """Score by transaction amount only. Flags amounts above $500."""
    flags: list[str] = []
    if amount > 500.0:
        flags.append("high_amount")

    score = round(0.1 + 0.8 * bool(flags), 1)
    approved = not flags
    activity.logger.info(
        f"Fraud screen (v1) — card={card_id} merchant={merchant_name!r} "
        f"amount=${amount:.2f} score={score} flags={flags} "
        f"result={'approved' if approved else 'declined (fraud)'}"
    )
    sleep(1)  # Simulate a delay
    return FraudResult(score=score, flags=flags, approved=approved)


@activity.defn
def record_authorization(card_id: str, amount: float, approved: bool) -> str | None:
    """Persist the authorization decision; return an auth code when approved."""
    auth_code = f"AUTH-{uuid.uuid4().hex[:8].upper()}" if approved else None
    activity.logger.info(
        f"Authorization recorded — card={card_id} amount=${amount:.2f} "
        f"approved={approved} auth_code={auth_code}"
    )
    sleep(1)  # Simulate a delay
    return auth_code
