#!/usr/bin/env python3
"""RedTrack CLI — A command-line interface for performance marketing tracking.

This CLI provides full access to the RedTrack REST API for managing campaigns,
offers, traffic channels, landers, conversions, costs, reports, and automation rules.

Usage:
    # One-shot commands
    cli-anything-redtrack campaign list
    cli-anything-redtrack --json campaign get 12345
    cli-anything-redtrack --api-key YOUR_KEY account info

    # Interactive REPL
    cli-anything-redtrack
"""

import sys
import os
import json
import click
from typing import Optional

from cli_anything.redtrack.utils.redtrack_backend import DEFAULT_BASE_URL
from cli_anything.redtrack.core import campaigns as campaigns_mod
from cli_anything.redtrack.core import offers as offers_mod
from cli_anything.redtrack.core import traffic as traffic_mod
from cli_anything.redtrack.core import landers as landers_mod
from cli_anything.redtrack.core import conversions as conversions_mod
from cli_anything.redtrack.core import reports as reports_mod
from cli_anything.redtrack.core import costs as costs_mod
from cli_anything.redtrack.core import rules as rules_mod
from cli_anything.redtrack.core import session as session_mod
from cli_anything.redtrack.core import domains as domains_mod
from cli_anything.redtrack.core import dictionary as dictionary_mod
from cli_anything.redtrack.utils.redtrack_backend import api_get, api_post, api_delete

# Global state
_json_output = False
_repl_mode = False
_api_key: str | None = None
_base_url = DEFAULT_BASE_URL


def output(data, message: str = ""):
    """Output data in human-readable or JSON format depending on --json flag."""
    if _json_output:
        click.echo(json.dumps(data if data is not None else [], indent=2, default=str))
    else:
        if message:
            click.echo(message)
        if data is None:
            click.echo("(no data)")
            return
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        else:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0):
    """Recursively print a dict in human-readable key: value format."""
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _extract_list(data) -> list:
    """Extract list from response — handles null, plain list, and paginated {items, total}."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return [data]


def _print_list(items: list, indent: int = 0):
    """Print a list of items, recursing into dicts."""
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    """Decorator that catches RuntimeError/ValueError and handles exit codes."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "runtime_error"}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except (ValueError, IndexError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def _get_key() -> str:
    """Get the active API key from global state or environment."""
    from cli_anything.redtrack.utils.redtrack_backend import _get_api_key
    return _get_api_key(_api_key)


def _extract_list(result):
    """Extract a list from an API result (handles list, dict with data, or None)."""
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("data", result)
    return result


# ── Main CLI Group ────────────────────────────────────────────────
@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.option("--api-key", "api_key_opt", type=str, default=None,
              help="RedTrack API key (overrides REDTRACK_API_KEY env var)")
@click.option("--base-url", type=str, default=None,
              help=f"RedTrack API base URL (default: {DEFAULT_BASE_URL})")
@click.pass_context
def cli(ctx, use_json, api_key_opt, base_url):
    """RedTrack CLI — Performance marketing tracking.

    Manage campaigns, offers, traffic channels, landers, conversions,
    costs, reports, and automation rules via the RedTrack REST API.

    Run without a subcommand to enter interactive REPL mode.
    """
    global _json_output, _api_key, _base_url
    _json_output = use_json
    if api_key_opt:
        _api_key = api_key_opt
    if base_url:
        _base_url = base_url

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── Account Commands ──────────────────────────────────────────────
@cli.group()
def account():
    """Account information commands."""
    pass


@account.command("info")
@handle_error
def account_info():
    """Show RedTrack account information."""
    result = api_get("/me/settings", api_key=_get_key(), base_url=_base_url)
    output(result, "Account Info")


# ── Campaign Commands ─────────────────────────────────────────────
@cli.group()
def campaign():
    """Campaign management commands."""
    pass


@campaign.command("list")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--page", type=int, default=1, help="Page number (default: 1)")
@click.option("--per", type=int, default=100, help="Results per page (default: 100)")
@handle_error
def campaign_list(date_from, date_to, page, per):
    """List all campaigns."""
    result = campaigns_mod.list_campaigns(
        _get_key(), _base_url,
        date_from=date_from, date_to=date_to, page=page, per=per
    )
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No campaigns found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40} {'STATUS':<12}")
            click.echo("─" * 66)
            for c in items:
                cid = str(c.get("id", ""))
                name = str(c.get("name", ""))[:38]
                status = str(c.get("status", ""))
                click.echo(f"{cid:<12} {name:<40} {status:<12}")
        else:
            output(result)


