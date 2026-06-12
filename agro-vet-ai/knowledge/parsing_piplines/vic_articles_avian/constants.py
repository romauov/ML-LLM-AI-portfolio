import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

SOURCE_DOCUMENT = "Статьи ГК ВИК (Птицеводство)"
KNOWLEDGE_PATH = 'knowledge/data/vic_articles_avian'
JSON_ARTICLES = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'vicgroup_articles.json'
)
IMAGES_PATH = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'images')

# Статья с аномально большим контентом (~687K символов).
# Задаём порог: статьи с content > MAX_CONTENT_CHARS будут пропущены с предупреждением.
MAX_CONTENT_CHARS = 200_000
