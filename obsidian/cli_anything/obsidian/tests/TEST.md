# Obsidian CLI — Test Plan & Results

## Test Strategy

### Unit Tests (`test_core.py`)

These tests do **NOT** require Obsidian to be running. They test:

- URL construction and path encoding in the backend module
- Authentication header injection and API key resolution
- Accept header selection for different output formats (markdown, json, map)
- PATCH header construction (Operation, Target-Type, Create-Target-If-Missing)
- Error handling for connection failures, timeout, 401, and 404
- CLI argument parsing via Click's test runner (all command groups)
- Output formatting helpers (`_print_dict`, `_print_list`, `output()`)
- Periodic note endpoint generation (all periods, with and without date)
- `encode_path` with special characters, spaces, and unicode
- `accept_for_format` mapping
- `ui.open_file()` endpoint construction and newLeaf param

### E2E Tests (`test_full_e2e.py`)

These tests **REQUIRE** Obsidian running at `https://127.0.0.1:27124` with:
- `obsidian-local-rest-api` plugin enabled
- `OBSIDIAN_API_KEY` environment variable set

They test the full API surface:
- Server status check
- Vault directory listing
- File creation (PUT), read (GET), append (POST), and delete (DELETE)
- Vault PATCH operations (append to heading, replace frontmatter)
- Active file operations (get, append)
- Periodic notes (daily get, append, delete)
- Simple search
- Command listing
- Tag listing
- Open file command

## Running Tests

```bash
cd obsidian/agent-harness

# Unit tests only (no Obsidian needed)
python -m pytest cli_anything/obsidian/tests/test_core.py -v

# E2E tests (requires Obsidian running)
export OBSIDIAN_API_KEY="your-api-key"
python -m pytest cli_anything/obsidian/tests/test_full_e2e.py -v

# All tests
python -m pytest cli_anything/obsidian/tests/ -v
```

## Test Results

| Test Suite | Status | Notes |
|-----------|--------|-------|
| test_core.py | ✓ Passed | 72/72 (run 2026-03-22) |
| test_full_e2e.py | ✓ Passed | 14 passed, 1 skipped (DQL requires Dataview plugin), run 2026-03-22 |
