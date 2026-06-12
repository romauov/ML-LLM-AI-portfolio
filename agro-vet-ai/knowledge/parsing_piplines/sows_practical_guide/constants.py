import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = 'Свиноматки. Практическое руководство по менеджменту лактационного периода и продуктивности свиноматок'
KNOWLEDGE_PATH = 'knowledge/data/sows_practical_guide'
IMAGES_PATH = 'knowledge/data/sows_practical_guide/images'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'Книга свиноматки crop.json'
)

EXCLUDED_PAGES = [
    *range(0, 4),
    *range(48, 51),
]

CHAPTERS = {
    (4, 6): 'Предисловие',
    (6, 14): '1 Свиноматка на площадке',
    (14, 22): '2 Опорос и подсосный период',
    (22, 32): '3 В преддверии следующего опороса',
    (32, 40): '4 Супоросная свиноматка',
    (40, 48): '5 Ремонтные свинки - будущее хозяйства',
}