@campaign.command("get")
@click.argument("campaign_id")
@handle_error
def campaign_get(campaign_id):
    """Get a campaign by ID."""
    result = campaigns_mod.get_campaign(_get_key(), _base_url, campaign_id)
    output(result, f"Campaign {campaign_id}")


@campaign.command("create")
@click.option("--name", required=True, help="Campaign name")
@click.option("--traffic-channel-id", required=True, help="Traffic channel ID")
@click.option("--domain", default=None, help="Custom tracking domain")
@click.option("--cost-type", default=None,
              help="Cost type (cpc, cpm, cpa, revshare, auto, daily_budget)")
@click.option("--cost-value", type=float, default=None, help="Cost value")
@handle_error
def campaign_create(name, traffic_channel_id, domain, cost_type, cost_value):
    """Create a new campaign."""
    result = campaigns_mod.create_campaign(
        _get_key(), _base_url,
        name=name, traffic_channel_id=traffic_channel_id,
        domain=domain, cost_type=cost_type, cost_value=cost_value
    )
    output(result, f"Campaign created: {name}")


@campaign.command("update")
@click.argument("campaign_id")
@click.option("--name", default=None, help="New campaign name")
@click.option("--status", type=click.Choice(["active", "paused"]),
              help="Campaign status.")
@click.option("--cost-type", default=None, help="New cost type")
@click.option("--cost-value", type=float, default=None, help="New cost value")
@handle_error
def campaign_update(campaign_id, name, status, cost_type, cost_value):
    """Update a campaign."""
    result = campaigns_mod.update_campaign(
        _get_key(), _base_url, campaign_id,
        name=name, status=status, cost_type=cost_type, cost_value=cost_value
    )
    output(result, f"Campaign {campaign_id} updated")


