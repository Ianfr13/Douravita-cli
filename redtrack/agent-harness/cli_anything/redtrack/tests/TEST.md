# RedTrack CLI — Test Plan & Results

## Test Strategy

The test suite is split into two files:

- **`test_core.py`** — 139 unit tests. No real API key required. All HTTP calls are mocked.
- **`test_full_e2e.py`** — 32 E2E tests. Most require `REDTRACK_API_KEY` to be set in the environment. Subprocess tests additionally require `CLI_ANYTHING_FORCE_INSTALLED=1` and a pip-installed CLI.

---

## Unit Tests (`test_core.py`)

All 139 tests run without a real API key. A dummy key (`test_api_key_1234`) is injected via a module-level autouse fixture. CLI globals are reset after every test to prevent state leakage.

### TestBackendConstants
Verifies `DEFAULT_BASE_URL == "https://api.redtrack.io"`.

### TestGetApiKey
- Explicit key is returned as-is
- Key is read from `REDTRACK_API_KEY` env var
- `RuntimeError("No API key")` is raised when env var is absent
- Explicit key overrides the env var

### TestBuildParams
- `api_key` is always injected into the params dict
- Extra params are merged correctly
- Empty extra-params dict produces only `{"api_key": ...}`

### TestBuildHeaders
Covered as part of `TestApiGet` — both `Api-Key` header and `api_key` query param are verified.

### TestApiGet
- `200` response returns parsed JSON body
- URL is constructed as `base_url + path`; trailing slash on base URL is stripped
- `api_key` appears in both query params and `Api-Key` header
- `ConnectionError` → `RuntimeError("Cannot connect to RedTrack")`
- HTTP error (e.g. 401) → `RuntimeError("RedTrack API error 401 ...")`
- `Timeout` → `RuntimeError("timed out")`
- `204 No Content` → `{"status": "ok"}`

### TestApiPost
- `201` response returns parsed JSON body
- `ConnectionError` / `Timeout` / HTTP error handling mirrors `api_get`
- `204 No Content` → `{"status": "ok"}`

### TestApiPut (NEW)
- Verifies `requests.put` is called exactly once and returns the parsed response body

### TestApiPatch
- `200` response returns the updated body
- `ConnectionError`, `Timeout`, HTTP error (404) all raise `RuntimeError` with the expected messages

### TestApiDelete
- `204` response → `{"status": "ok"}`
- `ConnectionError`, HTTP error (404), `Timeout` raise `RuntimeError`

### TestIsAvailable (FIXED)
- Valid key + 200 response → `True`
- `ConnectionError` → `False`
- `Timeout` → `False`
- Missing env key → `False` (no request made)
- Non-200 status (401) → `False`
- Confirms the probe hits `/me/settings`

### TestSessionMasking
- `_mask_key(None)` / `_mask_key("")` → `"(not set)"`
- Short key (≤8 chars) → all asterisks
- Long key → first 4 + asterisks + last 4 preserved

### TestGetSessionInfo
- With a key: returns `authenticated: True`; raw key value is absent from output
- Without a key: returns `authenticated: False` and `api_key: "(not set)"`

### TestCoreCampaigns
- `list_campaigns` sends `page`/`per` params (not `limit`/`offset`)
- `create_campaign` payload contains `name`, `traffic_channel_id`, `cost_type`, `cost_value`
- `update_campaign` sends only the fields that were changed and issues a PUT request
- `update_campaign_statuses` calls `PATCH /campaigns/status` with `{"ids": [...], "status": ...}` (NEW)

### TestUpdateCampaignStatuses (NEW)
- Confirms `api_patch` is called on `/campaigns/status` with the correct ids array and status value

### TestCampaignListV2 (NEW)
- `list_campaigns_v2` hits `/campaigns/v2`

### TestCoreOffers
- `update_offer_statuses` calls `PATCH /offers/status` with ids array (NEW)
- `create_offer` with `network_id` includes it in the payload (NEW)

### TestUpdateOfferStatuses (NEW)
- Confirms `api_patch` is called on `/offers/status`

