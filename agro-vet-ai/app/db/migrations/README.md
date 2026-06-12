# Руководство по обновлению базы данных

Это руководство описывает процесс обновления структуры и данных в базе данных с использованием миграций Alembic.

## Общая концепция

Система использует Alembic для управления миграциями базы данных. Каждая миграция представляет собой отдельный файл Python в папке `db/migrations/versions/`, который содержит функции `upgrade()` и `downgrade()` для обновления и отката изменений соответственно.

## Создание новой миграции

### 1. Создание файла миграции

Создайте новую миграцию с помощью команды:

```bash
alembic revision -m "Описание вашей миграции"
```

Это создаст новый файл миграции в папке `db/migrations/versions/` с уникальным ID.

### 2. Структура файла миграции

Файл миграции должен включать:
- `upgrade()` функцию для выполнения изменений вперед
- `downgrade()` функцию для отката изменений
- Импорт необходимых модулей

```python
from alembic import op
import os
from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic
revision = 'уникальный_айди_миграции'
down_revision = 'айди_предыдущей_миграции'
branch_labels = None
depends_on = None
```

## Загрузка SQL-дампов через raw_sql_loader

### 1. Подготовка дампов

- Дамп в формате .sql должен содержать запросы `INSERT INTO ...`, разделённые `;`
- Поместите SQL-дампы в папку `db/migrations/versions/dumps/`
- Создайте подпапку с названием в формате `{revision_id}_описание`
- Например: `db/migrations/versions/dumps/a2b3c4d5e6f7_load_drug_data/`

### 2. Использование raw_sql_loader в миграции

Для выполнения SQL-запросов из дампов используйте функцию `load_raw_sql` из `raw_sql_loader.py`:

```python
def upgrade():
    # Получение пути к дампу
    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", "a2b3c4d5e6f7_описание_миграции")
    
    # Загрузка SQL-дампов
    sql_files = [
        'source_document.sql',
        'knowledge_base_chunks.sql',
        'images.sql'
    ]
    
    for file_name in sql_files:
        file_path = os.path.join(dumps_dir, file_name)
        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {file_name}")
        else:
            print(f"Warning: {file_path} does not exist")

def downgrade():
    # Откат изменений
    op.execute("TRUNCATE TABLE your_table_name RESTART IDENTITY CASCADE;")
```

## Откат миграции

Для отката миграции используется команда:

```bash
alembic downgrade -1
```

Для отката до конкретной версии:

```bash
alembic downgrade <target_revision_id>
```

При реализации функции `downgrade()` учитывайте **каскадное удаление** через внешние ключи с опцией `ON DELETE CASCADE`:
   ```python
   # В upgrade() добавьте внешний ключ с каскадным удалением:
   op.create_foreign_key(
       'fk_table_name_ref_id_referenced_table',
       'table_name', 'referenced_table',
       ['ref_id'], ['id'],
       ondelete='CASCADE'
   )
   # Тогда в downgrade() достаточно очистить основную таблицу
   ```

Для удаления всех связанных данных из таблиц `source_document`, `knowledge_base_chunks` и `images` достаточно удалить соответствующую запись из `source_document`:
   ```python
   def downgrade():
       # Удаление по конкретному условию и сброс ID
       op.execute("DELETE FROM source_document WHERE name = 'source_name';")
   ```

## Проверка миграций

### 1. Проверка вперед
```bash
alembic upgrade head
```

### 2. Проверка назад (откат)
```bash
alembic downgrade -1
```

### 3. Проверка истории
```bash
alembic history
```

### 4. Проверка текущего состояния
```bash
alembic current
```

## Важные замечания

1. Функция `load_raw_sql(op, file_path)` принимает два параметра:
   - `op`: объект операций Alembic
   - `file_path`: путь к SQL-файлу

## Создание SQL-дампов

Для создания SQL-дампов записей из базы данных, связанных с определенным документом, можно использовать скрипт `scripts/dump_by_id.sh`:

Скрипт интерактивно запросит ID документа из таблицы `source_document`, и затем создаст SQL-дампы для всех связанных записей:
- Записи из таблицы `source_document`
- Связанные записи из таблицы `knowledge_base_chunks`
- Связанные записи из таблицы `images`

Для использования скрипта:
```bash
bash scripts/dump_by_id.sh
```

После запуска скрипт запросит ID source_document, и создаст 3 SQL-файла:
- `backup_document_<id>.sql`
- `backup_knowledge_base_chunks_<id>.sql`
- `backup_images_<id>.sql`

Созданные файлы можно использовать в миграциях для загрузки данных в базу.
