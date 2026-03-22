---
name: >-
  cli-anything-obsidian
description: >-
  Command-line interface for Obsidian Local REST API — read and write your Obsidian vault from the terminal or AI agents. Supports active file operations, vault CRUD, periodic notes, full-text search, Dataview DQL, JsonLogic queries, tag listing, and Obsidian command execution.
---

# cli-anything-obsidian

Read and write your Obsidian vault from the terminal or AI agents via the
Obsidian Local REST API plugin. Designed for automation, note management,
and AI agent workflows that need to interact with Obsidian without a GUI.

## Installation

This CLI is installed as part of the cli-anything-obsidian package:

```bash
pip install cli-anything-obsidian
```

**Prerequisites:**
- Python 3.10+
- Obsidian desktop app running
- obsidian-local-rest-api plugin installed and enabled
- `OBSIDIAN_API_KEY` environment variable set (find it in Obsidian Settings → Local REST API)


## Usage

### Basic Commands

```bash
# Show help
cli-anything-obsidian --help

# Start interactive REPL mode
cli-anything-obsidian

# Check server status (no auth needed)
cli-anything-obsidian status

# Run with JSON output (for agent consumption)
cli-anything-obsidian --json vault list
```

### REPL Mode

When invoked without a subcommand, the CLI enters an interactive REPL session:

```bash
cli-anything-obsidian
# Enter commands interactively with tab-completion and history
# Use 'help' to see available commands
```


## Command Groups


### active

Operations on the currently open file in Obsidian.

| Command | Description |
|---------|-------------|
| `get` | Get active file content (markdown, json, or document map) |
| `append` | Append markdown content to the active file |
| `put` | Replace entire active file content |
| `patch` | Partial update at a heading, block, or frontmatter key |
| `delete` | Delete the currently active file |


### vault

Read and write any file in the vault by its path.

| Command | Description |
|---------|-------------|
| `list` | List vault root or a specific directory |
| `get` | Read a file (markdown, json, or document map) |
| `append` | Append to a file (creates if it doesn't exist) |
| `put` | Create or replace a file |
| `patch` | Partial update at a heading, block, or frontmatter key |
| `delete` | Delete a file from the vault |


### periodic

Read and write periodic notes (daily, weekly, monthly, quarterly, yearly).

| Command | Description |
|---------|-------------|
| `get` | Get current period note (or a specific date with --date) |
| `append` | Append to current period note |
| `put` | Replace current period note |
| `patch` | Partial update at a heading, block, or frontmatter key |
| `delete` | Delete current period note |


### search

Search your vault using multiple strategies.

| Command | Description |
|---------|-------------|
| `simple` | Fuzzy full-text search with context snippets |
| `dql` | Dataview DQL TABLE query (requires Dataview plugin) |
| `jsonlogic` | JsonLogic expression with glob and regexp extensions |


### commands

List and execute Obsidian commands programmatically.

| Command | Description |
|---------|-------------|
| `list` | List all available Obsidian commands (filterable) |
| `run` | Execute a command by its ID |


### tags

List all tags in the vault with usage counts.

| Command | Description |
|---------|-------------|
| `tags` | Show all tags (filterable, min-count threshold) |


### open

Open files in the Obsidian desktop UI.

| Command | Description |
|---------|-------------|
| `open` | Open a file in Obsidian (optionally in a new tab) |


## Examples


### Check Server Status

```bash
cli-anything-obsidian status
cli-anything-obsidian --json status
```


### Read Your Daily Note

```bash
# Get today's daily note
cli-anything-obsidian periodic get daily

# Get a specific date's daily note as JSON
cli-anything-obsidian --json periodic get daily --date 2026-03-22 --format json
```


### Write to Your Vault

```bash
# Create a new note
cli-anything-obsidian vault put "Notes/Meeting 2026-03-22.md" \
  "# Meeting Notes\n\n## Attendees\n\n## Action Items"

# Append a task to today's daily note
cli-anything-obsidian periodic append daily "- [ ] Follow up with team"

# Update a frontmatter field
cli-anything-obsidian vault patch "Projects/Alpha.md" "in-progress" \
  --op replace --type frontmatter --target "status"
```


### Search Your Vault

```bash
# Fuzzy search
cli-anything-obsidian search simple "quarterly review"

# Find open tasks with Dataview
cli-anything-obsidian search dql 'TABLE file.name FROM "Tasks" WHERE status = "open"'

# Find files matching a glob pattern
cli-anything-obsidian --json search jsonlogic \
  '{"glob": ["Projects/*.md", {"var": "path"}]}'
```


### Run Obsidian Commands

```bash
# List all commands
cli-anything-obsidian commands list

# Run a command
cli-anything-obsidian commands run "editor:toggle-bold"
cli-anything-obsidian commands run "obsidian-git:pull"
```


### Interactive REPL Session

```bash
cli-anything-obsidian
# vault list
# vault get "Notes/My Note.md"
# search simple "project alpha"
# periodic append daily "- [x] Done"
# quit
```


### Connect to HTTP (instead of HTTPS)

```bash
cli-anything-obsidian --host http://127.0.0.1:27123 vault list
```


## State Management

The CLI maintains lightweight session state:

- **Host URL**: Configurable via `--host` (default: `https://127.0.0.1:27124`)
- **API key**: From `OBSIDIAN_API_KEY` env var or `--api-key` flag
- **JSON mode**: Toggled with `--json` flag

## Output Formats

All read commands support three output formats:

```bash
# Raw markdown (default)
cli-anything-obsidian vault get "Notes/My Note.md"

# Parsed note with frontmatter, tags, stats
cli-anything-obsidian vault get "Notes/My Note.md" --format json

# Document map (headings, blocks, frontmatter fields)
cli-anything-obsidian vault get "Notes/My Note.md" --format map
```

## Patch Operations

The `patch` command enables surgical note updates:

```bash
# Append a task under "Tasks" heading
cli-anything-obsidian vault patch "Notes/Project.md" "- [ ] Deploy" \
  --op append --type heading --target "Tasks"

# Create a section if it doesn't exist
cli-anything-obsidian vault patch "Notes/Project.md" "Content" \
  --op append --type heading --target "New Section" --create

# Nested heading with custom delimiter
cli-anything-obsidian vault patch "Notes.md" "item" \
  --op append --type heading --target "Work::Projects"

# Update frontmatter
cli-anything-obsidian vault patch "Notes/Project.md" "done" \
  --op replace --type frontmatter --target "status"
```

## For AI Agents

When using this CLI programmatically:

1. **Always use `--json` flag** for parseable output
2. **Check return codes** — 0 for success, non-zero for errors
3. **Parse stderr** for error messages on failure
4. **Set `OBSIDIAN_API_KEY`** env var to avoid repeating the key
5. **Verify Obsidian is running** with `status` before other commands
6. **Use `stdin (-)`** for multi-line content to avoid shell escaping
7. **Use `--format json`** on get commands for structured metadata

## More Information

- Full documentation: See README.md in the package
- Test coverage: See TEST.md in the package
- Methodology: See HARNESS.md in the cli-anything-plugin
- API docs: https://coddingtonbear.github.io/obsidian-local-rest-api/

## Version

1.0.0