### TestExportOffers (NEW)
- `export_offers` hits `/offers/export`

### TestCreateOfferNetworkId (NEW)
- `create_offer` with `network_id` includes `network_id` in the POST payload

### TestCoreLanders
- `lander list` — empty and non-empty, JSON and human modes
- `lander create --name ... --url ...`
- `lander delete <id>`
- `lander update` issues a PUT request

### TestCoreTraffic
- `traffic list` — empty and non-empty, JSON mode
- `traffic create --name ...`
- `traffic delete <id>`

### TestCoreConversions
- `upload_conversion` payload maps `conversion_type` to the `type` field
- `get_conversion_types()` returns a list that includes `"conversion"`, `"sale"`, `"lead"`

### TestExportConversions (NEW)
- `export_conversions` hits `/conversions/export` with `date_from` in query params

### TestCoreReports
- `stream_report` sends `group_by=stream` to the report endpoint

### TestCoreCosts
- `cost list` calls `GET /report` (costs are derived from the report endpoint, not a dedicated `/costs` path)
- `cost list --date-from ... --date-to ...`

### TestCoreRules
- `rule list` — empty and non-empty, JSON mode
- `rule get <id>`
- `rule create --name ... --condition ... --action ...`
- `rule update <id> --status active`
- `rule delete <id>`

### TestDomainsModule (NEW)
- `list_domains` hits `/domains`
- `update_domain` issues a PUT to `/domains/<id>`
- `delete_domain` issues DELETE → `{"status": "ok"}`
- `regenerate_ssl` POSTs to `/domains/regenerated_free_ssl/<id>`

### TestDictionaryModule (NEW)
- `get_countries` hits `/countries` without sending `api_key` (no auth required)
- `list_all_keys()` returns exactly 14 keys (countries, browsers, os, …)

### TestNullResponseHandling (NEW)
- `204 No Content` from GET, POST, and DELETE all return `{"status": "ok"}` rather than raising

### TestGetCostFromReport (NEW)
- Confirms the cost module resolves costs via `GET /report` rather than a dedicated costs endpoint

### TestCLIParsing (CLI argument parsing tests)
- `--help` exits 0 and mentions "RedTrack"
- `--help` for every command group (`campaign`, `offer`, `offer-source`, `traffic`, `lander`, `conversion`, `report`, `cost`, `rule`, `domain`, `session`) exits 0 and shows expected subcommands
- `--json session status` returns valid JSON with `api_key` and `base_url`
- `--base-url` flag overrides `base_url` in session status
- `--api-key` flag is masked in session status output

### TestCampaignCommands
- `campaign list` — empty list shows "No campaigns"; list with items works in both JSON and human mode
- `campaign get <id>` — returns item JSON
- `campaign create` — minimal and full-option invocations
- `campaign update <id>` — calls `api_put`; output contains "updated"
- `campaign delete <id> --confirm` — calls `api_patch`; output contains "archived"
- `campaign links <id>` — exits 0
- Error path: `--json` mode returns `{"error": ...}`; human mode exits 1

### TestOfferCommands
- `offer list` — empty and non-empty, JSON and human modes
- `offer get <id>`
- `offer create --name ... --payout ...`
- `offer update <id>`
- `offer delete <id>` — output contains "deleted"

### TestLookupCLI (NEW)
- `lookup list` returns JSON with `available_lookups` containing 14 entries
- `lookup get countries` returns a list
- `lookup get foobar` exits non-zero

### TestCampaignStatusUpdateCLI
- `campaign delete <id> --confirm` sends `PATCH /campaigns/status` with `{"ids": ["<id>"], "status": "archived"}`

### TestOfferStatusUpdateCLI
- Covered by `TestCoreOffers` / `TestUpdateOfferStatuses`

### TestCampaignDeleteArchive
- `campaign delete <id> --confirm` sends `PATCH /campaigns/status` with `{"ids": ["<id>"], "status": "archived"}`

### TestMissingApiKey
- `campaign list` with no key → exits 1
- `--json campaign list` with no key → exits 1 with `{"error": ...}` JSON

---

## E2E Tests (`test_full_e2e.py`)

