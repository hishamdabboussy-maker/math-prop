from pathlib import Path

import json
import pytest
from jsonschema import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from propfirm_ev.config import load_account_plan, validate_account_plan_json
from propfirm_ev.models import AccountPlan


def test_load_example_synthetic_success():
    root = Path(__file__).resolve().parents[1]
    plan_path = root / "data" / "firms" / "example_synthetic.json"
    plan = load_account_plan(plan_path, root=root)
    assert isinstance(plan, AccountPlan)
    assert plan.firm == "SYNTHETIC_FIRM"
    assert plan.account_size == 200000
    assert len(plan.stages) == 2
    assert plan.funded.profit_split == 0.80


def test_schema_rejects_missing_required_field(tmp_path: Path):
    bad_data = {
        "firm": "X",
        "plan_name": "Bad"
        # missing account_size, currency, fees, stages, funded
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad_data), encoding="utf-8")

    with pytest.raises(JsonSchemaValidationError):
        raw = json.loads(path.read_text(encoding="utf-8"))
        root = Path(__file__).resolve().parents[1]
        validate_account_plan_json(raw, root=root)


def test_invalid_profit_split_rejected(tmp_path: Path):
    """
    Profit split outside [0, 1] must be rejected by either schema or Pydantic.
    """
    root = Path(__file__).resolve().parents[1]
    example_path = root / "data" / "firms" / "example_synthetic.json"
    raw = json.loads(example_path.read_text(encoding="utf-8"))
    raw["funded"]["profit_split"] = 1.5  # invalid

    bad_path = tmp_path / "bad_plan.json"
    bad_path.write_text(json.dumps(raw), encoding="utf-8")

    # Accept either jsonschema or Pydantic as the rejecting layer
    with pytest.raises((JsonSchemaValidationError, PydanticValidationError)):
        load_account_plan(bad_path, root=root)
