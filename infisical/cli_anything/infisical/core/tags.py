"""Project-scoped secret tags: list, get, create, update, delete."""

from __future__ import annotations

import click

from cli_anything.infisical.utils.infisical_backend import (
    InfisicalBackend,
    InfisicalAPIError,
)
from cli_anything.infisical.utils.repl_skin import ReplSkin


skin = ReplSkin("infisical", version="1.1.0")


# ---------------------------------------------------------------------------
# Helpers (duplicated to avoid circular imports with infisical_cli.py)
# ---------------------------------------------------------------------------


def _handle_api_error(err):
    import json, sys
    skin.error(f"API error {err.status_code}:")
    if isinstance(err.body, dict):
        click.echo(json.dumps(err.body, indent=2), err=True)
    else:
        click.echo(str(err.body), err=True)
    sys.exit(1)


def _require_token(ctx):
    if not ctx.token:
        skin.error(
            "Authentication token is required. Set INFISICAL_TOKEN or pass --token."
        )
        import sys
        sys.exit(1)


def _require_workspace(ctx):
    if not ctx.workspace_id:
        skin.error(
            "Workspace ID is required. Set INFISICAL_WORKSPACE_ID or pass --workspace/-w."
        )
        import sys
        sys.exit(1)


def _print_json(data):
    import json
    click.echo(json.dumps(data, indent=2))


def _resolve_project(ctx, project: str) -> str:
    """Return the effective project id (flag takes precedence over context)."""
    if project:
        return project
    _require_workspace(ctx)
    return ctx.workspace_id


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class TagsClient:
    """High-level client for project-scoped tag operations."""

    def __init__(self, backend: InfisicalBackend, project_id: str):
        self.backend = backend
        self.project_id = project_id

    def list(self) -> list[dict]:
        return self.backend.list_tags(self.project_id)

    def get(self, tag_id: str) -> dict:
        return self.backend.get_tag(self.project_id, tag_id)

    def get_by_slug(self, slug: str) -> dict:
        return self.backend.get_tag_by_slug(self.project_id, slug)

    def create(self, slug: str, color: str | None = None) -> dict:
        return self.backend.create_tag(self.project_id, slug, color)

    def update(
        self,
        tag_id: str,
        slug: str | None = None,
        color: str | None = None,
    ) -> dict:
        return self.backend.update_tag(
            project_id=self.project_id,
            tag_id=tag_id,
            slug=slug,
            color=color,
        )

    def delete(self, tag_id: str) -> dict:
        return self.backend.delete_tag(self.project_id, tag_id)


# ---------------------------------------------------------------------------
# tags group
# ---------------------------------------------------------------------------


@click.group("tags")
def tags_group():
    """Manage project-scoped secret tags."""


def _render_tag_table(tags: list[dict]) -> None:
    headers = ["ID", "SLUG", "COLOR", "CREATED_AT"]
    rows = []
    for t in tags:
        tid = t.get("id") or t.get("_id") or ""
        slug = t.get("slug") or t.get("name") or ""
        color = t.get("color") or ""
        created = t.get("createdAt") or t.get("created_at") or ""
        rows.append([str(tid), str(slug), str(color), str(created)])
    skin.table(headers, rows, max_col_width=60)


@tags_group.command("list")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_list(click_ctx, project: str, output_json: bool) -> None:
    """List all tags for a project."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.list()
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        if not result:
            skin.info("No tags found.")
            return
        _render_tag_table(result)


@tags_group.command("get")
@click.argument("tag_id")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_get(click_ctx, tag_id: str, project: str, output_json: bool) -> None:
    """Get a tag by its ID."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.get(tag_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        _render_tag_table([result])


@tags_group.command("get-by-slug")
@click.argument("slug")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_get_by_slug(click_ctx, slug: str, project: str, output_json: bool) -> None:
    """Get a tag by its SLUG."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.get_by_slug(slug)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        _render_tag_table([result])


@tags_group.command("create")
@click.argument("slug")
@click.option("--color", default=None, help="Hex color for the tag (e.g. #AABBCC).")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_create(
    click_ctx, slug: str, color, project: str, output_json: bool
) -> None:
    """Create a new tag with SLUG."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)
    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.create(slug, color)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        tid = result.get("id") or result.get("_id", "")
        skin.success(f"Tag '{slug}' created (id: {tid}).")


@tags_group.command("update")
@click.argument("tag_id")
@click.option("--slug", default=None, help="New slug.")
@click.option("--color", default=None, help="New color.")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_update(
    click_ctx,
    tag_id: str,
    slug,
    color,
    project: str,
    output_json: bool,
) -> None:
    """Update a tag's slug and/or color."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)

    if slug is None and color is None:
        skin.error("At least one field is required: --slug or --color.")
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.update(tag_id, slug=slug, color=color)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Tag '{tag_id}' updated.")


@tags_group.command("delete")
@click.argument("tag_id")
@click.option("--yes", is_flag=True, default=False, help="Confirm deletion.")
@click.option("--project", default="", help="Project ID (overrides context).")
@click.option("--json", "output_json", is_flag=True, default=False)
@click.pass_context
def tags_delete(
    click_ctx, tag_id: str, yes: bool, project: str, output_json: bool
) -> None:
    """Delete a tag by TAG_ID (requires --yes)."""
    ctx = click_ctx.obj
    _require_token(ctx)
    project_id = _resolve_project(ctx, project)

    if not yes:
        skin.error("Refusing to delete tag. Pass --yes to confirm.")
        import sys
        sys.exit(1)

    use_json = output_json or ctx.output_json
    try:
        client = TagsClient(ctx.backend(), project_id)
        result = client.delete(tag_id)
    except InfisicalAPIError as err:
        _handle_api_error(err)
        return

    if use_json:
        _print_json(result)
    else:
        skin.success(f"Tag '{tag_id}' deleted.")


__all__ = ["TagsClient", "tags_group"]