Most test classes are decorated with `@_skip_no_key` and are skipped when `REDTRACK_API_KEY` is not set. Subprocess tests additionally check for `CLI_ANYTHING_FORCE_INSTALLED=1`.

### TestAccountE2E
- `GET /user` returns a dict; human mode shows "Account Info"

### TestAvailabilityE2E
- `is_available()` with valid key → `True`
- `is_available()` with an invalid key → `False`

### TestCampaignE2E
- `GET /campaigns` returns a list or dict
- `GET /campaigns` with date range using `page`/`per` pagination
- Human mode does not error

### TestCampaignStatusE2E (NEW)
- Bulk campaign status update (mocked): 3 IDs → `{"updated": 3}` (covered by `TestBulkOperationsE2E`)

### TestCampaignV2E2E (NEW)
- `GET /campaigns/v2` via `campaign list-v2`

### TestOfferE2E
- `GET /offers` — JSON and human modes

### TestOfferSourceE2E
- `GET /offer_sources`

### TestTrafficE2E
- `GET /traffic_channels`

### TestLanderE2E
- `GET /landers`

### TestReportE2E
- `GET /reports` (general, with date range)
- `GET /reports/campaigns`
- `GET /clicks`

### TestReportStreamE2E (NEW)
- `stream_report` sends `group_by=stream` (also covered by `TestCoreReports` in unit tests)

### TestConversionE2E
- `GET /conversions` with date range
- `conversion types` returns static list (no API call)

### TestDomainE2E (NEW)
- `GET /domains`

### TestRuleE2E
- `GET /rules`

### TestLookupE2E (NEW)
- `GET /countries` (no auth required)
- `GET /browsers`
- `lookup list` returns `available_lookups`

### TestSessionE2E
- Session status shows masked key and correct base URL

### TestCLISubprocess
7 subprocess tests (skipped unless `CLI_ANYTHING_FORCE_INSTALLED=1`):
- `--help` exits 0
- `--help` output is non-empty
- `campaign list --json` returns a list or dict
- `account info --json` returns a dict
- `session status --json` contains `api_key` and `base_url`
- Nonexistent command exits non-zero
- Missing API key exits non-zero

---

## Test Results

| Suite | Tests | Status | Notes |
|-------|------:|--------|-------|
| `test_core.py` | 139/139 | passing | No API key needed |
| `test_full_e2e.py` | 25/25 | passing | Requires `REDTRACK_API_KEY`; 7 subprocess tests skipped without `CLI_ANYTHING_FORCE_INSTALLED=1` |

---

## Running Tests

```bash
cd redtrack/agent-harness

# Unit tests (no API key needed)
python3 -m pytest cli_anything/redtrack/tests/test_core.py -v

# E2E tests (requires real API key)
REDTRACK_API_KEY=your_key python3 -m pytest cli_anything/redtrack/tests/test_full_e2e.py -v

# All tests with subprocess CLI tests
CLI_ANYTHING_FORCE_INSTALLED=1 REDTRACK_API_KEY=your_key python3 -m pytest cli_anything/redtrack/tests/ -v -s

# Single test by name
python3 -m pytest cli_anything/redtrack/tests/test_core.py -v -k "test_update_campaign_uses_put"

# With coverage
python3 -m pytest cli_anything/redtrack/tests/test_core.py -v \
    --cov=cli_anything.redtrack --cov-report=term-missing
```

---

## Known Gaps

- **Rule conditions/actions schema** — the full JSON schema for rule payloads is undocumented; tests only verify that the POST is made with the provided raw condition/action strings.
- **Offer export and conversion export** — `export_offers` and `export_conversions` are unit-tested for correct endpoint routing, but E2E validation requires real data in the account.
- **Domain mutation operations** — `domain add`, `domain update`, and `regenerate_ssl` are unit-tested but E2E tests only cover `domain list`, since mutations require a real custom domain registered in the account.
- **Cost update / cost auto** — `cost update` and `cost auto` CLI commands are not covered by unit tests; costs are retrieved via `GET /report`, not a dedicated `/costs` endpoint.
