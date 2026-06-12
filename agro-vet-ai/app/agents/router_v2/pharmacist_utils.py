import json

from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_substances_and_build_footnote(
    response_text: str,
    agent_instance,
) -> str:
    """
    Извлекает действующие вещества из контекста библиотекаря через LLM,
    ищет соответствующие препараты и формирует сноску.
    """
    from app.agents.pharmacist.searching_engine import DrugSearchEngine
    from app.agents.router_v2.prompts import EXTRACT_SUBSTANCES_PROMPT

    messages = [
        {
            "role": "user",
            "content": EXTRACT_SUBSTANCES_PROMPT.format(
                text=response_text[:4000],
            ),
        }
    ]
    llm_response = agent_instance.ask_llm(
        messages=messages,
        params={"temperature": 0},
    )

    raw = llm_response.content.strip()
    start = raw.find("[")
    end = raw.rfind("]") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    try:
        substances = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Не удалось распарсить JSON с веществами: {raw[:200]}")
        return ""

    if not substances or not isinstance(substances, list):
        return ""

    logger.info(f"Извлечено {len(substances)} действующих веществ: {substances}")

    search_engine = DrugSearchEngine()
    seen_trade_names = set()
    drug_entries = []

    for substance in substances:
        if not isinstance(substance, str) or not substance.strip():
            continue
        chunks = search_engine.search_by_generic_name(substance.strip(), limit=50)
        for chunk in chunks:
            tn = chunk.get("trade_name", "")
            if tn and tn not in seen_trade_names:
                seen_trade_names.add(tn)
                gn = chunk.get("generic_name", "") or ""
                mfr = chunk.get("manufacturer", "") or ""
                parts = [tn]
                if gn:
                    parts[0] += f" ({gn})"
                if mfr:
                    parts.append(mfr)
                drug_entries.append(", ".join(parts))

    if not drug_entries:
        return ""

    lines = ["\n\n<b>--- Препараты из каталога (агент-фармацевт) ---</b>"]
    for entry in drug_entries:
        lines.append(f"• {entry}")
    return "\n".join(lines)


def format_drug_chunks(chunks: list[dict]) -> str:
    """
    Форматирование чанков препаратов в читаемый текст.

    Args:
        chunks: Список словарей с данными чанков

    Returns:
        Отформатированная строка
    """
    if not chunks:
        return "Информация не найдена."

    drugs_map = {}
    for chunk in chunks:
        trade_name = chunk.get("trade_name", "Неизвестный препарат")
        if trade_name not in drugs_map:
            drugs_map[trade_name] = {
                "generic_name": chunk.get("generic_name"),
                "target_animals": chunk.get("target_animals", []),
                "manufacturer": chunk.get("manufacturer"),
                "drug_class": chunk.get("drug_class"),
                "dosage_form": chunk.get("dosage_form"),
                "route": chunk.get("route"),
                "sections": [],
            }
        drugs_map[trade_name]["sections"].append(
            {
                "section_type": chunk.get("section_type"),
                "section_title": chunk.get("section_title"),
                "content": chunk.get("content"),
            }
        )

    parts = []
    for trade_name, data in drugs_map.items():
        drug_text = f"=== Препарат: {trade_name} ===\n"

        if data["generic_name"]:
            drug_text += f"Действующее вещество: {data['generic_name']}\n"

        if data["manufacturer"]:
            drug_text += f"Производитель: {data['manufacturer']}\n"

        if data["drug_class"]:
            drug_text += f"Класс: {data['drug_class']}\n"

        if data["dosage_form"]:
            drug_text += f"Форма выпуска: {data['dosage_form']}\n"

        if data["route"]:
            drug_text += f"Способ применения: {data['route']}\n"

        if data["target_animals"]:
            animals = (
                ", ".join(data["target_animals"])
                if isinstance(data["target_animals"], list)
                else data["target_animals"]
            )
            drug_text += f"Целевые животные: {animals}\n"

        drug_text += "\n"

        section_priority = {
            "indications": 1,
            "dosing": 2,
            "contraindications": 3,
            "properties": 4,
            "composition": 5,
            "special_notes": 6,
            "storage": 7,
            "advantages": 8,
            "other": 9,
        }

        sorted_sections = sorted(
            data["sections"],
            key=lambda x: section_priority.get(x.get("section_type", "other"), 99),
        )

        seen_contents = set()
        unique_sections = []
        for section in sorted_sections:
            content = section.get("content", "") or ""
            if content not in seen_contents:
                seen_contents.add(content)
                unique_sections.append(section)

        for section in unique_sections:
            section_title = section.get(
                "section_title", section.get("section_type", "Информация")
            )
            content = section.get("content", "") or ""

            lines = content.split("\n")
            filtered_lines = []
            skip_header = True
            for line in lines:
                if skip_header and (
                    line.startswith("Препарат:")
                    or line.startswith("Действующее вещество:")
                    or line.startswith("Раздел:")
                ):
                    continue
                skip_header = False
                filtered_lines.append(line)

            clean_content = "\n".join(filtered_lines).strip()

            if clean_content:
                drug_text += f"--- {section_title} ---\n"
                drug_text += f"{clean_content}\n\n"

        parts.append(drug_text)

    return "\n".join(parts)


