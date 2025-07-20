#!/bin/bash
# Скрипт автоматического развертывания PrintFarm

set -e  # Останавливаем при ошибках

echo "🚀 Начинаем развертывание PrintFarm..."

# Переменные
REPO_URL="https://github.com/yourusername/printfarm.git"  # Замените на ваш репозиторий
APP_DIR="/opt/printfarm"
BRANCH="main"

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Функция для вывода успеха
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Функция для вывода ошибки
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Проверка, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен от root (используйте sudo)"
fi

# Обновление системы
echo "📦 Обновление системы..."
apt-get update && apt-get upgrade -y
success "Система обновлена"

# Установка необходимых пакетов
echo "📦 Установка необходимых пакетов..."
apt-get install -y \
    git \
    curl \
    wget \
    nginx \
    postgresql \
    redis-server \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    supervisor
success "Пакеты установлены"

# Установка Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    success "Docker установлен"
else
    success "Docker уже установлен"
fi

# Установка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    success "Docker Compose установлен"
else
    success "Docker Compose уже установлен"
fi

# Клонирование репозитория
if [ -d "$APP_DIR" ]; then
    echo "📂 Обновление существующего репозитория..."
    cd $APP_DIR
    git pull origin $BRANCH
else
    echo "📂 Клонирование репозитория..."
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
    git checkout $BRANCH
fi
success "Репозиторий готов"

# Копирование production конфигурации
echo "⚙️ Настройка конфигурации..."
if [ -f ".env.production" ]; then
    cp .env.production .env
    success "Конфигурация скопирована"
else
    error "Файл .env.production не найден!"
fi

# Создание директорий
echo "📁 Создание необходимых директорий..."
mkdir -p nginx/ssl
mkdir -p backend/logs
mkdir -p backend/media
mkdir -p backend/static
success "Директории созданы"

# Сборка и запуск контейнеров
echo "🏗️ Сборка Docker образов..."
docker-compose -f docker-compose.prod.yml build
success "Docker образы собраны"

echo "🚀 Запуск контейнеров..."
docker-compose -f docker-compose.prod.yml up -d
success "Контейнеры запущены"

# Ожидание запуска базы данных
echo "⏳ Ожидание запуска базы данных..."
sleep 10

# Выполнение миграций
echo "🗄️ Выполнение миграций..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
success "Миграции выполнены"

# Сбор статических файлов
echo "📦 Сбор статических файлов..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
success "Статические файлы собраны"

# Создание суперпользователя
echo "👤 Создание суперпользователя..."
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

# Настройка автозапуска
echo "🔄 Настройка автозапуска..."
cat > /etc/systemd/system/printfarm.service << EOF
[Unit]
Description=PrintFarm Production System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable printfarm.service
success "Автозапуск настроен"

# Проверка статуса
echo "✅ Проверка статуса..."
docker-compose -f docker-compose.prod.yml ps

echo ""
success "Развертывание завершено успешно!"
echo ""
echo "📝 Дальнейшие шаги:"
echo "1. Обновите .env файл с вашими настройками"
echo "2. Настройте SSL сертификат (см. инструкцию ниже)"
echo "3. Обновите домен в nginx.prod.conf"
echo "4. Перезапустите сервисы: docker-compose -f docker-compose.prod.yml restart"
echo ""
echo "🔐 Для настройки SSL с Let's Encrypt:"
echo "   certbot --nginx -d your-domain.com"
echo ""
echo "📊 Для просмотра логов:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""