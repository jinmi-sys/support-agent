"""CLI entry point for Support Agent."""

import asyncio
import sys

import click
from rich.console import Console
from rich.table import Table

from support_agent.core.engine import SupportEngine
from support_agent.utils.config import load_config
from support_agent.utils.logger import setup_logger
from support_agent.utils.metrics import MetricsCollector

console = Console()


@click.group()
@click.option("--config", "-c", default="config/config.yaml", help="Path to config file")
@click.option("--log-level", "-l", default="INFO", help="Log level")
@click.pass_context
def cli(ctx: click.Context, config: str, log_level: str) -> None:
    """Support Agent - AI-powered autonomous customer support."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["log_level"] = log_level
    setup_logger(log_level)


@cli.command()
@click.option("--ticket-id", "-t", required=True, help="Ticket ID to process")
@click.option("--channel", "-ch", default="email", help="Channel (email/chat/discord)")
@click.pass_context
def process(ctx: click.Context, ticket_id: str, channel: str) -> None:
    """Process a single support ticket."""
    config = load_config(ctx.obj["config_path"])
    engine = SupportEngine(config)

    console.print(f"[bold green]Processing ticket {ticket_id} via {channel}...[/]")
    result = asyncio.run(engine.process_ticket(
        ticket_id=ticket_id,
        channel=channel,
    ))

    table = Table(title=f"Ticket {ticket_id} Result")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Priority", result.get("priority", "N/A"))
    table.add_row("Sentiment", result.get("sentiment", "N/A"))
    table.add_row("Resolution", result.get("resolution", "N/A"))
    table.add_row("Confidence", str(result.get("confidence", "N/A")))
    console.print(table)


@cli.command()
@click.option("--channels", "-ch", default="email,chat,discord", help="Comma-separated channels")
@click.pass_context
def listen(ctx: click.Context, channels: str) -> None:
    """Start multi-channel listener."""
    config = load_config(ctx.obj["config_path"])
    engine = SupportEngine(config)
    channel_list = [c.strip() for c in channels.split(",")]

    console.print(f"[bold green]Starting listener on channels: {', '.join(channel_list)}[/]")
    asyncio.run(engine.start_listener(channel_list))


@cli.command()
@click.option("--status", "-s", default="pending", help="Ticket status filter")
@click.pass_context
def triage(ctx: click.Context, status: str) -> None:
    """Run triage on pending tickets."""
    config = load_config(ctx.obj["config_path"])
    engine = SupportEngine(config)

    console.print(f"[bold green]Running triage on {status} tickets...[/]")
    result = asyncio.run(engine.batch_triage(status))

    console.print(f"[bold green]Triaged {result.get('count', 0)} tickets[/]")


@cli.command()
@click.option("--period", "-p", default="24h", help="Time period (1h/24h/7d/30d)")
@click.pass_context
def metrics(ctx: click.Context, period: str) -> None:
    """View support metrics."""
    collector = MetricsCollector()
    data = collector.get_summary(period)

    table = Table(title=f"Support Metrics ({period})")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Tickets Processed", str(data.get("total_tickets", 0)))
    table.add_row("Resolution Rate", f"{data.get('resolution_rate', 0):.1%}")
    table.add_row("Avg Response Time", f"{data.get('avg_response_time', 0):.1f}s")
    table.add_row("CSAT Score", f"{data.get('csat_score', 0):.1f}/5.0")
    console.print(table)


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
