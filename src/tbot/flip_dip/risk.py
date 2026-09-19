from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPlan:
    account_equity: float
    risk_percent: float
    intended_risk_amount: float
    entry_price: float
    sizing_reference_price: float
    distance: float
    units_per_price_unit: float


def calculate_planning_risk(
    *,
    account_equity: float,
    risk_percent: float,
    entry_price: float,
    sizing_reference_price: float,
) -> RiskPlan:
    """Calculate abstract exposure for planning purposes.

    XAUUSD broker contract sizes vary. This returns units-per-price-unit rather
    than pretending a broker-specific lot size is known.

    The sizing reference price is not the strategy candle-close invalidation.
    It is a planning reference needed to estimate intended risk.
    """
    if account_equity <= 0:
        raise ValueError("account_equity must be positive")
    if not (0 < risk_percent <= 100):
        raise ValueError("risk_percent must be > 0 and <= 100")

    distance = abs(entry_price - sizing_reference_price)
    if distance == 0:
        raise ValueError("entry and sizing reference cannot be identical")

    risk_amount = account_equity * (risk_percent / 100)
    units = risk_amount / distance

    return RiskPlan(
        account_equity=account_equity,
        risk_percent=risk_percent,
        intended_risk_amount=risk_amount,
        entry_price=entry_price,
        sizing_reference_price=sizing_reference_price,
        distance=distance,
        units_per_price_unit=units,
    )
