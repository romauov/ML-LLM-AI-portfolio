import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = (
    "Биология и патология сельскохозяйственной птицы"
)
KNOWLEDGE_PATH = 'knowledge/data/birds_biology_and_pathology'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    f'Кочиш И.И. {SOURCE_DOCUMENT}.json'
)

IMAGES_PATH = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'parsed_images')

CHAPTERS = {
    (9, 37): 'ГЕНЕТИКА ПТИЦЫ',
    (36, 77): 'КОНСТИТУЦИЯ, ЭКСТЕРЬЕР И ИНТЕРЬЕР ПТИЦЫ',
    (76, 200): 'АНАТОМИЯ И ФИЗИОЛОГИЯ ПТИЦЫ',
    (200, 323): 'ЭТОЛОГИЯ ПТИЦЫ',
    (322, 549): 'ПАТОЛОГИЯ ПТИЦЫ'
}

EXCLUDED_PAGES = [*range(1, 9), *range(549, 552)]