from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import random


@dataclass
class TradeModel:
    """
    Simple statistical trade model (Mode A).

    Attributes
    ----------
    win_rate :
        Probability of a winning trade (0–1).
    risk_per_trade_pct :
        Fraction of initial account size risked per trade (e.g. 0.02 for 2%).
    reward_risk_ratio :
        Reward-to-risk ratio (e.g. 2.0 means win = +2R, loss = -1R).
    """

    win_rate: float
    risk_per_trade_pct: float
    reward_risk_ratio: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.win_rate <= 1.0):
            raise ValueError("win_rate must be between 0 and 1")
        if self.risk_per_trade_pct <= 0:
            raise ValueError("risk_per_trade_pct must be > 0")
        if self.reward_risk_ratio <= 0:
            raise ValueError("reward_risk_ratio must be > 0")


@dataclass
class TradeOutcome:
    """
    Result of a single trade, in currency and R-multiple terms.
    """

    pnl: float          # P/L in account currency
    r_multiple: float   # +R for win, -1R for loss (before costs)


def generate_trades(
    model: TradeModel,
    account_size: float,
    n_trades: int,
    seed: Optional[int] = None,
) -> List[TradeOutcome]:
    """
    Generate a sequence of trade outcomes under the simple Mode A model.

    Parameters
    ----------
    model :
        TradeModel specifying win rate, risk per trade, and RR.
    account_size :
        Initial account size in currency units.
    n_trades :
        Number of trades to simulate.
    seed :
        Optional random seed for reproducibility.

    Returns
    -------
    List[TradeOutcome]
    """
    if account_size <= 0:
        raise ValueError("account_size must be > 0")
    if n_trades < 0:
        raise ValueError("n_trades must be non-negative")

    rng = random.Random(seed)

    risk_amount = account_size * model.risk_per_trade_pct

    outcomes: List[TradeOutcome] = []
    for _ in range(n_trades):
        is_win = rng.random() < model.win_rate
        if is_win:
            r_mult = model.reward_risk_ratio
            pnl = risk_amount * r_mult
        else:
            r_mult = -1.0
            pnl = -risk_amount

        outcomes.append(TradeOutcome(pnl=pnl, r_multiple=r_mult))

    return outcomes
