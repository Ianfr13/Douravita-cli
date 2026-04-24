# Test Suite — cli-anything-railway

## Running tests

```bash
python3 -m pytest cli_anything/railway/tests/test_core.py -v
```

All tests mock the `RailwayBackend` so no real network calls are made.

## Logs refine (2026-04-24)

Added coverage for the refined logs module:

- `_parse_time` (relative `30m|2h|1d` and ISO-8601 passthrough)
- `_compose_filter` (merges `--filter` and `--severity` into Railway filter syntax)
- `_filter_severity_local` (client-side severity fallback)
- `logs deployment` with `--filter`, `--severity`, `--since`, `--raw`, `--no-color`, `--build`
- `logs http` tabular + JSON output, server-side `--filter`, empty + API-error paths
- `logs environment`:
  - Regression: no longer requires `--project` (Railway dropped `projectId` from `environmentLogs`).
  - `--service` shortcut appends `@service:<id>` to the composed filter.
  - `--severity` shortcut maps to `@level:<severity>`.
  - `--since` maps to `afterDate`.
  - `--lines` maps to `beforeLimit`.
- `railway_stream` module:
  - `ws_available()` returns a boolean.
  - `stream_subscription` raises `StreamError` when the WS client is missing.

## Results

```
$ python3 -m pytest cli_anything/railway/tests/test_core.py --tb=no -q
........................................................................ [ 30%]
........................................................................ [ 61%]
........................................................................ [ 91%]
...................                                                      [100%]
235 passed in 2.99s
```

## Smoke tests against the real API

Executed with a live `RAILWAY_TOKEN` against a real project/deployment:

| Command | Status |
|---------|--------|
| `logs environment --env <id> --lines 3` | ✅ fixed (previously returned HTTP 400: `Unknown argument "projectId"`) |
| `logs deployment <id> --filter 'backup' --lines 2` | ✅ server-side filter honored |
| `logs deployment <id> --severity info --lines 2` | ✅ severity maps to `@level:info` |
| `logs deployment <id> --since 2h --lines 2` | ✅ historical time window works |
| `logs deployment <id> --follow` | ✅ WS subscription opens via `graphql-transport-ws`, streams batches, closes cleanly on Ctrl-C |

## Known gaps

- No E2E test hitting the real Railway API end-to-end (gated by live token).
- `--follow` WS flow is not covered by unit tests beyond dependency sanity
  checks (would require a WS test server). Covered by manual smoke test above.
