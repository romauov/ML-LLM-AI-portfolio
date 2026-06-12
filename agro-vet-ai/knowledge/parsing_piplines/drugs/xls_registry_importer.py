"""
Импорт препаратов из XLS-реестра в таблицу drugs_chunks.

Читает файл из реестра "Гален" ветеринарных препаратов (.xls),
создаёт чанки по разделам инструкции и добавляет их в drugs_chunks
(не заменяет существующие данные, только дополняет).

Использование:
    python -m knowledge.parsing_piplines.drugs.xls_registry_importer
    python -m knowledge.parsing_piplines.drugs.xls_registry_importer --xls path/to/file.xls
    python -m knowledge.parsing_piplines.drugs.xls_registry_importer --dry-run
"""

import argparse
import re
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для импорта app.*
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import xlrd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.sqlalchemy_models import DrugChunk
from app.utils.logger import get_logger
from app.utils.settings import secrets as s


def build_db_url() -> str:
    """Подключение через проброшенный порт (localhost)"""
    return (
        f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
        f"@localhost:{s.db_port_host}/{s.postgres_db}"
    )


logger = get_logger(__name__)

# URL источника для всех чанков из реестра
REGISTRY_SOURCE_URL = 'https://galen.vetrf.ru/'

# Максимальный размер чанка
MAX_CHUNK_SIZE = 2000

# Маппинг ключевых слов в лекарственной форме → route.
# Порядок важен: более специфичные ключевые слова идут первыми.
# Одна форма может дать несколько маршрутов (через "/").
ROUTE_KEYWORD_MAP = [
    # Специфичные пути введения
    ('интрацистернальн',      'интрацистернально'),
    ('интерцистернальн',      'интрацистернально'),   # опечатка в реестре
    ('внутриматочн',          'внутриматочно'),
    ('интраутераль',          'внутриматочно'),
    ('внутривенн',            'внутривенно'),
    ('подкожн',               'подкожно'),
    ('внутрикожн',            'внутрикожно'),
    ('внутримышечн',          'внутримышечно'),
    ('интраназальн',          'интраназально'),
    ('аурикулярн',            'ушной'),
    ('ушн',                   'ушной'),
    ('глазн',                 'глазной'),
    ('окулярн',               'глазной'),
    ('клоачн',                'клоачно'),
    ('аэрозол',               'аэрозольно'),
    ('ингаляц',               'ингаляционно'),
    ('крупнодисперсного',     'аэрозольно'),
    ('термовозгон',           'аэрозольно'),
    # Инъекции (общие, после специфичных выше)
    ('инъекц',                'инъекционно'),
    ('иньекц',                'инъекционно'),   # опечатка в реестре
    ('итраназальн',           'интраназально'),  # опечатка в реестре
    ('для введения',          'инъекционно'),
    ('вагинальн',             'вагинально'),
    ('in ovo',                'in ovo'),
    ('in-ovo',                'in ovo'),
    # Пероральные
    ('ораль',                 'перорально'),
    ('приема внутрь',         'перорально'),
    ('приёма внутрь',         'перорально'),
    ('пероральн',             'перорально'),
    ('выпаивани',             'перорально'),
    ('энтераль',              'перорально'),
    ('таблетк',               'перорально'),
    ('капсул',                'перорально'),
    ('жидкость для приема',   'перорально'),
    ('приманк',               'перорально'),
    ('брикет',                'перорально'),
    # Наружные
    ('наружн',                'наружно'),
    ('местн',                 'местно'),
    ('шампунь',               'наружно'),
    ('пластин',               'наружно'),
    ('лента',                 'наружно'),
    ('ошейник',               'наружно'),
    ('мазь',                  'наружно'),
    ('настойк',               'перорально'),
    ('спрей',                 'спрей'),
    ('санаци',                'наружно'),
]


def normalize_trade_name(name: str) -> str:
    """
    Нормализация торгового названия для сравнения:
    убирает LaTeX-артефакты, знаки ®/™, лишние пробелы, приводит к нижнему регистру.
    """
    s = re.sub(r'\$[^$]*\$', '', name)          # $...$
    s = re.sub(r'[^\w\s%.,/-]', '', s)           # спецсимволы кроме буквенных
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()


