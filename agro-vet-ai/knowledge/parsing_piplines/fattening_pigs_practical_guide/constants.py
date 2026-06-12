import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

SOURCE_DOCUMENT = 'Откорм свиней. Практическое руководство по росту, здоровью и поведению животных'
KNOWLEDGE_PATH = 'knowledge/data/fattening_pigs_practical_guide/'
IMAGES_PATH = 'knowledge/data/fattening_pigs_practical_guide/images'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'Откорм свиней.json'
)

EXCLUDED_PAGES = [
    1,
]

CHAPTERS = {
    (2, 4): 'Предисловие',
    (4, 20): 'Хорошая подготовка',
    (20, 34): 'Оптимальный рост',
    (34, 46): 'Финишный рывок',
}
