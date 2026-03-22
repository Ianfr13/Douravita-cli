"""Templater plugin integration — list, create from template, and run Templater.

Templater is an Obsidian plugin for dynamic templates with variables.
It registers commands that can be triggered via the REST API.

Template files live in a configurable folder (default: "Templates/").
"""

from cli_anything.obsidian.utils.obsidian_backend import api_post, api_get, encode_path
from cli_anything.obsidian.core import vault as vault_mod, commands as commands_mod


# Common Templater command IDs
CMD_CREATE = "templater-obsidian:create-new-note-from-template"
CMD_INSERT = "templater-obsidian:insert-templater"
CMD_REPLACE = "templater-obsidian:replace-in-file-templater"
CMD_JUMP_CURSOR = "templater-obsidian:jump-to-next-cursor-location"


def list_templates(base_url: str, api_key: str | None,
                   folder: str = "Templates") -> list:
    """List available template files.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        folder: Templates folder path relative to vault root.

    Returns:
        List of template file paths.
    """
    result = vault_mod.list_dir(base_url, api_key, folder)
    files = result.get("files", result) if isinstance(result, dict) else result
    if not isinstance(files, list):
        return []
    return [f"{folder}/{f}" for f in files if not f.endswith("/")]


def get_template(base_url: str, api_key: str | None,
                 template_path: str) -> str:
    """Read a template file's content.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        template_path: Template file path relative to vault root.

    Returns:
        Template content string.
    """
    result = vault_mod.get(base_url, api_key, template_path, fmt="markdown")
    if isinstance(result, dict):
        return result.get("content", "")
    return str(result)


def create_from_template(base_url: str, api_key: str | None,
                         dest_path: str, template_path: str,
                         variables: dict | None = None) -> dict:
    """Create a new note from a template.

    Reads the template, applies simple variable substitutions, and writes
    the result to dest_path. Variables use Templater's {{variable}} syntax.

    For full Templater processing (dynamic commands, tp.* functions), use
    run_on_file() after creation.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        dest_path: Destination file path relative to vault root.
        template_path: Template file path relative to vault root.
        variables: Optional dict of {variable_name: value} for substitution.

    Returns:
        Status dict.

    Raises:
        RuntimeError: If template doesn't exist or destination already exists.
    """
    content = get_template(base_url, api_key, template_path)
    if not content:
        raise RuntimeError(f"Template is empty or not found: {template_path}")

    if variables:
        for key, value in variables.items():
            content = content.replace("{{" + key + "}}", str(value))

    if vault_mod.exists(base_url, api_key, dest_path):
        raise RuntimeError(f"Destination already exists: {dest_path}")

    vault_mod.put(base_url, api_key, dest_path, content)
    return {"status": "ok", "file": dest_path, "template": template_path}


def run_on_file(base_url: str, api_key: str | None) -> dict:
    """Run Templater on the currently active file.

    Triggers the 'templater-obsidian:replace-in-file-templater' command,
    which processes all Templater expressions in the active file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        Status dict.
    """
    return commands_mod.run_command(base_url, api_key, CMD_REPLACE)


def insert_template(base_url: str, api_key: str | None) -> dict:
    """Open the Templater template picker to insert a template at cursor.

    Triggers the 'templater-obsidian:insert-templater' command.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        Status dict.
    """
    return commands_mod.run_command(base_url, api_key, CMD_INSERT)


def create_note_from_template(base_url: str, api_key: str | None) -> dict:
    """Open Templater's create-from-template dialog.

    Triggers the 'templater-obsidian:create-new-note-from-template' command.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.

    Returns:
        Status dict.
    """
    return commands_mod.run_command(base_url, api_key, CMD_CREATE)
