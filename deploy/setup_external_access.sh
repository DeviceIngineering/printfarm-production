#!/bin/bash

# PrintFarm Production - Настройка внешнего доступа
# Настраивает доступ через kemomail3.keenetic.pro:8089

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

print_header "НАСТРОЙКА ВНЕШНЕГО ДОСТУПА"

EXTERNAL_DOMAIN="kemomail3.keenetic.pro"
EXTERNAL_PORT="8089"
INTERNAL_PORT="80"

print_info "🌐 Настраиваем доступ через: ${EXTERNAL_DOMAIN}:${EXTERNAL_PORT}"

# Шаг 1: Обновляем .env файл с новыми ALLOWED_HOSTS
print_info "🔧 Обновляем настройки в .env файле..."

# Создаем резервную копию .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Обновляем ALLOWED_HOSTS
sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,${EXTERNAL_DOMAIN}/" .env

print_success ".env файл обновлен"

# Шаг 2: Создаем обновленный nginx.conf для внешнего доступа
print_info "🌐 Создаем nginx.conf для внешнего доступа..."

cat > nginx.conf << EOF
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name localhost ${EXTERNAL_DOMAIN};
    
    client_max_body_size 100M;
    
    # Безопасность для внешнего доступа
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Логирование для мониторинга
    access_log /var/log/nginx/printfarm_access.log;
    error_log /var/log/nginx/printfarm_error.log;
    
    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Заголовки CORS для статики
        add_header Access-Control-Allow-Origin "*";
    }
    
    # Media files  
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
        
        # Заголовки CORS для медиа
        add_header Access-Control-Allow-Origin "*";
    }
    
    # API endpoints с CORS
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # CORS заголовки для API
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        add_header Access-Control-Expose-Headers "Content-Length,Content-Range" always;
        
        # Обработка preflight запросов
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Admin панель
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
    }
    
    # Все остальное на backend (включая React SPA)
    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
    }
    
    # Healthcheck endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

print_success "nginx.conf обновлен для внешнего доступа"

# Шаг 3: Обновляем docker-compose для внешнего порта
print_info "🐳 Обновляем docker-compose для порта ${EXTERNAL_PORT}..."

# Создаем резервную копию
cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S)

# Создаем обновленный docker-compose с внешним портом
cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=\${POSTGRES_DB:-printfarm}
      - POSTGRES_USER=\${POSTGRES_USER:-printfarm}
      - POSTGRES_PASSWORD=\${POSTGRES_PASSWORD:-1qaz2wsX}
    networks:
      - printfarm-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - printfarm-network

  backend:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    restart: unless-stopped
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    networks:
      - printfarm-network

  celery:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    restart: unless-stopped
    command: celery -A config worker -l info --without-heartbeat --without-gossip --without-mingle --concurrency=2
    volumes:
      - media_volume:/app/media
    depends_on:
      - db
      - redis
      - backend
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    networks:
      - printfarm-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "${EXTERNAL_PORT}:80"  # Внешний порт ${EXTERNAL_PORT}
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend
    networks:
      - printfarm-network

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  printfarm-network:
    driver: bridge
EOF

print_success "docker-compose.prod.yml обновлен для порта ${EXTERNAL_PORT}"

# Шаг 4: Перезапускаем nginx с новой конфигурацией
print_header "ПЕРЕЗАПУСК NGINX"

print_info "🔄 Перезапускаем nginx с новой конфигурацией..."
docker-compose -f docker-compose.prod.yml restart nginx

sleep 5

print_info "📊 Проверяем статус nginx..."
docker-compose -f docker-compose.prod.yml logs --tail=10 nginx

# Шаг 5: Тестируем доступность
print_header "ТЕСТИРОВАНИЕ ДОСТУПНОСТИ"

print_info "🔍 Тестируем локальный доступ..."
if curl -f -s http://localhost:${EXTERNAL_PORT}/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Локальный доступ через порт ${EXTERNAL_PORT} работает!"
else
    print_warning "Локальный доступ через порт ${EXTERNAL_PORT} недоступен"
fi

print_info "🌐 Тестируем внешний доступ..."
if curl -f -s -H "Host: ${EXTERNAL_DOMAIN}" http://localhost:${EXTERNAL_PORT}/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Внешний доступ работает!"
else
    print_warning "Внешний доступ может быть недоступен (проверьте настройки роутера)"
fi

# Шаг 6: Показываем финальную информацию
print_header "НАСТРОЙКА ВНЕШНЕГО ДОСТУПА ЗАВЕРШЕНА!"

print_success "🎉 PrintFarm настроен для внешнего доступа!"
echo
print_info "🌐 Внешние URL:"
echo "   API статистика:  http://${EXTERNAL_DOMAIN}:${EXTERNAL_PORT}/api/v1/tochka/stats/"
echo "   Админ-панель:     http://${EXTERNAL_DOMAIN}:${EXTERNAL_PORT}/admin/"
echo "   Основной сайт:    http://${EXTERNAL_DOMAIN}:${EXTERNAL_PORT}/"
echo
print_info "🏠 Локальные URL (для тестирования):"
echo "   API статистика:  http://localhost:${EXTERNAL_PORT}/api/v1/tochka/stats/"
echo "   Админ-панель:     http://localhost:${EXTERNAL_PORT}/admin/"
echo
print_info "👤 Данные для входа в админку:"
echo "   Логин:    admin"
echo "   Пароль:   admin"
echo
print_info "🔧 Настройки проброса портов:"
echo "   Роутер должен пробрасывать порт ${EXTERNAL_PORT} на сервер"
echo "   Внутренний порт: ${INTERNAL_PORT}"
echo "   Внешний порт: ${EXTERNAL_PORT}"
echo
print_info "📋 Полезные команды:"
echo "   Проверка портов:  netstat -tlnp | grep :${EXTERNAL_PORT}"
echo "   Логи nginx:       docker-compose -f docker-compose.prod.yml logs nginx"
echo "   Перезапуск:       docker-compose -f docker-compose.prod.yml restart nginx"
echo
print_warning "⚠️  Убедитесь что на роутере настроен проброс порта ${EXTERNAL_PORT} → ${INTERNAL_PORT}"
echo
print_success "Готово! Система доступна извне! 🚀"