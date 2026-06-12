"""Langchain Tools for MCP vetretro knowledge base access."""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.mcp_client import VetRetroMCPClient


class VetSearchInput(BaseModel):
    """Input schema for VetSearchTool."""

    query: str = Field(
        ...,
        description=(
            "Search query in natural language describing the veterinary problem, "
            "disease, treatment, or topic you want to find information about. "
            "Examples: 'E.coli diarrhea treatment piglets', 'PRRS vaccination protocols', "
            "'Mycoplasma pneumonia antibiotics'"
        )
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description=(
            "Maximum number of search results to return (1-20). "
            "Default is 5. Use higher values (10-20) when you need comprehensive information "
            "on a topic. Use lower values (3-5) for quick lookups."
        )
    )
    source_filter: Optional[str] = Field(
        default=None,
        description=(
            "Optional: Filter results by specific source document. "
            "Use vet_sources tool first to see available sources. "
            "Example: 'Antimicrobial Therapy in Veterinary Medicine, 5th Edition'"
        )
    )


class VetSearchTool(BaseTool):
    """
    Tool for semantic search across veterinary knowledge base.

    Use this tool to find evidence-based information from scientific veterinary sources
    when investigating disease outbreaks, planning treatments, or researching specific conditions.

    The tool searches across multiple authoritative sources including:
    - Antimicrobial therapy guidelines
    - Disease reference books
    - Pharmacokinetics studies
    - Practical health management guides

    Results include:
    - Relevant text excerpts with context
    - Source citations (book, page, chapter)
    - Similarity scores indicating relevance
    - Keywords for each result

    **When to use:**
    - At the start of an investigation to gather background on the disease/condition
    - When forming or evaluating diagnostic hypotheses
    - When planning treatment protocols
    - When determining appropriate antibiotic choices and dosages
    - When researching differential diagnoses

    **Best practices:**
    - Use specific, descriptive queries (e.g., "neonatal diarrhea ETEC treatment" rather than just "diarrhea")
    - Search multiple times with different query formulations to ensure comprehensive coverage
    - Always cite sources in your investigation files (book, page number)
    - Request 10-15 results for complex topics requiring thorough research
    """

    name: str = "vet_search"
    description: str = (
        "Performs semantic search across veterinary scientific literature to find relevant "
        "information about diseases, treatments, pharmacology, and health management. "
        "Returns excerpts from authoritative sources with citations. "
        "Use this tool proactively throughout the investigation to support evidence-based decision making."
    )
    args_schema: Type[BaseModel] = VetSearchInput

    mcp_client: VetRetroMCPClient

    def __init__(self, mcp_client: VetRetroMCPClient):
        super().__init__(mcp_client=mcp_client)

    def _run(self, query: str, limit: int = 5, source_filter: Optional[str] = None) -> str:
        """Execute veterinary knowledge base search."""
        import asyncio
        return asyncio.run(
            self.mcp_client.vet_search(
                query=query,
                limit=limit,
                offset=0,
                source_filter=source_filter
            )
        )


class VetSourcesTool(BaseTool):
    """
    Tool to list all available sources in the veterinary knowledge base.

    Use this tool at the beginning of an investigation session to understand what
    reference materials are available. This helps you:
    - Know which books/sources you can search
    - Understand the scope of available knowledge
    - Choose appropriate sources for specific topics
    - Filter searches to relevant sources

    Returns information about each source including:
    - Full title and description
    - Page range (total pages available)
    - Number of chapters
    - Subject areas covered
    """

    name: str = "vet_sources"
    description: str = (
        "Lists all available veterinary reference sources in the knowledge base. "
        "Returns source titles, descriptions, page ranges, and chapter counts. "
        "Use this at the start of a session to understand available resources."
    )

    mcp_client: VetRetroMCPClient

    def __init__(self, mcp_client: VetRetroMCPClient):
        super().__init__(mcp_client=mcp_client)

    def _run(self) -> str:
        """List all available veterinary sources."""
        import asyncio
        return asyncio.run(self.mcp_client.vet_sources())


