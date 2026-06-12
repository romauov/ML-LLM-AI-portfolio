import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

SOURCE_DOCUMENT = "Статьи ГК ВИК (Свиноводство)"
KNOWLEDGE_PATH = 'knowledge/data/vic_articles_swine'
JSON_ARTICLES = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'vicgroup_articles.json'
)
IMAGES_PATH = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'images')
