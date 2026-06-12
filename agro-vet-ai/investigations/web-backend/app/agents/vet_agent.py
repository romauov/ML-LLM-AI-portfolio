"""
Veterinary Investigation Agent setup with Langchain AgentExecutor.

This module creates and configures the main veterinary investigation agent
using Langchain's AgentExecutor with OpenAI-compatible function calling.
"""

from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from typing import Optional, List
from langchain_core.tools import BaseTool
import os

from app.agents.prompts import get_vet_agent_prompt, get_simple_vet_agent_prompt
from app.tools.mcp_tools import create_mcp_tools
from app.tools.investigation_tools import create_investigation_tools
from app.tools.todo_tool import TodoWriteTool
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from app.config import get_settings
from app.llm_config import LLMClientFactory

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

settings = get_settings()


def get_vet_agent_executor(
    investigation_id: str = "",
    animal_type: str = "pig",
    mcp_client: Optional[VetRetroMCPClient] = None,
    investigation_manager: Optional[InvestigationManager] = None,
    verbose: bool = True,
    max_iterations: int = 25,  # Increased from 15 to allow more investigation steps
) -> AgentExecutor:
    """
    Create and return a configured veterinary agent executor.

    This creates the main agent with all available tools:
    - MCP tools for knowledge base access (vet_search, get_pages, etc.)
    - Investigation tools for file operations (create, read, write, etc.)
    - Todo management tool for task tracking

    The agent follows a systematic investigation workflow adapted from
    Qwen Code architecture with veterinary domain specialization.

    The animal_type parameter determines which specialized prompt is used:
    - "pig" (default) - Uses AGENTS.md for pig farming
    - "poultry" - Uses AGENTS_POULTRY.md for poultry farming

    Args:
        investigation_id: Current investigation ID (optional, for context)
        animal_type: Type of animals ("pig", "poultry", "cattle", etc.) (default: "pig")
        mcp_client: MCP client for knowledge base access (required for full functionality)
        investigation_manager: Manager for investigation file operations (required for full functionality)
        verbose: Enable verbose logging of agent actions (default: True)
        max_iterations: Maximum number of agent iterations (default: 25)

    Returns:
        Configured AgentExecutor ready to process veterinary investigations

    Example:
        >>> from app.services.mcp_client import VetRetroMCPClient
        >>> from app.services.investigation_manager import InvestigationManager
        >>>
        >>> mcp_client = VetRetroMCPClient("http://localhost:8765")
        >>> await mcp_client.connect()
        >>>
        >>> inv_manager = InvestigationManager("/path/to/investigations")
        >>>
        >>> # For pigs (default)
        >>> agent = get_vet_agent_executor(
        ...     animal_type="pig",
        ...     mcp_client=mcp_client,
        ...     investigation_manager=inv_manager
        ... )
        >>>
        >>> # For poultry
        >>> agent_poultry = get_vet_agent_executor(
        ...     animal_type="poultry",
        ...     mcp_client=mcp_client,
        ...     investigation_manager=inv_manager
        ... )
        >>>
        >>> result = await agent.ainvoke({
        ...     "input": "I have a diarrhea outbreak in piglets 3-7 days old"
        ... })
    """
    # Log configuration for debugging
    if verbose:
        print(f"[VetAgent] LLM Model: {settings.LLM_MODEL}")
        print(f"[VetAgent] LLM API Base: {settings.LLM_API_BASE}")

    # Initialize LLM using factory (handles X-title header)
    llm_factory = LLMClientFactory(settings)
    llm = llm_factory.create_chat_llm(
        temperature=0,  # Deterministic for consistency
        streaming=True,  # Enable streaming for better UX
        use_for_agent=True
    )

    # Collect all tools
    tools: List[BaseTool] = []

    # MCP tools (knowledge base)
    if mcp_client:
        mcp_tools = create_mcp_tools(mcp_client)
        tools.extend(mcp_tools)
        if verbose:
            print(f"[VetAgent] Loaded {len(mcp_tools)} MCP tools")
    else:
        print("[VetAgent] Warning: No MCP client provided, knowledge base tools unavailable")

    # Investigation file operation tools
    if investigation_manager:
        inv_tools = create_investigation_tools(investigation_manager)
        tools.extend(inv_tools)
        if verbose:
            print(f"[VetAgent] Loaded {len(inv_tools)} investigation tools")
    else:
        print("[VetAgent] Warning: No investigation manager provided, file tools unavailable")

    # Todo management tool (DISABLED - uses too many iterations)
    # todo_tool = TodoWriteTool()
    # tools.append(todo_tool)

    if verbose:
        print(f"[VetAgent] Total tools available: {len(tools)}")
        print(f"[VetAgent] Tool names: {[tool.name for tool in tools]}")

    # Get prompt template (based on animal type)
    prompt = get_vet_agent_prompt(
        investigation_id=investigation_id,
        animal_type=animal_type
    )

    # Create agent using OpenAI tools format
    # This uses function calling / tool calling capabilities
    agent = create_openai_tools_agent(llm, tools, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        return_intermediate_steps=True,  # Return tool call details
        max_iterations=max_iterations,  # Prevent infinite loops
        handle_parsing_errors=True,  # Gracefully handle parsing errors
        # Note: langchain_classic only supports early_stopping_method="force" (default)
        # Agent must return final answer via Final Answer format in prompt
    )

    return agent_executor


