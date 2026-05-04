# mcprobe

You're building an MCP server. You want to see what tools it exposes, test a call, debug a schema. You don't want to wire up a full client just to do that.

`mcprobe` is the missing `curl` for MCP. Connect to any server, list its tools, call them, inspect schemas. From your terminal.

## Install

```bash
pip install mcprobe
```

## Usage

**List the tools on a server:**

```bash
mcprobe tools http://localhost:8100/sse
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

**Inspect a tool's schema:**

```bash
mcprobe inspect http://localhost:8100/sse cortex_signal
```

**Call a tool:**

```bash
mcprobe call http://localhost:8100/sse health
mcprobe call http://localhost:8100/sse query -a '{"sql": "SELECT count(*) FROM clients"}'
```

**Check a server is alive:**

```bash
mcprobe ping http://localhost:8100/sse
```

## Commands

| Command   | What it does                          |
|-----------|---------------------------------------|
| `tools`   | List all tools (add `-v` for schemas) |
| `inspect` | Full schema for one tool              |
| `call`    | Call a tool with JSON args            |
| `ping`    | Check the server responds             |

## Transports

`mcprobe` auto-detects SSE (`/sse`) and streamable HTTP (`/mcp`) endpoints. No flags needed.

## Why

MCP servers are everywhere now. There was no quick way to look inside one without reading source or writing a client. This is that quick way.

## License

MIT
