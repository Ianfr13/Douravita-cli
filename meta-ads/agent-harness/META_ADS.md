# META_ADS.md — Architecture SOP for cli-anything-meta-ads

## Backend Engine

The Meta Ads CLI wraps the **Meta Graph API v21.0** directly via HTTP requests
using the `requests` library (no SDK dependency). All calls go through
`utils/meta_ads_backend.py` which provides `api_get()`, `api_post()`,
`api_delete()`, and `api_paginate()`.

Authentication: access token passed as `access_token` query param on every
request. Stored in `~/.config/cli-anything-meta-ads/config.json` or via
`META_ADS_ACCESS_TOKEN` environment variable.

## Object Hierarchy

```
Ad Account (act_XXXXXXX)
└── Campaign  (objective, budget, schedule)
    └── Ad Set  (targeting, bid, billing event)
        └── Ad  (creative assignment, tracking)

Ad Creative  (page_id + object_story_spec — image or video)
Custom Audience  (CUSTOM, WEBSITE, APP, LOOKALIKE, etc.)
```

## Data Model

No intermediate project files. Every command makes direct Graph API calls.
REPL session state (active account/campaign/adset) is persisted in
`~/.config/cli-anything-meta-ads/session.json`.

## Command Groups

| Group     | Endpoint pattern                           |
|-----------|---------------------------------------------|
| config    | Local file only                             |
| account   | `GET /me/adaccounts`, `GET /act_xxx`        |
| campaign  | `GET/POST /act_xxx/campaigns`, `POST /id`   |
| adset     | `GET/POST /act_xxx/adsets`, `POST /id`      |
| ad        | `GET/POST /act_xxx/ads`, `POST /id`         |
| creative  | `GET/POST /act_xxx/adcreatives`             |
| audience  | `GET/POST /act_xxx/customaudiences`         |
| insights  | `GET /object_id/insights`                   |
| page      | `GET /me/accounts`                          |

## Pagination

`api_paginate()` follows cursor-based pagination via `paging.cursors.after`.
Default page size: 100 objects per request.

## Budget Units

All budgets are in the account currency's smallest unit.
Example (USD): 1000 = $10.00. Pass integers to `--daily-budget`.

## Targeting Spec

The `--targeting` option accepts a JSON string:
```
--targeting '{"geo_locations": {"countries": ["BR"]}, "age_min": 18}'
```

## Error Handling

`MetaAdsAPIError` is raised for all Graph API errors, preserving message,
code, and subcode. CLI commands catch all exceptions; with `--json` they
output `{"error": "..."}`.

## Testing

- **Unit tests** (`test_core.py`): Mock API using `responses` library. No network.
- **E2E tests** (`test_full_e2e.py`): Real API calls. Require
  `META_ADS_ACCESS_TOKEN` and `META_ADS_AD_ACCOUNT_ID`. Create and clean up objects.
- **Subprocess tests**: Test the installed `cli-anything-meta-ads` command via
  `_resolve_cli("cli-anything-meta-ads")`.
