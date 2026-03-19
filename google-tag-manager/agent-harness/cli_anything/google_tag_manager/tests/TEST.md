# TEST.md — Google Tag Manager CLI Test Plan

## Test Inventory Plan

| File | Type | Tests Planned |
|------|------|---------------|
| `test_core.py` | Unit tests (no API required) | 45 |
| `test_full_e2e.py` | E2E tests (real GTM API required) | 20 |

---

## Unit Test Plan (`test_core.py`)

All unit tests mock the GTM API service and test core logic in isolation.
No external dependencies or network calls are made.

### Module: `core/session.py`
- `test_session_default_init` — Session loads empty when no file exists
- `test_session_set_and_get_account_id` — account_id getter/setter persists
- `test_session_set_and_get_container_id` — container_id getter/setter persists
- `test_session_set_and_get_workspace_id` — workspace_id getter/setter persists
- `test_session_env_override` — GTM_ACCOUNT_ID env var overrides session file
- `test_session_require_account_raises` — require_account() raises if not set
- `test_session_require_container_raises` — require_container() raises if not set
- `test_session_require_workspace_raises` — require_workspace() raises if not set
- `test_session_set_context` — set_context() updates multiple IDs at once
- `test_session_clear` — clear() resets all data
- `test_session_to_dict` — to_dict() serializes correctly

### Module: `core/accounts.py`
- `test_list_accounts_success` — list_accounts returns list of dicts
- `test_get_account_validates_id` — get_account raises on empty account_id
- `test_update_account_name` — update_account sends correct body
- `test_account_format_row` — format_account_row outputs correct columns
- `test_list_accounts_http_error` — HttpError wrapped as RuntimeError

### Module: `core/containers.py`
- `test_list_containers_success` — returns container list
- `test_create_container_validates_name` — rejects empty name
- `test_create_container_validates_context` — rejects invalid usage_context
- `test_create_container_valid_contexts` — accepts all valid usage contexts
- `test_delete_container_returns_dict` — delete returns {"deleted": True}
- `test_get_snippet_success` — returns snippet dict
- `test_container_format_row` — format_container_row correct columns

### Module: `core/workspaces.py`
- `test_list_workspaces_success` — returns workspace list
- `test_create_workspace_validates_name` — rejects empty name
- `test_workspace_status_success` — returns status dict
- `test_sync_workspace_success` — returns sync result
- `test_create_version_success` — returns version dict
- `test_workspace_format_row` — truncates fingerprint to 12 chars

### Module: `core/tags.py`
- `test_list_tags_success` — returns tag list
- `test_create_tag_validates_name` — rejects empty name
- `test_create_tag_validates_type` — rejects empty type
- `test_create_tag_validates_firing_option` — rejects invalid firing option
- `test_delete_tag_returns_dict` — returns {"deleted": True, "tag_id": ...}
- `test_tag_format_row` — truncates long trigger lists
- `test_create_tag_with_parameters` — passes parameters correctly

### Module: `core/triggers.py`
- `test_list_triggers_success` — returns trigger list
- `test_create_trigger_validates_name` — rejects empty name
- `test_create_trigger_validates_type` — rejects empty type
- `test_delete_trigger_returns_dict` — returns {"deleted": True}
- `test_trigger_format_row` — correct columns

### Module: `core/variables.py`
- `test_list_variables_success` — returns variable list
- `test_create_variable_validates_name` — rejects empty name
- `test_create_variable_validates_type` — rejects empty type
- `test_delete_variable_returns_dict` — returns {"deleted": True}

### Module: `core/permissions.py`
- `test_create_permission_validates_email` — rejects invalid email
- `test_create_permission_validates_account_access` — rejects invalid access level
- `test_create_permission_validates_container_access` — rejects missing containerId
- `test_delete_permission_returns_dict` — returns {"revoked": True}
- `test_permission_format_row` — extracts email and access correctly

---

## E2E Test Plan (`test_full_e2e.py`)

These tests require real GTM API credentials. Set:
- `GOOGLE_APPLICATION_CREDENTIALS` or `GTM_CREDENTIALS_FILE`
- `GTM_ACCOUNT_ID` — the account to use for testing

**WARNING**: These tests create and delete real GTM resources.
Use a dedicated test GTM account/container.

### Authentication Tests
- `test_auth_service_account` — authenticates with service account
- `test_list_real_accounts` — lists accessible accounts

### Container Lifecycle Tests
- `test_create_and_delete_container` — create a test container, verify it appears in list, delete it
- `test_container_snippet` — verify snippet response has correct structure

### Workspace Tests
- `test_list_workspaces_in_container` — list workspaces (requires container)
- `test_workspace_status` — get workspace status dict

### Tag/Trigger/Variable Tests
- `test_create_pageview_trigger` — create All Pages trigger
- `test_create_html_tag` — create custom HTML tag with trigger
- `test_create_constant_variable` — create a constant variable
- `test_tag_list_after_create` — verify new tag appears in list
- `test_delete_created_resources` — clean up test resources

