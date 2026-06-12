"""
Скрипт извлекает изображения из Antimicrobial Therapy in Veterinary Medicine, 5th Edition.json
и сохраняет изображения в .jpeg
"""

import os

from knowledge.utils.vsegpt_pdf_ocr_utils import handle_images_from_json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SOURCE_DOCUMENT = "Antimicrobial Therapy in Veterinary Medicine, 5th Edition"
KNOWLEDGE_HANDBOOK_PATH = 'knowledge/data/antimicrobial_therapy_handbook'
JSON_HANDBOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_HANDBOOK_PATH,
    f'{SOURCE_DOCUMENT}.json'
)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, KNOWLEDGE_HANDBOOK_PATH, 'parsed_images')

if __name__ == '__main__':
    handle_images_from_json(JSON_HANDBOOK, OUTPUT_DIR)
