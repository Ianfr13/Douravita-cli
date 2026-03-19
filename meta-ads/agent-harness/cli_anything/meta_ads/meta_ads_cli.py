"""cli-anything-meta-ads — Main CLI entry point."""

import json
import sys

import click

from cli_anything.meta_ads.core import config as cfg_mod
from cli_anything.meta_ads.core import account as account_mod
from cli_anything.meta_ads.core import campaign as campaign_mod
from cli_anything.meta_ads.core import adset as adset_mod
from cli_anything.meta_ads.core import ad as ad_mod
from cli_anything.meta_ads.core import creative as creative_mod
from cli_anything.meta_ads.core import audience as audience_mod
from cli_anything.meta_ads.core import insights as insights_mod
from cli_anything.meta_ads.core.session import Session
from cli_anything.meta_ads.utils.meta_ads_backend import MetaAdsAPIError
from cli_anything.meta_ads.utils.repl_skin import ReplSkin

VERSION = "1.0.0"
skin = ReplSkin("meta-ads", version=VERSION)


class CliCtx:
    def __init__(self, json_mode, token=None, account=None):
        self.json_mode = json_mode
        self._token = token
        self._account = account

    @property
    def token(self):
        return self._token or cfg_mod.require_access_token()

    @property
    def account_id(self):
        return cfg_mod.require_ad_account_id(self._account)


pass_ctx = click.make_pass_decorator(CliCtx)


def _out(ctx, data):
    if ctx.json_mode:
        click.echo(json.dumps(data, indent=2, default=str))
    return data


def _handle_error(e, json_mode=False):
    if json_mode:
        click.echo(json.dumps({"error": str(e)}, indent=2), err=True)
    else:
        skin.error(str(e))
    sys.exit(1)


# ── Root group ────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output as JSON.")
@click.option("--token", default=None, envvar="META_ADS_ACCESS_TOKEN")
@click.option("--account", default=None, envvar="META_ADS_AD_ACCOUNT_ID")
@click.version_option(VERSION, prog_name="cli-anything-meta-ads")
@click.pass_context
def cli(ctx, json_mode, token, account):
    """cli-anything-meta-ads — Full CLI for the Meta Ads API.

    Manage campaigns, ad sets, ads, creatives, audiences, and insights.
    Run without subcommand to enter interactive REPL mode.
    Use --json for machine-readable output.
    """
    ctx.ensure_object(dict)
    ctx.obj = CliCtx(json_mode=json_mode, token=token, account=account)
    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── REPL ──────────────────────────────────────────────────────────────

@cli.command(hidden=True)
@click.pass_context
def repl(ctx):
    """Enter interactive REPL mode."""
    session = Session()
    skin.print_banner()
    COMMANDS = {
        "config show":              "Show credentials & config",
        "config set-token TOKEN":   "Save Meta access token",
        "config set-account ID":    "Save ad account ID",
        "config clear":             "Remove all stored credentials",
        "account info":             "Ad account details",
        "account list":             "List accessible ad accounts",
        "account spend":            "Account spend summary",
        "campaign list":            "List campaigns",
        "campaign get ID":          "Get campaign details",
        "campaign create ...":      "Create a campaign",
        "campaign pause ID":        "Pause a campaign",
        "campaign activate ID":     "Activate a campaign",
        "campaign delete ID":       "Delete a campaign",
        "adset list":               "List ad sets",
        "adset get ID":             "Get ad set details",
        "adset create ...":         "Create an ad set",
        "adset pause ID":           "Pause an ad set",
        "adset activate ID":        "Activate an ad set",
        "adset delete ID":          "Delete an ad set",
        "ad list":                  "List ads",
        "ad get ID":                "Get ad details",
        "ad create ...":            "Create an ad",
        "ad pause ID":              "Pause an ad",
        "ad activate ID":           "Activate an ad",
        "ad delete ID":             "Delete an ad",
        "creative list":            "List creatives",
        "creative get ID":          "Get creative details",
        "creative create ...":      "Create a creative",
        "creative images":          "List uploaded images",
        "creative upload-image F":  "Upload an image file",
        "creative delete ID":       "Delete a creative",
        "audience list":            "List custom audiences",
        "audience get ID":          "Get audience details",
        "audience create-custom":   "Create a custom audience",
        "audience create-lookalike":"Create a lookalike audience",
        "audience delete ID":       "Delete an audience",
        "insights account":         "Account-level insights",
        "insights campaign ID":     "Campaign-level insights",
        "insights adset ID":        "Ad set-level insights",
        "insights ad ID":           "Ad-level insights",
        "page list":                "List connected Facebook Pages",
        "help":                     "Show this help",
        "quit / exit":              "Exit REPL",
    }
    pt_session = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(pt_session, context=session.context_label)
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break
        if not line:
            continue
        cmd = line.split()[0].lower() if line.split() else ""
        if cmd in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if cmd == "help":
            skin.help(COMMANDS)
            continue
        try:
            from click.testing import CliRunner
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(cli, line.split(), catch_exceptions=False)
            if result.output:
                click.echo(result.output, nl=False)
            if result.exception and not isinstance(result.exception, SystemExit):
                raise result.exception
        except SystemExit:
            pass
        except MetaAdsAPIError as e:
            skin.error(str(e))
        except RuntimeError as e:
            skin.error(str(e))
        except Exception as e:
            skin.error(f"Unexpected error: {e}")


