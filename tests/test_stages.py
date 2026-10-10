from pathlib import Path

from propfirm_ev.config import load_account_plan
from propfirm_ev.state import AccountLimits, AccountStatus
from propfirm_ev.stages import (
    EvaluationStage,
    build_stage_progress,
    simulate_evaluation,
)
from propfirm_ev.trades import TradeOutcome


def make_trade(pnl: float) -> TradeOutcome:
    return TradeOutcome(pnl=pnl, r_multiple=pnl)  # r_multiple unused here


def test_build_stage_progress_from_plan():
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "data" / "firms" / "example_synthetic.json"
    plan = load_account_plan(plan_path, root=root)

    stages = build_stage_progress(plan)
    assert stages[0].stage is EvaluationStage.STEP1
    assert stages[1].stage is EvaluationStage.STEP2
    assert stages[2].stage is EvaluationStage.FUNDED

    assert stages[0].profit_target_pct == plan.stages[0].profit_target_pct
    assert stages[1].profit_target_pct == plan.stages[1].profit_target_pct
    assert stages[2].profit_target_pct == plan.funded.payout.min_profit_pct


def test_simulate_evaluation_reaches_step1_target_but_not_advanced_due_to_min_days():
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "data" / "firms" / "example_synthetic.json"
    plan = load_account_plan(plan_path, root=root)

    limits = AccountLimits(
        initial_balance=plan.account_size,
        max_static_loss_pct=0.10,
        max_daily_loss_pct=0.10,
    )

    # Step1 target: 10%, Step2: 5%, Funded: 10%.
    # 3 trades of +4% each give +12% total on initial balance.
    step_pnl = plan.account_size * 0.04
    trades = [
        make_trade(step_pnl),
        make_trade(step_pnl),
        make_trade(step_pnl),
    ]

    result = simulate_evaluation(plan, limits, trades)

    # Account should still be active
    assert result.status == AccountStatus.ACTIVE

    # We should still be in STEP1 because min_trading_days for step1 is 4
    assert result.final_stage is EvaluationStage.STEP1

    # But STEP1 target should be marked as reached
    sp_step1 = result.stage_progress[0]
    assert sp_step1.reached_target
    assert sp_step1.trades_taken == 3
    assert not sp_step1.meets_min_days  # need 4 days
