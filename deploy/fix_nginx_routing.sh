#!/bin/bash

# PrintFarm Production - Исправление nginx маршрутизации
# Устраняет ошибку "Not Found" для внешнего доступа

set -e

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

print_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_info "🔧 Исправляем nginx конфигурацию..."

# Шаг 1: Создаем правильный nginx.conf
cat > nginx.conf << 'EOF'
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
    
    # Корневой маршрут - направляем на backend
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # CORS заголовки
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
    }
    
    # Static files (если есть)
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files (если есть)
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Healthcheck
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

print_success "nginx.conf обновлен"

# Шаг 2: Исправляем ALLOWED_HOSTS в .env
print_info "Исправляем ALLOWED_HOSTS..."
sed -i '/ALLOWED_HOSTS=/d' .env
echo "ALLOWED_HOSTS=*" >> .env
print_success "ALLOWED_HOSTS исправлен"

# Шаг 3: Перезапускаем nginx
print_info "Перезапускаем nginx..."
docker-compose -f docker-compose.prod.yml restart nginx
sleep 5

# Шаг 4: Перезапускаем backend
print_info "Перезапускаем backend..."
docker-compose -f docker-compose.prod.yml restart backend
sleep 10

# Шаг 5: Тестируем
print_info "Тестируем доступ..."

echo "=== ТЕСТ 1: Health check ==="
if curl -f -s http://localhost:8089/health; then
    print_success "Health check работает!"
else
    echo "Health check не работает"
fi

echo -e "\n=== ТЕСТ 2: API статистика ==="
if curl -f -s http://localhost:8089/api/v1/tochka/stats/; then
    print_success "API работает!"
else
    echo "API не работает"
fi

echo -e "\n=== ТЕСТ 3: Корневая страница ==="
if curl -f -s http://localhost:8089/ | head -5; then
    print_success "Корневая страница работает!"
else
    echo "Корневая страница не работает"
fi

# Шаг 6: Показываем логи nginx для диагностики
print_info "Логи nginx:"
docker-compose -f docker-compose.prod.yml logs nginx | tail -10

print_success "Исправление завершено!"
echo "Теперь проверьте: http://kemomail3.keenetic.pro:8089/api/v1/tochka/stats/"