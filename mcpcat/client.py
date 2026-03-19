"""MCP Client — handles SSE connection and JSON-RPC messaging."""

import json
import httpx
import httpx_sse


class MCPClient:
    """Connects to an MCP server via SSE and sends JSON-RPC requests."""

    def __init__(self, sse_url: str, timeout: float = 30.0):
        self.sse_url = sse_url
        self.timeout = timeout
        self._session_url = None
        self._connect()

    def _connect(self):
        """Establish SSE connection and get the session endpoint."""
        with httpx.Client(timeout=self.timeout) as client:
            with httpx_sse.connect_sse(client, "GET", self.sse_url) as sse:
                for event in sse.iter_sse():
                    if event.event == "endpoint":
                        endpoint = event.data
                        # Handle relative URLs
                        if endpoint.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(self.sse_url)
                            self._session_url = f"{parsed.scheme}://{parsed.netloc}{endpoint}"
                        else:
                            self._session_url = endpoint
                        break
                    elif event.event == "message":
                        # Some servers send initialization message first
                        continue

        if not self._session_url:
            raise ConnectionError("Failed to get session endpoint from SSE stream")

    def _request(self, method: str, params: dict | None = None) -> dict | None:
        """Send a JSON-RPC request to the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
        }
        if params:
            payload["params"] = params

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self._session_url, json=payload)
            resp.raise_for_status()

            # Response may come via SSE or direct
            content_type = resp.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                # Parse SSE response
                for line in resp.text.split("\n"):
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data:
                            return json.loads(data)
            elif resp.text:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    return None

        return None

    def list_tools(self) -> list[dict]:
        """Get all available tools from the server."""
        result = self._request("tools/list")
        if result and "result" in result:
            return result["result"].get("tools", [])
        # Some servers return tools directly
        if result and "tools" in result:
            return result["tools"]
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> dict | None:
        """Call a specific tool with the given arguments."""
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        result = self._request("tools/call", params)
        if result and "result" in result:
            return result["result"]
        return result
