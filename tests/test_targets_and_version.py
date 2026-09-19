from datetime import datetime, timezone

import pytest

from tbot.flip_dip.targets import (
    PartialTakeProfitNotConfigured,
    TakeProfitLevel,
    TakeProfitPlan,
    default_provisional_tp_plan,
    plan_from_levels,
)
from tbot.strategy_version import StrategyVersionState, provisional_v0


def test_no_invented_default_partial_tp_plan():
    with pytest.raises(PartialTakeProfitNotConfigured):
        default_provisional_tp_plan()


def test_owner_configured_tp_plan_can_reach_5r_and_total_100():
    plan = plan_from_levels(((2.0, 25.0), (3.5, 25.0), (5.0, 50.0)))
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
