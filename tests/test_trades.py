from pathlib import Path

import pytest

from propfirm_ev.trades import TradeModel, generate_trades
from propfirm_ev.costs import CostModel, apply_costs


def test_generate_trades_reproducible():
    model = TradeModel(win_rate=0.5, risk_per_trade_pct=0.02, reward_risk_ratio=2.0)
    account_size = 100000.0
    trades1 = generate_trades(model, account_size, n_trades=5, seed=42)
    trades2 = generate_trades(model, account_size, n_trades=5, seed=42)

    assert len(trades1) == 5
    assert len(trades2) == 5
    # Same seed => identical sequence
    assert [t.pnl for t in trades1] == [t.pnl for t in trades2]


def test_generate_trades_basic_properties():
    model = TradeModel(win_rate=0.6, risk_per_trade_pct=0.01, reward_risk_ratio=3.0)
    account_size = 50000.0
    trades = generate_trades(model, account_size, n_trades=10, seed=1)

    risk_amount = account_size * model.risk_per_trade_pct
    win_pnl = risk_amount * model.reward_risk_ratio
    loss_pnl = -risk_amount

    assert all(t.pnl in (win_pnl, loss_pnl) for t in trades)
    assert any(t.pnl == win_pnl for t in trades)
    assert any(t.pnl == loss_pnl for t in trades)


def test_generate_trades_invalid_inputs():
    with pytest.raises(ValueError):
        TradeModel(win_rate=1.2, risk_per_trade_pct=0.01, reward_risk_ratio=2.0)

    with pytest.raises(ValueError):
        TradeModel(win_rate=0.5, risk_per_trade_pct=-0.01, reward_risk_ratio=2.0)

    with pytest.raises(ValueError):
        TradeModel(win_rate=0.5, risk_per_trade_pct=0.01, reward_risk_ratio=0.0)

    model = TradeModel(win_rate=0.5, risk_per_trade_pct=0.01, reward_risk_ratio=2.0)

    with pytest.raises(ValueError):
        generate_trades(model, account_size=0, n_trades=10)

    with pytest.raises(ValueError):
        generate_trades(model, account_size=10000, n_trades=-1)


def test_apply_costs_reduces_pnl():
    model = TradeModel(win_rate=1.0, risk_per_trade_pct=0.02, reward_risk_ratio=2.0)
    account_size = 100000.0
    trades = generate_trades(model, account_size, n_trades=3, seed=0)

    risk_amount = account_size * model.risk_per_trade_pct
    cost_model = CostModel(commission_per_trade=10.0, slippage_risk_fraction=0.05)

    adjusted = apply_costs(trades, risk_amount, cost_model)

    for original, adj in zip(trades, adjusted):
        assert adj.pnl < original.pnl  # costs reduce pnl
