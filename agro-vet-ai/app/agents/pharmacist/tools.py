from typing import Optional
from langchain_core.tools import tool
from app.agents.pharmacist.searching_engine import DrugSearchEngine
from app.agents.pharmacist.utils import format_drug_chunks, build_drug_summary_list
from config.config import Config

cfg = Config.from_yaml()
_search_engine = DrugSearchEngine()


@tool(parse_docstring=True)
def search_by_trade_name(
    trade_name: str,
    section_type: Optional[str] = None
) -> dict:
    """
    Поиск информации о препарате по торговому названию.

    КОГДА ИСПОЛЬЗОВАТЬ:
    - Пользователь спрашивает о конкретном препарате по названию
    - Примеры: "Расскажи про Тиланик", "Дозировка Байтрила", "Противопоказания Энрофлона"

    Args:
        trade_name: Торговое название препарата (или его часть, например "Тиланик", "Байтрил", "Энро")
        section_type: Фильтр по типу секции инструкции. Возможные значения:
                      indications (показания к применению), dosing (режим дозирования),
                      contraindications (противопоказания), properties (фармакологические свойства),
                      composition (состав и форма выпуска), special_notes (особые указания),
                      storage (условия хранения), advantages (преимущества),
                      side_effects (побочные эффекты), interactions (взаимодействия),
                      overdose (передозировка)
    """
    matching_drugs = _search_engine.find_drugs_by_name(trade_name)

    if not matching_drugs:
        return {
            "text": f"Препараты с названием похожим на '{trade_name}' не найдены в базе данных.",
            "documents": []
        }

    # Точное совпадение или единственный результат
    exact_match = None
    for drug in matching_drugs:
        if drug['trade_name'].lower() == trade_name.lower():
            exact_match = drug
            break

    if exact_match or len(matching_drugs) == 1:
        selected = exact_match or matching_drugs[0]
        selected_name = selected['trade_name']
        section_types = [section_type] if section_type else None

        if section_types:
            chunks = _search_engine.get_drug_sections(selected_name, section_types)
        else:
            chunks = _search_engine.query_executor.get_all_chunks_for_drug(selected_name)

        if not chunks:
            return {
                "text": f"Информация о препарате '{selected_name}' не найдена.",
                "documents": []
            }

        formatted_text = format_drug_chunks(chunks)
        return {
            "text": formatted_text,
            "documents": chunks
        }

    # Несколько совпадений — требуется уточнение
    drugs_list = []
    for drug in matching_drugs:
        generic = f" ({drug['generic_name']})" if drug.get('generic_name') else ""
        drugs_list.append(f"- {drug['trade_name']}{generic}")

    clarification_text = (
        f"По запросу '{trade_name}' найдено несколько препаратов. "
        f"Уточните, какой именно препарат вас интересует:\n\n"
        + "\n".join(drugs_list)
    )

    return {
        "text": clarification_text,
        "documents": matching_drugs
    }


@tool(parse_docstring=True)
def search_by_active_substance(
    generic_name: str,
    animal: Optional[str] = None,
    section_type: Optional[str] = None
) -> dict:
    """
    Поиск препаратов по действующему веществу (МНН / generic name).

    КОГДА ИСПОЛЬЗОВАТЬ:
    - Пользователь спрашивает о препаратах с определённым действующим веществом
    - Примеры: "Препараты с энрофлоксацином", "Кетопрофен для КРС", "Тилозин для свиней"

    Args:
        generic_name: Название действующего вещества / МНН (например, "энрофлоксацин", "тилозин", "кетопрофен")
        animal: Фильтр по виду животного (например, "свиньи", "КРС", "куры"). Передавай только если пользователь явно указал вид.
        section_type: Фильтр по типу секции инструкции. Возможные значения:
                      indications, dosing, contraindications, properties,
                      composition, special_notes, storage, advantages,
                      side_effects, interactions, overdose
    """
    section_types = [section_type] if section_type else None

    chunks = _search_engine.search_by_generic_name(
        generic_name=generic_name,
        animal=animal,
        section_types=section_types,
        limit=cfg.pharmacist.search.chunk_limit
    )

    if not chunks:
        return {
            "text": f"Препараты с действующим веществом '{generic_name}' не найдены.",
            "documents": []
        }

    # Проверяем overflow
    unique_drugs = set(c.get('trade_name') for c in chunks)
    if len(unique_drugs) > cfg.pharmacist.search.overflow_threshold:
        summary = build_drug_summary_list(chunks)
        return {
            "text": summary,
            "documents": chunks
        }

    formatted_text = format_drug_chunks(chunks)
    return {
        "text": formatted_text,
        "documents": chunks
    }


