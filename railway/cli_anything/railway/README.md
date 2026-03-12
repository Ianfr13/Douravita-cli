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

| Command | Description |
|---------|-------------|
| `logs service <ID> --env <ENV_ID> [--lines N]` | Recent service logs |
| `logs deployment <ID> [--lines N] [--build]` | Deployment or build logs |

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
