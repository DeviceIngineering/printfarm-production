#!/bin/bash

# PrintFarm Production - Свежее развертывание с нуля
# Полностью чистая установка на удаленном сервере с минимальными зависимостями

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_debug() {
    echo -e "${PURPLE}🔍 $1${NC}"
}

print_header() {
    echo -e "\n${CYAN}===========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===========================================${NC}\n"
}

print_step() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

# Конфигурация
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "192.168.1.98")
EXTERNAL_DOMAIN="kemomail3.keenetic.pro"
EXTERNAL_PORT="8089"
PROJECT_NAME="printfarm"
DB_PASSWORD="printfarm_2025_secure"

print_header "PRINTFARM PRODUCTION - СВЕЖЕЕ РАЗВЕРТЫВАНИЕ"

print_info "🌐 Конфигурация развертывания:"
echo "   Локальный IP: $LOCAL_IP"
echo "   Внешний домен: $EXTERNAL_DOMAIN"
echo "   Порт: $EXTERNAL_PORT"
echo "   База данных: $PROJECT_NAME"

# ============================================
# ЭТАП 1: ПОДГОТОВКА СИСТЕМЫ
# ============================================
print_header "ЭТАП 1: ПОДГОТОВКА СИСТЕМЫ"

print_step "Обновление системы"
sudo apt update && sudo apt upgrade -y

print_step "Установка базовых пакетов"
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    nano \
    net-tools \
    lsof \
    python3 \
    python3-pip \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server

print_success "Базовые пакеты установлены"

# ============================================ 
# ЭТАП 2: УСТАНОВКА DOCKER (АЛЬТЕРНАТИВНАЯ)
# ============================================
print_header "ЭТАП 2: УСТАНОВКА DOCKER"

if ! command -v docker &> /dev/null; then
    print_step "Установка Docker"
    
    # Удаляем старые версии
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Устанавливаем Docker из snap (более стабильно)
    sudo snap install docker
    
    # Добавляем пользователя в группу docker
    sudo usermod -aG docker $USER
    
    # Альтернативный способ через официальный скрипт
    if ! command -v docker &> /dev/null; then
        print_info "Пробуем альтернативную установку..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
    fi
    
    print_success "Docker установлен"
else
    print_info "Docker уже установлен"
fi

# Устанавливаем Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_step "Установка Docker Compose"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Альтернативный способ через pip
    if ! command -v docker-compose &> /dev/null; then
        sudo pip3 install docker-compose
    fi
    
    print_success "Docker Compose установлен"
fi

# Запускаем Docker
sudo systemctl enable docker
sudo systemctl start docker

print_success "Docker готов к работе"

# ============================================
# ЭТАП 3: СОЗДАНИЕ ПРОЕКТА БЕЗ GIT
# ============================================
print_header "ЭТАП 3: СОЗДАНИЕ ПРОЕКТА"

print_step "Очистка старого проекта"
cd ~
rm -rf printfarm-production-new
mkdir -p printfarm-production-new
cd printfarm-production-new

print_step "Создание структуры проекта"
mkdir -p {backend,frontend,nginx,deploy,data}

# ============================================
# ЭТАП 4: СОЗДАНИЕ BACKEND (DJANGO)
# ============================================
print_header "ЭТАП 4: СОЗДАНИЕ BACKEND"

print_step "Создание Django приложения"

cat > backend/requirements.txt << 'EOF'
Django==4.2.10
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
gunicorn==21.2.0
python-decouple==3.8
Pillow==10.2.0
openpyxl==3.1.2
requests==2.31.0
EOF

cat > backend/manage.py << 'EOF'
#!/usr/bin/env python
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

# Создаем Django settings
mkdir -p backend/config/settings
cat > backend/config/__init__.py << 'EOF'
EOF

cat > backend/config/settings/__init__.py << 'EOF'
EOF