@tool(parse_docstring=True)
def search_by_conditions(
    query: str,
    animal: Optional[str] = None,
    section_type: Optional[str] = None,
    drug_class: Optional[str] = None
) -> dict:
    """
    Поиск препаратов по условиям применения, заболеваниям, симптомам.

    Использует семантический поиск (FTS + vector + RRF fusion).

    КОГДА ИСПОЛЬЗОВАТЬ:
    - Пользователь описывает ситуацию, заболевание, симптомы
    - Нужно найти препараты для лечения чего-либо
    - Примеры: "Антибиотики для свиней при респираторных заболеваниях",
               "Чем лечить кокцидиоз у кур", "Противовоспалительные для КРС"

    Args:
        query: Текстовый запрос (заболевание, симптомы, условия применения)
        animal: Фильтр по виду животного (например, "свиньи", "КРС", "куры"). Передавай только если пользователь явно указал.
        section_type: Фильтр по типу секции. Возможные значения:
                      indications, dosing, contraindications, properties,
                      composition, special_notes, storage
        drug_class: Фильтр по классу препаратов (например, "Антибактериальные препараты")
    """
    # Строим metadata_filters из аргументов
    metadata_filters = {}
    if animal:
        metadata_filters['target_animals'] = [animal]
    if drug_class:
        metadata_filters['drug_class'] = [drug_class]

    section_types = [section_type] if section_type else None

    chunks = _search_engine.search_drugs(
        query=query,
        section_types=section_types,
        limit=cfg.pharmacist.search.chunk_limit,
        threshold=cfg.pharmacist.search.similarity_threshold,
        metadata_filters=metadata_filters if metadata_filters else None,
    )

    if not chunks:
        return {
            "text": "По вашему запросу препараты не найдены.",
            "documents": []
        }

    # Проверяем overflow
    unique_drugs = set(c.get('trade_name') for c in chunks)
    if len(unique_drugs) > cfg.pharmacist.search.overflow_threshold:
        summary = build_drug_summary_list(chunks)
        return {
            "text": summary,
            "documents": chunks
        }

    formatted_text = format_drug_chunks(chunks)
    return {
        "text": formatted_text,
        "documents": chunks
    }


@tool(parse_docstring=True)
def get_drug_full_info(trade_name: str) -> dict:
    """
    Получение ПОЛНОЙ инструкции по препарату в виде файла.

    КОГДА ИСПОЛЬЗОВАТЬ:
    - Пользователь явно просит "полную инструкцию", "всю инструкцию", "весь документ"
    - Примеры: "Дай полную инструкцию Тиланик", "Скинь инструкцию целиком",
               "Отправь инструкцию по препарату Флорикол"

    КОГДА НЕ ИСПОЛЬЗОВАТЬ (используй search_by_trade_name):
    - Вопросы о конкретных разделах: дозировка, противопоказания, показания

    Возвращает ФАЙЛ, без текста в чате.

    Args:
        trade_name: Торговое название препарата
    """
    matching_drugs = _search_engine.find_drugs_by_name(trade_name)

    if not matching_drugs:
        return {
            "text": f"Препараты с названием похожим на '{trade_name}' не найдены в базе данных.",
            "documents": [],
            "file_request": None,
        }

    # Точное совпадение или единственный результат
    exact_match = None
    for drug in matching_drugs:
        if drug['trade_name'].lower() == trade_name.lower():
            exact_match = drug
            break

    if exact_match or len(matching_drugs) == 1:
        selected = exact_match or matching_drugs[0]
        selected_name = selected['trade_name']

        md_content = _search_engine.get_drug_instruction_as_markdown(selected_name)
        if not md_content:
            return {
                "text": f"Не удалось сформировать инструкцию для препарата '{selected_name}'.",
                "documents": [],
                "file_request": None,
            }

        return {
            "text": f"Файл с полной инструкцией препарата '{selected_name}' будет отправлен пользователю.",
            "documents": [],
            "file_request": {
                "trade_name": selected_name,
                "file_content": md_content,
                "file_extension": ".md"
            },
        }

    # Несколько совпадений
    drugs_list = []
    for drug in matching_drugs:
        generic = f" ({drug['generic_name']})" if drug.get('generic_name') else ""
        drugs_list.append(f"- {drug['trade_name']}{generic}")

    return {
        "text": (
            f"По запросу '{trade_name}' найдено несколько препаратов. "
            f"Уточните, по какому именно препарату нужна инструкция:\n\n"
            + "\n".join(drugs_list)
        ),
        "documents": matching_drugs,
        "file_request": None,
    }
