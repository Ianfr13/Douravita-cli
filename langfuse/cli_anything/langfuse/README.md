# cli-anything-langfuse

CLI harness for the **Langfuse** LLM observability platform. Provides a full
command-line interface to manage traces, observations, scores, prompts,
datasets, sessions, models, and more.

## Prerequisites

- Python 3.10+
- A Langfuse account with API keys (cloud or self-hosted)

Get your API keys from: https://cloud.langfuse.com → Settings → API Keys

## Installation

```bash
cd agent-harness
pip install -e .
```

Verify:
```bash
which cli-anything-langfuse
cli-anything-langfuse --help
```

## Configuration

### Option 1: Config profile (recommended)
```bash
cli-anything-langfuse config set \
  --public-key pk-lf-xxxxxxxx \
  --secret-key sk-lf-xxxxxxxx \
  --base-url https://cloud.langfuse.com \
  --activate
```

### Option 2: Environment variables
```bash
export LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
export LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
export LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### Option 3: CLI flags
```bash
cli-anything-langfuse --public-key pk-lf-... --secret-key sk-lf-... traces list
```

Priority: CLI flags > environment variables > config profile.

## Usage

### Interactive REPL
```bash
cli-anything-langfuse
```

### One-shot commands
```bash
# Health check
cli-anything-langfuse health

# Traces
cli-anything-langfuse traces list --limit 10
cli-anything-langfuse traces get <trace-id>
cli-anything-langfuse --json traces list  # JSON output

# Observations
cli-anything-langfuse observations list --trace-id <id>
cli-anything-langfuse observations get <observation-id>

# Scores
cli-anything-langfuse scores list
cli-anything-langfuse scores create --trace-id <id> --name quality --value 0.95
cli-anything-langfuse scores delete <score-id> --yes

# Prompts
cli-anything-langfuse prompts list
cli-anything-langfuse prompts get my-prompt --version 3
cli-anything-langfuse prompts create --name my-prompt --prompt "You are {{role}}"

# Datasets
cli-anything-langfuse datasets list
cli-anything-langfuse datasets create --name eval-set --description "QA pairs"
cli-anything-langfuse dataset-items create --dataset eval-set --input '{"question": "What is LLM?"}'

# Sessions
cli-anything-langfuse sessions list
cli-anything-langfuse sessions get <session-id>

# Models
cli-anything-langfuse models list
cli-anything-langfuse models create --name gpt-4o-custom --match-pattern "gpt-4o.*"

# Config
cli-anything-langfuse config show
cli-anything-langfuse config set --profile staging --base-url https://staging.langfuse.com
```

### JSON output for agents
All commands support `--json` for machine-readable output:
```bash
cli-anything-langfuse --json traces list --limit 5
cli-anything-langfuse --json prompts get my-prompt
```

## Running Tests

```bash
cd agent-harness
pip install -e .
pytest cli_anything/langfuse/tests/ -v -s
```

With force-installed mode:
```bash
CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/langfuse/tests/ -v -s
```

## Command Groups

| Group | Description |
|-------|------------|
| `traces` | List, get, delete LLM traces |
| `observations` | List, get observations (spans, generations, events) |
| `scores` | Create, list, get, delete evaluation scores |
| `score-configs` | Manage score configuration templates |
| `prompts` | Create, list, get prompt templates |
| `datasets` | Create, list, get evaluation datasets |
| `dataset-items` | CRUD operations on dataset items |
| `dataset-runs` | List, get, delete dataset evaluation runs |
| `sessions` | List, get trace sessions |
| `models` | Create, list, get, delete model definitions |
| `comments` | Create, list comments on objects |
| `metrics` | Query daily usage metrics |
| `projects` | Get current project info |
| `health` | Check API health status |
| `config` | Manage CLI configuration profiles |
