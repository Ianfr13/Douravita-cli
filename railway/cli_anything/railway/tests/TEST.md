# Test Suite — cli-anything-railway

## Running tests

```bash
python3 -m pytest cli_anything/railway/tests/test_core.py -v
```

All tests mock the `RailwayBackend` so no real network calls are made.
