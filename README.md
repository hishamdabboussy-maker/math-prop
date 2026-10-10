\# math-prop — Prop Firm EV Engine (MVP)



Research simulator for proprietary trading firm evaluations and funded accounts.



Goals:



\- Model prop-firm evaluation and funded-account rules.

\- Simulate trade paths under configurable assumptions.

\- Estimate probabilities of passing, payout, and expected value under those assumptions.



This repo currently contains:



\- A JSON schema for account plan configuration.

\- Python dataclasses for account plans and rules.

\- A config loader that validates JSON against the schema.

\- A synthetic, clearly fictional example account plan.

\- Unit tests for the configuration layer.



\## Install



```bash

python -m venv .venv

\# Windows:

.venv\\Scripts\\activate

pip install -e .\[dev]

pytest
math-prop/
├── data/
│   ├── firms/        # account-plan JSON files
│   └── schema/       # JSON schema for validation
├── src/
│   └── propfirm_ev/  # Python package
└── tests/            # pytest tests
pydantic>=2.7
jsonschema>=4.21
pytest>=8.0




