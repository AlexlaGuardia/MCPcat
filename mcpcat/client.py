"""MCP Client — supports both Streamable HTTP and legacy SSE transports."""

import json
from urllib.parse import urlparse

import httpx
import httpx_sse


class MCPClient:
    """Connects to an MCP server and sends JSON-RPC requests.

    Auto-detects transport:
    - Streamable HTTP: POST JSON-RPC to the endpoint directly
    - Legacy SSE: GET /sse to get session endpoint, then POST to it
    """

    def __init__(self, url: str, timeout: float = 15.0):
        self.url = url
        self.timeout = timeout
        self._session_id = None
        self._transport = None  # "streamable" or "sse"
        self._post_url = None
        self._detect_transport()

    def _detect_transport(self):
        """Detect whether the server uses streamable HTTP or legacy SSE."""
        parsed = urlparse(self.url)

        # If URL ends with /sse, try legacy SSE first
        if parsed.path.rstrip("/").endswith("/sse"):
            self._try_legacy_sse()
            if self._transport:
                return

        # Try streamable HTTP (GET without SSE accept header)
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self.url)
                if resp.status_code == 200:
                    try:
                        info = resp.json()
                        if info.get("protocol") == "streamable-http" or "capabilities" in info:
                            self._transport = "streamable"
                            self._post_url = self.url
                            return
                    except (json.JSONDecodeError, ValueError):
                        pass
        except httpx.HTTPError:
            pass

        # Try legacy SSE as fallback
        if not self._transport:
            self._try_legacy_sse()

        if not self._transport:
            raise ConnectionError(
                f"Could not connect to MCP server at {self.url}. "
                "Tried both streamable HTTP and legacy SSE."
            )

    def _try_legacy_sse(self):
        """Try connecting via legacy SSE transport."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with httpx_sse.connect_sse(client, "GET", self.url) as sse:
                    for event in sse.iter_sse():
                        if event.event == "endpoint":
                            endpoint = event.data
                            if endpoint.startswith("/"):
                                parsed = urlparse(self.url)
                                self._post_url = f"{parsed.scheme}://{parsed.netloc}{endpoint}"
                            else:
                                self._post_url = endpoint
                            self._transport = "sse"
                            return
        except (httpx.HTTPError, Exception):
            pass

    def _request(self, method: str, params: dict | None = None) -> dict | None:
        """Send a JSON-RPC request to the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
        }
        if params:
            payload["params"] = params

        headers = {"Content-Type": "application/json"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self._post_url, json=payload, headers=headers)
            resp.raise_for_status()

            # Capture session ID from response
            session_id = resp.headers.get("Mcp-Session-Id")
            if session_id:
                self._session_id = session_id

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

    def server_info(self) -> dict | None:
        """Get server info via GET request."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(self.url)
                return resp.json()
        except Exception:
            return None

    def list_tools(self) -> list[dict]:
        """Get all available tools from the server."""
        result = self._request("tools/list")
        if result and "result" in result:
            return result["result"].get("tools", [])
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
