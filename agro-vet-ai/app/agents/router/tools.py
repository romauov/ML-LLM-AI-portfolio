import json

from langchain_core.tools import tool

from app.db.vector_search import VectorSearchEngine
from app.topics.questions.swine_diagnosis.topic_handler import SwineDiseasesDiagnosis
from app.topics.questions.avian_diagnosis.topic_handler import AvianDiseasesDiagnosis
from app.topics.questions.drug_instruction import DrugInstruction
from app.topics.questions.pcr_test_interpretation import PcrTestInterpretation
from app.topics.questions.elisa_test_interpretation import ElisaTestInterpretation
from app.topics.questions.librarian import Librarian
from app.topics.questions.pharmacist import Pharmacist
from app.topics.questions.combined_general import CombinedGeneral

ALL_BOOKS_NAME = '\n'.join(VectorSearchEngine().get_all_book_names())
librarian_tool_description = f"""Search veterinary books and scientific literature.

Use this tool when:
- The user EXPLICITLY says "в книгах", "в учебнике", "в литературе", "в научной литературе", "по книгам", "поищи в книгах"
- The question is about a disease TREATMENT PROTOCOL or APPROACH (not a specific drug)
- The question is about disease mechanisms, pathogenesis, epidemiology, clinical signs
- The question asks what medications/substances are GENERALLY used for a disease (without specifying a trade name)
- The question requires synthesis of veterinary knowledge from scientific sources
- The question is about vaccination schemes, biosecurity, prevention measures

DO NOT use for:
- Questions about a SPECIFIC drug by its trade name (use process_with_pharmacist instead)
- Follow-up questions about drugs already mentioned in the dialog

Available books:
{ALL_BOOKS_NAME}

Args:
    question: Question to search in veterinary literature and books.
"""

pharmacist_tool_description = """Search the veterinary drug database (drug instructions and catalog).

Use this tool when the user asks about a SPECIFIC, NAMED drug:
- A drug by its TRADE NAME ("Байтрил", "Тиланик", "Энрофлон", etc.)
- A drug by its ACTIVE INGREDIENT / INN ("энрофлоксацин", "тилозин", "амоксициллин")
- DOSAGE, route of administration, withdrawal period for a specific named drug
- CONTRAINDICATIONS or SIDE EFFECTS of a specific named drug
- INTERACTIONS or COMPATIBILITY of specific named drugs
- Follow-up questions about drugs already discussed ("Кто производитель?", "А дозировка?", "Для каких животных?")

DO NOT use for:
- Questions explicitly about books or literature (use process_with_librarian instead)
- General questions like "what drugs are used for [disease]" without specifying a drug name (use process_with_librarian instead)
- If process_with_librarian was already called in this session — do NOT call pharmacist additionally

Args:
    question: Question about a specific named veterinary drug, its dosages, usage, instructions.
"""


@tool(parse_docstring=True)
def process_with_avian_disease_diagnosis(question: str) -> str:
    """
    Process a question using the avian disease diagnosis handler.

    Args:
        question: Question about bird diseases, symptoms, diagnosis.
    """
    handler = AvianDiseasesDiagnosis()
    result = handler.process(question)
    # Return JSON with content and context
    return json.dumps({
        "content": result.get("content", ""),
        "context": result.get("context", "")
    }, ensure_ascii=False)


@tool(parse_docstring=True)
def process_with_swine_disease_diagnosis(question: str) -> str:
    """
    Process a question using the swine disease diagnosis handler.

    Args:
        question: Question about pig diseases, symptoms, diagnosis.
    """
    handler = SwineDiseasesDiagnosis()
    result = handler.process(question)
    # Return JSON with content and context
    return json.dumps({
        "content": result.get("content", ""),
        "context": result.get("context", "")
    }, ensure_ascii=False)


@tool(parse_docstring=True)
def process_with_drug_instruction(question: str) -> str:
    """
    Process a question using the drug instruction handler.

    Args:
        question: Question about veterinary drugs, dosages, usage.
    """
    handler = DrugInstruction()
    result = handler.process(question)
    # Return JSON with content and context
    return json.dumps({
        "content": result.get("content", ""),
        "context": result.get("context", "")
    }, ensure_ascii=False)


@tool(parse_docstring=True)
def process_with_pcr_test_interpretation(question: str, file_path: str = None) -> str:
    """
    Process a question using the PCR test interpretation handler.
    
    Args:
        question: Question about PCR test results, interpretation.
        file_path: Path to an optional file to be processed with the question.
    """
    handler = PcrTestInterpretation()
    result = handler.process(question, file_path=file_path)
    return result["content"]


@tool(parse_docstring=True)
def process_with_elisa_test_interpretation(question: str, file_path: str = None) -> str:
    """
    Process a question using the ELISA test interpretation handler.
    
    Args:
        question: Question about ELISA test results, interpretation.
        file_path: Path to an optional file to be processed with the question.
    """
    handler = ElisaTestInterpretation()
    result = handler.process(question, file_path=file_path)
    return result["content"]


@tool(description=librarian_tool_description)
def process_with_librarian(question: str) -> str:
    handler = Librarian()
    result = handler.process(question)
    return json.dumps({
        "content": result.get("content", ""),
        "context": result.get("context", ""),
        "context_images": result.get("context_images"),
    }, ensure_ascii=False)


@tool(description=pharmacist_tool_description)
def process_with_pharmacist(question: str, dialog_history: list[dict[str, str]] = None, context: dict = None) -> str:
    handler = Pharmacist()
    result = handler.process(question, dialog_history=dialog_history, context=context)
    return json.dumps({
        "content": result.get("content", ""),
        "context": result.get("context", ""),
        "context_images": result.get("context_images"),
        "file_requests": result.get("file_requests", []),
    }, ensure_ascii=False)


@tool(parse_docstring=True)
def process_with_combined_general(question: str) -> str:
    """
    Process a question using the combined general handler.
    
    Args:
        question: General veterinary question, capabilities question, or chatter.
    """
    handler = CombinedGeneral()
    result = handler.process(question)
    return result["content"]