def get_simple_vet_agent(
    llm_model: Optional[str] = None,
    temperature: float = 0,
    verbose: bool = False,
) -> AgentExecutor:
    """
    Create a simplified veterinary agent for testing without tools.

    This is useful for:
    - Testing basic LLM connectivity
    - Verifying prompt template
    - Quick experiments without full infrastructure

    Args:
        llm_model: Override default LLM model
        temperature: LLM temperature (0 = deterministic)
        verbose: Enable verbose logging

    Returns:
        Simple AgentExecutor with no tools

    Example:
        >>> agent = get_simple_vet_agent()
        >>> result = await agent.ainvoke({
        ...     "input": "What are common causes of neonatal diarrhea in piglets?"
        ... })
    """
    # Initialize LLM using factory (handles X-title header)
    llm_factory = LLMClientFactory(settings)
    llm = llm_factory.create_chat_llm(
        model=llm_model,
        temperature=temperature,
        streaming=True,
        use_for_agent=True
    )

    # Use simplified prompt without investigation context
    prompt = get_simple_vet_agent_prompt()

    # Create agent with empty tools list
    tools: List[BaseTool] = []
    agent = create_openai_tools_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        return_intermediate_steps=False,
        max_iterations=5,
    )

    return agent_executor


# Singleton instance for API endpoints
_global_agent_executor: Optional[AgentExecutor] = None


def initialize_global_agent(
    mcp_client: VetRetroMCPClient,
    investigation_manager: InvestigationManager,
) -> None:
    """
    Initialize the global agent executor instance.

    This should be called once during application startup.

    Args:
        mcp_client: Connected MCP client instance
        investigation_manager: Investigation manager instance
    """
    global _global_agent_executor
    _global_agent_executor = get_vet_agent_executor(
        mcp_client=mcp_client,
        investigation_manager=investigation_manager,
        verbose=False,  # Disable verbose for production
    )
    print("[VetAgent] Global agent executor initialized")


def get_global_agent() -> AgentExecutor:
    """
    Get the global agent executor instance.

    Returns:
        Global AgentExecutor instance

    Raises:
        RuntimeError: If agent not initialized (call initialize_global_agent first)
    """
    if _global_agent_executor is None:
        raise RuntimeError(
            "Agent executor not initialized. Call initialize_global_agent() first."
        )
    return _global_agent_executor


def create_investigation_agent(
    investigation_id: str,
    mcp_client: VetRetroMCPClient,
    investigation_manager: InvestigationManager,
    animal_type: str = "pig",
    max_iterations: int = 50,  # Increased default for complex investigations
) -> AgentExecutor:
    """
    Create an agent executor for a specific investigation.

    This creates a new agent instance with investigation-specific context
    in the system prompt. Use this when you need investigation-aware behavior.

    Args:
        investigation_id: ID of the investigation
        mcp_client: MCP client instance
        investigation_manager: Investigation manager instance
        animal_type: Type of animals ("pig", "poultry", etc.) (default: "pig")
        max_iterations: Maximum number of agent iterations (default: 50)

    Returns:
        AgentExecutor configured for specific investigation

    Example:
        >>> agent = create_investigation_agent(
        ...     investigation_id="20251107_ivanovka_diarrhea",
        ...     mcp_client=mcp_client,
        ...     investigation_manager=inv_manager
        ... )
        >>> result = await agent.ainvoke({
        ...     "input": "Update hypotheses based on new lab results"
        ... })
    """
    return get_vet_agent_executor(
        investigation_id=investigation_id,
        animal_type=animal_type,
        mcp_client=mcp_client,
        investigation_manager=investigation_manager,
        verbose=False,
        max_iterations=max_iterations,
    )