def infer_route(dosage_form: str) -> str | None:
    """
    Определение пути введения по лекарственной форме.

    Args:
        dosage_form: Лекарственная форма из реестра

    Returns:
        Строка с путём/путями введения или None
    """
    form_lower = dosage_form.lower()
    found: list[str] = []
    seen: set[str] = set()

    for keyword, route in ROUTE_KEYWORD_MAP:
        if keyword in form_lower and route not in seen:
            found.append(route)
            seen.add(route)

    return ' / '.join(found) if found else None

# Минимальная длина содержимого секции для включения в чанки
MIN_SECTION_LENGTH = 30

# Ключевые слова для определения целевых животных
ANIMAL_KEYWORDS = {
    'свинь': 'свиньи',
    'поросён': 'свиньи',
    'поросят': 'свиньи',
    'хряк': 'свиньи',
    'свиноматк': 'свиньи',
    'птиц': 'птица',
    'цыплёнок': 'птица',
    'цыплят': 'птица',
    'бройлер': 'птица',
    'курьи': 'птица',
    ' куры': 'птица',
    ' кур ': 'птица',
    'индейк': 'птица',
    'утк': 'птица',
    'гусей': 'птица',
    'крупный рогатый скот': 'КРС',
    ' крс': 'КРС',
    'теленк': 'КРС',
    'коров': 'КРС',
    'нетел': 'КРС',
    'бык': 'КРС',
    'овц': 'овцы',
    'ягнят': 'овцы',
    ' коз': 'козы',
    'козл': 'козы',
    'собак': 'собаки',
    ' пёс': 'собаки',
    ' псов': 'собаки',
    'кошк': 'кошки',
    'котёнок': 'кошки',
    'котят': 'кошки',
    'кролик': 'кролики',
    'лошад': 'лошади',
    'жеребён': 'лошади',
    ' рыб': 'рыба',
    'пчёл': 'пчёлы',
    'пчел': 'пчёлы',
}


def extract_target_animals(text: str) -> list[str]:
    """
    Извлечение целевых животных из текста показаний к применению.

    Args:
        text: Текст показаний к применению

    Returns:
        Список найденных видов животных (без дублей)
    """
    text_lower = text.lower()
    found = set()
    for keyword, animal in ANIMAL_KEYWORDS.items():
        if keyword in text_lower:
            found.add(animal)
    return sorted(found) if found else []


def split_long_text(text: str, section_title: str) -> list[str]:
    """
    Разбиение длинного текста на чанки по аналогии с DrugChunker.

    Args:
        text: Текст для разбиения
        section_title: Заголовок секции

    Returns:
        Список чанков в markdown-формате
    """
    header = f"### {section_title}\n\n---\n\n"

    # Если вмещается в один чанк
    if len(header + text) <= MAX_CHUNK_SIZE:
        return [header + text]

    # Разбиваем по абзацам
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        candidate = (current + '\n\n' + para) if current else para
        if len(header + candidate) <= MAX_CHUNK_SIZE:
            current = candidate
        else:
            if current:
                chunks.append(header + current)
            current = para

    if current:
        chunks.append(header + current)

    return chunks if chunks else [header + text[:MAX_CHUNK_SIZE - len(header)]]


def clean_manufacturer(raw: str) -> str:
    """
    Очистка строки производителя — берём первую значимую строку.

    Args:
        raw: Сырое значение из XLS

    Returns:
        Очищенное название производителя
    """
    # Разбиваем по переводам строки, берём первую непустую часть
    parts = [p.strip() for p in raw.replace('\r', '\n').split('\n') if p.strip()]
    return parts[0] if parts else raw.strip()


def clean_drug_class(raw: str) -> str:
    """
    Очистка фармакотерапевтической группы — убираем АТХ-коды в скобках.

    Args:
        raw: Сырое значение из XLS

    Returns:
        Очищённое название группы
    """
    # Убираем содержимое скобок с кодами типа (QA01AB12)
    cleaned = re.sub(r'\s*\([A-Z0-9]+\)', '', raw).strip()
    # Берём первую часть если разделено переносами
    parts = [p.strip() for p in cleaned.split('\n') if p.strip()]
    return parts[0] if parts else cleaned


