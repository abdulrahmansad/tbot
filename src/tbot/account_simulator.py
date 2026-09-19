from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


DEFAULT_OUTCOME_R: dict[str, float] = {
    "TARGET_5R": 5.0,
    "TARGET_3_5R": 3.5,
    "TARGET_2R": 2.0,
    "INVALIDATED": -1.0,
    "AMBIGUOUS": 0.0,
}


@dataclass(frozen=True)
class EquityPoint:
    index: int
    event_time: str | None
    outcome_status: str
    r_multiple: float
    balance_before: float
    pnl: float
    balance_after: float


@dataclass(frozen=True)
class AccountSimulation:
    starting_balance: float
    ending_balance: float
    net_profit: float
    return_percent: float
    risk_percent: float
    event_count: int
    winning_events: int
    losing_events: int
    flat_events: int
    max_drawdown_percent: float
    lowest_balance: float
    highest_balance: float
    points: tuple[EquityPoint, ...]


def simulate_account(
    events: Iterable[Mapping[str, object]],
    *,
    starting_balance: float = 100.0,
    risk_percent: float = 5.0,
    outcome_r: Mapping[str, float] | None = None,
) -> AccountSimulation:
    if starting_balance <= 0:
        raise ValueError("starting_balance must be positive")
    if not 0 < risk_percent <= 100:
        raise ValueError("risk_percent must be between 0 and 100")

    payout = dict(DEFAULT_OUTCOME_R)
    if outcome_r is not None:
        payout.update({str(k): float(v) for k, v in outcome_r.items()})

    balance = float(starting_balance)
    peak = balance
    lowest = balance
    highest = balance
    max_drawdown = 0.0
    points: list[EquityPoint] = []
    wins = 0
    losses = 0
    flats = 0

    for index, event in enumerate(events, start=1):
        status = str(event.get("outcome_status") or "")
        if status not in payout:
            continue

        r_multiple = payout[status]
        risk_amount = balance * (risk_percent / 100.0)
        pnl = risk_amount * r_multiple
        before = balance
        balance = max(0.0, balance + pnl)

        if r_multiple > 0:
            wins += 1
        elif r_multiple < 0:
            losses += 1
        else:
            flats += 1

        peak = max(peak, balance)
        lowest = min(lowest, balance)
        highest = max(highest, balance)
        drawdown = ((peak - balance) / peak * 100.0) if peak > 0 else 0.0
        max_drawdown = max(max_drawdown, drawdown)

        points.append(
            EquityPoint(
                index=len(points) + 1,
                event_time=(
                    str(event.get("outcome_resolved_at") or event.get("retest_at"))
                    if event.get("outcome_resolved_at") or event.get("retest_at")
                    else None
                ),
                outcome_status=status,
                r_multiple=r_multiple,
                balance_before=round(before, 6),
                pnl=round(pnl, 6),
                balance_after=round(balance, 6),
            )
        )

        if balance <= 0:
            break

    net = balance - starting_balance
    return AccountSimulation(
        starting_balance=round(starting_balance, 6),
        ending_balance=round(balance, 6),
        net_profit=round(net, 6),
        return_percent=round((net / starting_balance) * 100.0, 4),
        risk_percent=round(risk_percent, 4),
        event_count=len(points),
        winning_events=wins,
        losing_events=losses,
        flat_events=flats,
        max_drawdown_percent=round(max_drawdown, 4),
        lowest_balance=round(lowest, 6),
        highest_balance=round(highest, 6),
        points=tuple(points),
    )
