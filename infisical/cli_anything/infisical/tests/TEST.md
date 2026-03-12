# Test Suite — cli-anything-infisical

## Running the tests

```bash
python3 -m pytest cli_anything/infisical/tests/test_core.py -v
```

Or from anywhere:

```bash
python3 -m pytest /home/sandbox/workspace/repo/infisical/agent-harness/cli_anything/infisical/tests/test_core.py -v
```

## What is tested

- `InfisicalBackend` HTTP method helpers (GET, POST, PATCH) with mocked `requests.Session`
- Error handling: `InfisicalAPIError` raised on non-2xx responses
- `SecretsClient`: list, get, create, update, export_dotenv
- `ProjectsClient`: list, create
- CLI commands via Click's `CliRunner`: secrets list/get/export/create/edit, projects list/create
- `--json` flag produces valid JSON output
- Missing token / workspace produces error messages and non-zero exit code