def row_to_chunks(row_data: dict, source_file: str) -> list[dict]:
    """
    Преобразование строки реестра в список чанков для drugs_chunks.

    Args:
        row_data: Словарь с данными строки реестра
        source_file: Имя исходного файла

    Returns:
        Список словарей-чанков для вставки в БД
    """
    trade_name = row_data['trade_name']
    generic_name = row_data.get('generic_name') or None
    manufacturer = clean_manufacturer(row_data.get('manufacturer', ''))
    dosage_form = row_data.get('dosage_form') or None
    route = infer_route(row_data.get('dosage_form', ''))
    drug_class = clean_drug_class(row_data.get('drug_class', '')) or None
    indications_text = row_data.get('indications', '').strip()
    target_animals = extract_target_animals(indications_text)

    chunks = []

    # Определяем секции для обработки
    sections = [
        ('composition', 'Состав и форма выпуска', row_data.get('composition', '')),
        ('indications', 'Показания к применению', row_data.get('indications', '')),
        ('contraindications', 'Противопоказания', row_data.get('contraindications', '')),
        ('storage', 'Условия и сроки хранения', _combine_storage(
            row_data.get('shelf_life', ''),
            row_data.get('storage_conditions', '')
        )),
        ('side_effects', 'Побочные действия', row_data.get('side_effects', '')),
    ]

    for section_type, section_title, content in sections:
        content = content.strip()
        if len(content) < MIN_SECTION_LENGTH:
            continue

        text_chunks = split_long_text(content, section_title)
        for chunk_content in text_chunks:
            chunks.append({
                'source_file': source_file,
                'content': chunk_content,
                'generic_name': generic_name,
                'trade_name': trade_name,
                'manufacturer': manufacturer or None,
                'dosage_form': dosage_form,
                'route': route,
                'drug_class': drug_class,
                'target_animals': target_animals or None,
                'section_type': section_type,
                'section_title': section_title,
                'source_url': REGISTRY_SOURCE_URL,
            })

    return chunks


def _combine_storage(shelf_life: str, storage_conditions: str) -> str:
    """
    Объединение срока годности и условий хранения в один текст.

    Args:
        shelf_life: Срок годности
        storage_conditions: Условия хранения

    Returns:
        Объединённый текст
    """
    parts = []
    if storage_conditions.strip():
        parts.append(f"Хранят {storage_conditions.strip()}")
    if shelf_life.strip():
        parts.append(f"Срок годности: {shelf_life.strip()}")
    return ' '.join(parts)


def read_registry(xls_path: str) -> list[dict]:
    """
    Чтение реестра из XLS-файла.

    Args:
        xls_path: Путь к XLS-файлу

    Returns:
        Список словарей с данными препаратов
    """
    wb = xlrd.open_workbook(xls_path)
    ws = wb.sheet_by_index(0)

    logger.info(f"Открыт файл: {xls_path}")
    logger.info(f"Строк: {ws.nrows - 1}")

    rows = []
    for i in range(1, ws.nrows):
        row = {
            'trade_name': str(ws.cell_value(i, 1)).strip(),
            'generic_name': str(ws.cell_value(i, 2)).strip(),
            'manufacturer': str(ws.cell_value(i, 5)).strip(),
            'indications': str(ws.cell_value(i, 6)).strip(),
            'dosage_form': str(ws.cell_value(i, 7)).strip(),
            'drug_class': str(ws.cell_value(i, 8)).strip(),
            'composition': str(ws.cell_value(i, 9)).strip(),
            'contraindications': str(ws.cell_value(i, 10)).strip(),
            'shelf_life': str(ws.cell_value(i, 11)).strip(),
            'storage_conditions': str(ws.cell_value(i, 12)).strip(),
            'side_effects': str(ws.cell_value(i, 17)).strip(),
            'status': str(ws.cell_value(i, 24)).strip(),
        }

        # Пропускаем строки без торгового наименования
        if not row['trade_name']:
            continue

        rows.append(row)

    logger.info(f"Прочитано строк: {len(rows)}")
    return rows


