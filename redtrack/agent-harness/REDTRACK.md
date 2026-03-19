# RedTrack: Project-Specific Analysis & SOP

## Architecture Summary

RedTrack is a cloud-hosted performance marketing tracking platform accessible
exclusively via a REST API. There is no local server to run — all API calls
go to `https://api.redtrack.io`.

```
┌─────────────────────────────────────────────────────────────┐
│                    RedTrack Platform                        │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │   Campaign   │  │   Offer /  │  │   Traffic Channel  │  │
│  │   Tracking   │  │   Lander   │  │   Management       │  │
│  └──────┬───────┘  └─────┬──────┘  └────────┬───────────┘  │
│         │                │                  │               │
│  ┌──────┴────────────────┴──────────────────┴───────────┐   │
│  │           REST API (https://api.redtrack.io)         │   │
│  │  /user        /campaigns     /offers                 │   │
│  │  /offer_sources  /traffic_channels  /landers         │   │
│  │  /conversions    /reports    /clicks                 │   │
│  │  /costs          /rules      /domains                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┴──────────────────┐
           │     CLI-Anything RedTrack Harness    │
           │     (cli-anything-redtrack)          │
           └─────────────────────────────────────┘
```

## Authentication

RedTrack uses API key authentication with two supported methods:
1. **Query parameter**: `?api_key={key}` appended to every request URL
2. **HTTP header**: `Api-Key: {key}` sent with every request

The CLI sends both simultaneously for maximum compatibility.

**Key source priority:**
1. `--api-key` command-line flag (highest priority)
2. `REDTRACK_API_KEY` environment variable

The API key is never logged or displayed in plain text. The `session status`
command shows a masked version (first 4 + last 4 chars).

## CLI Strategy: REST API Wrapper

RedTrack provides a clean REST API. This CLI wraps it with:

1. **requests** — HTTP client for all API calls
2. **Click CLI** — Structured command groups matching the API surface
3. **REPL** — Interactive mode via `prompt_toolkit` with command history
4. **Dual output** — Human-readable tables OR `--json` for agents/scripts

## API Endpoints Map

| Endpoint | Methods | CLI Command |
|----------|---------|-------------|
| `/user` | GET | `account info` |
| `/campaigns` | GET, POST | `campaign list`, `campaign create` |
| `/campaigns/{id}` | GET, PATCH, DELETE | `campaign get`, `campaign update`, `campaign delete`, `campaign links` |
| `/offers` | GET, POST | `offer list`, `offer create` |
| `/offers/{id}` | GET, PATCH, DELETE | `offer get`, `offer update`, `offer delete` |
| `/offer_sources` | GET, POST | `offer-source list`, `offer-source create` |
| `/offer_sources/{id}` | GET, PATCH, DELETE | `offer-source get`, `offer-source update`, `offer-source delete` |
| `/traffic_channels` | GET, POST | `traffic list`, `traffic create` |
| `/traffic_channels/{id}` | GET, PATCH, DELETE | `traffic get`, `traffic update`, `traffic delete` |
| `/landers` | GET, POST | `lander list`, `lander create` |
| `/landers/{id}` | GET, PATCH, DELETE | `lander get`, `lander update`, `lander delete` |
| `/conversions` | GET, POST | `conversion list`, `conversion upload` |
| `/reports` | GET | `report general` |
| `/reports/campaigns` | GET | `report campaigns` |
| `/clicks` | GET | `report clicks` |
| `/costs` | GET, POST | `cost list`, `cost update` |
| `/costs/auto` | GET | `cost auto` |
| `/rules` | GET, POST | `rule list`, `rule create` |
| `/rules/{id}` | GET, PATCH, DELETE | `rule get`, `rule update`, `rule delete` |
| `/domains` | GET, POST | `domain list`, `domain add` |

## Key Design Decisions

### 1. Namespace Package (PEP 420)
The `cli_anything/` directory has no `__init__.py`. This is intentional —
it uses Python namespace packages so multiple CLI harnesses can coexist under
the same `cli_anything.*` namespace without conflicts.

### 2. Single Backend Module
All HTTP calls go through `utils/redtrack_backend.py`. This is the only module
that imports `requests`. Core modules import from the backend, not from requests
directly. This makes mocking trivial in unit tests.

### 3. Global CLI State
The CLI uses module-level globals (`_json_output`, `_api_key`, `_base_url`) set
in the `@click.group` callback. This pattern (from ollama harness) avoids
Click's context passing complexity while supporting the `--json` and `--api-key`
flags that apply to all subcommands.

### 4. handle_error Decorator
Every command function is wrapped with `@handle_error`, which catches
`RuntimeError` and `ValueError`. In REPL mode errors are printed and execution
continues. In one-shot mode, errors cause `sys.exit(1)` with appropriate output
(JSON error object when `--json` is set, plain text otherwise).

### 5. Dual Output Format
Every command supports both:
- **Human**: formatted with headers, tables, `─` separators
- **JSON**: `json.dumps(data, indent=2)` — consistent structure for agents

### 6. API Key Masking
Session status masks the API key. Only the first 4 and last 4 characters are
shown. Keys of 8 or fewer characters are fully masked. This prevents accidental
API key exposure in logs or terminal output.

## Campaign Cost Types

RedTrack supports the following cost models for campaigns:

| Cost Type | Description |
|-----------|-------------|
| `cpc` | Cost per click |
| `cpm` | Cost per 1000 impressions |
| `cpa` | Cost per action |
| `revshare` | Revenue share percentage |
| `auto` | Auto-detect from traffic source |
| `daily_budget` | Fixed daily budget |

## Conversion Statuses

| Status | Description |
|--------|-------------|
| `approved` | Verified conversion, counts toward KPIs |
| `pending` | Awaiting verification |
| `declined` | Rejected conversion |
| `fired` | Postback fired but not yet confirmed |

## Report Group-By Values

The `/reports` endpoint's `group_by` parameter accepts:
`campaign`, `offer`, `lander`, `traffic_channel`, `offer_source`,
`country`, `device`, `os`, `browser`, `sub1`–`sub8`

## Test Coverage Plan

1. **Unit tests** (`test_core.py`): No API key needed
   - Backend HTTP method wrappers
   - Authentication header/param inclusion
   - All error cases: connection error, HTTP errors, timeout, 204
   - Session masking
   - CLI argument parsing for every command group
   - Core module payload construction

2. **E2E tests** (`test_full_e2e.py`): Requires `REDTRACK_API_KEY`
   - Account info
   - All list commands
   - Report endpoints
   - Session display
   - Subprocess CLI invocation (with `CLI_ANYTHING_FORCE_INSTALLED=1`)
