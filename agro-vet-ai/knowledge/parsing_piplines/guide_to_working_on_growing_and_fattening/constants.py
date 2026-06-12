import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

SOURCE_DOCUMENT = 'Руководство по работе на доращивании и откорме'
KNOWLEDGE_PATH = 'knowledge/data/guide_to_working_on_growing_and_fattening'
JSON_BOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_PATH,
    'RUS_Руководство_по_работе_на_доращивании_и_откорме_PIC_2019.json'
)

IMAGES_PATH = os.path.join(KNOWLEDGE_PATH, 'parsed_images')

EXCLUDED_PAGES = [*range(0, 5), 50, *range(55, 57)]
CHAPTERS = {
    (4, 6): 'Раздел 1: Производственные цели PIC',
    (6, 12): 'Раздел 2: Корм',
    (12, 15): 'Раздел 3: Вод',
    (15, 24): 'Раздел 4: Микроклимат',
    (24, 28): 'Раздел 5: Плотность посадки и планирование размещения животных',
    (28, 36): 'Раздел 6: Работа с отъемными поросятами',
    (36, 40): 'Раздел 7: Стандартные процедуры ухода за животными',
    (40, 45): 'Раздел 8: Рекомендации по перевозке животных',
    (45, 55): 'Приложения',
}
