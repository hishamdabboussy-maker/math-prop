from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class SourceRecord(BaseModel):
    url: str
    date_accessed: str
    status: Literal["verified", "ambiguous", "conflicting", "unavailable"]
    quote: Optional[str] = None
    notes: Optional[str] = None


class RefundRule(BaseModel):
    type: Literal["first_payout", "never"]
    # "entry" means refund equals entry fee; a number is an explicit currency amount
    amount: str | float


class FeeConfig(BaseModel):
    entry: float = Field(ge=0)
    reset: Optional[float] = Field(default=None, ge=0)
    activation: Optional[float] = Field(default=None, ge=0)
    recurring_monthly: Optional[float] = Field(default=None, ge=0)
    refund: Optional[RefundRule] = None


class DrawdownRule(BaseModel):
    pct: float = Field(ge=0)
    type: Literal["static", "trailing"]
    basis: Literal["balance", "equity"]
    timing: Literal["intraday", "end_of_day"]


class ConsistencyRule(BaseModel):
    max_best_day_fraction: float = Field(ge=0, le=1)


class ProfitableDaysRequirement(BaseModel):
    min_profitable_days: int = Field(ge=0)
    min_daily_return_pct: float


class StageConfig(BaseModel):
    name: str
    profit_target_pct: float
    min_trading_days: Optional[int] = Field(default=None, ge=0)
    max_trading_days: Optional[int] = Field(default=None, ge=0)
    max_drawdown: DrawdownRule
    daily_loss_pct: Optional[float] = None
    consistency_rule: Optional[ConsistencyRule] = None
    profitable_days_requirement: Optional[ProfitableDaysRequirement] = None


class PayoutRules(BaseModel):
    min_profit_pct: Optional[float] = None
    min_days: Optional[int] = Field(default=None, ge=0)
    p_received_given_eligible: float = Field(ge=0, le=1)


class Restrictions(BaseModel):
    news_trading: Optional[str] = None
    overnight: Optional[str] = None
    weekend: Optional[str] = None


class FundedConfig(BaseModel):
    profit_split: float = Field(ge=0, le=1)
    payout: PayoutRules
    max_drawdown: DrawdownRule
    restrictions: Restrictions = Restrictions()


class AccountPlan(BaseModel):
    """
    Top-level configuration for a single account plan.
    This is purely declarative: no simulation logic here.
    """

    firm: str
    plan_name: str
    verified: bool = False
    sources: List[SourceRecord] = Field(default_factory=list)
    account_size: float = Field(gt=0)
    currency: str
    fees: FeeConfig
    stages: List[StageConfig]
    funded: FundedConfig

    @field_validator("stages")
    @classmethod
    def validate_stages_non_empty(cls, v: List[StageConfig]) -> List[StageConfig]:
        if not v:
            raise ValueError("At least one stage must be defined")
        return v