def import_registry(
    xls_path: str = 'knowledge/data/drugs/registry_pharm_2026_03_26.xls',
    dry_run: bool = False,
    batch_size: int = 100,
):
    """
    Основная функция импорта реестра в drugs_chunks.

    Args:
        xls_path: Путь к XLS-файлу реестра
        dry_run: Если True — только считает чанки, не вставляет в БД
        batch_size: Размер батча для commit
    """
    logger.info("=" * 80)
    logger.info("ИМПОРТ РЕЕСТРА ВЕТЕРИНАРНЫХ ПРЕПАРАТОВ")
    logger.info("=" * 80)

    source_file = Path(xls_path).name

    # 1. Чтение реестра
    logger.info("\n1. Чтение XLS-реестра...")
    registry_rows = read_registry(xls_path)

    # 2. Создание чанков
    logger.info("\n2. Создание чанков...")
    all_chunks = []
    for row in registry_rows:
        chunks = row_to_chunks(row, source_file)
        all_chunks.extend(chunks)

    logger.info(f"   Создано чанков: {len(all_chunks)} из {len(registry_rows)} строк реестра")

    # Статистика по типам секций
    section_counts: dict[str, int] = {}
    for chunk in all_chunks:
        st = chunk['section_type']
        section_counts[st] = section_counts.get(st, 0) + 1

    logger.info("   Распределение по секциям:")
    for section_type, count in sorted(section_counts.items()):
        logger.info(f"     {section_type}: {count}")

    if dry_run:
        logger.info("\n   [DRY RUN] Вставка пропущена.")
        return

    # 3. Подключение к БД
    logger.info("\n3. Подключение к БД...")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("   ✓ Подключено")

    # 4. Получаем все trade_name, уже присутствующие в drugs_chunks
    logger.info("\n4. Загрузка существующих препаратов из БД...")
    existing_normalized: list[str] = [
        normalize_trade_name(row[0])
        for row in session.execute(text("SELECT DISTINCT trade_name FROM drugs_chunks"))
        if row[0]
    ]
    logger.info(f"   Препаратов уже в БД: {len(existing_normalized)}")

    def already_exists(trade_name: str) -> bool:
        """Препарат считается дублем если его нормализованное имя
        содержится в нормализованном имени из БД или наоборот."""
        n = normalize_trade_name(trade_name)
        return any(n in ex or ex in n for ex in existing_normalized)

    # Оставляем только чанки для отсутствующих препаратов
    all_chunks = [c for c in all_chunks if not already_exists(c['trade_name'])]
    new_drugs = len({c['trade_name'] for c in all_chunks})
    logger.info(f"   Новых препаратов из реестра: {new_drugs}, чанков для вставки: {len(all_chunks)}")

    if not all_chunks:
        logger.info("   Нечего добавлять — все препараты уже есть в БД.")
        session.close()
        return

    # 5. Вставка чанков
    logger.info(f"\n5. Вставка {len(all_chunks)} чанков (batch_size={batch_size})...")
    inserted = 0

    for chunk_data in all_chunks:
        chunk = DrugChunk(
            source_file=chunk_data['source_file'],
            content=chunk_data['content'],
            generic_name=chunk_data['generic_name'],
            trade_name=chunk_data['trade_name'],
            manufacturer=chunk_data['manufacturer'],
            dosage_form=chunk_data['dosage_form'],
            route=chunk_data['route'],
            drug_class=chunk_data['drug_class'],
            target_animals=chunk_data['target_animals'],
            section_type=chunk_data['section_type'],
            section_title=chunk_data['section_title'],
            source_url=chunk_data['source_url'],
            embedding=None,  # Векторизуется отдельно
        )
        session.add(chunk)
        inserted += 1

        if inserted % batch_size == 0:
            session.commit()
            logger.info(f"   ...вставлено {inserted}/{len(all_chunks)}")

    session.commit()
    logger.info(f"   ✓ Вставлено: {inserted}")

    # 6. Финальная статистика
    total_in_db = session.query(DrugChunk).count()
    without_emb = session.query(DrugChunk).filter(DrugChunk.embedding.is_(None)).count()

    logger.info("\n" + "=" * 80)
    logger.info("ИМПОРТ ЗАВЕРШЁН")
    logger.info("=" * 80)
    logger.info(f"   Вставлено новых чанков: {inserted}")
    logger.info(f"   Всего чанков в drugs_chunks: {total_in_db}")
    logger.info(f"   Чанков без эмбеддинга: {without_emb}")
    logger.info("\n   Следующий шаг — векторизация:")
    logger.info("   python -m knowledge.parsing_piplines.drugs.vectorize_chunks")

    session.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Импорт реестра ветпрепаратов в drugs_chunks')
    parser.add_argument(
        '--xls',
        default='knowledge/data/drugs/registry_pharm_2026_03_26.xls',
        help='Путь к XLS-файлу реестра (default: registry_pharm_2026_03_26.xls)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Только подсчитать чанки, не вставлять в БД'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Размер батча для commit (default: 100)'
    )
    args = parser.parse_args()

    import_registry(
        xls_path=args.xls,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
