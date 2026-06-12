import os

from knowledge.parsing_piplines.poultry_health_guide.constants import PROJECT_ROOT, KNOWLEDGE_PATH, JSON_BOOK
from knowledge.utils.vsegpt_pdf_ocr_utils import handle_images_from_json


OUTPUT_DIR = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'parsed_images')

if __name__ == '__main__':
    handle_images_from_json(JSON_BOOK, OUTPUT_DIR)
