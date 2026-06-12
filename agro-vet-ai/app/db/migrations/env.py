from app.db.sqlalchemy_models import Base
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.utils.settings import secrets as s


db_user = s.postgres_user
db_password = s.postgres_password
db_host = s.db_host
db_port = s.db_port_container
db_name = s.postgres_db

# Формируем строку подключения с драйвером psycopg (версия 3)
DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# Это объект конфигурации Alembic
config = context.config

# Устанавливаем URL подключения
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Настройка логгирования
fileConfig(config.config_file_name)

# Здесь можно подключить MetaData (если используешь SQLAlchemy ORM)
target_metadata = Base.metadata


def run_migrations_offline():
    """Запуск миграций в оффлайн-режиме."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Запуск миграций в онлайн-режиме."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
