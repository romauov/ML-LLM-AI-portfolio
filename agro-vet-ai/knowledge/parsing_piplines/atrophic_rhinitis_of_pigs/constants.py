import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = 'Атрофический ринит свиней'
KNOWLEDGE_PATH = 'knowledge/data/atrophic_rhinitis_of_pigs'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'атрофический ренит.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [
    *range(11, 14),
]

CHAPTERS = {
    (1, 2): 'РЕЗЮМЕ',
    (2, 3): 'ВВЕДЕНИЕ',
    (3, 7): 'ДИАГНОСТИЧЕСКИЕ МЕТОДЫ',
    (7, 11): 'ТРЕБОВАНИЯ К ВАКЦИНАМ',
}
