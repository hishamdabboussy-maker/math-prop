from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import jsonschema

from .models import AccountPlan


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_schema(root: Path) -> Dict[str, Any]:
    """
    Load the account plan JSON schema from data/schema relative to project root.
    """
    schema_path = root / "data" / "schema" / "account_plan.schema.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return _load_json(schema_path)


def validate_account_plan_json(data: Dict[str, Any], root: Path | None = None) -> None:
    """
    Validate a raw account-plan dict against the JSON schema.
    """
    if root is None:
        root = Path(__file__).resolve().parents[2]
    schema = _load_schema(root)
    jsonschema.validate(instance=data, schema=schema)


def load_account_plan(path: str | Path, root: Path | None = None) -> AccountPlan:
    """
    Load and validate an account plan JSON file, returning an AccountPlan model.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Account plan file not found: {p}")
    raw = _load_json(p)
    validate_account_plan_json(raw, root=root)
    return AccountPlan.model_validate(raw)
