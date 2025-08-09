# Multi-stage Dockerfile для Django приложения

# Stage 1: Development
FROM python:3.11-slim as development

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя приложения
RUN useradd --create-home --shell /bin/bash app

# Установка рабочей директории
WORKDIR /app

# Копирование requirements
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY backend/ /app/

# Создание директорий
RUN mkdir -p /app/static /app/media /app/logs

# Установка прав
RUN chown -R app:app /app
USER app

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Stage 2: Production
FROM python:3.11-slim as production

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя приложения
RUN useradd --create-home --shell /bin/bash app

# Установка рабочей директории
WORKDIR /app

# Копирование requirements
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt gunicorn gevent

# Копирование кода приложения
COPY backend/ /app/

# Создание директорий
RUN mkdir -p /app/static /app/media /app/logs

# Компиляция байт-кода Python
RUN python -m compileall .

# Установка прав
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Команда по умолчанию
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]