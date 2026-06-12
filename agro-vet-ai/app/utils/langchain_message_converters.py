import json

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)


def to_openai_format(message):
    """
    Конвертирует LangChain сообщения в OpenAI API формат.
    """
    if isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    elif isinstance(message, AIMessage):
        result = {"role": "assistant", "content": message.content}
        if hasattr(message, 'tool_calls') and message.tool_calls:
            result['content'] = None
            result["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"], ensure_ascii=False)
                    }
                }
                for tc in message.tool_calls
            ]

        return result
    elif isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    elif isinstance(message, ToolMessage):
        return {
            "role": "tool",
            "content": message.content,
            "tool_call_id": message.tool_call_id
        }
    else:
        raise ValueError(f"Unsupported message type: {type(message)}")


def from_openai_format(message_dict):
    """
    Конвертирует сообщения из OpenAI API формата в LangChain сообщения.
    """
    role = message_dict.get("role", "")
    content = message_dict.get("content", "")

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "system":
        return SystemMessage(content=content)
    elif role == "tool":
        return ToolMessage(content=content, tool_call_id=message_dict.get("tool_call_id"))
    else:
        # Default to HumanMessage for unknown roles
        return HumanMessage(content=content)
