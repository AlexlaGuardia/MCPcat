"""mcpcat CLI — MCP Server Inspector"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich.syntax import Syntax
import json

from mcpcat.client import MCPClient

app = typer.Typer(
    name="mcpcat",
    help="MCP Server Inspector — connect, explore, and test any MCP server from your terminal.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def tools(
    url: str = typer.Argument(help="MCP server SSE URL (e.g. http://localhost:8100/sse)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full parameter schemas"),
):
    """List all tools exposed by an MCP server."""
    with console.status("Connecting to MCP server..."):
        client = MCPClient(url)
        tool_list = client.list_tools()

    if not tool_list:
        console.print("[yellow]No tools found.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Tools — {url}", show_lines=verbose)
    table.add_column("#", style="dim", width=4)
    table.add_column("Tool", style="bold cyan")
    table.add_column("Description", style="white", max_width=60)
    if verbose:
        table.add_column("Parameters", style="dim")

    for i, tool in enumerate(tool_list, 1):
        name = tool.get("name", "?")
        desc = tool.get("description", "")
        # Truncate description if not verbose
        if not verbose and len(desc) > 60:
            desc = desc[:57] + "..."

        if verbose:
            params = tool.get("inputSchema", {}).get("properties", {})
            param_str = ", ".join(
                f"{k}: {v.get('type', '?')}" for k, v in params.items()
            ) if params else "none"
            table.add_row(str(i), name, desc, param_str)
        else:
            table.add_row(str(i), name, desc)

    console.print(table)
    console.print(f"\n[dim]{len(tool_list)} tools available[/dim]")


@app.command()
def inspect(
    url: str = typer.Argument(help="MCP server SSE URL"),
    tool_name: str = typer.Argument(help="Tool name to inspect"),
):
    """Show full schema for a specific tool."""
    with console.status("Connecting..."):
        client = MCPClient(url)
        tool_list = client.list_tools()

    tool = next((t for t in tool_list if t["name"] == tool_name), None)
    if not tool:
        console.print(f"[red]Tool '{tool_name}' not found.[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        Syntax(json.dumps(tool, indent=2), "json", theme="monokai"),
        title=f"[bold]{tool_name}[/bold]",
        subtitle=tool.get("description", ""),
    ))


@app.command()
def call(
    url: str = typer.Argument(help="MCP server SSE URL"),
    tool_name: str = typer.Argument(help="Tool name to call"),
    args: str = typer.Option("{}", "--args", "-a", help='JSON arguments (e.g. \'{"query": "SELECT 1"}\')'),
):
    """Call a tool on the MCP server and display the result."""
    try:
        parsed_args = json.loads(args)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON args: {e}[/red]")
        raise typer.Exit(1)

    with console.status(f"Calling {tool_name}..."):
        client = MCPClient(url)
        result = client.call_tool(tool_name, parsed_args)

    if result is None:
        console.print("[red]No response from server.[/red]")
        raise typer.Exit(1)

    # Handle different result formats
    if isinstance(result, dict):
        if "content" in result:
            for item in result["content"]:
                if item.get("type") == "text":
                    try:
                        parsed = json.loads(item["text"])
                        console.print(JSON(json.dumps(parsed)))
                    except (json.JSONDecodeError, TypeError):
                        console.print(item["text"])
        else:
            console.print(JSON(json.dumps(result)))
    else:
        console.print(str(result))


@app.command()
def ping(
    url: str = typer.Argument(help="MCP server SSE URL"),
):
    """Check if an MCP server is reachable and responding."""
    try:
        with console.status("Pinging..."):
            client = MCPClient(url)
            tool_list = client.list_tools()
        console.print(f"[green]Connected.[/green] {len(tool_list)} tools available.")
    except Exception as e:
        console.print(f"[red]Failed:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
