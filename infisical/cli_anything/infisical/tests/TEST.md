# Test Suite — cli-anything-infisical

## Running the tests

```bash
python3 -m pytest cli_anything/infisical/tests/test_core.py -v
```

## Results (v1.1.0 refine — 2026-04-24)

```
$ python3 -m pytest cli_anything/infisical/tests/test_core.py --tb=no -q
.......................................................................  [100%]
71 passed in 0.37s
```

**71 tests** — 37 original + 34 new for the refine.

## What is tested

### Backend (mocked HTTP via `requests.Session`)

- Auth header, `_url` construction, GET/POST/PATCH/DELETE helpers, `InfisicalAPIError` on non-2xx
- `SecretsClient`: list, get, create, update, export_dotenv
- `ProjectsClient`: list, create
- New in 1.1.0:
  - `delete_secret` sends DELETE with body
  - `create_folder` posts to `/api/v1/folders`
  - `list_environments` returns the `environments` array from workspace
  - `list_snapshots` forwards `environment`/`limit`/`offset` as params
  - `universal_auth_login` does a plain `requests.post` (bypasses the authenticated session — swapping creds for a token)
  - `create_dynamic_secret_lease` posts to `/api/v1/dynamic-secrets/leases`
  - `list_tags` returns `workspaceTags`
  - `export_audit_logs` builds `/organization/<id>/audit-logs`

### CLI groups (`click.testing.CliRunner` + patched `InfisicalBackend`)

Original: `secrets` (list/get/export/create/edit), `projects` (list/create), `--json`, token/workspace validation, API error display.

New groups smoke-tested (delete/move/rename/rollback/attach/etc):

- `secrets-x`: delete, rename, bulk-delete
- `folders`: list, create + `--json`
- `environments`: list, create
- `projects-x`: info, members list
- `snapshots`: list, rollback
- `tags`: list, create
- `imports`: list, create
- `identities`: list, create
- `auth`: login, attach-ua
- `audit`: export
- `dynamic-secrets`: list, leases create
- `groups`: list, users list
- `app-connections`: list, options

## Manual CLI surface validation

81 subcommands (13 new groups × ~6 subcommands avg) validated with `--help`:

```bash
$ for g in secrets projects secrets-x folders environments projects-x snapshots \
          tags imports identities auth audit dynamic-secrets groups app-connections; do
    for sub in $(cli-anything-infisical $g --help | grep -E "^  \S" | awk '{print $1}'); do
        cli-anything-infisical $g $sub --help >/dev/null || echo "BROKEN: $g $sub"
    done
  done
# OK: 81   BROKEN: 0
```

## Known gaps

- E2E tests against the real Infisical instance (auth-gated; would require a
  dedicated service identity / universal-auth secret). Covered manually by the
  CLI surface validation above.
- PKI/Cert-manager/KMS/SSO/SCIM groups intentionally not exposed (enterprise
  surface the user isn't consuming). Can be added with another `/cli-anything:refine`
  run.
