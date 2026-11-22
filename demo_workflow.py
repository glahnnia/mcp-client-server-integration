"""Local end-to-end MCP smoke test; requires the MCP Python SDK, but no API key."""

import asyncio
import sys
from pathlib import Path

from mcp_client import MCPClient


def text_from_tool_result(result) -> str:
    return "\n".join(part.text for part in result.content if getattr(part, "type", "") == "text")


async def main() -> None:
    server_file = Path(__file__).with_name("mcp_server.py")
    async with MCPClient(sys.executable, [str(server_file)]) as client:
        tools = [tool.name for tool in await client.list_tools()]
        assert {"read_doc", "edit_doc"}.issubset(tools), f"Unexpected tool list: {tools}"
        print("Discovered tools:", tools)

        prompts = [prompt.name for prompt in await client.list_prompts()]
        assert {"format", "summarize"}.issubset(prompts), f"Unexpected prompts: {prompts}"
        print("Discovered prompts:", prompts)

        ids = await client.read_resource("docs://documents")
        assert isinstance(ids, list) and "report.pdf" in ids, f"Missing document IDs: {ids}"
        print("Available documents:", ids)

        before = await client.call_tool("read_doc", {"doc_id": "report.pdf"})
        assert not before.isError and "condenser" in text_from_tool_result(before)
        print("Read demo document:", text_from_tool_result(before))

        update = await client.call_tool(
            "edit_doc",
            {"doc_id": "report.pdf", "new_content": "Updated test content (in memory only)."},
        )
        assert not update.isError
        after = await client.read_resource("docs://documents/report.pdf")
        assert after == "Updated test content (in memory only).", after
        print("Updated document resource:", after)

        messages = await client.get_prompt("summarize", {"doc_id": "report.pdf"})
        assert messages, "Prompt message list was empty"
        print("Retrieved summarize prompt:", messages[0].content)

        print("PASS: MCP tool, resource, and prompt smoke test")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
