"""Minimal Model Context Protocol document server.

The six documents are illustrative strings stored in process memory. This
project demonstrates MCP primitives, not filesystem persistence or PDF parsing.
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")

# Example documents: these strings are NOT files on disk.
docs: dict[str, str] = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


@mcp.tool()
def read_doc(doc_id: str) -> str:
    """Read example document text by ID."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id!r} not found")
    return docs[doc_id]


@mcp.tool()
def edit_doc(doc_id: str, new_content: str) -> str:
    """Replace the text of an example document until the server restarts."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id!r} not found")
    docs[doc_id] = new_content
    return f"Document {doc_id} updated successfully"


@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    """List available example document IDs."""
    return list(docs.keys())


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def fetch_doc(doc_id: str) -> str:
    """Return the current text for one example document."""
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id!r} not found")
    return docs[doc_id]


@mcp.prompt(name="format", description="Reformat an example document as Markdown.")
def format_document(doc_id: str = Field(description="ID of the document to format")) -> list[base.Message]:
    """Prompt template only: an LLM client must execute the instructions."""
    prompt = (
        "Reformat the following document using Markdown syntax. "
        "Use read_doc to read the content and edit_doc to save the formatted content. "
        f"Document ID: {doc_id}"
    )
    return [base.UserMessage(prompt)]


@mcp.prompt(name="summarize", description="Summarize an example document.")
def summarize_document(doc_id: str = Field(description="ID of the document to summarize")) -> list[base.Message]:
    """Prompt template only: an LLM client must execute the instructions."""
    prompt = f"Summarize document {doc_id} clearly and concisely. Use read_doc to retrieve its contents first."
    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
