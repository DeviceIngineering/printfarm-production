# PrintFarm Backend Simple Dockerfile - v4.1.8
FROM python:3.11-slim

# Аргументы сборки
ARG ENVIRONMENT=production
ARG APP_VERSION=4.1.8

# Устанавливаем метки
LABEL maintainer="PrintFarm Team"
LABEL version="${APP_VERSION}"
LABEL environment="${ENVIRONMENT}"

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.${ENVIRONMENT} \
    APP_VERSION=${APP_VERSION}

# Создаем пользователя для запуска приложения
RUN groupadd -r printfarm && useradd -r -g printfarm printfarm

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-traditional \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Создаем необходимые директории
RUN mkdir -p /app/static /app/media /app/logs && \
    chown -R printfarm:printfarm /app

# Копируем код приложения
WORKDIR /app
COPY --chown=printfarm:printfarm backend/ .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем entrypoint скрипт
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Ждем готовности базы данных\n\
if [ "$DATABASE_URL" ]; then\n\
    echo "Waiting for database..."\n\
    while ! nc -z ${DB_HOST:-printfarm-test-db} ${DB_PORT:-5432}; do\n\
        sleep 0.1\n\
    done\n\
    echo "Database is ready!"\n\
fi\n\
\n\
# Выполняем миграции если это основной контейнер\n\
if [ "$RUN_MIGRATIONS" = "true" ]; then\n\
    echo "Running migrations..."\n\
    python manage.py migrate --noinput\n\
    echo "Collecting static files..."\n\
    python manage.py collectstatic --noinput\n\
fi\n\
\n\
# Запускаем команду\n\
exec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    chown printfarm:printfarm /entrypoint.sh

# Переключаемся на пользователя printfarm
USER printfarm

# Указываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Entrypoint и команда по умолчанию
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2"]