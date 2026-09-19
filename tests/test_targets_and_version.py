from datetime import datetime, timezone

import pytest

from tbot.flip_dip.targets import TakeProfitLevel, TakeProfitPlan, default_provisional_tp_plan
from tbot.strategy_version import StrategyVersionState, provisional_v0


def test_default_tp_plan_reaches_5r_and_totals_100():
    plan = default_provisional_tp_plan()
    assert sum(level.close_percent for level in plan.levels) == 100
    assert max(level.r_multiple for level in plan.levels) >= 5


def test_invalid_partial_total_rejected():
    plan = TakeProfitPlan(
        levels=(
            TakeProfitLevel(2, 20),
            TakeProfitLevel(5, 70),
        )
    )
    with pytest.raises(ValueError):
        plan.validate()


def test_provisional_version_is_calibrating():
    version = provisional_v0(datetime.now(timezone.utc))
    assert version.state is StrategyVersionState.CALIBRATING
