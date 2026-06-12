import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

SOURCE_DOCUMENT = 'Современное свиноводство'
KNOWLEDGE_PATH = 'knowledge/data/modern_pig_farming'
IMAGES_PATH = 'knowledge/data/modern_pig_farming/images'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'modern pig farming.json'
)

EXCLUDED_PAGES = []

CHAPTERS = {
    (0, 18): 'Оборудование свиноводческих ферм',
    (18, 32): 'Кормление',
    (32, 44): 'Ремонт поголовья и осеменение',
}
