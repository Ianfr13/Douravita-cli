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

## Run / Exec / SSH refine (2026-04-24, v1.2.0)

Added 17 tests covering:

- `railway_relay._decode_payload_data` — string / list / `{type:"Buffer"}` forms
- `railway_relay._headers` — required Railway scoping headers + optional instance-id
- `RelayError` raised when `websocket-client` is missing
- Backend: `ssh_keys_list/create/delete`, `deployment_instance_execution_create`,
  `variables_for_deployment` alias
- CLI: `run --print-env`, `exec` forwarding to relay, dependency guard, `ssh keys list/remove`

### Full suite

```
$ python3 -m pytest cli_anything/railway/tests/test_core.py --tb=no -q
........................................................................ [ 28%]
........................................................................ [ 57%]
........................................................................ [ 85%]
....................................                                     [100%]
252 passed in 3.40s
```

### Smoke tests against the real API (paperclip service, live container)

| Command | Status |
|---------|--------|
| `run --print-env` | ✅ pulled 10+ real env vars (DATABASE_URL, BETTER_AUTH_*, etc.) |
| `run -- printenv RAILWAY_STATIC_URL` | ✅ returned the actual deployment URL |
| `exec -- ls -la /app` | ✅ listed the real container filesystem (14+ files) |
| `exec -- echo "hello from claude"` | ✅ output echoed, exit 0 |
| `exec -- sh -c "hostname; uname -a"` | ✅ container `d624ca64db4e`, Linux 6.18.5 kernel |
| `exec -- ps aux` | ⚠ exit 0, but container has no `ps` binary (not a CLI bug) |
| `ssh keys list` / `ssh keys github` | ⚠ `Not Authorized` with a project-scope token (expected — account-level ops need an account token) |

### Relay protocol (reverse-engineered from `railwayapp/cli`)

Upgrade to `wss://backboard.railway.com/relay` with headers:
`Authorization: Bearer <tok>`, `X-Railway-Project-Id`, `X-Railway-Service-Id`,
`X-Railway-Environment-Id`, `X-Railway-Deployment-Instance-Id` (opt), `X-Source`.

Client → server JSON:
- `init_shell` `{shell}` — start PTY
- `exec_command` `{command, args, env}` — one-shot exec
- `data` `{data}` — stdin
- `window_size` `{cols, rows}` — resize (via SIGWINCH)
- `signal` `{signal}` — send signal

Server → client JSON:
- `welcome` — handshake
- `session_data` — stdio (`payload.data` is `{type:"Buffer", data:[u8,...]}`)
- `command_exit` `{code}` — exit code
- `pty_closed` — session done
- `error` `{message}`

## Known gaps

- `ssh` interactive PTY session is not unit-tested (needs a WS test server + TTY).
  Covered by a manual smoke run.
- SSH key management requires an account/workspace token, not a project token;
  we don't exercise the live endpoint in CI.
