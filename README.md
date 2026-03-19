# mcpcat

Inspect any MCP server from your terminal. List tools, read schemas, call endpoints.

I built this because I run a [70+ tool MCP server](https://github.com/AlexlaGuardia/guardia-mcp) and got tired of guessing what was exposed. `mcpcat` connects via SSE, pulls the tool list, and lets you poke around without writing a client.

## Install

```bash
pip install mcpcat
```

Or from source:

```bash
git clone https://github.com/AlexlaGuardia/mcpcat.git
cd mcpcat
pip install -e .
```

## Usage

**List all tools on a server:**

```bash
mcpcat tools http://localhost:8100/sse
```

```
┌──────────────────────────────────────────────────┐
│  #  │ Tool              │ Description            │
├──────────────────────────────────────────────────┤
│  1  │ health            │ Full system status     │
│  2  │ query             │ Run SELECT queries     │
│  3  │ cortex_signal     │ Log observations       │
│ ... │                   │                        │
└──────────────────────────────────────────────────┘
70 tools available
```

**Inspect a specific tool's schema:**

```bash
mcpcat inspect http://localhost:8100/sse cortex_signal
```

**Call a tool:**

```bash
mcpcat call http://localhost:8100/sse health
mcpcat call http://localhost:8100/sse query -a '{"sql": "SELECT count(*) FROM clients"}'
```

**Check if a server is alive:**

```bash
mcpcat ping http://localhost:8100/sse
```

## Commands

| Command   | What it does                          |
|-----------|---------------------------------------|
| `tools`   | List all tools (add `-v` for schemas) |
| `inspect` | Full schema for one tool              |
| `call`    | Call a tool with JSON args            |
| `ping`    | Check if server responds              |

## Why

MCP servers are popping up everywhere but there's no quick way to see what's inside one. You either read the source or wire up a client. `mcpcat` is the missing `curl` for MCP.

## License

MIT
