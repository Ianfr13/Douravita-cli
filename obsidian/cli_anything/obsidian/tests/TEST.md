# TEST.md — cli-anything-obsidian

## Part 1: Test Plan

### Test Inventory

- `test_core.py`: 146 unit tests (mocked HTTP, no Obsidian needed)
- `test_full_e2e.py`: 28 E2E tests (requires running Obsidian + API key)

### Unit Test Plan (`test_core.py`)

| Module | Tests | Coverage |
|--------|-------|----------|
| `obsidian_backend.py` | URL construction, path encoding, Accept headers, API key resolution, auth headers, connection/timeout errors | 26 |
| `periodic.py` | Endpoint generation for all 5 periods, date handling, validation | 9 |
| `vault.py` | list_dir path normalization ("/", "", trailing slashes), exists, move | 7 |
| `search.py` | Input validation (empty queries), _to_list normalization | 10 |
| `dataview.py` | DQL query construction (table, list, task, calendar, raw), content-type, empty validation | 8 |
| `templater.py` | list_templates, get_template, create_from_template with vars, dest-exists guard, run_on_file | 5 |
| `foldernotes.py` | Index path (inside/outside style), exists, create auto-index, exists guard | 7 |
| `charts.py` | Bar/pie/line chart generation, title, stacked, invalid type/labels/datasets, color assignment | 7 |
| `obsidian_cli.py` | CLI arg parsing (all groups --help), --json flag, --host flag, handle_error decorator, output formatting, _resolve_content (stdin, tty, pipes, dash-content, frontmatter) | 48 |
| Bug fix verification | Status OK parsing, patch append newline, delete --yes flag, OBSIDIAN_HOST env var | 10 |
| Plugin CLI commands | Help text for all dataview/templater/foldernotes/charts subcommands | 17 |

### E2E Test Plan (`test_full_e2e.py`)

Requires Obsidian running with Local REST API plugin. Auto-skips if unavailable.

| Scenario | Tests |
|----------|-------|
| Server status (human + JSON) | 3 |
| Vault list (root, JSON, "/" normalization) | 3 |
| Vault CRUD (put, get markdown/json/map, append, replace, patch heading, create-if-missing, stdin, nonexistent) | 9 |
| Vault exists (found, missing, JSON) | 3 |
| Vault move (success, verify src deleted + dst exists) | 1 |
| Search (simple, JSON, no-results, jsonlogic) | 4 |
| Commands (list, JSON, filter, invalid run) | 4 |
| Tags (list, JSON, filter) | 3 |
| Periodic (get daily, append, specific date) | 3 |

---

## Part 2: Test Results

```
======================== 146 passed in 0.12s ========================

test_core.py::TestBackendURLs (8 tests) .......................... PASSED
test_core.py::TestAcceptHeaders (4 tests) ........................ PASSED
test_core.py::TestAPIKeyResolution (7 tests) ..................... PASSED
test_core.py::TestConnectionErrors (6 tests) ..................... PASSED
test_core.py::TestPeriodicEndpoints (9 tests) .................... PASSED
test_core.py::TestCLIArgParsing (14 tests) ....................... PASSED
test_core.py::TestNewVaultCommands (5 tests) ..................... PASSED
test_core.py::TestStatusResponseParsing (3 tests) ................ PASSED
test_core.py::TestVaultListPathNormalization (3 tests) ........... PASSED
test_core.py::TestDeleteConfirmation (3 tests) ................... PASSED
test_core.py::TestPatchAppendNewline (2 tests) ................... PASSED
test_core.py::TestObsidianHostEnvVar (1 test) .................... PASSED
test_core.py::TestContentResolution (6 tests) .................... PASSED
test_core.py::TestVaultExists (2 tests) .......................... PASSED
test_core.py::TestVaultMove (2 tests) ............................ PASSED
test_core.py::TestOutputFormatting (4 tests) ..................... PASSED
test_core.py::TestUIModule (3 tests) ............................. PASSED
test_core.py::TestPatchHeaders (2 tests) ......................... PASSED
test_core.py::TestSearchValidation (10 tests) .................... PASSED
test_core.py::TestDataviewModule (8 tests) ....................... PASSED
test_core.py::TestTemplaterModule (5 tests) ...................... PASSED
test_core.py::TestFolderNotesModule (7 tests) .................... PASSED
test_core.py::TestChartsModule (7 tests) ......................... PASSED
test_core.py::TestPluginCLICommands (17 tests) ................... PASSED
test_core.py::TestHandleErrorDecorator (4 tests) ................. PASSED
```

