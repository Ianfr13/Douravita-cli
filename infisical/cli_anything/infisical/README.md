# cli-anything-infisical

A CLI wrapper for the [Infisical](https://infisical.com) secrets manager REST API.

## Installation

```bash
pip install -e /path/to/infisical/agent-harness/
```

## Configuration

| Variable | Flag | Default |
|---|---|---|
| `INFISICAL_TOKEN` | `--token` | (required) |
| `INFISICAL_WORKSPACE_ID` | `--workspace` / `-w` | (required for secrets) |
| `INFISICAL_ENV` | `--env` / `-e` | `dev` |
| `INFISICAL_URL` | `--url` | `https://sec.douravita.com.br` |
| `INFISICAL_ORG_ID` | `--org-id` | (required for project create) |

## Usage

```bash
# List all secrets
cli-anything-infisical -w <workspace-id> secrets list

# Get a specific secret
cli-anything-infisical -w <workspace-id> secrets get MY_SECRET

# Export as KEY=VALUE
cli-anything-infisical -w <workspace-id> secrets export

# Export as JSON
cli-anything-infisical -w <workspace-id> secrets export --json

# Create a secret
cli-anything-infisical -w <workspace-id> secrets create MY_KEY my_value

# Update a secret
cli-anything-infisical -w <workspace-id> secrets edit MY_KEY new_value

# List projects
cli-anything-infisical projects list

# Create a project
cli-anything-infisical projects create "My Project" --org-id <org-id>

# Interactive REPL mode
cli-anything-infisical
```

## Full command surface (v1.1.0)

15 command groups, 81 subcommands. Every subcommand supports `--json`.

| Group | Commands |
|---|---|
| `secrets` | list, get, export, create, edit |
| `secrets-x` | delete, rename, move, bulk-create, bulk-delete, tag, untag, history, rollback |
| `projects` | list, create |
| `projects-x` | info, update, delete, members (list, set-role, remove) |
| `environments` | list, get, create, rename, delete |
| `folders` | list, get, create, rename, delete |
| `snapshots` | list, rollback |
| `tags` | list, get, get-by-slug, create, update, delete |
| `imports` | list, create, update, delete |
| `identities` | list, get, create, update, delete |
| `auth` | login, attach-ua, get-ua, revoke-ua, client-secrets (list, create, revoke) |
| `audit` | export |
| `dynamic-secrets` | list, get, create, update, delete, leases (list, create, get, renew, delete) |
| `groups` | list, get, create, update, delete, users (list, add, remove) |
| `app-connections` | list, options |

### Extended usage examples

```bash
# Bulk create from a .env file
cli-anything-infisical -w <ws> secrets-x bulk-create --file .env.production

# Delete a secret
cli-anything-infisical -w <ws> secrets-x delete OLD_KEY

# Move secrets between envs
cli-anything-infisical -w <ws> secrets-x move FOO BAR --to-env staging --to-path /

# History + rollback
cli-anything-infisical -w <ws> secrets-x history <secret-id>
cli-anything-infisical -w <ws> secrets-x rollback <version-id>

# Folders
cli-anything-infisical -w <ws> folders create api --path /services
cli-anything-infisical -w <ws> folders list --recursive

# Environments
cli-anything-infisical -w <ws> environments create Staging staging
cli-anything-infisical -w <ws> environments list

# Snapshots (point-in-time rollback)
cli-anything-infisical -w <ws> snapshots list --limit 10
cli-anything-infisical -w <ws> snapshots rollback <snapshot-id> --yes

# Tags (project-scoped)
cli-anything-infisical -w <ws> tags create prod --color "#FF0000"
cli-anything-infisical -w <ws> secrets-x tag MY_SECRET prod

# Secret imports (link from another env)
cli-anything-infisical -w <ws> imports create --from-env prod --from-path /

# Identities + auth (machine users)
cli-anything-infisical identities create ci-bot --org-id <org> --role member
cli-anything-infisical auth attach-ua <identity-id> --ttl 7200 --max-ttl 86400
cli-anything-infisical auth client-secrets create <identity-id> --description "CI"
cli-anything-infisical auth login --client-id <id> --client-secret <secret>

# Audit logs
cli-anything-infisical audit export --org-id <org> --event-type secret-read --limit 100

# Dynamic secrets (temporary DB credentials)
cli-anything-infisical dynamic-secrets leases create my-pg-lease --ttl 1h

# Groups
cli-anything-infisical groups list --org-id <org>
cli-anything-infisical groups users add <group-id> <username>
```

## Python module

```bash
python -m cli_anything.infisical --help
```