def format_drug_list(drugs: list[dict]) -> str:
    """
    Форматирование списка препаратов в читаемый текст.
    """
    if not drugs:
        return "Препараты не найдены."

    parts = []
    for i, drug in enumerate(drugs, 1):
        trade_name = drug.get("trade_name", "Неизвестный")
        generic_name = drug.get("generic_name", "-")
        drug_class = drug.get("drug_class", "-")
        dosage_form = drug.get("dosage_form", "-")
        route = drug.get("route", "-")
        target_animals = drug.get("target_animals", [])
        manufacturer = drug.get("manufacturer", "-")

        animals_str = (
            ", ".join(target_animals)
            if isinstance(target_animals, list)
            else target_animals
        )

        drug_text = f"{i}. {trade_name}\n"
        drug_text += f"   Действующее вещество: {generic_name}\n"
        drug_text += f"   Класс: {drug_class}\n"
        drug_text += f"   Форма: {dosage_form}\n"
        drug_text += f"   Способ применения: {route}\n"
        drug_text += f"   Животные: {animals_str}\n"
        drug_text += f"   Производитель: {manufacturer}\n"

        parts.append(drug_text)

    return "\n".join(parts)


def build_drug_summary_list(chunks: list[dict]) -> str:
    """
    Строит краткий список уникальных препаратов из чанков для отображения при overflow.
    """
    if not chunks:
        return "Препараты не найдены."

    drugs_seen = {}
    for chunk in chunks:
        trade_name = chunk.get("trade_name", "Неизвестный")
        if trade_name not in drugs_seen:
            drugs_seen[trade_name] = {
                "generic_name": chunk.get("generic_name", "-"),
                "drug_class": chunk.get("drug_class", "-"),
                "target_animals": chunk.get("target_animals", []),
            }

    parts = []
    for i, (trade_name, data) in enumerate(drugs_seen.items(), 1):
        animals_str = (
            ", ".join(data["target_animals"])
            if isinstance(data["target_animals"], list)
            else str(data["target_animals"])
        )
        parts.append(
            f"{i}. {trade_name} ({data['generic_name']}) — {data['drug_class']}"
            + (
                f", животные: {animals_str}"
                if animals_str and animals_str != "-"
                else ""
            )
        )

    return (
        f"Найдено {len(drugs_seen)} препаратов. "
        "Уточните запрос или выберите конкретный препарат:\n\n" + "\n".join(parts)
    )


def fix_broken_tool_call(message):
    """Исправляет кривой вызов инструмента, перенося параметры из content в arguments."""
    if not message.tool_calls or not message.content:
        return message

    tool_call = message.tool_calls[0]

    try:
        if json.loads(tool_call.function.arguments):
            return message
    except json.JSONDecodeError:
        pass

    tool_call.function.arguments = (
        message.content + tool_call.function.arguments
    ).strip()
    message.content = ""

    return message
