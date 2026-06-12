import json

from langchain_core.tools import tool

from app.db.vector_search import VectorSearchEngine
from app.topics.questions.swine_diagnosis.topic_handler import SwineDiseasesDiagnosis
from app.topics.questions.avian_diagnosis.topic_handler import AvianDiseasesDiagnosis
from app.topics.questions.drug_instruction import DrugInstruction
from app.topics.questions.pcr_test_interpretation import PcrTestInterpretation
from app.topics.questions.elisa_test_interpretation import ElisaTestInterpretation


ALL_BOOKS_NAME = "\n".join(VectorSearchEngine().get_all_book_names())


@tool(parse_docstring=True)
def process_with_avian_disease_diagnosis(question: str) -> str:
    """
    Process a question using the avian disease diagnosis handler.

    Args:
        question: Question about bird diseases, symptoms, diagnosis.
    """
    handler = AvianDiseasesDiagnosis()
    result = handler.process(question)
    return json.dumps(
        {"content": result.get("content", ""), "context": result.get("context", "")},
        ensure_ascii=False,
    )


@tool(parse_docstring=True)
def process_with_swine_disease_diagnosis(question: str) -> str:
    """
    Process a question using the swine disease diagnosis handler.

    Args:
        question: Question about pig diseases, symptoms, diagnosis.
    """
    handler = SwineDiseasesDiagnosis()
    result = handler.process(question)
    return json.dumps(
        {"content": result.get("content", ""), "context": result.get("context", "")},
        ensure_ascii=False,
    )


@tool(parse_docstring=True)
def process_with_drug_instruction(question: str) -> str:
    """
    Process a question using the drug instruction handler.

    Args:
        question: Question about veterinary drugs, dosages, usage.
    """
    handler = DrugInstruction()
    result = handler.process(question)
    return json.dumps(
        {"content": result.get("content", ""), "context": result.get("context", "")},
        ensure_ascii=False,
    )


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