**Summary:** 146 unit tests, 100% pass rate, 0.11s execution time.

### E2E Tests (`test_full_e2e.py`)

```
[_resolve_cli] found: /usr/local/bin/cli-anything-obsidian
======================== 35 skipped in 0.05s ========================
```

35 E2E tests collected. All skipped — Obsidian not running in this environment.
Backend resolved correctly: `/usr/local/bin/cli-anything-obsidian`

### E2E Full Run (live Obsidian via host.docker.internal)

```
[_resolve_cli] found: /usr/local/bin/cli-anything-obsidian
OBSIDIAN_HOST=https://host.docker.internal:27124

TestServerStatus::test_status_human_output          PASSED
TestServerStatus::test_status_json_output            PASSED
TestServerStatus::test_status_shows_authenticated    PASSED
TestVaultList::test_vault_list_root                  PASSED
TestVaultList::test_vault_list_json                  PASSED
TestVaultList::test_vault_list_with_slash            PASSED
TestVaultCRUD::test_vault_put_creates_file           PASSED
TestVaultCRUD::test_vault_get_markdown               PASSED
TestVaultCRUD::test_vault_get_json_format            PASSED
TestVaultCRUD::test_vault_get_map_format             PASSED
TestVaultCRUD::test_vault_append                     PASSED
TestVaultCRUD::test_vault_put_replaces_content       PASSED
TestVaultCRUD::test_vault_patch_append_heading       PASSED
TestVaultCRUD::test_vault_patch_create_if_missing    PASSED
TestVaultCRUD::test_vault_put_stdin                  PASSED
TestVaultCRUD::test_vault_get_nonexistent_fails      PASSED
TestVaultExists::test_exists_returns_0_for_existing  PASSED
TestVaultExists::test_exists_returns_1_for_missing   PASSED
TestVaultExists::test_exists_json_output             PASSED
TestVaultMove::test_move_success                     PASSED
TestSearch::test_simple_search_returns_results       PASSED
TestSearch::test_simple_search_json                  PASSED
TestSearch::test_simple_search_no_results            PASSED
TestSearch::test_dql_search                          SKIPPED (Dataview not installed)
TestSearch::test_jsonlogic_search                    PASSED
TestCommands::test_commands_list                     PASSED
TestCommands::test_commands_list_json                PASSED
TestCommands::test_commands_list_filter              PASSED
TestCommands::test_commands_run_invalid_id           PASSED
TestTags::test_tags_list                             PASSED
TestTags::test_tags_json                             PASSED
TestTags::test_tags_filter                           PASSED
TestPeriodicNotes::test_periodic_get_daily           PASSED
TestPeriodicNotes::test_periodic_append_daily        PASSED
TestPeriodicNotes::test_periodic_get_with_specific_date PASSED

=================== 34 passed, 1 skipped in 5.81s ===================
```

### Last Run

- **Date:** 2026-03-22
- **Unit tests:** 146 passed, 0 failed (100%)
- **E2E tests:** 34 passed, 1 skipped (Dataview not installed), 0 failed (100%)
- **Backend:** `[_resolve_cli] found: /usr/local/bin/cli-anything-obsidian`
- **Host:** `https://host.docker.internal:27124` (Obsidian v1.12.4, API v3.5.0)
