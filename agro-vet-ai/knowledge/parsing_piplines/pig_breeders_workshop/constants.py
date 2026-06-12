import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

SOURCE_DOCUMENT = 'Практикум свиновода. Наблюдай и действуй!'
KNOWLEDGE_PATH = 'knowledge/data/pig_breeders_workshop/'
IMAGES_PATH = 'knowledge/data/pig_breeders_workshop/images'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'Практикум свиновода.json'
)

EXCLUDED_PAGES = [
    *range(0, 4),
    *range(95, 97),
]

CHAPTERS = {
    (4, 6): 'ВВЕДЕНИЕ',
    (6, 20): '1. Развитие навыков наблюдательности',
    (20, 30): '2. Супоросность',
    (30, 52): '3. В помещении для опороса',
    (52, 74): '4. Осеменение',
    (74, 86): '6. Свиньи в заключительной стадии откорма',
    (86, 95): '7. Уход за свиньями и лечение',
}