# ── CONFIG ────────────────────────────────────────────────────────────

@cli.group()
def config():
    """Manage credentials and configuration."""

@config.command("show")
@click.pass_obj
def config_show(ctx):
    """Show current configuration."""
    try:
        data = cfg_mod.show_config()
        if ctx.json_mode:
            click.echo(json.dumps(data, indent=2))
        else:
            skin.status_block(
                {k: str(v) if v is not None else "(not set)" for k, v in data.items()},
                title="Configuration",
            )
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@config.command("set-token")
@click.argument("token")
@click.pass_obj
def config_set_token(ctx, token):
    """Store a Meta access token."""
    try:
        cfg_mod.set_credentials(access_token=token)
        if ctx.json_mode:
            click.echo(json.dumps({"status": "ok", "message": "Token saved."}))
        else:
            skin.success("Access token saved.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@config.command("set-account")
@click.argument("account_id")
@click.pass_obj
def config_set_account(ctx, account_id):
    """Store a default ad account ID."""
    try:
        cfg_mod.set_credentials(ad_account_id=account_id)
        if ctx.json_mode:
            click.echo(json.dumps({"status": "ok", "message": "Account ID saved."}))
        else:
            skin.success(f"Ad account ID saved: {account_id}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@config.command("set-app")
@click.option("--app-id", required=True)
@click.option("--app-secret", required=True)
@click.pass_obj
def config_set_app(ctx, app_id, app_secret):
    """Store Meta App ID and Secret."""
    try:
        cfg_mod.set_credentials(app_id=app_id, app_secret=app_secret)
        if ctx.json_mode:
            click.echo(json.dumps({"status": "ok"}))
        else:
            skin.success("App credentials saved.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@config.command("clear")
@click.pass_obj
def config_clear(ctx):
    """Remove all stored credentials."""
    try:
        cfg_mod.clear_credentials()
        if ctx.json_mode:
            click.echo(json.dumps({"status": "ok"}))
        else:
            skin.success("All credentials cleared.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)


# ── ACCOUNT ───────────────────────────────────────────────────────────

@cli.group()
def account():
    """Ad account information."""

@account.command("info")
@pass_ctx
def account_info(ctx):
    """Show ad account details."""
    try:
        data = account_mod.get_account_info(ctx.token, ctx.account_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({
                "ID": data.get("id", "-"), "Name": data.get("name", "-"),
                "Status": str(data.get("account_status", "-")),
                "Currency": data.get("currency", "-"),
                "Timezone": data.get("timezone_name", "-"),
                "Spent": data.get("amount_spent", "-"),
                "Balance": data.get("balance", "-"),
                "Spend Cap": data.get("spend_cap", "-"),
            }, title="Ad Account Info")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@account.command("list")
@pass_ctx
def account_list(ctx):
    """List all accessible ad accounts."""
    try:
        accounts = account_mod.list_ad_accounts(ctx.token)
        if ctx.json_mode:
            _out(ctx, accounts)
        else:
            skin.info(f"{len(accounts)} ad account(s)")
            skin.table(["ID", "Name", "Status", "Currency", "Spent"],
                [[a.get("id"), a.get("name"), str(a.get("account_status")),
                  a.get("currency"), a.get("amount_spent", "-")] for a in accounts])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@account.command("spend")
@pass_ctx
def account_spend(ctx):
    """Show spending summary."""
    try:
        data = account_mod.get_spending_summary(ctx.token, ctx.account_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({
                "Account": data.get("name", "-"), "Currency": data.get("currency", "-"),
                "Spent": data.get("amount_spent", "-"), "Balance": data.get("balance", "-"),
                "Spend Cap": data.get("spend_cap", "unlimited"),
            }, title="Spend Summary")
    except Exception as e:
        _handle_error(e, ctx.json_mode)


# ── CAMPAIGN ──────────────────────────────────────────────────────────

@cli.group()
def campaign():
    """Campaign creation, management, and status control."""

@campaign.command("list")
@click.option("--status", default=None, help="ACTIVE, PAUSED, or DELETED.")
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def campaign_list(ctx, status, limit):
    """List campaigns."""
    try:
        items = campaign_mod.list_campaigns(ctx.token, ctx.account_id, status, limit)
        if ctx.json_mode:
            _out(ctx, items)
        else:
            skin.info(f"{len(items)} campaign(s)")
            skin.table(["ID", "Name", "Objective", "Status", "Daily Budget", "Lifetime Budget"],
                [[c.get("id"), c.get("name"), c.get("objective"),
                  c.get("effective_status"), c.get("daily_budget", "-"),
                  c.get("lifetime_budget", "-")] for c in items])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("get")
@click.argument("campaign_id")
@pass_ctx
def campaign_get(ctx, campaign_id):
    """Get campaign details."""
    try:
        data = campaign_mod.get_campaign(ctx.token, campaign_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({k: str(v) for k, v in data.items() if v is not None}, title="Campaign")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("create")
@click.option("--name", required=True)
@click.option("--objective", required=True,
              type=click.Choice(campaign_mod.VALID_OBJECTIVES, case_sensitive=False))
@click.option("--status", default="PAUSED", show_default=True,
              type=click.Choice(["ACTIVE", "PAUSED"], case_sensitive=False))
@click.option("--daily-budget", type=int, default=None, help="Daily budget in cents.")
@click.option("--lifetime-budget", type=int, default=None)
@click.option("--start-time", default=None, help="ISO 8601 start time.")
@click.option("--stop-time", default=None)
@pass_ctx
def campaign_create(ctx, name, objective, status, daily_budget, lifetime_budget, start_time, stop_time):
    """Create a new campaign."""
    try:
        data = campaign_mod.create_campaign(
            ctx.token, ctx.account_id, name=name, objective=objective,
            status=status, daily_budget=daily_budget, lifetime_budget=lifetime_budget,
            start_time=start_time, stop_time=stop_time)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Campaign created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("update")
@click.argument("campaign_id")
@click.option("--name", default=None)
@click.option("--status", default=None,
              type=click.Choice(campaign_mod.VALID_STATUSES, case_sensitive=False))
@click.option("--daily-budget", type=int, default=None)
@click.option("--lifetime-budget", type=int, default=None)
@pass_ctx
def campaign_update(ctx, campaign_id, name, status, daily_budget, lifetime_budget):
    """Update a campaign."""
    try:
        data = campaign_mod.update_campaign(ctx.token, campaign_id, name=name, status=status,
            daily_budget=daily_budget, lifetime_budget=lifetime_budget)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Campaign {campaign_id} updated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("pause")
@click.argument("campaign_id")
@pass_ctx
def campaign_pause(ctx, campaign_id):
    """Pause a campaign."""
    try:
        campaign_mod.set_campaign_status(ctx.token, campaign_id, "PAUSED")
        if ctx.json_mode:
            _out(ctx, {"id": campaign_id, "status": "PAUSED"})
        else:
            skin.success(f"Campaign {campaign_id} paused.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("activate")
@click.argument("campaign_id")
@pass_ctx
def campaign_activate(ctx, campaign_id):
    """Activate a campaign."""
    try:
        campaign_mod.set_campaign_status(ctx.token, campaign_id, "ACTIVE")
        if ctx.json_mode:
            _out(ctx, {"id": campaign_id, "status": "ACTIVE"})
        else:
            skin.success(f"Campaign {campaign_id} activated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@campaign.command("delete")
@click.argument("campaign_id")
@click.confirmation_option(prompt="Delete this campaign?")
@pass_ctx
def campaign_delete(ctx, campaign_id):
    """Delete a campaign."""
    try:
        campaign_mod.delete_campaign(ctx.token, campaign_id)
        if ctx.json_mode:
            _out(ctx, {"id": campaign_id, "deleted": True})
        else:
            skin.success(f"Campaign {campaign_id} deleted.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)


# ── ADSET ─────────────────────────────────────────────────────────────

@cli.group()
def adset():
    """Ad set targeting, budgets, and scheduling."""

@adset.command("list")
@click.option("--campaign", "campaign_id", default=None)
@click.option("--status", default=None)
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def adset_list(ctx, campaign_id, status, limit):
    """List ad sets."""
    try:
        items = adset_mod.list_adsets(ctx.token, ctx.account_id, campaign_id, status, limit)
        if ctx.json_mode:
            _out(ctx, items)
        else:
            skin.info(f"{len(items)} ad set(s)")
            skin.table(["ID", "Name", "Campaign ID", "Status", "Daily Budget", "Opt. Goal"],
                [[a.get("id"), a.get("name"), a.get("campaign_id"),
                  a.get("effective_status"), a.get("daily_budget", "-"),
                  a.get("optimization_goal", "-")] for a in items])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("get")
@click.argument("adset_id")
@pass_ctx
def adset_get(ctx, adset_id):
    """Get ad set details."""
    try:
        data = adset_mod.get_adset(ctx.token, adset_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({k: str(v) for k, v in data.items() if v is not None}, title="Ad Set")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("create")
@click.option("--name", required=True)
@click.option("--campaign", "campaign_id", required=True)
@click.option("--daily-budget", type=int, default=None)
@click.option("--lifetime-budget", type=int, default=None)
@click.option("--bid-amount", type=int, default=None)
@click.option("--billing-event", default="IMPRESSIONS", show_default=True,
              type=click.Choice(adset_mod.BILLING_EVENTS, case_sensitive=False))
@click.option("--optimization-goal", default="REACH", show_default=True,
              type=click.Choice(adset_mod.OPTIMIZATION_GOALS, case_sensitive=False))
@click.option("--targeting", default=None, help='JSON targeting spec.')
@click.option("--status", default="PAUSED", show_default=True,
              type=click.Choice(["ACTIVE", "PAUSED"], case_sensitive=False))
@click.option("--start-time", default=None)
@click.option("--end-time", default=None)
@pass_ctx
def adset_create(ctx, name, campaign_id, daily_budget, lifetime_budget, bid_amount,
                 billing_event, optimization_goal, targeting, status, start_time, end_time):
    """Create an ad set."""
    try:
        targeting_spec = json.loads(targeting) if targeting else None
        data = adset_mod.create_adset(
            ctx.token, ctx.account_id, name=name, campaign_id=campaign_id,
            daily_budget=daily_budget, lifetime_budget=lifetime_budget,
            bid_amount=bid_amount, billing_event=billing_event,
            optimization_goal=optimization_goal, targeting=targeting_spec,
            status=status, start_time=start_time, end_time=end_time)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Ad set created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("update")
@click.argument("adset_id")
@click.option("--name", default=None)
@click.option("--status", default=None)
@click.option("--daily-budget", type=int, default=None)
@click.option("--lifetime-budget", type=int, default=None)
@click.option("--targeting", default=None)
@pass_ctx
def adset_update(ctx, adset_id, name, status, daily_budget, lifetime_budget, targeting):
    """Update an ad set."""
    try:
        targeting_spec = json.loads(targeting) if targeting else None
        data = adset_mod.update_adset(ctx.token, adset_id, name=name, status=status,
            daily_budget=daily_budget, lifetime_budget=lifetime_budget, targeting=targeting_spec)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Ad set {adset_id} updated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("pause")
@click.argument("adset_id")
@pass_ctx
def adset_pause(ctx, adset_id):
    """Pause an ad set."""
    try:
        adset_mod.set_adset_status(ctx.token, adset_id, "PAUSED")
        if ctx.json_mode:
            _out(ctx, {"id": adset_id, "status": "PAUSED"})
        else:
            skin.success(f"Ad set {adset_id} paused.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("activate")
@click.argument("adset_id")
@pass_ctx
def adset_activate(ctx, adset_id):
    """Activate an ad set."""
    try:
        adset_mod.set_adset_status(ctx.token, adset_id, "ACTIVE")
        if ctx.json_mode:
            _out(ctx, {"id": adset_id, "status": "ACTIVE"})
        else:
            skin.success(f"Ad set {adset_id} activated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@adset.command("delete")
@click.argument("adset_id")
@click.confirmation_option(prompt="Delete this ad set?")
@pass_ctx
def adset_delete(ctx, adset_id):
    """Delete an ad set."""
    try:
        adset_mod.delete_adset(ctx.token, adset_id)
        if ctx.json_mode:
            _out(ctx, {"id": adset_id, "deleted": True})
        else:
            skin.success(f"Ad set {adset_id} deleted.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)


# ── AD ────────────────────────────────────────────────────────────────

@cli.group()
def ad():
    """Ad creation, creative assignment, and status control."""

@ad.command("list")
@click.option("--adset", "adset_id", default=None)
@click.option("--campaign", "campaign_id", default=None)
@click.option("--status", default=None)
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def ad_list(ctx, adset_id, campaign_id, status, limit):
    """List ads."""
    try:
        items = ad_mod.list_ads(ctx.token, ctx.account_id, adset_id, campaign_id, status, limit)
        if ctx.json_mode:
            _out(ctx, items)
        else:
            skin.info(f"{len(items)} ad(s)")
            skin.table(["ID", "Name", "Ad Set ID", "Status", "Creative ID"],
                [[a.get("id"), a.get("name"), a.get("adset_id"),
                  a.get("effective_status"),
                  a.get("creative", {}).get("id", "-") if isinstance(a.get("creative"), dict) else "-"]
                 for a in items])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("get")
@click.argument("ad_id")
@pass_ctx
def ad_get(ctx, ad_id):
    """Get ad details."""
    try:
        data = ad_mod.get_ad(ctx.token, ad_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({k: str(v) for k, v in data.items() if v is not None}, title="Ad")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("create")
@click.option("--name", required=True)
@click.option("--adset", "adset_id", required=True)
@click.option("--creative", "creative_id", required=True)
@click.option("--status", default="PAUSED", show_default=True,
              type=click.Choice(["ACTIVE", "PAUSED"], case_sensitive=False))
@pass_ctx
def ad_create(ctx, name, adset_id, creative_id, status):
    """Create an ad."""
    try:
        data = ad_mod.create_ad(ctx.token, ctx.account_id, name=name,
                                adset_id=adset_id, creative_id=creative_id, status=status)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Ad created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("update")
@click.argument("ad_id")
@click.option("--name", default=None)
@click.option("--status", default=None)
@click.option("--creative", "creative_id", default=None)
@pass_ctx
def ad_update(ctx, ad_id, name, status, creative_id):
    """Update an ad."""
    try:
        data = ad_mod.update_ad(ctx.token, ad_id, name=name, status=status, creative_id=creative_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Ad {ad_id} updated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("pause")
@click.argument("ad_id")
@pass_ctx
def ad_pause(ctx, ad_id):
    try:
        ad_mod.set_ad_status(ctx.token, ad_id, "PAUSED")
        if ctx.json_mode:
            _out(ctx, {"id": ad_id, "status": "PAUSED"})
        else:
            skin.success(f"Ad {ad_id} paused.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("activate")
@click.argument("ad_id")
@pass_ctx
def ad_activate(ctx, ad_id):
    try:
        ad_mod.set_ad_status(ctx.token, ad_id, "ACTIVE")
        if ctx.json_mode:
            _out(ctx, {"id": ad_id, "status": "ACTIVE"})
        else:
            skin.success(f"Ad {ad_id} activated.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@ad.command("delete")
@click.argument("ad_id")
@click.confirmation_option(prompt="Delete this ad?")
@pass_ctx
def ad_delete(ctx, ad_id):
    try:
        ad_mod.delete_ad(ctx.token, ad_id)
        if ctx.json_mode:
            _out(ctx, {"id": ad_id, "deleted": True})
        else:
            skin.success(f"Ad {ad_id} deleted.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)


# ── CREATIVE ──────────────────────────────────────────────────────────

@cli.group()
def creative():
    """Ad creative management."""

@creative.command("list")
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def creative_list(ctx, limit):
    try:
        items = creative_mod.list_creatives(ctx.token, ctx.account_id, limit)
        if ctx.json_mode:
            _out(ctx, items)
        else:
            skin.info(f"{len(items)} creative(s)")
            skin.table(["ID", "Name", "Type", "Status", "Created"],
                [[c.get("id"), c.get("name"), c.get("object_type", "-"),
                  c.get("status", "-"), c.get("created_time", "-")] for c in items])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@creative.command("get")
@click.argument("creative_id")
@pass_ctx
def creative_get(ctx, creative_id):
    try:
        data = creative_mod.get_creative(ctx.token, creative_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({k: str(v) for k, v in data.items() if v is not None}, title="Creative")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@creative.command("create")
@click.option("--name", required=True)
@click.option("--page-id", required=True)
@click.option("--message", default=None)
@click.option("--link", default=None)
@click.option("--image-hash", default=None)
@click.option("--video-id", default=None)
@click.option("--headline", default=None)
@click.option("--link-description", default=None)
@click.option("--call-to-action", default=None,
              type=click.Choice(creative_mod.CALL_TO_ACTION_TYPES, case_sensitive=False))
@pass_ctx
def creative_create(ctx, name, page_id, message, link, image_hash,
                    video_id, headline, link_description, call_to_action):
    """Create a new ad creative."""
    try:
        data = creative_mod.create_creative(
            ctx.token, ctx.account_id, name=name, page_id=page_id,
            message=message, link=link, image_hash=image_hash,
            video_id=video_id, call_to_action_type=call_to_action,
            link_description=link_description, headline=headline)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Creative created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@creative.command("delete")
@click.argument("creative_id")
@click.confirmation_option(prompt="Delete this creative?")
@pass_ctx
def creative_delete(ctx, creative_id):
    try:
        creative_mod.delete_creative(ctx.token, creative_id)
        if ctx.json_mode:
            _out(ctx, {"id": creative_id, "deleted": True})
        else:
            skin.success(f"Creative {creative_id} deleted.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@creative.command("images")
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def creative_images(ctx, limit):
    """List uploaded ad images."""
    try:
        images = creative_mod.list_images(ctx.token, ctx.account_id, limit)
        if ctx.json_mode:
            _out(ctx, images)
        else:
            skin.info(f"{len(images)} image(s)")
            skin.table(["Hash", "Name", "Width", "Height", "Created"],
                [[i.get("hash", "-"), i.get("name", "-"),
                  str(i.get("width", "-")), str(i.get("height", "-")),
                  i.get("created_time", "-")] for i in images])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@creative.command("upload-image")
@click.argument("image_path")
@pass_ctx
def creative_upload_image(ctx, image_path):
    """Upload an image file; returns its hash for use in creatives."""
    try:
        data = creative_mod.upload_image(ctx.token, ctx.account_id, image_path)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Image uploaded — hash: {data.get('hash', '-')}")
            skin.status("URL", data.get("url", "-"))
    except Exception as e:
        _handle_error(e, ctx.json_mode)


@cli.group()
def audience():
    """Custom and lookalike audience management."""

@audience.command("list")
@click.option("--limit", default=50, show_default=True)
@pass_ctx
def audience_list(ctx, limit):
    try:
        items = audience_mod.list_audiences(ctx.token, ctx.account_id, limit)
        if ctx.json_mode:
            _out(ctx, items)
        else:
            skin.info(f"{len(items)} audience(s)")
            skin.table(["ID", "Name", "Subtype", "Approx. Count", "Created"],
                [[a.get("id"), a.get("name"), a.get("subtype"),
                  str(a.get("approximate_count", "-")), a.get("created_time", "-")] for a in items])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@audience.command("get")
@click.argument("audience_id")
@pass_ctx
def audience_get(ctx, audience_id):
    try:
        data = audience_mod.get_audience(ctx.token, audience_id)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.status_block({k: str(v) for k, v in data.items() if v is not None}, title="Audience")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@audience.command("create-custom")
@click.option("--name", required=True)
@click.option("--subtype", default="CUSTOM", show_default=True,
              type=click.Choice(audience_mod.CUSTOM_AUDIENCE_SUBTYPES, case_sensitive=False))
@click.option("--description", default=None)
@pass_ctx
def audience_create_custom(ctx, name, subtype, description):
    """Create a custom audience."""
    try:
        data = audience_mod.create_custom_audience(
            ctx.token, ctx.account_id, name=name, subtype=subtype, description=description)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Custom audience created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@audience.command("create-lookalike")
@click.option("--name", required=True)
@click.option("--source-id", required=True)
@click.option("--country", default="US", show_default=True)
@click.option("--ratio", default=0.01, show_default=True, type=float)
@click.option("--description", default=None)
@pass_ctx
def audience_create_lookalike(ctx, name, source_id, country, ratio, description):
    """Create a lookalike audience."""
    try:
        data = audience_mod.create_lookalike_audience(
            ctx.token, ctx.account_id, name=name, origin_audience_id=source_id,
            country=country, ratio=ratio, description=description)
        if ctx.json_mode:
            _out(ctx, data)
        else:
            skin.success(f"Lookalike audience created: {data.get('id')}")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@audience.command("delete")
@click.argument("audience_id")
@click.confirmation_option(prompt="Delete this audience?")
@pass_ctx
def audience_delete(ctx, audience_id):
    try:
        audience_mod.delete_audience(ctx.token, audience_id)
        if ctx.json_mode:
            _out(ctx, {"id": audience_id, "deleted": True})
        else:
            skin.success(f"Audience {audience_id} deleted.")
    except Exception as e:
        _handle_error(e, ctx.json_mode)

# ── INSIGHTS ──────────────────────────────────────────────────────────

@cli.group()
def insights():
    """Performance metrics and reporting."""

def _print_insights(ctx, data):
    if ctx.json_mode:
        _out(ctx, data)
        return
    if not data:
        skin.warning("No insights data for this period.")
        return
    skin.info(f"{len(data)} row(s)")
    all_keys = []
    for row in data:
        for k in row.keys():
            if k not in all_keys:
                all_keys.append(k)
    skin.table(all_keys, [[str(row.get(k, "-")) for k in all_keys] for row in data])

@insights.command("account")
@click.option("--preset", default="last_30d", show_default=True,
              type=click.Choice(insights_mod.DATE_PRESETS, case_sensitive=False))
@click.option("--since", default=None, help="Start date YYYY-MM-DD.")
@click.option("--until", default=None, help="End date YYYY-MM-DD.")
@click.option("--fields", default=None, help="Comma-separated metric fields.")
@click.option("--breakdown", "breakdowns", multiple=True,
              type=click.Choice(insights_mod.BREAKDOWN_OPTIONS, case_sensitive=False))
@pass_ctx
def insights_account(ctx, preset, since, until, fields, breakdowns):
    """Account-level performance insights."""
    try:
        data = insights_mod.get_account_insights(
            ctx.token, ctx.account_id, date_preset=preset,
            since=since, until=until, fields=fields,
            breakdowns=list(breakdowns) or None)
        _print_insights(ctx, data)
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@insights.command("campaign")
@click.argument("campaign_id")
@click.option("--preset", default="last_30d", show_default=True,
              type=click.Choice(insights_mod.DATE_PRESETS, case_sensitive=False))
@click.option("--since", default=None)
@click.option("--until", default=None)
@click.option("--fields", default=None)
@click.option("--breakdown", "breakdowns", multiple=True,
              type=click.Choice(insights_mod.BREAKDOWN_OPTIONS, case_sensitive=False))
@pass_ctx
def insights_campaign(ctx, campaign_id, preset, since, until, fields, breakdowns):
    """Campaign-level insights."""
    try:
        data = insights_mod.get_campaign_insights(
            ctx.token, campaign_id, date_preset=preset,
            since=since, until=until, fields=fields,
            breakdowns=list(breakdowns) or None)
        _print_insights(ctx, data)
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@insights.command("adset")
@click.argument("adset_id")
@click.option("--preset", default="last_30d", show_default=True,
              type=click.Choice(insights_mod.DATE_PRESETS, case_sensitive=False))
@click.option("--since", default=None)
@click.option("--until", default=None)
@click.option("--fields", default=None)
@click.option("--breakdown", "breakdowns", multiple=True,
              type=click.Choice(insights_mod.BREAKDOWN_OPTIONS, case_sensitive=False))
@pass_ctx
def insights_adset(ctx, adset_id, preset, since, until, fields, breakdowns):
    """Ad set-level insights."""
    try:
        data = insights_mod.get_adset_insights(
            ctx.token, adset_id, date_preset=preset,
            since=since, until=until, fields=fields,
            breakdowns=list(breakdowns) or None)
        _print_insights(ctx, data)
    except Exception as e:
        _handle_error(e, ctx.json_mode)

@insights.command("ad")
@click.argument("ad_id")
@click.option("--preset", default="last_30d", show_default=True,
              type=click.Choice(insights_mod.DATE_PRESETS, case_sensitive=False))
@click.option("--since", default=None)
@click.option("--until", default=None)
@click.option("--fields", default=None)
@click.option("--breakdown", "breakdowns", multiple=True,
              type=click.Choice(insights_mod.BREAKDOWN_OPTIONS, case_sensitive=False))
@pass_ctx
def insights_ad(ctx, ad_id, preset, since, until, fields, breakdowns):
    """Ad-level insights."""
    try:
        data = insights_mod.get_ad_insights(
            ctx.token, ad_id, date_preset=preset,
            since=since, until=until, fields=fields,
            breakdowns=list(breakdowns) or None)
        _print_insights(ctx, data)
    except Exception as e:
        _handle_error(e, ctx.json_mode)

# ── PAGE ──────────────────────────────────────────────────────────────

@cli.group()
def page():
    """Facebook Pages connected to this user."""

@page.command("list")
@pass_ctx
def page_list(ctx):
    """List Facebook Pages accessible by the current token."""
    try:
        pages = account_mod.list_pages(ctx.token)
        if ctx.json_mode:
            _out(ctx, pages)
        else:
            skin.info(f"{len(pages)} page(s)")
            skin.table(["ID", "Name", "Category", "Fans", "Link"],
                [[p.get("id"), p.get("name"), p.get("category", "-"),
                  str(p.get("fan_count", "-")), p.get("link", "-")] for p in pages])
    except Exception as e:
        _handle_error(e, ctx.json_mode)

# ── Entry point ───────────────────────────────────────────────────────

def main():
    cli()

if __name__ == "__main__":
    main()
