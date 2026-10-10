from __future__ import annotations

from dataclasses import dataclass

from .simulate import MonteCarloSummary
from .models import AccountPlan


@dataclass
class AttemptCostModel:
    """
    Cost structure for a single challenge attempt.

    For now, we focus on:
    - Entry fee (non-recurring per attempt)
    - Activation fee (if any)
    - Other fixed costs can be added later.

    All values are in account currency.
    """

    entry_fee: float
    activation_fee: float = 0.0

    @property
    def total_fixed_cost(self) -> float:
        return self.entry_fee + self.activation_fee


@dataclass
class PayoutModel:
    """
    Simple funded-account payout model for EV calculations.

    Attributes
    ----------
    target_return_pct :
        Profit target on the funded account in % of account_size
        (e.g. 0.10 for 10%).
    profit_split :
        Fraction of profit paid to trader (e.g. 0.8 for 80%).
    include_fee_refund :
        If True, we add the entry fee back on first payout to mimic
        firms that refund fees.
    """

    target_return_pct: float
    profit_split: float
    include_fee_refund: bool = False


@dataclass
class EVResult:
    """
    Expected value for a single attempt, plus components.
    """

    ev_per_attempt: float
    expected_gross_payout: float
    expected_fee_refund: float
    expected_total_cost: float
    p_payout: float


def build_default_attempt_cost(plan: AccountPlan) -> AttemptCostModel:
    """
    Derive a simple AttemptCostModel from an AccountPlan.

    Uses:
    - fees.entry as entry_fee
    - fees.activation as activation_fee (0.0 if None)
    """
    entry = plan.fees.entry
    activation = plan.fees.activation or 0.0
    return AttemptCostModel(entry_fee=entry, activation_fee=activation)


def build_default_payout_model(plan: AccountPlan) -> PayoutModel:
    """
    Derive a simple PayoutModel from an AccountPlan, using:

    - target_return_pct from funded.payout.min_profit_pct
      (or 0.10 if missing)
    - profit_split from funded.profit_split
    - include_fee_refund if fees.refund.type == "first_payout"
    """
    target = plan.funded.payout.min_profit_pct or 0.10
    split = plan.funded.profit_split
    include_refund = False
    if plan.fees.refund is not None and plan.fees.refund.type == "first_payout":
        include_refund = True
    return PayoutModel(
        target_return_pct=target,
        profit_split=split,
        include_fee_refund=include_refund,
    )


def compute_ev_one_attempt(
    plan: AccountPlan,
    mc_summary: MonteCarloSummary,
    attempt_cost: AttemptCostModel | None = None,
    payout_model: PayoutModel | None = None,
) -> EVResult:
    """
    Compute expected value for a single attempt.

    EV = p_payout * E[net_payout | payout] - expected_total_cost

    where:
      net_payout = trader_share_of_profit + (fee_refund_if_applicable)
    """
    if attempt_cost is None:
        attempt_cost = build_default_attempt_cost(plan)
    if payout_model is None:
        payout_model = build_default_payout_model(plan)

    account_size = plan.account_size

    # Assumption: when funded and "payout" occurs, we hit the configured
    # target_return_pct on funded account exactly once, and withdraw that.
    gross_profit_if_payout = payout_model.target_return_pct * account_size
    trader_share_if_payout = gross_profit_if_payout * payout_model.profit_split

    # Probability of payout assumed to equal p_reached_funded for now.
    # (Later we can decouple eligibility from receipt if needed.)
    p_payout = mc_summary.p_reached_funded

    # Fee refund: counted only on payout, if configured.
    fee_refund_if_payout = attempt_cost.entry_fee if payout_model.include_fee_refund else 0.0

    expected_gross_payout = p_payout * trader_share_if_payout
    expected_fee_refund = p_payout * fee_refund_if_payout

    expected_total_cost = attempt_cost.total_fixed_cost  # costs are paid in all attempts

    ev = expected_gross_payout + expected_fee_refund - expected_total_cost

    return EVResult(
        ev_per_attempt=ev,
        expected_gross_payout=expected_gross_payout,
        expected_fee_refund=expected_fee_refund,
        expected_total_cost=expected_total_cost,
        p_payout=p_payout,
    )
