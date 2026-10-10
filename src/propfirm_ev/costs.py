from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .trades import TradeOutcome


@dataclass
class CostModel:
    """
    Simple per-trade cost model.

    Attributes
    ----------
    commission_per_trade :
        Fixed commission per trade in account currency.
    slippage_risk_fraction :
        Slippage as a fraction of the risk amount per trade (e.g. 0.05 = 5% of risk).
        This will be applied as additional loss on both wins and losses.
    """

    commission_per_trade: float = 0.0
    slippage_risk_fraction: float = 0.0


def apply_costs(
    trades: List[TradeOutcome],
    risk_amount: float,
    cost_model: CostModel,
) -> List[TradeOutcome]:
    """
    Apply trading costs to a list of trade outcomes.

    Parameters
    ----------
    trades :
        Original trade outcomes before costs.
    risk_amount :
        Risk amount per trade in currency units (same as used when generating trades).
    cost_model :
        CostModel configuration.

    Returns
    -------
    List[TradeOutcome]
        New TradeOutcome list with pnl adjusted for costs.
    """
    if risk_amount < 0:
        raise ValueError("risk_amount must be >= 0")

    adjusted: List[TradeOutcome] = []
    for t in trades:
        cost = cost_model.commission_per_trade + cost_model.slippage_risk_fraction * risk_amount
        new_pnl = t.pnl - cost
        # R-multiple changes accordingly
        new_r = new_pnl / risk_amount if risk_amount > 0 else t.r_multiple
        adjusted.append(TradeOutcome(pnl=new_pnl, r_multiple=new_r))

    return adjusted
