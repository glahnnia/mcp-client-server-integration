"""Asynchronous MCP client for the local DocumentMCP demonstration."""

import asyncio
import json
import sys
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic import AnyUrl


class MCPClient:
    def __init__(self, command: str, args: list[str], env: Optional[dict[str, str]] = None):
        self._command = command
        self._args = args
        self._env = env
        self._session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    async def connect(self) -> None:
        params = StdioServerParameters(command=self._command, args=self._args, env=self._env)
        transport = await self._exit_stack.enter_async_context(stdio_client(params))
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("MCP client is not connected. Call connect() first.")
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        response = await self.session().list_tools()
        return response.tools

    async def call_tool(self, tool_name: str, tool_input: dict[str, Any]) -> types.CallToolResult:
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        response = await self.session().list_prompts()
        return response.prompts

    async def get_prompt(self, prompt_name: str, args: dict[str, str]) -> list[types.PromptMessage]:
        response = await self.session().get_prompt(prompt_name, arguments=args)
        return response.messages

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(uri))
        if not result.contents:
            return None
        content = result.contents[0]
        if isinstance(content, types.TextResourceContents):
            if content.mimeType == "application/json":
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text
            return content.text
        return content

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.cleanup()


async def main() -> None:
    from pathlib import Path
    server_file = Path(__file__).with_name("mcp_server.py")
    async with MCPClient(sys.executable, [str(server_file)]) as client:
        print("Tools:", [tool.name for tool in await client.list_tools()])
        print("Prompts:", [prompt.name for prompt in await client.list_prompts()])
        print("Document IDs:", await client.read_resource("docs://documents"))


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
