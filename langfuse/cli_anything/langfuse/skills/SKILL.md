---
name: "cli-anything-langfuse"
description: "CLI for the Langfuse LLM observability platform — manage traces, prompts, datasets, scores, and more via command line or REPL."
---

# cli-anything-langfuse

CLI harness for the **Langfuse** LLM observability platform. Wraps the Langfuse
REST API for managing traces, observations, scores, prompts, datasets, sessions,
models, comments, and metrics.

## Prerequisites

- Python 3.10+
- Langfuse API keys (from https://cloud.langfuse.com → Settings → API Keys)

## Installation

```bash
pip install -e .   # from agent-harness directory
```

## Authentication

Configure via one of:

```bash
# Option 1: Config profile
cli-anything-langfuse config set --public-key pk-lf-... --secret-key sk-lf-... --activate

# Option 2: Environment variables
export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
export LANGFUSE_BASE_URL=https://cloud.langfuse.com  # optional

# Option 3: CLI flags
cli-anything-langfuse --public-key pk-lf-... --secret-key sk-lf-... <command>
```

## Command Groups

| Group | Description |
|-------|------------|
| `traces` | list, get, delete — LLM execution traces |
| `observations` | list, get — spans, generations, events within traces |
| `scores` | create, list, get, delete — evaluation scores |
| `score-configs` | create, list — score configuration templates |
| `prompts` | create, list, get — versioned prompt templates |
| `datasets` | create, list, get — evaluation datasets |
| `dataset-items` | create, list, delete — items within datasets |
| `dataset-runs` | list, get, delete — dataset evaluation runs |
| `sessions` | list, get — trace sessions |
| `models` | create, list, get, delete — model definitions with pricing |
| `comments` | create, list — annotations on objects |
| `metrics` | daily — usage metrics |
| `projects` | current project info |
| `health` | API health check |
| `config` | set, show, activate, delete — CLI profiles |

## Usage Examples

### Agent workflow: Inspect recent traces
```bash
cli-anything-langfuse --json traces list --limit 10
cli-anything-langfuse --json traces get <trace-id>
cli-anything-langfuse --json observations list --trace-id <trace-id>
```

### Agent workflow: Create and populate a dataset
```bash
cli-anything-langfuse --json datasets create --name "qa-eval" --description "QA pairs"
cli-anything-langfuse --json dataset-items create --dataset qa-eval --input '{"q":"What is RAG?"}' --expected-output '{"a":"Retrieval Augmented Generation"}'
cli-anything-langfuse --json dataset-items list --dataset qa-eval
```

### Agent workflow: Score traces
```bash
cli-anything-langfuse --json scores create --trace-id <id> --name quality --value 0.95
cli-anything-langfuse --json scores create --trace-id <id> --name relevance --value 0.8 --comment "mostly relevant"
```

### Agent workflow: Prompt management
```bash
cli-anything-langfuse --json prompts create --name system-prompt --prompt "You are a helpful assistant for {{domain}}"
cli-anything-langfuse --json prompts get system-prompt
cli-anything-langfuse --json prompts get system-prompt --version 1
```

### Agent workflow: Health and metrics
```bash
cli-anything-langfuse health
cli-anything-langfuse --json metrics daily --from 2024-01-01T00:00:00Z --to 2024-01-31T23:59:59Z
```

## Agent-Specific Guidance

- **Always use `--json`** for programmatic consumption — all commands support it
- **Pagination:** Use `--limit` and `--page` for large result sets
- **Error handling:** Non-zero exit code on errors; JSON errors include `status_code`
- **Config profiles:** Use `--profile` flag to switch between environments (prod, staging)
- **No local software required** — this CLI is purely an API client
- **Auth priority:** CLI flags > env vars > config profile