class SourceInfoInput(BaseModel):
    """Input schema for SourceInfoTool."""

    source_document: str = Field(
        ...,
        description=(
            "Exact name of the source document to get information about. "
            "Use vet_sources tool first to get the correct source name. "
            "Example: 'Antimicrobial Therapy in Veterinary Medicine, 5th Edition'"
        )
    )


class SourceInfoTool(BaseTool):
    """
    Tool to get detailed information and table of contents for a specific source.

    Use this tool when you need to:
    - Navigate to specific chapters on a topic
    - Understand the structure and coverage of a source
    - Find the right section before using get_pages
    - See what topics are covered in a book

    Returns:
    - Complete table of contents with chapter titles
    - Page ranges for each chapter
    - Total page count
    - Source description
    """

    name: str = "source_info"
    description: str = (
        "Retrieves detailed information about a specific veterinary source including "
        "table of contents with chapter titles and page ranges. "
        "Use this to navigate sources and find relevant chapters."
    )
    args_schema: Type[BaseModel] = SourceInfoInput

    mcp_client: VetRetroMCPClient

    def __init__(self, mcp_client: VetRetroMCPClient):
        super().__init__(mcp_client=mcp_client)

    def _run(self, source_document: str) -> str:
        """Get detailed source information."""
        import asyncio
        return asyncio.run(self.mcp_client.source_info(source_document))


class GetPagesInput(BaseModel):
    """Input schema for GetPagesTool."""

    source_document: str = Field(
        ...,
        description=(
            "Exact name of the source document. "
            "Example: 'Antimicrobial Therapy in Veterinary Medicine, 5th Edition'"
        )
    )
    page_start: int = Field(
        ...,
        ge=1,
        description="Starting page number to retrieve (1-based indexing)"
    )
    page_end: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Optional: Ending page number. If not provided, only retrieves page_start. "
            "Use range (page_end - page_start + 1) for reading multiple consecutive pages."
        )
    )


class GetPagesTool(BaseTool):
    """
    Tool to retrieve full text content from specific pages of a source.

    Use this tool when:
    - Search results reference interesting content but you need more context
    - You want to read complete sections or chapters
    - Search excerpts are truncated and you need the full text
    - You need to verify detailed information (e.g., exact drug dosages, protocols)

    **Important notes:**
    - This returns complete page content, which can be lengthy
    - Use page ranges efficiently (e.g., 3-5 pages max per call)
    - Always cite page numbers in your investigation files
    - Prefer targeted searches over reading many pages sequentially

    **Example workflow:**
    1. Use vet_search to find relevant pages
    2. Use source_info to see chapter structure (if needed)
    3. Use get_pages to read the full content of 2-3 pages
    4. Extract and cite specific information in investigation files
    """

    name: str = "get_pages"
    description: str = (
        "Retrieves full text content from specific page(s) of a veterinary source. "
        "Use this when search results need more context or you need complete text from specific pages. "
        "Can retrieve single pages or page ranges. Always include page citations in your investigation files."
    )
    args_schema: Type[BaseModel] = GetPagesInput

    mcp_client: VetRetroMCPClient

    def __init__(self, mcp_client: VetRetroMCPClient):
        super().__init__(mcp_client=mcp_client)

    def _run(
        self,
        source_document: str,
        page_start: int,
        page_end: Optional[int] = None
    ) -> str:
        """Retrieve pages from source."""
        import asyncio
        return asyncio.run(
            self.mcp_client.get_pages(
                source_document=source_document,
                page_start=page_start,
                page_end=page_end
            )
        )


def create_mcp_tools(mcp_client: VetRetroMCPClient) -> list[BaseTool]:
    """
    Create all MCP-based tools for veterinary knowledge base access.

    Args:
        mcp_client: Initialized VetRetroMCPClient instance

    Returns:
        List of Langchain BaseTool instances for MCP operations
    """
    return [
        VetSearchTool(mcp_client=mcp_client),
        VetSourcesTool(mcp_client=mcp_client),
        SourceInfoTool(mcp_client=mcp_client),
        GetPagesTool(mcp_client=mcp_client),
    ]