### Version Tests
- `test_list_version_headers` — returns list (may be empty for new container)
- `test_workspace_quick_preview` — creates preview URL

### CLI Subprocess Tests (`TestCLISubprocess`)
- `test_help` — `--help` returns exit code 0
- `test_help_subcommands` — each major subcommand `--help` works
- `test_auth_info_json` — `auth info --json` returns valid JSON
- `test_account_list_json` — `account list --json` returns JSON array
- `test_container_list_json` — `container list --json` with account ID

---

## Realistic Workflow Scenarios

### Scenario 1: GA4 Setup Workflow
**Simulates**: Setting up Google Analytics 4 tracking on a website
**Operations**:
1. Create a workspace "GA4 Setup"
2. Create "All Pages" pageview trigger
3. Create GA4 Configuration tag linked to trigger
4. Create GA4 Event tag for button clicks
5. Check workspace status
6. Create version "GA4 Initial Setup"
**Verified**: All resources appear in respective list commands with correct types

### Scenario 2: Container Migration
**Simulates**: Copying tag structure to a new container
**Operations**:
1. List all tags, triggers, variables in source workspace
2. Create equivalent resources in target workspace
3. Verify counts match
**Verified**: Resource counts match between workspaces

### Scenario 3: Permission Management
**Simulates**: Onboarding a new team member
**Operations**:
1. Grant user@example.com read access to account
2. Grant edit access to specific container
3. Verify permission appears in list
4. Revoke permission
**Verified**: Permission lifecycle completes without errors

### Scenario 4: Environment Setup
**Simulates**: Setting up staging/production environments
**Operations**:
1. List default environments (live, latest)
2. Create "Staging" user environment with staging URL
3. Get the auth code for the environment
4. Reauthorize to get a new auth code
**Verified**: Environment created, auth code present and changes after reauth

---

## Test Results

### Unit Tests — `test_core.py`

Run: `python3 -m pytest cli_anything/google_tag_manager/tests/test_core.py -v`

```
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-9.0.2, pluggy-1.6.0
collected 74 items

test_core.py::TestSession::test_session_default_init PASSED
test_core.py::TestSession::test_session_set_and_get_account_id PASSED
test_core.py::TestSession::test_session_set_and_get_container_id PASSED
test_core.py::TestSession::test_session_set_and_get_workspace_id PASSED
test_core.py::TestSession::test_session_env_override PASSED
test_core.py::TestSession::test_session_require_account_raises PASSED
test_core.py::TestSession::test_session_require_container_raises PASSED
test_core.py::TestSession::test_session_require_workspace_raises PASSED
test_core.py::TestSession::test_session_set_context PASSED
test_core.py::TestSession::test_session_clear PASSED
test_core.py::TestSession::test_session_to_dict PASSED
test_core.py::TestAccounts::test_list_accounts_success PASSED
test_core.py::TestAccounts::test_list_accounts_empty PASSED
test_core.py::TestAccounts::test_get_account_validates_id PASSED
test_core.py::TestAccounts::test_get_account_success PASSED
test_core.py::TestAccounts::test_update_account_name PASSED
test_core.py::TestAccounts::test_account_format_row PASSED
test_core.py::TestAccounts::test_list_accounts_http_error PASSED
test_core.py::TestContainers::test_list_containers_success PASSED
test_core.py::TestContainers::test_create_container_validates_name PASSED
test_core.py::TestContainers::test_create_container_validates_context PASSED
test_core.py::TestContainers::test_create_container_valid_contexts PASSED
test_core.py::TestContainers::test_create_container_validates_empty_context PASSED
test_core.py::TestContainers::test_delete_container_returns_dict PASSED
test_core.py::TestContainers::test_get_snippet_success PASSED
test_core.py::TestContainers::test_container_format_row PASSED
test_core.py::TestWorkspaces::test_list_workspaces_success PASSED
test_core.py::TestWorkspaces::test_create_workspace_validates_name PASSED
test_core.py::TestWorkspaces::test_workspace_status_success PASSED
test_core.py::TestWorkspaces::test_sync_workspace_success PASSED
test_core.py::TestWorkspaces::test_create_version_success PASSED
test_core.py::TestWorkspaces::test_workspace_format_row PASSED
test_core.py::TestTags::test_list_tags_success PASSED
test_core.py::TestTags::test_create_tag_validates_name PASSED
test_core.py::TestTags::test_create_tag_validates_type PASSED
test_core.py::TestTags::test_create_tag_validates_firing_option PASSED
test_core.py::TestTags::test_delete_tag_returns_dict PASSED
test_core.py::TestTags::test_tag_format_row PASSED
test_core.py::TestTags::test_create_tag_with_parameters PASSED
test_core.py::TestTags::test_tag_format_row_truncates_long_triggers PASSED
test_core.py::TestTriggers::test_list_triggers_success PASSED
test_core.py::TestTriggers::test_create_trigger_validates_name PASSED
test_core.py::TestTriggers::test_create_trigger_validates_type PASSED
test_core.py::TestTriggers::test_delete_trigger_returns_dict PASSED
test_core.py::TestTriggers::test_trigger_format_row PASSED
test_core.py::TestVariables::test_list_variables_success PASSED
test_core.py::TestVariables::test_create_variable_validates_name PASSED
test_core.py::TestVariables::test_create_variable_validates_type PASSED
test_core.py::TestVariables::test_delete_variable_returns_dict PASSED
test_core.py::TestVariables::test_variable_format_row PASSED
test_core.py::TestPermissions::test_create_permission_validates_email PASSED
test_core.py::TestPermissions::test_create_permission_validates_account_access PASSED
test_core.py::TestPermissions::test_create_permission_validates_container_access PASSED
test_core.py::TestPermissions::test_create_permission_validates_container_permission PASSED
test_core.py::TestPermissions::test_delete_permission_returns_dict PASSED
test_core.py::TestPermissions::test_permission_format_row PASSED
test_core.py::TestPermissions::test_list_permissions_validates_account PASSED
test_core.py::TestFolders::test_list_folders_success PASSED
test_core.py::TestFolders::test_create_folder_validates_name PASSED
test_core.py::TestFolders::test_delete_folder_returns_dict PASSED
test_core.py::TestFolders::test_move_to_folder_requires_entities PASSED
test_core.py::TestFolders::test_folder_format_row PASSED
test_core.py::TestEnvironments::test_create_environment_validates_name PASSED
test_core.py::TestEnvironments::test_create_environment_validates_type PASSED
test_core.py::TestEnvironments::test_delete_environment_returns_dict PASSED
test_core.py::TestEnvironments::test_environment_format_row PASSED
test_core.py::TestVersions::test_list_version_headers_success PASSED
test_core.py::TestVersions::test_latest_version_header_success PASSED
test_core.py::TestVersions::test_version_format_row PASSED
test_core.py::TestValidationEdgeCases::test_containers_requires_account_and_container PASSED
test_core.py::TestValidationEdgeCases::test_workspaces_requires_all_ids PASSED
test_core.py::TestValidationEdgeCases::test_tags_requires_all_ids PASSED
test_core.py::TestValidationEdgeCases::test_triggers_requires_all_ids PASSED
test_core.py::TestValidationEdgeCases::test_variables_requires_all_ids PASSED

============================== 74 passed in 0.27s ==============================
```

