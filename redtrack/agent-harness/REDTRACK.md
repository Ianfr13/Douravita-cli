# RedTrack: Project-Specific Analysis & SOP

## Architecture Summary

RedTrack is a cloud-hosted performance marketing tracking platform accessible
exclusively via a REST API. There is no local server to run — all API calls
go to `https://api.redtrack.io`.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          RedTrack Platform                               │
│                  REST API (https://api.redtrack.io)                      │
│                                                                          │
│  /me/settings   /campaigns   /campaigns/v2   /campaigns/{id}            │
│  /campaigns/status           /offers         /offers/{id}               │
│  /offers/status  /offers/export              /networks  /networks/{id}  │
│  /landings       /landings/{id}              /sources   /sources/{id}   │
│  /conversions    /conversions/export         /report                    │
│  /rules          /rules/{id}                 /domains   /domains/{id}   │
│  /domains/regenerated_free_ssl/{id}                                     │
│  /browsers  /countries  /os  /devices  (+ 10 more unauthenticated)      │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │       CLI-Anything RedTrack Harness      │
              │        (cli-anything-redtrack)           │
              │                                          │
              │  redtrack_cli.py  (Click entry point)    │
              │  ├── core/campaigns.py                   │
              │  ├── core/offers.py                      │
              │  ├── core/landers.py                     │
              │  ├── core/traffic.py                     │
              │  ├── core/conversions.py                 │
              │  ├── core/reports.py                     │
              │  ├── core/costs.py                       │
              │  ├── core/rules.py                       │
              │  ├── core/domains.py                     │
              │  ├── core/dictionary.py                  │
              │  ├── core/session.py                     │
              │  └── utils/redtrack_backend.py           │
              └─────────────────────────────────────────┘
```

## Authentication

RedTrack uses API key authentication. The backend sends the key in **two places**
simultaneously on every authenticated request:

1. **Query parameter**: `?api_key={key}` appended to every request URL
2. **HTTP header**: `Api-Key: {key}` sent with every request

**IMPORTANT**: The real RedTrack API only accepts the `?api_key=` query parameter.
Sending the header alone returns HTTP 401. The dual approach is kept for maximum
compatibility, but the query param is the authoritative credential carrier.

**Key source priority** (highest to lowest):
1. `--api-key` command-line flag
2. `REDTRACK_API_KEY` environment variable

The API key is never logged or displayed in plain text. The `session status`
command shows a masked version: first 4 chars + asterisks + last 4 chars.
Keys of 8 characters or fewer are fully masked.

Dictionary/lookup endpoints (`/browsers`, `/countries`, etc.) are **unauthenticated**
and require no API key at all.

## CLI Strategy: REST API Wrapper

RedTrack provides a clean REST API. This CLI wraps it with:

1. **requests** — HTTP client for all API calls (only used in `redtrack_backend.py`
   and `dictionary.py`)
2. **Click CLI** — Structured command groups matching the API surface
3. **REPL** — Interactive mode via `prompt_toolkit` with command history
4. **Dual output** — Human-readable tables OR `--json` for agents/scripts

## Complete API Endpoints Map

| Endpoint | Methods | CLI Command |
|----------|---------|-------------|
| `/me/settings` | GET | `account info` |
| `/campaigns` | GET, POST | `campaign list`, `campaign create` |
| `/campaigns/v2` | GET | `campaign list-v2` |
| `/campaigns/{id}` | GET, PUT | `campaign get`, `campaign update` |
| `/campaigns/status` | PATCH | `campaign status-update`, `campaign delete` (archives) |
| `/sources` | GET, POST | `traffic list`, `traffic create` |
| `/sources/{id}` | GET, PUT, DELETE | `traffic get`, `traffic update`, `traffic delete` |
| `/offers` | GET, POST | `offer list`, `offer create` |
| `/offers/{id}` | GET, PUT | `offer get`, `offer update` |
| `/offers/status` | PATCH | `offer status-update`, `offer delete` (archives) |
| `/offers/export` | GET | `offer export` |
| `/networks` | GET, POST | `offer-source list`, `offer-source create` |
| `/networks/{id}` | GET, PUT, DELETE | `offer-source get`, `offer-source update`, `offer-source delete` |
| `/landings` | GET, POST | `lander list`, `lander create` |
| `/landings/{id}` | GET, PUT, DELETE | `lander get`, `lander update`, `lander delete` |
| `/conversions` | GET, POST | `conversion list`, `conversion upload` |
| `/conversions/export` | GET | `conversion export` |
| `/report` | GET | `report general`, `report campaigns`, `report clicks`, `report stream`, `cost list` |
| `/domains` | GET, POST | `domain list`, `domain add` |
| `/domains/{id}` | PUT, DELETE | `domain update`, `domain delete` |
| `/domains/regenerated_free_ssl/{id}` | POST | `domain ssl-renew` |
| `/rules` | GET, POST | `rule list`, `rule create` |
| `/rules/{id}` | GET, PATCH, DELETE | `rule get`, `rule update`, `rule delete` |
| `/browsers`, `/countries`, `/os`, etc. | GET (no auth) | `lookup get <type>` |

## Endpoints That Do NOT Exist

These endpoints return 404 from the real RedTrack API and must not be used:

| Endpoint | Status | Correct Alternative |
|----------|--------|---------------------|
| `/costs` | 404 — confirmed with real API | Cost data accessed via `GET /report?group_by=campaign` |
| `/costs/auto` | 404 | No equivalent — cost automation is dashboard-only |
| `/user` | 404 | Use `/me/settings` instead |
| `DELETE /campaigns/{id}` | Does not exist | Archive via `PATCH /campaigns/status` with `status=archived` |

The old REDTRACK.md incorrectly listed `/user`, `/costs`, `/costs/auto`,
`/offer_sources`, `/traffic_channels`, `/reports`, `/reports/campaigns`,
and `/clicks` as valid endpoints. None of these exist. The correct endpoints
are `/me/settings`, `/networks`, `/sources`, and `/report` respectively.

## Module Structure

Each module in `core/` is a thin function library. No module imports from
another core module (except `campaigns.py` calling its own helpers). All HTTP
calls are delegated to `utils/redtrack_backend.py`.

### `core/campaigns.py`
Wraps `/campaigns` and `/campaigns/v2` and `/campaigns/status`.
Functions: `list_campaigns`, `get_campaign`, `create_campaign`,
`update_campaign` (PUT), `update_campaign_statuses` (bulk PATCH to
`/campaigns/status`), `get_campaign_links` (GET campaign, extract URL fields),
`list_campaigns_v2`.

### `core/offers.py`
Wraps `/offers`, `/offers/status`, `/offers/export`, and `/networks`.
Functions: `list_offers`, `get_offer`, `create_offer`, `update_offer` (PUT),
`update_offer_statuses` (PATCH `/offers/status`), `export_offers` (GET
`/offers/export`), `delete_offer` (DELETE `/offers/{id}` — confirm support
before relying on this), `list_offer_sources`, `get_offer_source`,
`create_offer_source`, `update_offer_source` (PUT), `delete_offer_source`.

### `core/landers.py`
Full CRUD via `/landings` (note: CLI group is `lander`, API path is `/landings`).
Functions: `list_landers`, `get_lander`, `create_lander`, `update_lander` (PUT),
`delete_lander`.

### `core/traffic.py`
Full CRUD via `/sources` (note: CLI group is `traffic`, API path is `/sources`).
Functions: `list_traffic_channels`, `get_traffic_channel`,
`create_traffic_channel`, `update_traffic_channel` (PUT),
`delete_traffic_channel`.

### `core/conversions.py`
Wraps `/conversions` and `/conversions/export`.
Functions: `list_conversions`, `upload_conversion` (POST), `export_conversions`
(GET `/conversions/export`), `get_conversion_types` (local constant — no API call).

### `core/reports.py`
All report variants call the single `/report` endpoint with different `group_by`
values. Functions: `general_report` (flexible group_by), `campaigns_report`
(`group_by=campaign`), `stream_report` (`group_by=stream`), `click_logs`
(`group_by=click`).

### `core/costs.py`
There is no `/costs` endpoint. `get_cost_from_report()` proxies through
`GET /report?group_by=campaign` and returns cost metrics embedded in the
report response. The `cost list` CLI command uses this function.

### `core/rules.py`
CRUD via `/rules` and `/rules/{id}`. Uses PATCH (not PUT) for updates.
Note: `/rules` endpoints are not formally confirmed in RedTrack's Swagger
documentation but are implemented based on RedTrack's documented automation
rules feature.
Functions: `list_rules`, `get_rule`, `create_rule`, `update_rule` (PATCH),
`delete_rule`.

### `core/domains.py`
Full CRUD plus SSL renewal via `/domains`, `/domains/{id}`, and
`/domains/regenerated_free_ssl/{id}`.
Functions: `list_domains`, `add_domain`, `update_domain` (PUT),
`delete_domain`, `regenerate_ssl` (POST).

### `core/dictionary.py`
14 unauthenticated reference endpoints. Makes direct `requests.get()` calls
(no API key). Raises `RuntimeError` on connection failure, HTTP error, or timeout.
Functions: `get_browsers`, `get_browser_fullnames`, `get_categories`,
`get_cities`, `get_connection_types`, `get_countries`, `get_currencies`,
`get_device_brands`, `get_device_fullnames`, `get_devices`, `get_isp`,
`get_languages`, `get_os`, `get_os_fullnames`, `list_all_keys`.

### `core/session.py`
Local session info only — no API calls. Functions: `get_session_info` (returns
masked key + base URL), `_mask_key` (shows first 4 + last 4, rest asterisks).

### `utils/redtrack_backend.py`
The **only** module that calls `requests` for authenticated API calls.
Functions: `api_get`, `api_post`, `api_put`, `api_patch`, `api_delete`,
`is_available` (probes `/me/settings`), `_get_api_key`, `_build_params`,
`_build_headers`.

All five HTTP method wrappers follow the same pattern:
- Resolve API key via `_get_api_key()`
- Build URL as `{base_url}{endpoint}`
- Always include `?api_key=` query param via `_build_params()`
- Always include `Api-Key:` header via `_build_headers()`
- On HTTP 204 or empty body: return `{"status": "ok"}`
- On `ConnectionError`, `HTTPError`, or `Timeout`: raise `RuntimeError`

## Response Shape Variations

The RedTrack API is not consistent in its response envelope. The CLI handles
all cases transparently:

| Response shape | Endpoints | CLI handling |
|----------------|-----------|--------------|
| `null` | `/campaigns`, `/offers`, `/landings`, `/networks` when empty | `_extract_list()` returns empty list |
| `[]` | `/rules`, `/report` when empty | treated as empty list |
| `{"items": [...], "total": N}` | `/conversions`, `/domains` | paginated — iterate `items` key |
| Raw object | Single resource GET | displayed as dict |

The `_extract_list()` helper in `redtrack_cli.py` normalises the first three
cases. It returns the response as-is if it's already a list, reads `data` key
from a dict if present, or returns the dict unchanged otherwise.

## Pagination

The RedTrack API uses `page` (1-based) and `per` (results per page) parameters.

**Do NOT use** `limit` or `offset` — these are not supported.

Endpoints with pagination: `/campaigns`, `/campaigns/v2`, `/domains`.
Endpoints that return all records without pagination: `/offers`, `/networks`,
`/landings`, `/sources`, `/rules`.

## Key Design Decisions

### 1. Namespace Package (PEP 420)
The `cli_anything/` directory has no `__init__.py`. This is intentional —
it uses Python namespace packages so multiple CLI harnesses can coexist under
the same `cli_anything.*` namespace without conflicts.

### 2. Single Backend Module
All authenticated HTTP calls go through `utils/redtrack_backend.py`. This is
the only module that imports `requests` for authenticated calls. Core modules
import from the backend, not from requests directly. This makes mocking trivial
in unit tests.

### 3. Global CLI State
The CLI uses module-level globals (`_json_output`, `_api_key`, `_base_url`) set
in the `@click.group` callback. This pattern avoids Click's context passing
complexity while supporting the `--json` and `--api-key` flags that apply to
all subcommands.

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

### 7. No /costs Endpoint
There is no `/costs` API endpoint. All cost metrics are embedded in `/report`
responses. The `cost list` command transparently calls `GET /report?group_by=campaign`.
This is documented in `core/costs.py` with a module-level NOTE.

### 8. Archiving vs. Deletion for Campaigns
RedTrack does not expose `DELETE /campaigns/{id}`. The `campaign delete` CLI
command calls `PATCH /campaigns/status` with `status=archived`. The CLI prompts
for confirmation unless `--confirm` is passed.

## Campaign Cost Types

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

## Conversion Types

Standard event types accepted by the `conversion upload` command:
`conversion`, `lead`, `sale`, `install`, `registration`, `deposit`, `custom`

## Report group_by Values

The `/report` endpoint's `group_by` parameter selects the grouping dimension.
Valid values used by this CLI:

| Value | Used by |
|-------|---------|
| `campaign` | `report campaigns`, `cost list` |
| `click` | `report clicks` |
| `stream` | `report stream` |
| `offer` | `report general --group-by offer` |
| `lander` | `report general --group-by lander` |
| `source` | `report general --group-by source` |
| `network` | `report general --group-by network` |
| `country` | `report general --group-by country` |
| `device` | `report general --group-by device` |
| `os` | `report general --group-by os` |
| `browser` | `report general --group-by browser` |

## Lookup Types

All 14 dictionary endpoints are unauthenticated (`no api_key` required):

| Lookup key | API endpoint |
|------------|-------------|
| `browsers` | `/browsers` |
| `browser_fullnames` | `/browser_fullnames` |
| `categories` | `/categories` |
| `cities` | `/cities` |
| `connection_types` | `/connection_types` |
| `countries` | `/countries` |
| `currencies` | `/currencies` |
| `device_brands` | `/device_brands` |
| `device_fullnames` | `/device_fullnames` |
| `devices` | `/devices` |
| `isp` | `/isp` |
| `languages` | `/languages` |
| `os` | `/os` |
| `os_fullnames` | `/os_fullnames` |

Use `lookup list` to display all keys; `lookup get <key>` to retrieve data.

## Test Coverage Plan

### Unit tests (`test_core.py`) — no API key needed
- Backend HTTP method wrappers (`api_get`, `api_post`, `api_put`, `api_patch`,
  `api_delete`)
- Authentication: confirm `?api_key=` query param is always included
- Authentication: confirm `Api-Key:` header is always included
- Error cases: `ConnectionError` → `RuntimeError`, HTTP 4xx/5xx → `RuntimeError`,
  `Timeout` → `RuntimeError`, HTTP 204 / empty body → `{"status": "ok"}`
- `_get_api_key`: raises when neither arg nor env var is set
- `is_available`: returns True on 200, False on error
- Session masking: short keys fully masked, long keys show first4/last4
- `_extract_list()`: handles list, dict-with-data, None
- Core module payload construction (campaigns, offers, conversions, etc.)
- CLI argument parsing for every command group (using Click's test runner)
- Dictionary module: `list_all_keys` returns all 14 entries

### E2E tests (`test_full_e2e.py`) — requires `REDTRACK_API_KEY`
- `account info` calls `/me/settings` and returns non-error response
- `campaign list` returns list or null (no exception)
- `offer list` returns list or null
- `traffic list` returns list or null
- `lander list` returns list or null
- `domain list` returns paginated response
- `report general` returns data or empty list
- `cost list` calls `/report` (not `/costs`) and succeeds
- `lookup get countries` returns data without API key
- `session status` shows masked key
- Subprocess CLI invocation via `CLI_ANYTHING_FORCE_INSTALLED=1`
