# Contributing to BullRun

> AI proposes. Evidence decides. Humans authorize.

## Core Rule

The LLM is NEVER in the decision path. Python does all math and validation. The LLM only explains.

## Code Style

### Python
- Type hints on all function signatures
- Docstrings on all public functions (Google style)
- Use `rich` for console output
- Use `pydantic` for data models
- No secrets in source (use .env)

### TypeScript
- Strict mode enabled
- `"use client"` directive for hooks
- Type all interfaces
- Functional components + hooks only

## How to Add a Risk Gate

1. Add limit to `RiskLimits` in `config.py`
2. Add check block to `RiskEngine.check()` in `agents/risk_engine.py`
3. Surface required data in proposal via Quant agent
4. Test with `python agents/risk_engine.py`

## How to Add a Teaching Feature

1. Add to `FEATURE_POINTS` in `teaching_engine.py`
2. Write deterministic explainer function (no LLM)
3. Call from `orchestrator.py`
4. Update TypeScript interfaces if needed

## Running Tests

```bash
python agents/scout_agent.py       # Scout smoke test
python agents/risk_engine.py        # Risk engine test
python orchestrator.py              # Full pipeline
curl http://localhost:8000/api/audit/verify  # Audit chain
```

## PR Guidelines

- Branch from main with descriptive name
- Run relevant smoke tests
- Update docs if user-facing
- No hardcoded secrets
- Flag if change touches trading behavior