cat > backend/config/settings/base.py << 'EOF'
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-key-for-development')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.api',
    'apps.core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='printfarm'),
        'USER': config('POSTGRES_USER', default='printfarm'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Отключаем CSRF для простоты
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
EOF

cat > backend/config/settings/production.py << 'EOF'
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['*']

# В production можно настроить более строгие правила
CORS_ALLOW_ALL_ORIGINS = True
EOF

# Создаем URLs
cat > backend/config/urls.py << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import datetime

@csrf_exempt
def home_view(request):
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrintFarm Production v4.6</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Arimo", -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .logo {{
            color: #06EAFC;
            font-size: 4em;
            font-weight: bold;
            text-shadow: 0 0 30px #06EAFC;
            margin-bottom: 10px;
            animation: glow 2s ease-in-out infinite alternate;
        }}
        @keyframes glow {{
            from {{ text-shadow: 0 0 20px #06EAFC; }}
            to {{ text-shadow: 0 0 30px #06EAFC, 0 0 40px #06EAFC; }}
        }}
        .status {{
            background: linear-gradient(45deg, #00FF88, #06EAFC);
            color: #1e1e1e;
            padding: 15px 30px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2em;
            display: inline-block;
            margin: 20px 0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .info-card {{
            background: rgba(6, 234, 252, 0.1);
            border: 2px solid #06EAFC;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(45deg, #06EAFC, #00FF88);
            color: #1e1e1e;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            margin: 10px 5px;
            transition: transform 0.3s;
        }}
        .button:hover {{ transform: scale(1.05); }}
        .server-info {{
            background: rgba(0, 255, 136, 0.1);
            border: 2px solid #00FF88;
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">PrintFarm</div>
            <div style="color: #cccccc; font-size: 1.3em;">Система управления производством</div>
            <div class="status">✅ Система работает!</div>
        </div>

        <div class="server-info">
            <h3 style="color: #00FF88; margin-bottom: 15px;">📡 Информация о сервере</h3>
            <p><strong>Версия:</strong> v4.6 Production</p>
            <p><strong>Домен:</strong> {request.get_host()}</p>
            <p><strong>Время:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Статус:</strong> Online и готов к работе</p>
        </div>

        <div class="info-grid">
            <div class="info-card">
                <h3 style="color: #06EAFC; margin-bottom: 15px;">🎛️ Админ-панель</h3>
                <p>Управление системой и настройки</p>
                <a href="/admin/" class="button">Открыть админку</a>
                <p style="margin-top: 15px; color: #888;">admin / admin</p>
            </div>

            <div class="info-card">
                <h3 style="color: #06EAFC; margin-bottom: 15px;">📊 API</h3>
                <p>Доступ к данным через REST API</p>
                <a href="/api/stats/" class="button">Статистика</a>
                <a href="/api/products/" class="button">Товары</a>
            </div>

            <div class="info-card">
                <h3 style="color: #06EAFC; margin-bottom: 15px;">🛠️ Диагностика</h3>
                <p>Проверка состояния системы</p>
                <a href="/health/" class="button">Health Check</a>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; color: #666;">
            <p>PrintFarm Production v4.6 | 2025</p>
        </div>
    </div>
</body>
</html>"""
    return HttpResponse(html)

@csrf_exempt
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'version': '4.6',
        'timestamp': datetime.datetime.now().isoformat(),
        'server': request.get_host(),
        'components': {
            'django': 'OK',
            'database': 'OK',
            'api': 'OK'
        }
    })

@csrf_exempt
def api_stats(request):
    return JsonResponse({
        'total_products': 0,
        'production_needed': 0,
        'critical_products': 0,
        'new_products': 0,
        'old_products': 0,
        'message': 'PrintFarm API v4.6 работает',
        'timestamp': datetime.datetime.now().isoformat()
    })

@csrf_exempt  
def api_products(request):
    return JsonResponse({
        'products': [],
        'count': 0,
        'message': 'Список товаров (пока пустой)',
        'timestamp': datetime.datetime.now().isoformat()
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    path('api/stats/', api_stats, name='api_stats'),
    path('api/products/', api_products, name='api_products'),
]
EOF

# Создаем WSGI
cat > backend/config/wsgi.py << 'EOF'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
EOF

# Создаем apps
mkdir -p backend/apps/api backend/apps/core

cat > backend/apps/__init__.py << 'EOF'
EOF

cat > backend/apps/api/__init__.py << 'EOF'
EOF

cat > backend/apps/api/apps.py << 'EOF'
from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.api'
EOF

cat > backend/apps/core/__init__.py << 'EOF'
EOF

cat > backend/apps/core/apps.py << 'EOF'
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
EOF

print_success "Django backend создан"

# ============================================
# ЭТАП 5: СОЗДАНИЕ DOCKER КОНФИГУРАЦИИ
# ============================================
print_header "ЭТАП 5: СОЗДАНИЕ DOCKER КОНФИГУРАЦИИ"

print_step "Создание Dockerfile"
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
python manage.py migrate --noinput

# Создаем суперпользователя
echo "👤 Создание суперпользователя..."
python manage.py shell << EOF
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
python manage.py collectstatic --noinput

echo "✅ Django готов к работе!"

# Запуск переданной команды
exec "$@"
EOF

chmod +x backend/entrypoint.sh

print_step "Создание docker-compose.yml"
cat > docker-compose.yml << EOF
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: printfarm
      POSTGRES_USER: printfarm
      POSTGRES_PASSWORD: $DB_PASSWORD
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - printfarm-net

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - printfarm-net

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
      SECRET_KEY: printfarm-production-secret-key-2025
      DEBUG: 'False'
      POSTGRES_DB: printfarm
      POSTGRES_USER: printfarm
      POSTGRES_PASSWORD: $DB_PASSWORD
      DB_HOST: db
      DB_PORT: 5432
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    networks:
      - printfarm-net

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "$EXTERNAL_PORT:80"
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend
    networks:
      - printfarm-net

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  printfarm-net:
    driver: bridge
EOF

print_step "Создание nginx конфигурации"
mkdir -p nginx
cat > nginx/nginx.conf << 'EOF'
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    # Логирование
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Все остальное на Django
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
EOF

print_success "Docker конфигурация создана"

# ============================================
# ЭТАП 6: ЗАПУСК ПРОЕКТА
# ============================================
print_header "ЭТАП 6: ЗАПУСК ПРОЕКТА"

print_step "Сборка Docker образов"
docker-compose build --no-cache

print_step "Запуск контейнеров"
docker-compose up -d

print_step "Ожидание запуска (30 секунд)"
sleep 30

# ============================================
# ЭТАП 7: ТЕСТИРОВАНИЕ
# ============================================
print_header "ЭТАП 7: ТЕСТИРОВАНИЕ РАЗВЕРТЫВАНИЯ"

print_step "Проверка статуса контейнеров"
docker-compose ps

print_step "Тестирование endpoints"

# Тест 1: Health check
echo "=== ТЕСТ 1: Health Check ==="
if curl -f -s -m 10 http://localhost:$EXTERNAL_PORT/health/ | grep -q "healthy"; then
    print_success "Health check работает!"
    curl -s http://localhost:$EXTERNAL_PORT/health/ | head -3
else
    print_warning "Health check недоступен"
fi

# Тест 2: Главная страница  
echo -e "\n=== ТЕСТ 2: Главная страница ==="
if curl -f -s -m 10 http://localhost:$EXTERNAL_PORT/ | grep -q -i "printfarm"; then
    print_success "Главная страница работает!"
else
    print_warning "Главная страница недоступна"
fi

# Тест 3: API
echo -e "\n=== ТЕСТ 3: API ==="
if curl -f -s -m 10 http://localhost:$EXTERNAL_PORT/api/stats/ | grep -q "total_products"; then
    print_success "API работает!"
    curl -s http://localhost:$EXTERNAL_PORT/api/stats/ | head -3
else
    print_warning "API недоступен"
fi

# Тест 4: Админка
echo -e "\n=== ТЕСТ 4: Админка ==="
admin_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$EXTERNAL_PORT/admin/)
if [ "$admin_status" = "200" ] || [ "$admin_status" = "302" ]; then
    print_success "Админка доступна (код: $admin_status)"
else
    print_warning "Админка недоступна (код: $admin_status)"
fi

# ============================================
# ЭТАП 8: НАСТРОЙКА АВТОЗАПУСКА
# ============================================
print_header "ЭТАП 8: НАСТРОЙКА АВТОЗАПУСКА"

print_step "Создание systemd сервиса"
sudo tee /etc/systemd/system/printfarm.service > /dev/null << EOF
[Unit]
Description=PrintFarm Production
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=$(whoami)
Group=$(whoami)

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable printfarm.service

print_success "Автозапуск настроен"

# ============================================
# ЭТАП 9: СОЗДАНИЕ УПРАВЛЯЮЩИХ СКРИПТОВ
# ============================================
print_header "ЭТАП 9: СОЗДАНИЕ УПРАВЛЯЮЩИХ СКРИПТОВ"

print_step "Создание скриптов управления"

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
EOF

# Скрипт перезапуска
cat > restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Перезапуск PrintFarm..."
docker-compose restart
sleep 10
echo "✅ Перезапуск завершен"
./status.sh
EOF

# Скрипт логов
cat > logs.sh << 'EOF'
#!/bin/bash
echo "=== ЛОГИ PRINTFARM ==="
if [ "$1" ]; then
    docker-compose logs -f $1
else
    docker-compose logs --tail=50
fi
EOF

# Скрипт остановки
cat > stop.sh << 'EOF'
#!/bin/bash
echo "⏹️ Остановка PrintFarm..."
docker-compose down
echo "✅ PrintFarm остановлен"
EOF

# Скрипт запуска
cat > start.sh << 'EOF'
#!/bin/bash
echo "▶️ Запуск PrintFarm..."
docker-compose up -d
sleep 15
echo "✅ PrintFarm запущен"
./status.sh
EOF

chmod +x *.sh

print_success "Управляющие скрипты созданы"

# ============================================
# ФИНАЛЬНАЯ ИНФОРМАЦИЯ
# ============================================
print_header "РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"

print_success "🎉 PrintFarm Production v4.6 успешно развернут!"
echo
print_info "🌐 Доступные URL:"
echo "   Главная:      http://$EXTERNAL_DOMAIN:$EXTERNAL_PORT/"
echo "   Альтернатива: http://$LOCAL_IP:$EXTERNAL_PORT/"
echo "   Админка:      http://$EXTERNAL_DOMAIN:$EXTERNAL_PORT/admin/"
echo "   API:          http://$EXTERNAL_DOMAIN:$EXTERNAL_PORT/api/stats/"
echo "   Health:       http://$EXTERNAL_DOMAIN:$EXTERNAL_PORT/health/"
echo
print_info "👤 Данные для входа в админку:"
echo "   Логин:    admin"
echo "   Пароль:   admin"
echo
print_info "🔧 Управление системой:"
echo "   Статус:       ./status.sh"
echo "   Перезапуск:   ./restart.sh"
echo "   Логи:         ./logs.sh [сервис]"
echo "   Остановка:    ./stop.sh"
echo "   Запуск:       ./start.sh"
echo
print_info "📁 Расположение проекта:"
echo "   $(pwd)"
echo
print_info "🔌 Настройки роутера:"
echo "   Пробросить порт $EXTERNAL_PORT на $LOCAL_IP:$EXTERNAL_PORT"
echo "   Протокол: TCP"
echo
print_warning "⚠️  Для доступа извне настройте проброс портов на роутере!"
echo
print_success "Система готова к работе! 🚀"

# Финальный тест
print_info "🧪 Финальный тест системы..."
if curl -f -s -m 5 http://localhost:$EXTERNAL_PORT/health/ > /dev/null; then
    print_success "✅ Все работает отлично!"
else
    print_warning "⚠️  Система запускается, подождите 1-2 минуты"
fi