#!/bin/sh

# Ожидание готовности PostgreSQL
# We expect the environment variables to be available via Docker Compose
while ! pg_isready -h "$DB_HOST" -p "$DB_PORT_CONTAINER" > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 10
done

echo "PostgreSQL is ready, running migrations..."

# Выполнение миграций Alembic
alembic upgrade head

echo "Migrations completed, starting the application..."

# Запуск основного приложения
exec "$@"
