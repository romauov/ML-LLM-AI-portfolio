"""MCP Client for connecting to VetRetro knowledge base server."""

import logging
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers via HTTP/SSE."""

    def __init__(self, url: str, timeout: float = 30.0, sse_read_timeout: float = 300.0):
        """
        Initialize MCP Client.

        Args:
            url: Base URL of the MCP server (e.g., http://localhost:8765)
            timeout: HTTP timeout for regular operations in seconds
            sse_read_timeout: Timeout for SSE read operations in seconds
        """
        self.url = url
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self._session: Optional[ClientSession] = None
        self._connected = False

    @asynccontextmanager
    async def connect(self):
        """
        Connect to MCP server and yield the session.

        Usage:
            async with client.connect() as session:
                tools = await session.list_tools()
                result = await session.call_tool("tool_name", {"arg": "value"})
        """
        # SSE endpoint URL
        sse_url = f"{self.url}/sse"

        logger.info(f"Connecting to MCP server at {sse_url}")

        try:
            # Create SSE client transport
            async with sse_client(
                url=sse_url,
                timeout=self.timeout,
                sse_read_timeout=self.sse_read_timeout,
            ) as (read, write):
                # Create client session
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    self._session = session
                    self._connected = True

                    logger.info("Successfully connected to MCP server")

                    try:
                        yield session
                    finally:
                        self._connected = False
                        self._session = None

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self._connected = False
            self._session = None
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from the MCP server.

        Returns:
            List of tool definitions with name, description, and inputSchema

        Raises:
            RuntimeError: If not connected to server
        """
        async with self.connect() as session:
            result = await session.list_tools()

            # Convert Tool objects to dictionaries
            tools = []
            for tool in result.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                })

            logger.info(f"Retrieved {len(tools)} tools from MCP server")
            return tools

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Call a tool on the MCP server.

        Args:
            name: Name of the tool to call
            arguments: Tool arguments as a dictionary

        Returns:
            Tool result as a string (concatenated text content)

        Raises:
            RuntimeError: If not connected to server
            ValueError: If tool call fails
        """
        if arguments is None:
            arguments = {}

        async with self.connect() as session:
            logger.info(f"Calling tool '{name}' with arguments: {arguments}")

            result = await session.call_tool(name, arguments)

            # Extract text content from result
            text_parts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    text_parts.append(content.text)
                elif isinstance(content, dict) and 'text' in content:
                    text_parts.append(content['text'])

            response_text = "\n".join(text_parts)

            logger.info(f"Tool '{name}' returned {len(response_text)} characters")
            return response_text

    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected to the server."""
        return self._connected

    async def ping(self) -> bool:
        """
        Ping the MCP server to check connectivity.

        Returns:
            True if server responds, False otherwise
        """
        try:
            async with self.connect() as session:
                await session.send_ping()
                return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False


class VetRetroMCPClient(MCPClient):
    """Specialized MCP client for VetRetro knowledge base with convenience methods."""

    async def vet_search(
        self,
        query: str,
        limit: int = 5,
        offset: int = 0,
        source_filter: Optional[str] = None,
    ) -> str:
        """
        Semantic search across veterinary knowledge base.

        Args:
            query: Search query in natural language
            limit: Maximum number of results (1-20, default 5)
            offset: Number of results to skip for pagination
            source_filter: Optional filter by source document name

        Returns:
            Formatted search results with sources, pages, and similarity scores
        """
        arguments = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }

        if source_filter:
            arguments["source_filter"] = source_filter

        return await self.call_tool("vet_search", arguments)

    async def vet_sources(self) -> str:
        """
        Get list of all available sources in the knowledge base.

        Returns:
            Formatted list of sources with descriptions and page ranges
        """
        return await self.call_tool("vet_sources", {})

    async def source_info(self, source_document: str) -> str:
        """
        Get detailed information about a specific source.

        Args:
            source_document: Name of the source document

        Returns:
            Source details including table of contents with page ranges
        """
        return await self.call_tool("source_info", {"source_document": source_document})

    async def get_pages(
        self,
        source_document: str,
        page_start: int,
        page_end: Optional[int] = None,
    ) -> str:
        """
        Retrieve full text from specific page range.

        Args:
            source_document: Name of the source document
            page_start: Starting page number
            page_end: Ending page number (optional, defaults to page_start)

        Returns:
            Sequential page content
        """
        arguments = {
            "source_document": source_document,
            "page_start": page_start,
        }

        if page_end is not None:
            arguments["page_end"] = page_end

        return await self.call_tool("get_pages", arguments)

    async def extract_document(self, file_path: str) -> str:
        """
        Extract text from PDF/DOCX files with OCR support.

        Args:
            file_path: Absolute path to the file

        Returns:
            Extraction result with metadata and content preview
        """
        return await self.call_tool("extract_document", {"file_path": file_path})
