from pathlib import Path

from propfirm_ev.config import load_account_plan
from propfirm_ev.ev import (
    EVResult,
    AttemptCostModel,
    PayoutModel,
    compute_ev_one_attempt,
)
from propfirm_ev.simulate import MonteCarloSummary


def test_ev_basic_no_refund():
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "data" / "firms" / "example_synthetic.json"
    plan = load_account_plan(plan_path, root=root)

    # Synthetic summary: 20% of paths reach funded
    mc = MonteCarloSummary(
        n_paths=1000,
        n_failed=800,
        n_reached_funded=200,
        p_failed=0.8,
        p_reached_funded=0.2,
    )

    attempt_cost = AttemptCostModel(entry_fee=1000.0, activation_fee=0.0)
    payout_model = PayoutModel(
        target_return_pct=0.10,  # 10% funded target
        profit_split=0.8,
        include_fee_refund=False,
    )

    result = compute_ev_one_attempt(
        plan,
        mc,
        attempt_cost=attempt_cost,
        payout_model=payout_model,
    )

    assert isinstance(result, EVResult)
    # Gross payout if payout occurs: 10% * account_size * 80% split
    gross_if_payout = 0.10 * plan.account_size * 0.8
    expected_gross = mc.p_reached_funded * gross_if_payout
    assert abs(result.expected_gross_payout - expected_gross) < 1e-6
    assert result.expected_fee_refund == 0.0
    assert result.expected_total_cost == 1000.0

    # EV = expected_gross_payout - cost
    assert abs(result.ev_per_attempt - (expected_gross - 1000.0)) < 1e-6


def test_ev_with_fee_refund():
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "data" / "firms" / "example_synthetic.json"
    plan = load_account_plan(plan_path, root=root)

    # Use plan's default fee and payout model
    mc = MonteCarloSummary(
        n_paths=1000,
        n_failed=900,
        n_reached_funded=100,
        p_failed=0.9,
        p_reached_funded=0.1,
    )

    # Override fees with a simple structure that has refund
    plan.fees.entry = 1200.0  # type: ignore[attr-defined]
    # Assume refund on first payout in plan (we set that in example_synthetic)
    result = compute_ev_one_attempt(plan, mc)

    # With refund, expected fee refund = p_payout * entry_fee
    expected_refund = mc.p_reached_funded * plan.fees.entry
    assert abs(result.expected_fee_refund - expected_refund) < 1e-6

    # EV should be greater than without refund, all else equal
    attempt_cost_no_refund = AttemptCostModel(entry_fee=plan.fees.entry)
    payout_no_refund = PayoutModel(
        target_return_pct=0.10,
        profit_split=plan.funded.profit_split,
        include_fee_refund=False,
    )
    result_no_refund = compute_ev_one_attempt(
        plan,
        mc,
        attempt_cost=attempt_cost_no_refund,
        payout_model=payout_no_refund,
    )
    assert result.ev_per_attempt > result_no_refund.ev_per_attempt
