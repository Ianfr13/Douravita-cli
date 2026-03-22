# cli-anything-obsidian

Read and write your Obsidian vault from the terminal or AI agents via the
[Obsidian Local REST API](https://coddingtonbear.github.io/obsidian-local-rest-api/) plugin.

## Prerequisites

- **Python 3.10+**
- **Obsidian** desktop app running
- **obsidian-local-rest-api** plugin installed and enabled in Obsidian
- **API key** from Obsidian Settings → Local REST API

## Installation

```bash
pip install cli-anything-obsidian
```

Or install from source:

```bash
git clone https://github.com/HKUDS/CLI-Anything
cd CLI-Anything/obsidian/agent-harness
pip install -e .
```

## Configuration

Set your API key as an environment variable:

```bash
export OBSIDIAN_API_KEY="your-api-key-here"
```

Or pass it on every command:

```bash
cli-anything-obsidian --api-key "your-key" vault list
```

By default the CLI connects to `https://127.0.0.1:27124` (HTTPS with self-signed cert).
Use HTTP with `--host http://127.0.0.1:27123` if you prefer.

## Usage

### Basic Commands

```bash
# Show help
cli-anything-obsidian --help

# Start interactive REPL mode
cli-anything-obsidian

# Check server status
cli-anything-obsidian status

# JSON output (for agent consumption)
cli-anything-obsidian --json vault list
```

### REPL Mode

When invoked without a subcommand, the CLI enters an interactive REPL session:

```bash
cli-anything-obsidian
# Type commands interactively with tab-completion and history
# Use 'help' to see available commands, 'quit' to exit
```

## Command Reference

### `status`

Check if the Obsidian REST API plugin is running (no auth required).

```bash
cli-anything-obsidian status
cli-anything-obsidian --json status
```

---

### `active` — Active File Operations

Operate on the currently open file in Obsidian.

| Command | Description |
|---------|-------------|
| `active get [--format markdown\|json\|map]` | Get active file content |
| `active append <content>` | Append to active file |
| `active put <content>` | Replace active file content |
| `active patch <content> --op <op> --type <type> --target <target>` | Partial update |
| `active delete` | Delete the active file |

```bash
# Get active note as markdown
cli-anything-obsidian active get

# Get active note as parsed JSON (with frontmatter, tags, etc.)
cli-anything-obsidian active get --format json

# Append a task
cli-anything-obsidian active append "- [ ] Review pull request"

# Replace entire content
cli-anything-obsidian active put "# New Content\n\nHello world."

# Append under a heading
cli-anything-obsidian active patch "- new item" --op append --type heading --target "Tasks"

# Update frontmatter status
cli-anything-obsidian active patch "done" --op replace --type frontmatter --target "status"
```

---

### `vault` — Vault File Operations

Read and write any file in the vault by path.

| Command | Description |
|---------|-------------|
| `vault list [path]` | List vault root or directory |
| `vault get <file> [--format]` | Read a file |
| `vault append <file> <content>` | Append to file (creates if missing) |
| `vault put <file> <content>` | Create or replace file |
| `vault patch <file> <content> --op --type --target` | Partial update |
| `vault delete <file>` | Delete file |

```bash
# List vault root
cli-anything-obsidian vault list

# List a subdirectory
cli-anything-obsidian vault list "Projects"

# Read a note
cli-anything-obsidian vault get "Notes/My Note.md"

# Create or replace a note (use stdin for multi-line content)
echo "# Hello\n\nWorld" | cli-anything-obsidian vault put "Notes/Hello.md" -

# Append a log entry
cli-anything-obsidian vault append "Journal/Log.md" "\n## 2026-03-22\n- Done a thing"

# Patch a specific heading section
cli-anything-obsidian vault patch "Projects/Work.md" "- [x] Deploy v2" \
  --op append --type heading --target "Done"

# Delete a note
cli-anything-obsidian vault delete "Notes/Old Note.md"
```

---

### `periodic` — Periodic Notes

Manage daily, weekly, monthly, quarterly, and yearly notes.

| Command | Description |
|---------|-------------|
| `periodic get <period> [--date YYYY-MM-DD]` | Get period note |
| `periodic append <period> <content> [--date]` | Append to period note |
| `periodic put <period> <content> [--date]` | Replace period note |
| `periodic patch <period> <content> --op --type --target [--date]` | Partial update |
| `periodic delete <period> [--date]` | Delete period note |

```bash
# Get today's daily note
cli-anything-obsidian periodic get daily

# Append to today's daily note
cli-anything-obsidian periodic append daily "- [x] Morning standup"

# Get a specific date's daily note
cli-anything-obsidian periodic get daily --date 2026-03-01

# Append to this week's note
cli-anything-obsidian periodic append weekly "## Completed\n- Shipped feature X"

# Patch this month's note under a heading
cli-anything-obsidian periodic patch monthly "- Shipped v2.0" \
  --op append --type heading --target "Wins" --create
```

---

### `search` — Search Commands

Search your vault with multiple strategies.

| Command | Description |
|---------|-------------|
| `search simple <query> [--context N]` | Fuzzy full-text search |
| `search dql <query>` | Dataview DQL query (requires Dataview plugin) |
| `search jsonlogic <json>` | JsonLogic expression |

```bash
# Simple fuzzy search
cli-anything-obsidian search simple "meeting notes"
cli-anything-obsidian search simple "project alpha" --context 200

# Dataview DQL search (requires Dataview plugin)
cli-anything-obsidian search dql 'TABLE file.name FROM "Projects"'
cli-anything-obsidian search dql 'TABLE status FROM "Tasks" WHERE status = "open"'

# JsonLogic search
cli-anything-obsidian search jsonlogic '{"glob": ["Projects/*.md", {"var": "path"}]}'
cli-anything-obsidian search jsonlogic '{"==": [{"var": "frontmatter.status"}, "done"]}'
```

---

### `commands` — Obsidian Commands

| Command | Description |
|---------|-------------|
| `commands list [--filter <str>]` | List all Obsidian commands |
| `commands run <id>` | Execute a command by ID |

```bash
# List all commands
cli-anything-obsidian commands list

# Filter commands by name
cli-anything-obsidian commands list --filter "editor"

# Run a command
cli-anything-obsidian commands run "editor:toggle-bold"
cli-anything-obsidian commands run "obsidian-git:pull"
```

---

### `tags` — Tag Management

```bash
# List all tags with usage counts
cli-anything-obsidian tags

# Filter and minimum count
cli-anything-obsidian tags --filter "project" --min-count 3

# JSON output
cli-anything-obsidian --json tags
```

---

### `open` — Open in Obsidian UI

```bash
# Open a file in the Obsidian window
cli-anything-obsidian open "Notes/My Note.md"

# Open in a new tab
cli-anything-obsidian open "Projects/Work.md" --new-leaf
```

---

## Global Options

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON (for agent consumption) |
| `--host URL` | Obsidian server URL (default: `https://127.0.0.1:27124`) |
| `--api-key KEY` | Bearer token (or set `OBSIDIAN_API_KEY`) |

## For AI Agents

When using this CLI programmatically:

1. **Always use `--json` flag** for parseable output
2. **Check return codes** — 0 for success, non-zero for errors
3. **Parse stderr** for error messages on failure
4. **Use `OBSIDIAN_API_KEY`** env var to avoid passing the key in every command
5. **Verify Obsidian is running** with `status` before other commands
6. **Use stdin (`-`)** for multi-line content to avoid shell escaping issues

## Patch Operation Reference

The `patch` command supports precise note editing:

| Flag | Values | Description |
|------|--------|-------------|
| `--op` | `append`, `prepend`, `replace` | Operation type |
| `--type` | `heading`, `block`, `frontmatter` | Target type |
| `--target` | `Section Name`, `^blockref`, `key` | What to target |
| `--delimiter` | `::` (default) | Nested heading separator |
| `--create` | flag | Create section if it doesn't exist |

```bash
# Append under nested heading "Work::Current Projects"
cli-anything-obsidian vault patch "Notes.md" "- New project" \
  --op append --type heading --target "Work::Current Projects"

# Prepend to a block reference
cli-anything-obsidian active patch "NOTE: " \
  --op prepend --type block --target "^abc123"

# Create a new heading section and add content
cli-anything-obsidian vault patch "Notes.md" "Initial content" \
  --op append --type heading --target "New Section" --create
```

## Version

1.0.0