@campaign.command("delete")
@click.argument("campaign_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@handle_error
def campaign_delete(campaign_id, confirm):
    """Archive a campaign (RedTrack uses status=archived instead of DELETE).

    CAMPAIGN_ID: The ID of the campaign to archive.
    """
    if not confirm:
        click.confirm(
            f"Archive campaign {campaign_id}? (use --confirm to skip)",
            abort=True
        )
    result = campaigns_mod.update_campaign_statuses(
        _get_key(), _base_url, ids=[campaign_id], status="archived"
    )
    output(result, f"Campaign {campaign_id} archived.")


@campaign.command("list-v2")
@click.option("--date-from", help="Start date (YYYY-MM-DD).")
@click.option("--date-to", help="End date (YYYY-MM-DD).")
@click.option("--page", default=1, show_default=True, help="Page number.")
@click.option("--per", default=100, show_default=True, help="Results per page.")
@handle_error
def campaign_list_v2(date_from, date_to, page, per):
    """List campaigns via the v2 endpoint (lighter, no total_stat)."""
    result = campaigns_mod.list_campaigns_v2(
        _get_key(), _base_url, date_from=date_from, date_to=date_to,
        page=page, per=per
    )
    output(_extract_list(result), "Campaigns (v2)")


@campaign.command("status-update")
@click.argument("ids", nargs=-1, required=True)
@click.option("--status", required=True,
              type=click.Choice(["active", "paused", "archived"]),
              help="New status for the campaigns.")
@handle_error
def campaign_status_update(ids, status):
    """Bulk update campaign statuses.

    IDS: One or more campaign IDs to update.
    """
    result = campaigns_mod.update_campaign_statuses(
        _get_key(), _base_url, list(ids), status
    )
    output(result, f"Updated {len(ids)} campaign(s) to '{status}'")


@campaign.command("links")
@click.argument("campaign_id")
@handle_error
def campaign_links(campaign_id):
    """Show tracking links for a campaign."""
    result = campaigns_mod.get_campaign_links(_get_key(), _base_url, campaign_id)
    output(result, f"Tracking links for campaign {campaign_id}")


# ── Offer Commands ────────────────────────────────────────────────
@cli.group()
def offer():
    """Offer management commands."""
    pass


@offer.command("list")
@handle_error
def offer_list():
    """List all offers."""
    result = offers_mod.list_offers(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No offers found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40} {'PAYOUT':<12}")
            click.echo("─" * 66)
            for o in items:
                oid = str(o.get("id", ""))
                name = str(o.get("name", ""))[:38]
                payout = str(o.get("payout", ""))
                click.echo(f"{oid:<12} {name:<40} {payout:<12}")
        else:
            output(result)


@offer.command("get")
@click.argument("offer_id")
@handle_error
def offer_get(offer_id):
    """Get an offer by ID."""
    result = offers_mod.get_offer(_get_key(), _base_url, offer_id)
    output(result, f"Offer {offer_id}")


@offer.command("create")
@click.option("--name", required=True, help="Offer name")
@click.option("--offer-source-id", default=None, help="Offer source (affiliate network) ID")
@click.option("--url", default=None, help="Offer destination URL")
@click.option("--payout", type=float, default=None, help="Default payout amount")
@handle_error
def offer_create(name, offer_source_id, url, payout):
    """Create a new offer."""
    result = offers_mod.create_offer(
        _get_key(), _base_url,
        name=name, network_id=offer_source_id, url=url, payout=payout
    )
    output(result, f"Offer created: {name}")


@offer.command("update")
@click.argument("offer_id")
@click.option("--name", default=None, help="New offer name")
@click.option("--url", default=None, help="New offer URL")
@click.option("--payout", type=float, default=None, help="New payout amount")
@click.option("--status", type=click.Choice(["active", "paused"]),
              help="Offer status.")
@handle_error
def offer_update(offer_id, name, url, payout, status):
    """Update an offer."""
    result = offers_mod.update_offer(
        _get_key(), _base_url, offer_id,
        name=name, url=url, payout=payout, status=status
    )
    output(result, f"Offer {offer_id} updated")


@offer.command("delete")
@click.argument("offer_id")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
@handle_error
def offer_delete(offer_id, confirm):
    """Archive an offer (RedTrack uses status=archived instead of DELETE).

    OFFER_ID: The ID of the offer to archive.
    """
    if not confirm:
        click.confirm(
            f"Archive offer {offer_id}? (use --confirm to skip)",
            abort=True
        )
    result = offers_mod.update_offer_statuses(
        _get_key(), _base_url, ids=[offer_id], status="archived"
    )
    output(result, f"Offer {offer_id} archived.")


@offer.command("status-update")
@click.argument("ids", nargs=-1, required=True)
@click.option("--status", required=True,
              type=click.Choice(["active", "paused", "archived"]),
              help="New status for the offers.")
@handle_error
def offer_status_update(ids, status):
    """Bulk update offer statuses.

    IDS: One or more offer IDs to update.
    """
    result = offers_mod.update_offer_statuses(
        _get_key(), _base_url, list(ids), status
    )
    output(result, f"Updated {len(ids)} offer(s) to '{status}'")


@offer.command("export")
@click.option("--ids", help="Comma-separated offer IDs to export.")
@click.option("--status", help="Filter by status.")
@click.option("--networks", help="Filter by network IDs.")
@click.option("--countries", help="Filter by country codes.")
@handle_error
def offer_export(ids, status, networks, countries):
    """Export offers to S3 via GET /offers/export."""
    result = offers_mod.export_offers(
        _get_key(), _base_url, ids=ids, status=status,
        networks=networks, countries=countries
    )
    output(result, "Offer Export")


@offer.command("status-update")
@click.argument("ids", nargs=-1, required=True)
@click.option("--status", required=True,
              type=click.Choice(["active", "paused", "archived"]),
              help="New status for the offers.")
@handle_error
def offer_status_update(ids, status):
    """Bulk update offer statuses.

    IDS: One or more offer IDs to update.
    """
    result = offers_mod.update_offer_statuses(
        _get_key(), _base_url, list(ids), status
    )
    output(result, f"Updated {len(ids)} offer(s) to '{status}'")


@offer.command("export")
@click.option("--ids", help="Comma-separated offer IDs to export.")
@click.option("--status", help="Filter by status.")
@click.option("--networks", help="Filter by network IDs.")
@click.option("--countries", help="Filter by country codes.")
@handle_error
def offer_export(ids, status, networks, countries):
    """Export offers to S3 via GET /offers/export."""
    result = offers_mod.export_offers(
        _get_key(), _base_url, ids=ids, status=status,
        networks=networks, countries=countries
    )
    output(result, "Offer Export")


@offer.command("status-update")
@click.argument("ids", nargs=-1, required=True)
@click.option("--status", required=True,
              type=click.Choice(["active", "paused", "archived"]),
              help="New status for the offers.")
@handle_error
def offer_status_update(ids, status):
    """Bulk update offer statuses.

    IDS: One or more offer IDs to update.
    """
    result = offers_mod.update_offer_statuses(
        _get_key(), _base_url, list(ids), status
    )
    output(result, f"Updated {len(ids)} offer(s) to '{status}'")


@offer.command("export")
@click.option("--ids", help="Comma-separated offer IDs to export.")
@click.option("--status", help="Filter by status.")
@click.option("--networks", help="Filter by network IDs.")
@click.option("--countries", help="Filter by country codes.")
@handle_error
def offer_export(ids, status, networks, countries):
    """Export offers to S3 via GET /offers/export."""
    result = offers_mod.export_offers(
        _get_key(), _base_url, ids=ids, status=status,
        networks=networks, countries=countries
    )
    output(result, "Offer Export")


@offer.command("status-update")
@click.argument("ids", nargs=-1, required=True)
@click.option("--status", required=True,
              type=click.Choice(["active", "paused", "archived"]),
              help="New status for the offers.")
@handle_error
def offer_status_update(ids, status):
    """Bulk update offer statuses.

    IDS: One or more offer IDs to update.
    """
    result = offers_mod.update_offer_statuses(
        _get_key(), _base_url, list(ids), status
    )
    output(result, f"Updated {len(ids)} offer(s) to '{status}'")


@offer.command("export")
@click.option("--ids", help="Comma-separated offer IDs to export.")
@click.option("--status", help="Filter by status.")
@click.option("--networks", help="Filter by network IDs.")
@click.option("--countries", help="Filter by country codes.")
@handle_error
def offer_export(ids, status, networks, countries):
    """Export offers to S3 via GET /offers/export."""
    result = offers_mod.export_offers(
        _get_key(), _base_url, ids=ids, status=status,
        networks=networks, countries=countries
    )
    output(result, "Offer Export")


# ── Offer Source Commands ─────────────────────────────────────────
@cli.group("offer-source")
def offer_source():
    """Offer source (affiliate network) management commands."""
    pass


@offer_source.command("list")
@handle_error
def offer_source_list():
    """List all offer sources (affiliate networks)."""
    result = offers_mod.list_offer_sources(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No offer sources found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40}")
            click.echo("─" * 54)
            for s in items:
                sid = str(s.get("id", ""))
                name = str(s.get("name", ""))[:38]
                click.echo(f"{sid:<12} {name:<40}")
        else:
            output(result)


@offer_source.command("get")
@click.argument("source_id")
@handle_error
def offer_source_get(source_id):
    """Get an offer source by ID."""
    result = offers_mod.get_offer_source(_get_key(), _base_url, source_id)
    output(result, f"Offer source {source_id}")


@offer_source.command("create")
@click.option("--name", required=True, help="Offer source name")
@click.option("--postback-url", default=None, help="Postback URL template")
@click.option("--click-id-param", default=None, help="Click ID parameter name")
@click.option("--payout-param", default=None, help="Payout parameter name")
@handle_error
def offer_source_create(name, postback_url, click_id_param, payout_param):
    """Create a new offer source."""
    result = offers_mod.create_offer_source(
        _get_key(), _base_url,
        name=name, postback_url=postback_url,
        click_id_param=click_id_param, payout_param=payout_param
    )
    output(result, f"Offer source created: {name}")


@offer_source.command("update")
@click.argument("source_id")
@click.option("--name", default=None, help="New name")
@click.option("--postback-url", default=None, help="New postback URL")
@click.option("--click-id-param", default=None, help="New click ID param name")
@click.option("--payout-param", default=None, help="New payout param name")
@handle_error
def offer_source_update(source_id, name, postback_url, click_id_param, payout_param):
    """Update an offer source."""
    result = offers_mod.update_offer_source(
        _get_key(), _base_url, source_id,
        name=name, postback_url=postback_url,
        click_id_param=click_id_param, payout_param=payout_param
    )
    output(result, f"Offer source {source_id} updated")


@offer_source.command("delete")
@click.argument("source_id")
@handle_error
def offer_source_delete(source_id):
    """Delete an offer source."""
    result = offers_mod.delete_offer_source(_get_key(), _base_url, source_id)
    output(result, f"Offer source {source_id} deleted")


# ── Traffic Channel Commands ──────────────────────────────────────
@cli.group()
def traffic():
    """Traffic channel management commands."""
    pass


@traffic.command("list")
@handle_error
def traffic_list():
    """List all traffic channels."""
    result = traffic_mod.list_traffic_channels(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No traffic channels found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40} {'STATUS':<12}")
            click.echo("─" * 66)
            for t in items:
                tid = str(t.get("id", ""))
                name = str(t.get("name", ""))[:38]
                status = str(t.get("status", ""))
                click.echo(f"{tid:<12} {name:<40} {status:<12}")
        else:
            output(result)


@traffic.command("get")
@click.argument("channel_id")
@handle_error
def traffic_get(channel_id):
    """Get a traffic channel by ID."""
    result = traffic_mod.get_traffic_channel(_get_key(), _base_url, channel_id)
    output(result, f"Traffic channel {channel_id}")


@traffic.command("create")
@click.option("--name", required=True, help="Traffic channel name")
@click.option("--template", default=None, help="Template name for pre-configured settings")
@handle_error
def traffic_create(name, template):
    """Create a new traffic channel."""
    result = traffic_mod.create_traffic_channel(
        _get_key(), _base_url, name=name, template=template
    )
    output(result, f"Traffic channel created: {name}")


@traffic.command("update")
@click.argument("channel_id")
@click.option("--name", default=None, help="New name")
@click.option("--status", default=None, help="New status (active, paused)")
@handle_error
def traffic_update(channel_id, name, status):
    """Update a traffic channel."""
    result = traffic_mod.update_traffic_channel(
        _get_key(), _base_url, channel_id, name=name, status=status
    )
    output(result, f"Traffic channel {channel_id} updated")


@traffic.command("delete")
@click.argument("channel_id")
@handle_error
def traffic_delete(channel_id):
    """Delete a traffic channel."""
    result = traffic_mod.delete_traffic_channel(_get_key(), _base_url, channel_id)
    output(result, f"Traffic channel {channel_id} deleted")


# ── Lander Commands ───────────────────────────────────────────────
@cli.group()
def lander():
    """Lander (landing page) management commands."""
    pass


@lander.command("list")
@handle_error
def lander_list():
    """List all landers."""
    result = landers_mod.list_landers(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No landers found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40} {'STATUS':<12}")
            click.echo("─" * 66)
            for l in items:
                lid = str(l.get("id", ""))
                name = str(l.get("name", ""))[:38]
                status = str(l.get("status", ""))
                click.echo(f"{lid:<12} {name:<40} {status:<12}")
        else:
            output(result)


@lander.command("get")
@click.argument("lander_id")
@handle_error
def lander_get(lander_id):
    """Get a lander by ID."""
    result = landers_mod.get_lander(_get_key(), _base_url, lander_id)
    output(result, f"Lander {lander_id}")


@lander.command("create")
@click.option("--name", required=True, help="Lander name")
@click.option("--url", default=None, help="Landing page URL")
@click.option("--tracking-type", default=None,
              help="Tracking type (redirect, direct)")
@handle_error
def lander_create(name, url, tracking_type):
    """Create a new lander."""
    result = landers_mod.create_lander(
        _get_key(), _base_url, name=name, url=url, tracking_type=tracking_type
    )
    output(result, f"Lander created: {name}")


@lander.command("update")
@click.argument("lander_id")
@click.option("--name", default=None, help="New name")
@click.option("--url", default=None, help="New URL")
@click.option("--tracking-type", default=None, help="New tracking type")
@click.option("--status", default=None, help="New status")
@handle_error
def lander_update(lander_id, name, url, tracking_type, status):
    """Update a lander."""
    result = landers_mod.update_lander(
        _get_key(), _base_url, lander_id,
        name=name, url=url, tracking_type=tracking_type, status=status
    )
    output(result, f"Lander {lander_id} updated")


@lander.command("delete")
@click.argument("lander_id")
@handle_error
def lander_delete(lander_id):
    """Delete a lander."""
    result = landers_mod.delete_lander(_get_key(), _base_url, lander_id)
    output(result, f"Lander {lander_id} deleted")


# ── Conversion Commands ───────────────────────────────────────────
@cli.group()
def conversion():
    """Conversion tracking commands."""
    pass


@conversion.command("list")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--campaign-id", default=None, help="Filter by campaign ID")
@click.option("--status", default=None,
              help="Filter by status (approved, pending, declined, fired)")
@handle_error
def conversion_list(date_from, date_to, campaign_id, status):
    """List conversions."""
    result = conversions_mod.list_conversions(
        _get_key(), _base_url,
        date_from=date_from, date_to=date_to,
        campaign_id=campaign_id, status=status
    )
    if _json_output:
        output(result)
    else:
        items = _extract_list(result)
        if not items:
            click.echo("No conversions found.")
            return
        click.echo(f"{'ID':<16} {'CLICK ID':<20} {'STATUS':<12} {'PAYOUT':<10}")
        click.echo("─" * 60)
        for c in items:
            cid = str(c.get("id", ""))[:14]
            click_id = str(c.get("click_id", ""))[:18]
            st = str(c.get("status", ""))
            payout = str(c.get("payout", ""))
            click.echo(f"{cid:<16} {click_id:<20} {st:<12} {payout:<10}")


@conversion.command("upload")
@click.option("--click-id", required=True, help="RedTrack click ID")
@click.option("--status", default="approved",
              help="Conversion status (approved, pending, declined)")
@click.option("--payout", type=float, default=None, help="Payout amount")
@click.option("--type", "conversion_type", default=None, help="Conversion type")
@handle_error
def conversion_upload(click_id, status, payout, conversion_type):
    """Manually upload a conversion."""
    result = conversions_mod.upload_conversion(
        _get_key(), _base_url,
        click_id=click_id, status=status,
        payout=payout, conversion_type=conversion_type
    )
    output(result, f"Conversion uploaded for click_id: {click_id}")


@conversion.command("types")
@handle_error
def conversion_types():
    """List available conversion types."""
    types = conversions_mod.get_conversion_types()
    if _json_output:
        output({"conversion_types": types})
    else:
        click.echo("Conversion Types:")
        for t in types:
            click.echo(f"  - {t}")


@conversion.command("export")
@click.option("--date-from", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--date-to", required=True, help="End date (YYYY-MM-DD).")
@click.option("--campaign-id", help="Filter by campaign ID.")
@click.option("--offer-id", help="Filter by offer ID.")
@handle_error
def conversion_export(date_from, date_to, campaign_id, offer_id):
    """Export conversions to S3 via GET /conversions/export."""
    result = conversions_mod.export_conversions(
        _get_key(), _base_url, date_from=date_from, date_to=date_to,
        campaign_id=campaign_id, offer_id=offer_id
    )
    output(result, "Conversion Export")


# ── Report Commands ───────────────────────────────────────────────
@cli.group()
def report():
    """Reporting commands."""
    pass


@report.command("general")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--group-by", default=None,
              help="Group by field (campaign, offer, country, etc.)")
@click.option("--filters", default=None, help="Filter expression or JSON")
@handle_error
def report_general(date_from, date_to, group_by, filters):
    """Get a general performance report."""
    result = reports_mod.general_report(
        _get_key(), _base_url,
        date_from=date_from, date_to=date_to,
        group_by=group_by, filters=filters
    )
    output(result, "General Report")


@report.command("campaigns")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@handle_error
def report_campaigns(date_from, date_to):
    """Get a campaigns performance report."""
    result = reports_mod.campaigns_report(
        _get_key(), _base_url,
        date_from=date_from, date_to=date_to
    )
    output(result, "Campaigns Report")


@report.command("clicks")
@click.option("--date-from", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--date-to", default=None, help="End date (YYYY-MM-DD)")
@click.option("--campaign-id", default=None, help="Filter by campaign ID")
@handle_error
def report_clicks(date_from, date_to, campaign_id):
    """Get click-level logs via /report endpoint.

    Note: Uses group_by='click'. Returns empty list if no click data exists
    for the date range, or if this group_by value is unsupported by your
    RedTrack plan.
    """
    result = reports_mod.click_logs(
        _get_key(), _base_url,
        date_from=date_from, date_to=date_to, campaign_id=campaign_id
    )
    output(result, "Click Logs")


@report.command("stream")
@click.option("--date-from", help="Start date (YYYY-MM-DD).")
@click.option("--date-to", help="End date (YYYY-MM-DD).")
@handle_error
def report_stream(date_from, date_to):
    """Get stream-level performance report."""
    result = reports_mod.stream_report(_get_key(), _base_url,
                                       date_from=date_from, date_to=date_to)
    output(result, "Stream Report")


# ── Cost Commands ─────────────────────────────────────────────────
@cli.group()
def cost():
    """Cost tracking commands."""
    pass


@cost.command("list")
@click.option("--date-from", help="Start date (YYYY-MM-DD).")
@click.option("--date-to", help="End date (YYYY-MM-DD).")
@click.option("--campaign-id", help="Filter by campaign ID.")
@handle_error
def cost_list(date_from, date_to, campaign_id):
    """Get cost metrics via the report endpoint (grouped by campaign)."""
    result = costs_mod.get_cost_from_report(
        _get_key(), _base_url,
        date_from=date_from,
        date_to=date_to,
        campaign_id=campaign_id,
    )
    output(result, "Cost Report")


# ── Rule Commands ─────────────────────────────────────────────────
@cli.group()
def rule():
    """Automation rule management commands."""
    pass


@rule.command("list")
@handle_error
def rule_list():
    """List all automation rules."""
    result = rules_mod.list_rules(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = result if isinstance(result, list) else (result.get("data", result) if result is not None else [])
        if isinstance(items, list):
            if not items:
                click.echo("No rules found.")
                return
            click.echo(f"{'ID':<12} {'NAME':<40} {'STATUS':<12}")
            click.echo("─" * 66)
            for r in items:
                rid = str(r.get("id", ""))
                name = str(r.get("name", ""))[:38]
                status = str(r.get("status", ""))
                click.echo(f"{rid:<12} {name:<40} {status:<12}")
        else:
            output(result)


@rule.command("get")
@click.argument("rule_id")
@handle_error
def rule_get(rule_id):
    """Get an automation rule by ID."""
    result = rules_mod.get_rule(_get_key(), _base_url, rule_id)
    output(result, f"Rule {rule_id}")


@rule.command("create")
@click.option("--name", required=True, help="Rule name")
@click.option("--condition", default=None, help="Condition expression or JSON")
@click.option("--action", default=None, help="Action to take when condition is met")
@handle_error
def rule_create(name, condition, action):
    """Create a new automation rule."""
    result = rules_mod.create_rule(
        _get_key(), _base_url, name=name, condition=condition, action=action
    )
    output(result, f"Rule created: {name}")


@rule.command("update")
@click.argument("rule_id")
@click.option("--status", default=None,
              help="New status: 'active' to enable, 'paused' to disable")
@click.option("--name", default=None, help="New rule name")
@handle_error
def rule_update(rule_id, status, name):
    """Update an automation rule (enable/disable or rename)."""
    result = rules_mod.update_rule(
        _get_key(), _base_url, rule_id, name=name, status=status
    )
    output(result, f"Rule {rule_id} updated")


@rule.command("delete")
@click.argument("rule_id")
@handle_error
def rule_delete(rule_id):
    """Delete an automation rule."""
    result = rules_mod.delete_rule(_get_key(), _base_url, rule_id)
    output(result, f"Rule {rule_id} deleted")


# ── Domain Commands ───────────────────────────────────────────────
@cli.group()
def domain():
    """Custom tracking domain management commands."""
    pass


@domain.command("list")
@handle_error
def domain_list():
    """List custom tracking domains."""
    result = domains_mod.list_domains(_get_key(), _base_url)
    if _json_output:
        output(result)
    else:
        items = _extract_list(result)
        if not items:
            click.echo("No custom domains found.")
            return
        click.echo(f"{'ID':<12} {'DOMAIN':<50}")
        click.echo("─" * 64)
        for d in items:
            did = str(d.get("id", ""))
            dname = str(d.get("domain", d.get("name", "")))[:48]
            click.echo(f"{did:<12} {dname:<50}")


@domain.command("add")
@click.option("--domain", "domain_name", required=True, help="Domain to add")
@handle_error
def domain_add(domain_name):
    """Add a custom tracking domain."""
    result = domains_mod.add_domain(_get_key(), _base_url, domain=domain_name)
    output(result, f"Domain added: {domain_name}")


@domain.command("update")
@click.argument("domain_id")
@click.option("--domain-name", help="New domain name.")
@handle_error
def domain_update(domain_id, domain_name):
    """Update a custom domain. DOMAIN_ID: The domain ID."""
    result = domains_mod.update_domain(
        _get_key(), _base_url, domain_id, domain=domain_name
    )
    output(result, f"Domain {domain_id} updated.")


@domain.command("delete")
@click.argument("domain_id")
@click.option("--confirm", is_flag=True)
@handle_error
def domain_delete(domain_id, confirm):
    """Delete a custom domain. DOMAIN_ID: The domain ID."""
    if not confirm:
        click.confirm(f"Delete domain {domain_id}?", abort=True)
    result = domains_mod.delete_domain(_get_key(), _base_url, domain_id)
    output(result, f"Domain {domain_id} deleted.")


@domain.command("ssl-renew")
@click.argument("domain_id")
@handle_error
def domain_ssl_renew(domain_id):
    """Regenerate the free SSL certificate for a domain."""
    result = domains_mod.regenerate_ssl(_get_key(), _base_url, domain_id)
    output(result, f"SSL regeneration triggered for domain {domain_id}.")


# ── Lookup Commands ───────────────────────────────────────────────
@cli.group()
def lookup():
    """Reference data lookups — browsers, countries, OS, devices, etc.

    These endpoints do not require authentication.
    """
    pass


@lookup.command("list")
@handle_error
def lookup_list():
    """List all available lookup types."""
    keys = dictionary_mod.list_all_keys()
    output({"available_lookups": keys}, "Available Lookups")


@lookup.command("get")
@click.argument("lookup_type")
@handle_error
def lookup_get(lookup_type):
    """Get reference data for a specific type.

    LOOKUP_TYPE: One of: browsers, countries, os, devices, isp, languages,
    currencies, cities, categories, connection_types, device_brands,
    device_fullnames, browser_fullnames, os_fullnames
    """
    lookup_map = {
        "browsers": dictionary_mod.get_browsers,
        "browser_fullnames": dictionary_mod.get_browser_fullnames,
        "categories": dictionary_mod.get_categories,
        "cities": dictionary_mod.get_cities,
        "connection_types": dictionary_mod.get_connection_types,
        "countries": dictionary_mod.get_countries,
        "currencies": dictionary_mod.get_currencies,
        "device_brands": dictionary_mod.get_device_brands,
        "device_fullnames": dictionary_mod.get_device_fullnames,
        "devices": dictionary_mod.get_devices,
        "isp": dictionary_mod.get_isp,
        "languages": dictionary_mod.get_languages,
        "os": dictionary_mod.get_os,
        "os_fullnames": dictionary_mod.get_os_fullnames,
    }
    if lookup_type not in lookup_map:
        valid = ", ".join(sorted(lookup_map.keys()))
        raise click.BadParameter(
            f"Unknown lookup type '{lookup_type}'. Valid: {valid}",
            param_hint="LOOKUP_TYPE"
        )
    result = lookup_map[lookup_type](_base_url)
    output(result, f"Lookup: {lookup_type}")


# ── Session Commands ──────────────────────────────────────────────
@cli.group()
def session():
    """Session state commands."""
    pass


@session.command("status")
@handle_error
def session_status():
    """Show current session state (API key masked, base URL)."""
    info = session_mod.get_session_info(_api_key, _base_url)
    output(info, "Session Status")


# ── REPL ──────────────────────────────────────────────────────────
@cli.command()
@handle_error
def repl():
    """Start interactive REPL session."""
    from cli_anything.redtrack.utils.repl_skin import ReplSkin

    global _repl_mode
    _repl_mode = True

    skin = ReplSkin("redtrack", version="1.0.0")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    _repl_commands = {
        "account":      "info",
        "campaign":     "list|list-v2|get|create|update|delete|status-update|links",
        "offer":        "list|get|create|update|delete|status-update|export",
        "offer-source": "list|get|create|update|delete",
        "traffic":      "list|get|create|update|delete",
        "lander":       "list|get|create|update|delete",
        "conversion":   "list|upload|types",
        "report":       "general|campaigns|clicks",
        "cost":         "list",
        "rule":         "list|get|create|update|delete",
        "domain":       "list|add|update|delete|ssl-renew",
        "lookup":       "list|get",
        "session":      "status",
        "help":         "Show this help",
        "quit":         "Exit REPL",
    }

    while True:
        try:
            line = skin.get_input(pt_session, project_name="", modified=False)
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                skin.print_goodbye()
                break
            if line.lower() == "help":
                skin.help(_repl_commands)
                continue

            # Parse and execute command
            args = line.split()
            try:
                cli.main(args, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                skin.warning(f"Usage error: {e}")
            except Exception as e:
                skin.error(f"{e}")

        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

    _repl_mode = False


# ── Entry Point ───────────────────────────────────────────────────
def main():
    cli()


if __name__ == "__main__":
    main()
