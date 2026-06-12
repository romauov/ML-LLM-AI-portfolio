"""
Prompts for the veterinary investigation agent.

This module contains prompt templates for the veterinary assistant agent,
adapted from Qwen Code system prompts for veterinary investigation domain.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pathlib import Path

# Path to agent workspace
AGENT_WORKSPACE = Path(__file__).parent.parent.parent.parent / "agent-workspace"


def load_agents_md(animal_type: str = "pig") -> str:
    """
    Load the AGENTS.md file from agent-workspace based on animal type.

    This file contains domain-specific veterinary investigation instructions.

    Args:
        animal_type: Type of animals ("pig", "poultry", "cattle", etc.)

    Returns:
        Content of the appropriate AGENTS.md file
    """
    # Determine which prompt file to load based on animal type
    if animal_type.lower() in ["poultry", "chicken", "broiler", "птица", "птицы", "бройлер", "несушка"]:
        agents_md_path = AGENT_WORKSPACE / "AGENTS_POULTRY.md"
    else:
        # Default to pig (swine) prompt
        agents_md_path = AGENT_WORKSPACE / "AGENTS.md"

    if agents_md_path.exists():
        return agents_md_path.read_text(encoding="utf-8")

    # Fallback to default if specific file doesn't exist
    default_path = AGENT_WORKSPACE / "AGENTS.md"
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")

    return ""


# Основной системный промпт теперь загружается из AGENTS.md / AGENTS_POULTRY.md
# Этот файл содержит только функции для загрузки промптов


def get_vet_agent_prompt(
    investigation_id: str = "",
    animal_type: str = "pig"
) -> ChatPromptTemplate:
    """
    Создаёт полный системный промпт для ветеринарного агента.

    Загружает промпт из соответствующего файла:
    - AGENTS.md для свиней
    - AGENTS_POULTRY.md для птицы

    Args:
        investigation_id: ID текущего расследования (если есть)
        animal_type: Тип животных ("pig", "poultry", "cattle" и т.д.)

    Returns:
        ChatPromptTemplate со всеми необходимыми переменными
    """
    # Загружаем промпт из соответствующего AGENTS*.md файла
    system_prompt = load_agents_md(animal_type=animal_type)

    if not system_prompt:
        raise ValueError(f"Не удалось загрузить промпт для animal_type={animal_type}")

    # Добавляем контекст текущего расследования в конец промпта
    if investigation_id:
        system_prompt += f"\n\n**Current Investigation:** {investigation_id}"

    # Создаём prompt template в формате Langchain / OpenAI
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    return prompt


# Для тестирования: упрощённый промпт без контекста расследования
def get_simple_vet_agent_prompt(animal_type: str = "pig") -> ChatPromptTemplate:
    """
    Получить упрощённый промпт для тестирования без контекста расследования.

    Args:
        animal_type: Тип животных ("pig", "poultry" и т.д.)
    """
    system_prompt = load_agents_md(animal_type=animal_type)

    if not system_prompt:
        raise ValueError(f"Не удалось загрузить промпт для animal_type={animal_type}")

    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
