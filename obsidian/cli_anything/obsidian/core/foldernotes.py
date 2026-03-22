"""Folder Notes plugin integration — auto-index notes for folders.

Folder Notes creates a note with the same name as a folder, acting as its
index/overview page. This module provides helpers to create, read, and list
folder notes programmatically.

Convention: folder "Projects/" has index note "Projects/Projects.md"
(configurable in the plugin — this module defaults to inside-folder style).
"""

from cli_anything.obsidian.core import vault as vault_mod


def _index_path(folder: str, style: str = "inside") -> str:
    """Build the expected folder note path.

    Args:
        folder: Folder path relative to vault root (e.g., "Projects").
        style: Naming style:
            - "inside": Projects/Projects.md  (default, Folder Notes default)
            - "outside": Projects.md (note sits next to the folder)

    Returns:
        Path string for the folder note.
    """
    folder = folder.strip("/")
    name = folder.rsplit("/", 1)[-1]
    if style == "outside":
        parent = folder.rsplit("/", 1)[0] if "/" in folder else ""
        return f"{parent}/{name}.md".lstrip("/")
    return f"{folder}/{name}.md"


def exists(base_url: str, api_key: str | None, folder: str,
           style: str = "inside") -> bool:
    """Check if a folder note exists for the given folder.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        folder: Folder path relative to vault root.
        style: Folder note naming style ("inside" or "outside").

    Returns:
        True if the folder note exists.
    """
    path = _index_path(folder, style)
    return vault_mod.exists(base_url, api_key, path)


def get(base_url: str, api_key: str | None, folder: str,
        style: str = "inside", fmt: str = "markdown") -> dict:
    """Read a folder note's content.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        folder: Folder path relative to vault root.
        style: Folder note naming style.
        fmt: Output format — 'markdown', 'json', or 'map'.

    Returns:
        Dict with 'content' key or full NoteJson.
    """
    path = _index_path(folder, style)
    return vault_mod.get(base_url, api_key, path, fmt=fmt)


def create(base_url: str, api_key: str | None, folder: str,
           title: str | None = None, content: str | None = None,
           style: str = "inside", overwrite: bool = False) -> dict:
    """Create a folder note for the given folder.

    Generates a default index with links to all files in the folder
    if no content is provided.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        folder: Folder path relative to vault root.
        title: Optional title (defaults to folder name).
        content: Optional custom content. If None, auto-generates an index.
        style: Folder note naming style.
        overwrite: If False and note exists, raises RuntimeError.

    Returns:
        Status dict with 'file' key.

    Raises:
        RuntimeError: If note exists and overwrite=False.
    """
    path = _index_path(folder, style)
    folder_name = folder.strip("/").rsplit("/", 1)[-1]

    if not overwrite and vault_mod.exists(base_url, api_key, path):
        raise RuntimeError(
            f"Folder note already exists: {path}  (use --overwrite to replace)"
        )

    if content is None:
        heading = title or folder_name
        lines = [f"# {heading}\n"]

        result = vault_mod.list_dir(base_url, api_key, folder)
        files = result.get("files", result) if isinstance(result, dict) else result
        if isinstance(files, list):
            for f in sorted(files):
                if f.endswith("/"):
                    lines.append(f"- 📁 [[{folder}/{f.rstrip('/')}|{f.rstrip('/')}]]")
                else:
                    name_no_ext = f.rsplit(".", 1)[0] if "." in f else f
                    if f == f"{folder_name}.md":
                        continue  # skip self
                    lines.append(f"- [[{folder}/{f}|{name_no_ext}]]")

        content = "\n".join(lines) + "\n"

    vault_mod.put(base_url, api_key, path, content)
    return {"status": "ok", "file": path, "folder": folder}


def refresh(base_url: str, api_key: str | None, folder: str,
            title: str | None = None, style: str = "inside") -> dict:
    """Regenerate a folder note's auto-index content.

    Overwrites the existing folder note with a fresh file listing.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        folder: Folder path relative to vault root.
        title: Optional title override.
        style: Folder note naming style.

    Returns:
        Status dict.
    """
    return create(base_url, api_key, folder, title=title,
                  style=style, overwrite=True)


def list_folders_with_notes(base_url: str, api_key: str | None,
                            root: str = "",
                            style: str = "inside") -> list:
    """List folders that have folder notes.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        root: Root directory to scan (default: vault root).
        style: Folder note naming style.

    Returns:
        List of dicts: [{folder, note_path, has_note}].
    """
    result = vault_mod.list_dir(base_url, api_key, root)
    files = result.get("files", result) if isinstance(result, dict) else result
    if not isinstance(files, list):
        return []

    folders = []
    for f in files:
        if f.endswith("/"):
            folder_path = f"{root}/{f}".strip("/").rstrip("/") if root else f.rstrip("/")
            note_path = _index_path(folder_path, style)
            has_note = vault_mod.exists(base_url, api_key, note_path)
            folders.append({
                "folder": folder_path,
                "note_path": note_path,
                "has_note": has_note,
            })
    return folders
