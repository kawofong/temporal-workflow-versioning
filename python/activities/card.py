from dataclasses import dataclass

from temporalio import activity


@dataclass
class Transaction:
    amount: float
    merchant: str


@dataclass
class Statement:
    account_id: str
    cycle: int
    total_spend: float
    transaction_count: int


@activity.defn
def generate_statement(
    account_id: str,
    cycle: int,
    transactions: list[Transaction],
) -> Statement:
    total_spend = sum(t.amount for t in transactions)
    activity.logger.info(
        f"Generating statement for account={account_id} cycle={cycle} "
        f"transactions={len(transactions)} total_spend=${total_spend:.2f}"
    )
    return Statement(
        account_id=account_id,
        cycle=cycle,
        total_spend=total_spend,
        transaction_count=len(transactions),
    )


@activity.defn
def persist_statement(statement: Statement) -> None:
    activity.logger.info(
        f"Persisting statement for account={statement.account_id} cycle={statement.cycle}"
    )


@activity.defn
def calculate_rewards(transactions: list[Transaction]) -> int:
    """v1: 1 reward point per dollar spent."""
    points = int(sum(t.amount for t in transactions))
    activity.logger.info(
        f"Calculated {points} reward points (1x multiplier) for {len(transactions)} transactions"
    )
    return points


@activity.defn
def send_statement_notification(
    statement: Statement,
    rewards_points: int,
) -> None:
    activity.logger.info(
        f"[NOTIFICATION] Account {statement.account_id} — Cycle {statement.cycle} statement: "
        f"spend=${statement.total_spend:.2f}, "
        f"transactions={statement.transaction_count}, "
        f"rewards={rewards_points} pts"
    )
