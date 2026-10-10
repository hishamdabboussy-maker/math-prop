from typing import List

from propfirm_ev.state import AccountLimits, AccountState, AccountStatus, simulate_account_over_trades
from propfirm_ev.trades import TradeOutcome


def make_loss_trade(amount: float) -> TradeOutcome:
    return TradeOutcome(pnl=-amount, r_multiple=-1.0)


def make_win_trade(amount: float) -> TradeOutcome:
    return TradeOutcome(pnl=amount, r_multiple=1.0)


def test_static_max_loss_breach():
    limits = AccountLimits(
        initial_balance=100000.0,
        max_static_loss_pct=0.10,   # 10k
        max_daily_loss_pct=0.10,    # irrelevant here
    )
    state = AccountState(limits=limits, balance=limits.initial_balance)

    # First loss: 5k (ok)
    state.apply_trade(make_loss_trade(5000.0))
    assert state.status == AccountStatus.ACTIVE

    # Second loss: another 6000 (total 11k > 10k)
    state.apply_trade(make_loss_trade(6000.0))
    assert state.status == AccountStatus.FAILED
    assert state.failure_reason == "MAX_STATIC_LOSS_BREACH"


def test_daily_loss_breach_resets_each_day():
    limits = AccountLimits(
        initial_balance=100000.0,
        max_static_loss_pct=0.50,   # very high, won't hit
        max_daily_loss_pct=0.05,    # 5k per day
    )
    state = AccountState(limits=limits, balance=limits.initial_balance)

    # Day 0: lose 4k -> ok (below 5k)
    state.apply_trade(make_loss_trade(4000.0))
    assert state.status == AccountStatus.ACTIVE

    # Start new day
    state.start_new_day()

    # Day 1: lose 5100 -> breach daily limit
    state.apply_trade(make_loss_trade(5100.0))
    assert state.status == AccountStatus.FAILED
    assert state.failure_reason == "MAX_DAILY_LOSS_BREACH"


def test_simulate_account_over_trades_stops_on_failure():
    limits = AccountLimits(
        initial_balance=100000.0,
        max_static_loss_pct=0.10,   # 10k total
        max_daily_loss_pct=1.00,    # 100% daily so daily loss never hits first
    )
    trades: List[TradeOutcome] = [
        make_loss_trade(2000.0),
        make_win_trade(3000.0),
        make_loss_trade(12000.0),   # triggers static loss (>10k total)
        make_win_trade(5000.0),     # should not be applied
    ]

    final_state = simulate_account_over_trades(limits, trades)

    assert final_state.status == AccountStatus.FAILED
    assert final_state.failure_reason == "MAX_STATIC_LOSS_BREACH"
    # Only first 3 trades applied
    expected_balance = limits.initial_balance - 2000.0 + 3000.0 - 12000.0
    assert abs(final_state.balance - expected_balance) < 1e-6
