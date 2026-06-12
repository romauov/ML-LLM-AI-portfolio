"""VetRetro Backend - FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from app.api import chat_router, investigations_router
from app.auth import verify_api_key

import os
# Remove proxy settings to avoid conflicts with OpenAI client
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("SOCKS_PROXY", None)
os.environ.pop("socks_proxy", None)
os.environ.pop("ALL_PROXY", None)
os.environ.pop("all_proxy", None)
os.environ.pop("FTP_PROXY", None)
os.environ.pop("ftp_proxy", None)

logger = logging.getLogger(__name__)

# Get settings singleton
settings = get_settings()

# Global MCP client and investigation manager instances
mcp_client: VetRetroMCPClient = None
investigation_manager: InvestigationManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global mcp_client, investigation_manager

    # Startup
    logger.info("Starting VetRetro Backend...")
    logger.info(f"MCP Server URL: {settings.VETRETRO_MCP_URL}")
    logger.info(f"Investigations Directory: {settings.INVESTIGATIONS_DIR}")

    # Initialize MCP client
    mcp_client = VetRetroMCPClient(
        url=settings.VETRETRO_MCP_URL,
        timeout=30.0,
        sse_read_timeout=300.0,
    )
    logger.info("MCP client initialized")

    # Initialize Investigation Manager
    investigation_manager = InvestigationManager(workspace_path=settings.INVESTIGATIONS_DIR)
    logger.info("Investigation manager initialized")

    # Store in app state for access in routes
    app.state.mcp_client = mcp_client
    app.state.investigation_manager = investigation_manager

    yield

    # Shutdown
    logger.info("Shutting down VetRetro Backend...")
    mcp_client = None
    investigation_manager = None


# Initialize FastAPI application
app = FastAPI(
    title="VetRetro Backend API",
    description="AI-powered veterinary incident investigation system",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)
app.include_router(investigations_router)


@app.get("/")
async def root(api_key: str = Depends(verify_api_key)):
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "VetRetro Backend",
        "version": "0.1.0",
    }


@app.get("/hello")
async def hello(api_key: str = Depends(verify_api_key)):
    """Test endpoint with LLM call."""
    from app.llm_config import LLMClientFactory

    # Initialize LLM using factory (handles X-title header)
    llm_factory = LLMClientFactory(settings)
    llm = llm_factory.create_chat_llm(
        model=settings.LLM_MODEL,
        temperature=0.7,
        streaming=False,
    )

    # Make a simple async call
    response = await llm.ainvoke("Say hello in one sentence")

    return {
        "message": "LLM connected successfully",
        "model": settings.LLM_MODEL,
        "response": response.content,
    }


@app.get("/mcp/test")
async def test_mcp(api_key: str = Depends(verify_api_key)):
    """Test endpoint for MCP connection."""
    try:
        # List available tools
        tools = await mcp_client.list_tools()

        return {
            "status": "ok",
            "message": "MCP client connected successfully",
            "mcp_url": settings.VETRETRO_MCP_URL,
            "tools_count": len(tools),
            "tools": [tool["name"] for tool in tools],
        }
    except Exception as e:
        logger.error(f"MCP test failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


@app.get("/mcp/search")
async def test_mcp_search(query: str = "E.coli diarrhea piglets", api_key: str = Depends(verify_api_key)):
    """Test endpoint for MCP vet_search tool."""
    try:
        # Perform search
        result = await mcp_client.vet_search(query=query, limit=3)

        return {
            "status": "ok",
            "query": query,
            "result": result,
        }
    except Exception as e:
        logger.error(f"MCP search failed: {e}")
        return {
            "status": "error",
            "message": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
