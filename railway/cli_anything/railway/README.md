# cli-anything-railway

Interactive CLI and one-shot commands for the [Railway](https://railway.app)
deployment platform.

## Quick start

```bash
pip install -e /home/sandbox/workspace/repo/railway/agent-harness/
export RAILWAY_TOKEN=<your_token>
cli-anything-railway          # interactive REPL
cli-anything-railway --help   # one-shot help
```

## Commands

All commands accept `--json` for machine-readable output and
`--token TEXT` (or `$RAILWAY_TOKEN`) for authentication.

### Projects

| Command | Description |
|---------|-------------|
| `projects list` | List all projects |
| `projects create <NAME>` | Create a project |
| `projects info <ID>` | Project details |

### Services

| Command | Description |
|---------|-------------|
| `services list --project <ID>` | Services in a project |
| `services info <ID>` | Service details |
| `services create-cron <NAME> <SCHEDULE> --project <ID>` | Create a cron service |

### Deployments

| Command | Description |
|---------|-------------|
| `deployments list --service <ID>` | Deployments for a service |
| `deployments trigger <ID> --env <ENV_ID>` | Trigger a deployment |
| `deployments status <ID>` | Deployment status |
| `deployments rollback <ID>` | Rollback to a deployment |

### Variables

| Command | Description |
|---------|-------------|
| `variables list --project <ID> --env <ENV_ID>` | List variables |
| `variables set KEY VALUE --project <ID> --env <ENV_ID>` | Set a variable |
| `variables delete KEY --project <ID> --env <ENV_ID>` | Delete a variable |

### Environments

| Command | Description |
|---------|-------------|
| `environments list --project <ID>` | List environments |
| `environments create <NAME> --project <ID>` | Create an environment |

### Logs

All log commands support:

- `--filter "<query>"` — Railway filter syntax (`@level:error AND "failed"`, `@httpStatus:>=500`, `@service:<id>`, etc.). See https://docs.railway.com/reference/logging.
- `--severity {debug|info|warn|error}` — minimum level (merged into `--filter`).
- `--since 30m|2h|1d|<ISO>` / `--until ...` — time window (relative or ISO-8601).
- `--follow` / `-f` — live stream via **WebSocket** (`graphql-transport-ws`). Falls back to polling if `websocket-client` is missing.
- `--no-color`, `--raw`, `--json` — output formatting.

| Command | Description |
|---------|-------------|
| `logs service <ID> --env <ENV_ID>` | Recent logs for a service (latest deployment) |
| `logs deployment <ID> [--build]` | Runtime or build logs for a specific deployment |
| `logs http <ID>` | HTTP request logs with method / path / status / duration |
| `logs environment --env <ENV_ID> [--service <ID>]` | Logs across every service in an environment (`--service` is a shortcut for `@service:<id>`) |

Examples:

```bash
# Stream errors from the latest deployment
cli-anything-railway logs service svc-1 --env env-1 --severity error --follow

# Last 50 log lines from the past hour matching a keyword
cli-anything-railway logs deployment dep-1 --filter '"timeout"' --since 1h --lines 50

# 5xx HTTP logs, raw
cli-anything-railway logs http dep-1 --filter '@httpStatus:>=500' --json

# Env-wide errors from a specific service
cli-anything-railway logs environment --env env-1 --service svc-1 --severity error
```

### Run / Shell / Exec / SSH (v1.2.0)

**Local execution** (your machine, with the service's env vars injected):

| Command | Description |
|---------|-------------|
| `run --project <id> --env-id <id> --service <id> -- <cmd> [args...]` | Run a local command with Railway variables as env |
| `run --print-env --project <id> --env-id <id> --service <id>` | Dump resolved env without running anything |
| `shell --project <id> --env-id <id> --service <id>` | Open a subshell (`$SHELL`) with variables available |

**Remote execution** (inside the deployed container, over the WebSocket relay `wss://backboard.railway.com/relay`):

| Command | Description |
|---------|-------------|
| `exec --service <id> --project <id> --env-id <id> -- <cmd> [args...]` | One-shot command inside the live container, stream output, exit with remote code |
| `ssh --service <id> --project <id> --env-id <id>` | Interactive PTY shell (raw mode, forwards resize + stdin) |
| `ssh --deployment-instance <id> ...` | Target a specific replica |

**SSH keys** (account-level; needs an account/workspace token, not a project-scope token):

| Command | Description |
|---------|-------------|
| `ssh keys list` | List registered SSH public keys |
| `ssh keys add [--key <path>] [--name <label>]` | Register a public key (auto-detects `~/.ssh/*.pub`) |
| `ssh keys remove <KEY_ID>` | Delete a registered key |
| `ssh keys github` | List SSH keys from the linked GitHub account |

Examples:

```bash
# Local run with Railway env
cli-anything-railway run -p <proj> --env-id <env> -s web -- node scripts/migrate.js

# Local subshell
cli-anything-railway shell -p <proj> --env-id <env> -s web

# Remote one-shot
cli-anything-railway exec -s web -p <proj> --env-id <env> -- ls -la /app
cli-anything-railway exec -s web -p <proj> --env-id <env> -- sh -c "hostname; uname -a"

# Interactive remote shell (requires TTY)
cli-anything-railway ssh -s web -p <proj> --env-id <env>
```

### Domains

| Command | Description |
|---------|-------------|
| `domains list --service <ID> --env <ENV_ID>` | List domains |
| `domains create <DOMAIN> --service <ID> --env <ENV_ID>` | Add custom domain |
| `domains delete <DOMAIN_ID>` | Delete a custom domain |
| `domains generate --service <ID> --env <ENV_ID>` | Generate railway.app domain |

### Volumes

| Command | Description |
|---------|-------------|
| `volumes list --project <ID>` | List volumes |
| `volumes create <NAME> --project <ID>` | Create a volume |
| `volumes delete <VOLUME_ID>` | Delete a volume |

### Metrics

| Command | Description |
|---------|-------------|
| `metrics service <ID> --env <ENV_ID>` | CPU, memory, network metrics |

### Templates

| Command | Description |
|---------|-------------|
| `templates list` | List available templates |
| `templates deploy <CODE> --project <ID>` | Deploy a template |

### Service Configuration

| Command | Description |
|---------|-------------|
| `service-config get <ID> --env <ENV_ID>` | Show build/start config |
| `service-config set-start-command <ID> <CMD> --env <ENV_ID>` | Set start command |
| `service-config set-build-command <ID> <CMD> --env <ENV_ID>` | Set build command |
| `service-config set-dockerfile <ID> <PATH> --env <ENV_ID>` | Set Dockerfile path |
| `service-config set-health-check <ID> <PATH> --env <ENV_ID>` | Set health check path |
| `service-config set-restart-policy <ID> ALWAYS\|ON_FAILURE\|NEVER --env <ENV_ID>` | Set restart policy |
| `service-config set-root-dir <ID> <DIR> --env <ENV_ID>` | Set root directory |

### TCP Proxies

| Command | Description |
|---------|-------------|
| `tcp-proxies list --service <ID> --env <ENV_ID>` | List TCP proxies |
| `tcp-proxies create --service <ID> --env <ENV_ID> --port <PORT>` | Create TCP proxy |
| `tcp-proxies delete <PROXY_ID>` | Delete TCP proxy |

### Webhooks

| Command | Description |
|---------|-------------|
| `webhooks list --project <ID>` | List webhooks |
| `webhooks create <URL> --project <ID>` | Create a webhook |
| `webhooks delete <WEBHOOK_ID>` | Delete a webhook |

### Team

| Command | Description |
|---------|-------------|
| `team list` | List team members |
| `team invite <EMAIL> --team <ID> [--role ADMIN\|MEMBER]` | Invite a member |
| `team remove <USER_ID> --team <ID>` | Remove a member |

### Private Networking

| Command | Description |
|---------|-------------|
| `networking list --project <ID>` | List private network endpoints |

### Git Integration

| Command | Description |
|---------|-------------|
| `git connect <SERVICE_ID> <REPO> <BRANCH>` | Connect GitHub repo to service |
| `git disconnect <SERVICE_ID>` | Disconnect repo |

## GraphQL endpoint

`https://backboard.railway.app/graphql/v2`
