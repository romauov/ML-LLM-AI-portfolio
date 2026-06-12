"""Veterinary investigation agents and prompts."""

from app.agents.vet_agent import (
    get_vet_agent_executor,
    get_simple_vet_agent,
    initialize_global_agent,
    get_global_agent,
    create_investigation_agent,
)
from app.agents.prompts import (
    get_vet_agent_prompt,
    get_simple_vet_agent_prompt,
)

__all__ = [
    "get_vet_agent_executor",
    "get_simple_vet_agent",
    "initialize_global_agent",
    "get_global_agent",
    "create_investigation_agent",
    "get_vet_agent_prompt",
    "get_simple_vet_agent_prompt",
]