### CLI Subprocess Tests — `TestCLISubprocess`

Run: `CLI_ANYTHING_FORCE_INSTALLED=1 python3 -m pytest cli_anything/google_tag_manager/tests/test_full_e2e.py::TestCLISubprocess -v -s`

```
[_resolve_cli] Using installed command: /home/sandbox/.local/bin/cli-anything-google-tag-manager

test_full_e2e.py::TestCLISubprocess::test_help PASSED
test_full_e2e.py::TestCLISubprocess::test_account_help PASSED
test_full_e2e.py::TestCLISubprocess::test_container_help PASSED
test_full_e2e.py::TestCLISubprocess::test_workspace_help PASSED
test_full_e2e.py::TestCLISubprocess::test_tag_help PASSED
test_full_e2e.py::TestCLISubprocess::test_trigger_help PASSED
test_full_e2e.py::TestCLISubprocess::test_variable_help PASSED
test_full_e2e.py::TestCLISubprocess::test_auth_info_json PASSED
test_full_e2e.py::TestCLISubprocess::test_account_list_json_with_credentials SKIPPED (GOOGLE_APPLICATION_CREDENTIALS not set)
test_full_e2e.py::TestCLISubprocess::test_container_list_json_with_account SKIPPED (GTM_ACCOUNT_ID and GOOGLE_APPLICATION_CREDENTIALS required)
test_full_e2e.py::TestCLISubprocess::test_no_credentials_shows_clear_error PASSED

========================= 9 passed, 2 skipped in 2.42s =========================
```

### Summary

| Suite | Tests | Passed | Skipped | Failed |
|-------|-------|--------|---------|--------|
| `test_core.py` (unit) | 74 | 74 | 0 | 0 |
| `test_full_e2e.py::TestCLISubprocess` | 11 | 9 | 2 | 0 |

**Total: 83 tests, 83 pass (74 unit + 9 subprocess). 2 subprocess tests skipped — require GTM API credentials.**

### Coverage Notes

- All 11 core modules covered by unit tests
- Full input validation coverage for all resource types
- HTTP error wrapping tested for accounts module (pattern applies to all)
- E2E API tests (requires GTM credentials): 20 planned scenarios covering auth, container lifecycle, workspace operations, tag/trigger/variable CRUD, version management, and environment operations
- API-dependent tests skip gracefully when credentials are not available
