# RedTrack CLI — Test Plan

## Test Strategy

### Unit Tests (`test_core.py`)
These tests do NOT require a real RedTrack API key. They test:
- Backend module: `_get_api_key`, `_build_params`, `_build_headers`
- Backend HTTP methods: `api_get`, `api_post`, `api_patch`, `api_delete`, `is_available`
- All HTTP error cases: connection error, HTTP error codes, timeout, 204 no content
- Session management: `get_session_info`, `_mask_key`
- CLI argument parsing for all command groups via Click's test runner
- All core modules: campaigns, offers, offer sources, traffic, landers, conversions, reports, costs, rules
- Error handling with `--json` and human output modes
- Missing API key error propagation

### E2E Tests (`test_full_e2e.py`)
These tests require `REDTRACK_API_KEY` to be set. They test:
- Real API connectivity (`is_available`)
- Account info (`GET /user`)
- Campaign listing (`GET /campaigns`)
- Offer listing (`GET /offers`)
- Offer source listing (`GET /offer_sources`)
- Traffic channel listing (`GET /traffic_channels`)
- Lander listing (`GET /landers`)
- Report endpoints (`GET /reports`, `GET /reports/campaigns`, `GET /clicks`)
- Conversion listing (`GET /conversions`)
- Domain listing (`GET /domains`)
- Rule listing (`GET /rules`)
- Session status display
- CLI subprocess tests (when `CLI_ANYTHING_FORCE_INSTALLED=1`)

## Running Tests

```bash
cd redtrack/agent-harness

# Unit tests only (no API key needed)
python -m pytest cli_anything/redtrack/tests/test_core.py -v

# E2E tests (requires API key)
REDTRACK_API_KEY=your_key python -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v

# All tests
python -m pytest cli_anything/redtrack/tests/ -v

# With coverage
python -m pytest cli_anything/redtrack/tests/test_core.py -v --cov=cli_anything.redtrack --cov-report=term-missing

# Subprocess tests (requires installed CLI)
CLI_ANYTHING_FORCE_INSTALLED=1 REDTRACK_API_KEY=your_key \
    python -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v -k subprocess
```

## Test Results

| Test Suite | Status | Notes |
|-----------|--------|-------|
| test_core.py | — | Run without API key |
| test_full_e2e.py | — | Requires REDTRACK_API_KEY |
