"""
VG CLI — Rich-based beautiful terminal interface.

Usage:
  python -m veritas.cli "Your political question here"
  python -m veritas.cli --build-rag
"""

import argparse
import asyncio
import sys
import os
import json

if __package__ in (None, ""):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if PROJECT_ROOT in sys.path:
        sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich import box

console = Console()


def print_banner():
    """Print the VG banner."""
    banner = """
    ██╗   ██╗ ██████╗ 
    ██║   ██║██╔════╝ 
    ██║   ██║██║  ███╗
    ╚██╗ ██╔╝██║   ██║
     ╚████╔╝ ╚██████╔╝
      ╚═══╝   ╚═════╝ 
    """
    console.print(banner, style="bold cyan")
    console.print("  [dim]VG — Political Intelligence Engine[/dim]")
    console.print("  [dim]10 Agents • RAG Wisdom • Simulation Layer[/dim]\n")


def byok_setup():
    """Check for API keys and prompt if missing."""
    from vg.setup import byok_setup_rich
    byok_setup_rich(console)


def build_rag():
    """Build the RAG knowledge base."""
    console.print(Panel("Building RAG Knowledge Base", style="bold green"))
    from vg.rag.builder import build_all
    build_all()
    console.print("[bold green]✓ RAG build complete![/bold green]")


def print_rich_report(result: dict):
    """Print a beautiful Rich-formatted report."""
    verdict = result.get("verdict", {})
    agents = result.get("agent_results", [])
    question = result.get("question", "Unknown")

    # Header
    console.print()
    console.print(Panel(
        f"[bold white]{question}[/bold white]",
        title="[bold cyan]VG INTELLIGENCE REPORT[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE_EDGE,
    ))

    # Verdict
    confidence = verdict.get("confidence", 0)
    conf_color = "green" if confidence >= 70 else "yellow" if confidence >= 40 else "red"

    console.print(Panel(
        f"[bold white]{verdict.get('majority_verdict', 'No verdict produced')}[/bold white]\n\n"
        f"[{conf_color}]Confidence: {confidence}%[/{conf_color}]",
        title="[bold green]⚖ MAJORITY VERDICT[/bold green]",
        border_style="green",
    ))

    # Key Pattern
    pattern = verdict.get("key_pattern", "")
    if pattern:
        console.print(Panel(pattern, title="[bold yellow]🔍 Key Pattern[/bold yellow]", border_style="yellow"))

    # Historical Precedent
    precedent = verdict.get("historical_precedent", "")
    if precedent:
        console.print(Panel(precedent, title="[bold blue]📜 Historical Precedent[/bold blue]", border_style="blue"))

    # Agent Table
    table = Table(title="Agent Breakdown", box=box.ROUNDED, border_style="cyan")
    table.add_column("Agent", style="bold white", width=22)
    table.add_column("Stance", width=68, overflow="fold")
    table.add_column("Conf", justify="right", width=6)
    table.add_column("", width=3)

    for agent in agents:
        if agent.get("error"):
            marker = "[red]✗[/red]"
            style = "dim"
        else:
            marker = "[green]✓[/green]"
            style = ""

        conf = agent.get("confidence", 0)
        conf_style = "green" if conf >= 70 else "yellow" if conf >= 40 else "red"

        table.add_row(
            agent.get("agent_name", "?"),
            str(agent.get("stance", "N/A")),
            f"[{conf_style}]{conf}%[/{conf_style}]",
            marker,
        )

    console.print(table)

    # Dissent
    dissent = verdict.get("strongest_dissent", "")
    if dissent:
        console.print(Panel(
            f"[italic]{dissent}[/italic]",
            title="[bold red]⚡ Minority Dissent[/bold red]",
            border_style="red",
        ))

    # Reasoning
    reasoning = verdict.get("reasoning", "")
    if reasoning:
        console.print(Panel(reasoning, title="[bold magenta]💡 Reasoning[/bold magenta]", border_style="magenta"))

    # Disclaimer
    console.print(
        "\n  [dim]DISCLAIMER: Speculative pattern analysis. "
        "Not verified intelligence. For research only.[/dim]\n"
    )


async def run_analysis(question: str) -> dict:
    """Run the full pipeline with Rich progress display."""
    from vg.core.debate import DebateCoordinator

    coordinator = DebateCoordinator()
    return await coordinator.run_full_pipeline(question)


def main():
    parser = argparse.ArgumentParser(description="VG — Political Intelligence Engine")
    parser.add_argument("question", nargs="?", help="Political question to analyze")
    parser.add_argument("--build-rag", action="store_true", help="Build/rebuild RAG knowledge base")
    parser.add_argument("--json", "-j", help="Save report to JSON file")

    args = parser.parse_args()

    print_banner()

    if args.build_rag:
        byok_setup()
        build_rag()
        return

    byok_setup()

    if args.question:
        question = args.question
    else:
        question = console.input("[bold cyan]🧠 Your question:[/bold cyan] ").strip()

    if not question:
        console.print("[red]No question provided. Exiting.[/red]")
        sys.exit(1)

    console.print(f"\n[dim]Analyzing: {question}[/dim]\n")

    from vg.setup import run_async
    result = run_async(run_analysis(question))
    print_rich_report(result)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(result, f, indent=2, default=str)
        console.print(f"[green]📄 Report saved to {args.json}[/green]")


if __name__ == "__main__":
    main()
