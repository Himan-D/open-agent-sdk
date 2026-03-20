"""CLI for OpenAgent - Full-featured CLI like OpenClaw.

Usage:
    open-agent                    # Start interactive shell
    open-agent --help            # Show help
    open-agent init              # Initialize configuration
    open-agent health            # Run health checks
    open-agent status            # Show system status
    open-agent agents list       # List agents
    open-agent skills list       # List skills
    open-agent memory search     # Search memory
    open-agent gateway start     # Start gateway
    open-agent tui               # Start TUI
"""

import asyncio
import os
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from open_agent import (
    __version__,
    create_deep_agent,
    create_gateway,
    create_health_checker,
    create_memory_store,
    create_skill_registry,
    create_channel_manager,
    create_secrets_manager,
    SoulConfig,
    AgentContext,
)
from open_agent.config.settings import get_config

app = typer.Typer(help="OpenAgent - Multi-model AI agent orchestration")
console = Console()


@app.command()
def main(
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i", help="Interactive mode"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    agent_name: str = typer.Option("open-agent", "--name", "-n", help="Agent name"),
    use_openshell: bool = typer.Option(False, "--openshell/--no-openshell", help="Use OpenShell sandbox"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """OpenAgent CLI - Multi-model AI agent orchestration."""
    cfg = get_config()

    if model:
        cfg.agent_config.model = model

    api_key = os.environ.get("NVIDIA_API_KEY", cfg.nvidia.api_key)
    if not api_key:
        console.print("[yellow]Warning: NVIDIA_API_KEY not set[/yellow]")
        console.print("Set it with: export NVIDIA_API_KEY=your_key")

    agent = create_deep_agent(
        name=agent_name,
        model=cfg.agent_config.model,
        use_openshell=use_openshell,
        system_prompt=f"You are {agent_name}, a helpful AI assistant powered by NVIDIA Nemotron.",
    )

    if interactive:
        asyncio.run(interactive_shell(agent))
    else:
        console.print(Panel(f"[green]OpenAgent v{__version__}[/green]\nAgent: {agent_name}\nModel: {cfg.agent_config.model}"))


async def interactive_shell(agent):
    """Run an interactive shell session."""
    await agent.initialize()

    console.print(Panel("[green]OpenAgent Interactive Shell[/green]\nType 'exit' or 'quit' to end session"))
    console.print(f"[dim]Agent: {agent.name}[/dim]\n")

    session_id = "cli_session"
    context = AgentContext(session_id=session_id)

    while True:
        try:
            user_input = console.input("[blue]> [/blue]")

            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if user_input.lower() == "help":
                show_help()
                continue

            if user_input.lower() == "reset":
                await agent.reset(session_id)
                console.print("[yellow]Conversation reset[/yellow]")
                continue

            if user_input.lower() == "memory":
                show_memory()
                continue

            if user_input.lower() == "skills":
                show_skills()
                continue

            if user_input.lower() == "status":
                await show_status()
                continue

            response = await agent.process_message(user_input, context)
            console.print(f"[green]Agent[/green]: {response}\n")

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def show_help():
    """Show help information."""
    console.print("""
[bold]Commands:[/bold]
  exit, quit, q - Exit the shell
  help           - Show this help
  reset          - Reset conversation
  memory         - Show memory status
  skills         - List available skills
  status         - Run health checks
""")


def show_memory():
    """Show memory status."""
    store = create_memory_store()
    stats = store.get_stats()

    table = Table(title="Memory Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Entries", str(stats["total"]))
    table.add_row("File Path", stats["file_path"])

    for entry_type, count in stats["by_type"].items():
        table.add_row(entry_type.capitalize(), str(count))

    console.print(table)


def show_skills():
    """Show available skills."""
    registry = create_skill_registry()
    stats = registry.get_stats()

    table = Table(title=f"Skills ({stats['total']} loaded)")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")

    for skill in registry.list():
        table.add_row(skill.name, skill.category, skill.description[:50])

    console.print(table)


async def show_status():
    """Show system status."""
    checker = create_health_checker()
    checks = await checker.check_all()
    report = checker.format_report(checks)
    console.print(report)


# Subcommands
@app.command()
def init(
    path: str = typer.Option(".env", "--path", "-p", help="Path for .env file"),
):
    """Initialize OpenAgent configuration."""
    env_content = """# OpenAgent Configuration
# NVIDIA API Key (get from https://build.nvidia.com/)
NVIDIA_API_KEY=your_nvidia_api_key_here

# Agent Configuration
AGENT_MODEL=nvidia/nemotron-3-super-120b-a12b
AGENT_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=50

# OpenShell Configuration
OPENSHELL_ENABLED=true
OPENSHELL_SANDBOX_TYPE=auto

# Memory Configuration
MEMORY_ENABLED=true
MEMORY_BACKEND=store
"""
    with open(path, "w") as f:
        f.write(env_content)
    console.print(f"[green]Created configuration at {path}[/green]")
    console.print("[dim]Edit the file and add your NVIDIA_API_KEY[/dim]")


@app.command()
def health():
    """Run health checks."""
    checker = create_health_checker()
    checks = asyncio.run(checker.check_all())
    report = checker.format_report(checks)
    console.print(report)


@app.command()
def status():
    """Show system status."""
    asyncio.run(show_status())


@app.command()
def models():
    """List available Nemotron models."""
    from open_agent.models.nemotron import get_available_nemotron_models
    console.print("[bold]Available NVIDIA Nemotron Models:[/bold]\n")
    for model in get_available_nemotron_models():
        console.print(f"  • {model}")


@app.command()
def version():
    """Show version information."""
    console.print(f"OpenAgent v{__version__}")


@app.command()
def secrets():
    """Show secrets status."""
    manager = create_secrets_manager()
    secrets_list = manager.list()

    validation = manager.validate()

    if validation["valid"]:
        console.print("[green]✓ All required secrets are set[/green]")
    else:
        console.print("[yellow]⚠ Some secrets are missing:[/yellow]")
        for missing in validation["missing"]:
            console.print(f"  - {missing['name']}: {missing['description']}")

    console.print("\n[bold]Configured Secrets:[/bold]")
    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Source", style="yellow")
    table.add_column("Status", style="green")

    for secret in secrets_list:
        table.add_row(
            secret["name"],
            secret["source"],
            "✓ Set" if secret["is_set"] else "✗ Not set",
        )

    console.print(table)


# Gateway commands
gateway_app = typer.Typer(help="Gateway management commands")
app.add_typer(gateway_app, name="gateway")


@gateway_app.command("start")
def gateway_start(
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on"),
    enable_http: bool = typer.Option(True, "--http/--no-http", help="Enable HTTP API"),
    enable_ws: bool = typer.Option(True, "--ws/--no-ws", help="Enable WebSocket"),
):
    """Start the OpenAgent gateway server."""
    gateway = create_gateway(
        port=port,
        enable_http=enable_http,
        enable_websocket=enable_ws,
    )

    agent = create_deep_agent(name="default")
    gateway.register_agent(agent)

    console.print(f"[green]Starting Gateway on port {port}...[/green]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")

    try:
        asyncio.run(gateway.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Gateway stopped[/yellow]")


# Memory commands
memory_app = typer.Typer(help="Memory management commands")
app.add_typer(memory_app, name="memory")


@memory_app.command("list")
def memory_list():
    """List memory entries."""
    store = create_memory_store()
    stats = store.get_stats()

    console.print(f"[bold]Memory:[/bold] {stats['total']} entries\n")

    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Content", style="white")

    for entry_type, count in stats["by_type"].items():
        table.add_row(entry_type.capitalize(), f"{count} entries")

    console.print(table)


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(..., help="Search query"),
):
    """Search memory."""
    store = create_memory_store()
    results = store.search(query)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"[bold]Results:[/bold] {len(results)} found\n")

    for entry in results:
        console.print(f"[cyan]{entry.type}[/cyan]: {entry.content[:100]}")


# Skills commands
skills_app = typer.Typer(help="Skills management commands")
app.add_typer(skills_app, name="skills")


@skills_app.command("list")
def skills_list():
    """List available skills."""
    registry = create_skill_registry()
    skills = registry.list()

    table = Table(title=f"Skills ({len(skills)} loaded)")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")

    for skill in skills:
        table.add_row(skill.name, skill.category, skill.description[:60])

    console.print(table)


# Channels commands
channels_app = typer.Typer(help="Channel management commands")
app.add_typer(channels_app, name="channels")


@channels_app.command("list")
def channels_list():
    """List configured channels."""
    manager = create_channel_manager()
    channels = manager.list_channels()

    if not channels:
        console.print("[yellow]No channels configured[/yellow]")
        console.print("[dim]Configure channels in your config file[/dim]")
        return

    table = Table(title="Channels")
    table.add_column("Type", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Connected", style="yellow")

    for channel in channels:
        table.add_row(
            channel["type"],
            "✓" if channel["enabled"] else "✗",
            "✓" if channel["connected"] else "✗",
        )

    console.print(table)


# Agent commands
agent_app = typer.Typer(help="Agent management commands")
app.add_typer(agent_app, name="agents")


@agent_app.command("list")
def agents_list():
    """List available agents."""
    console.print("[bold]Available Agent Types:[/bold]\n")
    console.print("  • coding-agent  - Specialized for code generation")
    console.print("  • research-agent - Specialized for research tasks")
    console.print("  • general       - General purpose assistant")


@agent_app.command("create")
def agent_create(
    name: str = typer.Option(..., "--name", "-n", help="Agent name"),
    model: str = typer.Option("nvidia/nemotron-3-super-120b-a12b", "--model", "-m", help="Model"),
    team: Optional[str] = typer.Option(None, "--team", help="Team assignment"),
):
    """Create a new agent configuration."""
    soul = SoulConfig(
        name=name,
        team=team,
        responsibilities=["Handle user requests"],
    )

    console.print(f"[green]Created agent: {name}[/green]")
    console.print(f"Model: {model}")
    if team:
        console.print(f"Team: {team}")


# TUI command
@app.command()
def tui():
    """Start the Terminal UI."""
    console.print("[yellow]TUI coming soon...[/yellow]")
    console.print("[dim]Use open-agent without --no-interactive for now[/dim]")


if __name__ == "__main__":
    app()
