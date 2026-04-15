"""Volumes commands for cli-anything-railway."""

from __future__ import annotations

import json
import sys

import click

from cli_anything.railway.utils.railway_backend import RailwayBackend, RailwayAPIError


@click.group("volumes")
def volumes_group():
    """Manage Railway persistent volumes."""


@volumes_group.command("list")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_list(ctx: click.Context, project_id: str, as_json: bool):
    """List volumes in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        volumes = backend.volumes_list(project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(volumes, indent=2))
        return

    if not volumes:
        skin.info("No volumes found.")
        return

    skin.table(
        ["ID", "Name", "Created"],
        [
            [v.get("id", ""), v.get("name", ""), (v.get("createdAt") or "")[:19]]
            for v in volumes
        ],
    )


@volumes_group.command("create")
@click.argument("name")
@click.option("--project", "project_id", required=True, help="Project ID.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_create(ctx: click.Context, name: str, project_id: str, as_json: bool):
    """Create a volume in a project."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        volume = backend.volume_create(name, project_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(volume, indent=2))
        return

    skin.success(f"Volume created: {volume.get('name')} (id: {volume.get('id')})")


@volumes_group.command("delete")
@click.argument("volume_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_delete(ctx: click.Context, volume_id: str, as_json: bool):
    """Delete a volume by ID."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_delete(volume_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "id": volume_id}, indent=2))
        return

    if result:
        skin.success(f"Volume {volume_id} deleted.")
    else:
        skin.warning(f"Volume delete returned false for {volume_id}.")


@volumes_group.command("update")
@click.argument("volume_id")
@click.option("--name", required=True, help="New volume name.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_update(ctx: click.Context, volume_id: str, name: str, as_json: bool):
    """Rename a volume."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_update(volume_id, name)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"updated": result, "id": volume_id}, indent=2))
        return

    if result:
        skin.success(f"Volume {volume_id} renamed to '{name}'.")
    else:
        skin.warning("Update returned false — check Railway dashboard.")


@volumes_group.command("info")
@click.argument("volume_instance_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_info(ctx: click.Context, volume_instance_id: str, as_json: bool):
    """Show volume instance details (mount path, size, state)."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        info = backend.volume_instance_info(volume_instance_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(info, indent=2))
        return

    if not info:
        skin.error(f"Volume instance not found: {volume_instance_id}")
        sys.exit(1)

    volume = info.get("volume") or {}
    svc_inst = info.get("serviceInstance") or {}
    skin.status_block(
        {
            "ID": info.get("id", ""),
            "Volume": f"{volume.get('name', '')} ({volume.get('id', '')})",
            "Service": svc_inst.get("serviceName") or "",
            "Mount Path": info.get("mountPath") or "",
            "Current Size (MB)": str(info.get("currentSizeMB") or ""),
            "State": info.get("state") or "",
        },
        title="Volume Instance",
    )


@volumes_group.command("set-mount")
@click.argument("volume_id")
@click.argument("mount_path")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_set_mount(
    ctx: click.Context, volume_id: str, mount_path: str, as_json: bool
):
    """Update the mount path for a volume instance."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_instance_update(volume_id, mount_path)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"updated": result, "volumeId": volume_id, "mountPath": mount_path}, indent=2))
        return

    if result:
        skin.success(f"Volume {volume_id} mount path set to '{mount_path}'.")
    else:
        skin.warning("Update returned false — check Railway dashboard.")


@volumes_group.command("backup-list")
@click.argument("volume_instance_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_backup_list(ctx: click.Context, volume_instance_id: str, as_json: bool):
    """List backups for a volume instance."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        backups = backend.volume_backup_list(volume_instance_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(backups, indent=2))
        return

    if not backups:
        skin.info("No backups found.")
        return

    skin.table(
        ["ID", "Name", "Created", "Expires", "Used (MB)", "Referenced (MB)"],
        [
            [
                b.get("id", ""),
                b.get("name") or "",
                (b.get("createdAt") or "")[:19],
                (b.get("expiresAt") or "")[:19],
                str(b.get("usedMB", "")),
                str(b.get("referencedMB", "")),
            ]
            for b in backups
        ],
    )


@volumes_group.command("backup-create")
@click.argument("volume_instance_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_backup_create(ctx: click.Context, volume_instance_id: str, as_json: bool):
    """Create a backup of a volume instance."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_backup_create(volume_instance_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(result, indent=2))
        return

    skin.success("Backup created successfully.")


@volumes_group.command("backup-restore")
@click.argument("backup_id")
@click.argument("volume_instance_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_backup_restore(
    ctx: click.Context, backup_id: str, volume_instance_id: str, as_json: bool
):
    """Restore a volume from a backup."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_backup_restore(backup_id, volume_instance_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"restored": result, "backupId": backup_id}, indent=2))
        return

    if result:
        skin.success(f"Volume restored from backup {backup_id}.")
    else:
        skin.warning("Restore returned false — check Railway dashboard.")


@volumes_group.command("backup-delete")
@click.argument("backup_id")
@click.argument("volume_instance_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
@click.pass_context
def volumes_backup_delete(
    ctx: click.Context, backup_id: str, volume_instance_id: str, as_json: bool
):
    """Delete a volume backup."""
    backend: RailwayBackend = ctx.obj["backend"]
    skin = ctx.obj["skin"]
    try:
        result = backend.volume_backup_delete(backup_id, volume_instance_id)
    except RailwayAPIError as exc:
        skin.error(str(exc))
        sys.exit(1)

    if as_json:
        click.echo(json.dumps({"deleted": result, "backupId": backup_id}, indent=2))
        return

    if result:
        skin.success(f"Backup {backup_id} deleted.")
    else:
        skin.warning("Delete returned false — check Railway dashboard.")
