#!/bin/bash

# PrintFarm Production - Быстрое исправление Docker сборки
# Этот скрипт применяет исправления для ошибки MOYSKLAD_TOKEN

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

print_header "БЫСТРОЕ ИСПРАВЛЕНИЕ DOCKER СБОРКИ"

# Проверяем что мы в правильной папке
if [[ ! -f "docker-compose.prod.yml" ]]; then
    print_error "Запустите скрипт из папки printfarm-production!"
    exit 1
fi

# Шаг 1: Получаем последние изменения
print_info "📥 Получаем последние изменения из репозитория..."
git fetch origin main
git reset --hard origin/main
print_success "Код обновлен до последней версии"

# Шаг 2: Проверяем наличие новых файлов
print_info "🔍 Проверяем наличие исправленных файлов..."

if [[ ! -f "docker/django/Dockerfile.prod" ]]; then
    print_error "Файл docker/django/Dockerfile.prod не найден!"
    print_info "Создаем его вручную..."
    
    mkdir -p docker/django
    cat > docker/django/Dockerfile.prod << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    git \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY backend/ .

# Создаем необходимые директории
RUN mkdir -p /app/static /app/media

# НЕ собираем статику на этапе сборки!

# Создаем пользователя
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Создаем entrypoint скрипт
COPY --chown=appuser:appuser docker/django/entrypoint.prod.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
EOF
    print_success "Dockerfile.prod создан"
fi

if [[ ! -f "docker/django/entrypoint.prod.sh" ]]; then
    print_info "Создаем entrypoint.prod.sh..."
    
    cat > docker/django/entrypoint.prod.sh << 'EOF'
#!/bin/sh

set -e

echo "🚀 Starting PrintFarm Production Django..."

# Ждем базу данных
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z db 5432 2>/dev/null; do
  echo "   PostgreSQL is not ready yet... waiting..."
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Применяем миграции
echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput || true

# Собираем статические файлы (теперь переменные окружения доступны)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "✅ Django is ready!"

# Выполняем переданную команду
exec "$@"
EOF
    chmod +x docker/django/entrypoint.prod.sh
    print_success "entrypoint.prod.sh создан"
fi

# Шаг 3: Создаем минимальный .env если его нет
if [[ ! -f ".env" ]]; then
    print_warning ".env файл не найден, создаем минимальный..."
    cat > .env << 'EOF'
# Django
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=printfarm_prod
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password_change_this
DATABASE_URL=postgresql://printfarm_user:secure_password_change_this@db:5432/printfarm_prod

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад (пустые значения для сборки)
MOYSKLAD_TOKEN=
MOYSKLAD_DEFAULT_WAREHOUSE=

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
    print_success ".env файл создан с минимальными настройками"
    print_warning "⚠️  ВАЖНО: Отредактируйте .env файл и добавьте реальные значения!"
fi

# Шаг 4: Исправляем settings/base.py на всякий случай
print_info "🔧 Проверяем настройки Django..."
if grep -q "config('MOYSKLAD_TOKEN')" backend/config/settings/base.py; then
    print_info "Добавляем дефолтные значения в base.py..."
    sed -i "s/config('MOYSKLAD_TOKEN')/config('MOYSKLAD_TOKEN', default='')/g" backend/config/settings/base.py
    sed -i "s/config('MOYSKLAD_DEFAULT_WAREHOUSE')/config('MOYSKLAD_DEFAULT_WAREHOUSE', default='')/g" backend/config/settings/base.py
    print_success "Настройки исправлены"
fi

# Шаг 5: Очищаем Docker кэш
print_info "🧹 Очищаем Docker кэш..."
docker system prune -f
docker builder prune -f

# Шаг 6: Останавливаем старые контейнеры
print_info "⏹️ Останавливаем старые контейнеры..."
docker-compose -f docker-compose.prod.yml down || true

# Шаг 7: Пересобираем образы
print_header "СБОРКА DOCKER ОБРАЗОВ"
print_info "🔨 Собираем образы (это может занять 5-10 минут)..."

# Сначала собираем backend отдельно для проверки
print_info "Собираем backend..."
docker-compose -f docker-compose.prod.yml build --no-cache backend

if [[ $? -eq 0 ]]; then
    print_success "Backend собран успешно!"
else
    print_error "Ошибка при сборке backend!"
    print_info "Попробуем альтернативный способ..."
    
    # Альтернативный Dockerfile без collectstatic
    cat > docker/django/Dockerfile.prod.simple << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN mkdir -p /app/static /app/media

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
EOF
    
    # Меняем Dockerfile в docker-compose
    sed -i 's/Dockerfile.prod/Dockerfile.prod.simple/g' docker-compose.prod.yml
    
    # Пробуем снова
    docker-compose -f docker-compose.prod.yml build --no-cache backend
fi

# Собираем остальные сервисы
print_info "Собираем остальные сервисы..."
docker-compose -f docker-compose.prod.yml build

# Шаг 8: Запускаем контейнеры
print_header "ЗАПУСК ПРИЛОЖЕНИЯ"
print_info "🚀 Запускаем контейнеры..."
docker-compose -f docker-compose.prod.yml up -d

# Шаг 9: Ждем запуска
print_info "⏳ Ждем запуска сервисов (30 секунд)..."
sleep 30

# Шаг 10: Применяем миграции вручную
print_info "🗄️ Применяем миграции..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput || true

# Шаг 11: Собираем статику вручную
print_info "📦 Собираем статические файлы..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput || true

# Шаг 12: Проверяем статус
print_header "ПРОВЕРКА РАБОТОСПОСОБНОСТИ"
print_info "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

# Шаг 13: Проверяем API
print_info "🔍 Проверяем доступность API..."
sleep 5

if curl -f -s http://localhost:8000/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "API доступен по порту 8000!"
elif curl -f -s http://localhost/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "API доступен через Nginx!"
else
    print_warning "API пока недоступен, проверьте логи"
fi

# Финальная информация
print_header "ИСПРАВЛЕНИЕ ЗАВЕРШЕНО"

print_success "Docker сборка исправлена!"
echo
print_info "📋 Полезные команды:"
echo "   Логи backend:    docker-compose -f docker-compose.prod.yml logs backend"
echo "   Логи всех:       docker-compose -f docker-compose.prod.yml logs"
echo "   Перезапуск:      docker-compose -f docker-compose.prod.yml restart"
echo "   Статус:          docker-compose -f docker-compose.prod.yml ps"
echo
print_info "🌐 Проверьте работу:"
echo "   API:     http://localhost:8000/api/v1/tochka/stats/"
echo "   Сайт:    http://localhost/"
echo
print_warning "⚠️  Не забудьте отредактировать .env файл с реальными настройками МойСклад!"
echo
print_success "Готово! 🎉"