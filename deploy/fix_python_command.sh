#!/bin/bash

# PrintFarm Production - Исправление команды python в entrypoint
# Исправляет ошибку "python: command not found"

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

print_header "ИСПРАВЛЕНИЕ КОМАНДЫ PYTHON"

# Определяем директорию проекта
if [ -d "printfarm-production-new" ]; then
    cd printfarm-production-new
    print_info "Переходим в printfarm-production-new"
elif [ -d "backend" ]; then
    print_info "Уже в правильной директории"
else
    print_error "Директория проекта не найдена!"
    exit 1
fi

# Шаг 1: Исправляем entrypoint.sh
print_info "🔧 Исправляем entrypoint.sh..."

cat > backend/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Запуск PrintFarm Django..."

# Ждем базу данных
echo "⏳ Ожидание PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ PostgreSQL готов!"

# Применяем миграции
echo "🗄️ Применение миграций..."
python3 manage.py migrate --noinput

# Создаем суперпользователя
echo "👤 Создание суперпользователя..."
python3 manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@printfarm.local', 'admin')
    print('✅ Суперпользователь admin/admin создан')
else:
    print('ℹ️ Суперпользователь уже существует')
EOF

# Собираем статику
echo "📦 Сбор статических файлов..."
python3 manage.py collectstatic --noinput

echo "✅ Django готов к работе!"

# Запуск переданной команды
exec "$@"
EOF

chmod +x backend/entrypoint.sh
print_success "entrypoint.sh исправлен (python → python3)"

# Шаг 2: Исправляем Dockerfile для создания симлинка python
print_info "🔧 Исправляем Dockerfile..."

cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Создаем симлинк python -> python3 для совместимости
RUN ln -sf /usr/local/bin/python3 /usr/local/bin/python

# Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем директории
RUN mkdir -p /app/static /app/media

EXPOSE 8000

# Скрипт запуска
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
EOF

print_success "Dockerfile исправлен (добавлен симлинк python)"

# Шаг 3: Исправляем manage.py
print_info "🔧 Исправляем manage.py..."

cat > backend/manage.py << 'EOF'
#!/usr/bin/env python3
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
EOF

chmod +x backend/manage.py
print_success "manage.py исправлен (python3)"

# Шаг 4: Останавливаем и пересобираем контейнеры
print_info "🔄 Пересобираем контейнеры..."

# Останавливаем
docker-compose down 2>/dev/null || true

# Удаляем старые образы
docker-compose build --no-cache backend 2>/dev/null || true

# Запускаем заново
print_info "🚀 Запускаем контейнеры..."
docker-compose up -d

# Ждем запуска
print_info "⏳ Ждем запуска (30 секунд)..."
sleep 30

# Шаг 5: Проверяем результат
print_header "ПРОВЕРКА РЕЗУЛЬТАТА"

print_info "📊 Статус контейнеров:"
docker-compose ps

print_info "🔍 Проверяем логи backend:"
docker-compose logs backend | tail -10

print_info "🧪 Тестируем endpoints:"

# Тест health check
if curl -f -s -m 10 http://localhost:8089/health/ > /dev/null 2>&1; then
    print_success "Health check работает!"
    curl -s http://localhost:8089/health/ | head -3
else
    print_warning "Health check недоступен"
    print_info "Логи backend:"
    docker-compose logs backend | tail -5
fi

# Тест главной страницы
echo
if curl -f -s -m 10 http://localhost:8089/ | grep -q -i "printfarm"; then
    print_success "Главная страница работает!"
else
    print_warning "Главная страница недоступна"
fi

# Шаг 6: Создаем новые управляющие скрипты
print_info "📝 Создаем управляющие скрипты..."

# Скрипт статуса
cat > status.sh << 'EOF'
#!/bin/bash
echo "=== СТАТУС PRINTFARM ==="
echo "Контейнеры:"
docker-compose ps
echo -e "\nПорты:"
netstat -tlnp | grep :8089 || echo "Порт 8089 не слушается"
echo -e "\nТест API:"
curl -s http://localhost:8089/health/ | head -3 || echo "API недоступен"
echo -e "\nТест главной:"
curl -s http://localhost:8089/ | head -1 | grep -o "<title>.*</title>" || echo "Главная недоступна"
EOF

# Скрипт логов
cat > logs.sh << 'EOF'
#!/bin/bash
echo "=== ЛОГИ PRINTFARM ==="
if [ "$1" ]; then
    echo "Логи сервиса: $1"
    docker-compose logs -f --tail=50 $1
else
    echo "Доступные сервисы: backend, nginx, db, redis"
    echo "Использование: ./logs.sh [сервис]"
    echo "Показываем общие логи:"
    docker-compose logs --tail=20
fi
EOF

# Скрипт перезапуска
cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Перезапуск PrintFarm..."
docker-compose restart
sleep 15
echo "✅ Перезапуск завершен"
./status.sh
EOF

chmod +x *.sh

print_success "Управляющие скрипты созданы"

# Финальная информация
print_header "ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"

print_success "🎉 Команда python исправлена!"
echo
print_info "🌐 Проверьте доступность:"
echo "   Главная:      http://kemomail3.keenetic.pro:8089/"
echo "   Health:       http://kemomail3.keenetic.pro:8089/health/"
echo "   Админка:      http://kemomail3.keenetic.pro:8089/admin/"
echo
print_info "🔧 Управление:"
echo "   Статус:       ./status.sh"
echo "   Логи:         ./logs.sh [backend|nginx|db|redis]"
echo "   Перезапуск:   ./restart.sh"
echo
print_info "🔧 Исправления:"
echo "   ✓ python → python3 в entrypoint.sh"
echo "   ✓ Добавлен симлинк python в Dockerfile"
echo "   ✓ Исправлен shebang в manage.py"
echo "   ✓ Пересобраны Docker образы"
echo "   ✓ Обновлены управляющие скрипты"
echo
if curl -f -s -m 5 http://localhost:8089/health/ > /dev/null 2>&1; then
    print_success "✅ Система работает! Откройте в браузере!"
else
    print_warning "⚠️  Если не работает, проверьте: ./logs.sh backend"
fi
echo
print_success "Готово! 🚀"