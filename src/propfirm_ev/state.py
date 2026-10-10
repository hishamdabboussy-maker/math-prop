from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

from .trades import TradeOutcome


class AccountStatus(Enum):
    ACTIVE = auto()
    FAILED = auto()


@dataclass
class AccountLimits:
    """
    Simple account-level risk limits for MVP.

    Attributes
    ----------
    initial_balance :
        Starting balance of the account.
    max_static_loss_pct :
        Maximum total loss as a fraction of initial balance (e.g. 0.10 for 10%).
    max_daily_loss_pct :
        Maximum daily loss as a fraction of initial balance (e.g. 0.05 for 5%).
    """

    initial_balance: float
    max_static_loss_pct: float
    max_daily_loss_pct: float

    def __post_init__(self) -> None:
        if self.initial_balance <= 0:
            raise ValueError("initial_balance must be > 0")
        if self.max_static_loss_pct < 0:
            raise ValueError("max_static_loss_pct must be >= 0")
        if self.max_daily_loss_pct < 0:
            raise ValueError("max_daily_loss_pct must be >= 0")

    @property
    def max_static_loss_amount(self) -> float:
        return self.initial_balance * self.max_static_loss_pct

    @property
    def max_daily_loss_amount(self) -> float:
        return self.initial_balance * self.max_daily_loss_pct


@dataclass
class AccountState:
    """
    Minimal account state for static max loss and daily loss checks.

    We assume:
    - Equity == balance (no open positions).
    - One trade per "day" for now, unless caller groups trades into days.
    """

    limits: AccountLimits
    balance: float
    status: AccountStatus = AccountStatus.ACTIVE
    failure_reason: Optional[str] = None
    current_day_index: int = 0
    day_start_balance: float = field(init=False)
    cumulative_profit: float = 0.0

    def __post_init__(self) -> None:
        self.day_start_balance = self.balance

    @property
    def total_loss_from_initial(self) -> float:
        return self.limits.initial_balance - self.balance

    @property
    def daily_loss(self) -> float:
        return self.day_start_balance - self.balance

    def _fail(self, reason: str) -> None:
        self.status = AccountStatus.FAILED
        self.failure_reason = reason

    def start_new_day(self) -> None:
        """
        Reset day_start_balance for a new trading day.
        """
        if self.status is AccountStatus.FAILED:
            return
        self.current_day_index += 1
        self.day_start_balance = self.balance

    def apply_trade(self, trade: TradeOutcome) -> None:
        """
        Apply a single trade outcome, then check limits.

        If limits are breached, mark account as FAILED.
        """
        if self.status is AccountStatus.FAILED:
            return

        self.balance += trade.pnl
        self.cumulative_profit = self.balance - self.limits.initial_balance

        # Check static max loss
        if self.total_loss_from_initial > self.limits.max_static_loss_amount + 1e-9:
            self._fail("MAX_STATIC_LOSS_BREACH")
            return

        # Check daily loss
        if self.daily_loss > self.limits.max_daily_loss_amount + 1e-9:
            self._fail("MAX_DAILY_LOSS_BREACH")
            return


def simulate_account_over_trades(
    limits: AccountLimits,
    trades: List[TradeOutcome],
) -> AccountState:
    """
    Simulate an account over a sequence of trades, one trade per day.

    For this MVP:
    - Each trade is considered a new day.
    - After each trade, we check static max loss and daily loss.
    """
    state = AccountState(limits=limits, balance=limits.initial_balance)

    for i, t in enumerate(trades):
        if i > 0:
            state.start_new_day()
        state.apply_trade(t)
        if state.status is AccountStatus.FAILED:
            break

    return state
