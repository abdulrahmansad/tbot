from tbot.account_simulator import simulate_account


def test_account_simulator_compounds_balance():
    events = [
        {"outcome_status": "TARGET_5R", "retest_at": "2026-01-01T00:00:00+00:00"},
        {"outcome_status": "INVALIDATED", "retest_at": "2026-01-02T00:00:00+00:00"},
    ]

    result = simulate_account(events, starting_balance=100, risk_percent=5)

    # 100 + 25 = 125, then -6.25 = 118.75
    assert result.ending_balance == 118.75
    assert result.net_profit == 18.75
    assert result.event_count == 2
    assert result.winning_events == 1
    assert result.losing_events == 1


def test_account_simulator_tracks_drawdown():
    events = [
        {"outcome_status": "TARGET_2R"},
        {"outcome_status": "INVALIDATED"},
        {"outcome_status": "INVALIDATED"},
    ]

    result = simulate_account(events, starting_balance=100, risk_percent=5)

    assert result.highest_balance == 110.0
    assert result.lowest_balance < 110.0
    assert result.max_drawdown_percent > 0


def test_ambiguous_is_flat_by_default():
    result = simulate_account(
        [{"outcome_status": "AMBIGUOUS"}],
        starting_balance=100,
        risk_percent=5,
    )

    assert result.ending_balance == 100.0
    assert result.flat_events == 1
