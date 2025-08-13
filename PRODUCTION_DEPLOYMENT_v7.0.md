# 🚀 Production Deployment Guide - PrintFarm v7.0

**Версия документа:** 1.0  
**Дата:** 13 августа 2025  
**Версия приложения:** v7.0  
**Ответственный:** DevOps Team

## 📋 Обзор релиза v7.0

### Ключевые изменения:
- 🔧 **Docker Frontend & API Authentication Fixes** 
- 🔐 **Фиксированная аутентификация API** с жестко прописанным токеном
- 🐳 **Исправления Docker контейнеров** - доступность frontend (HOST=0.0.0.0)
- 📊 **Celery worker dependencies** исправлены (psutil)
- 🔄 **Полная функциональность синхронизации** - 711/725 продуктов
- 🧪 **Debug компоненты** активны для мониторинга

### Системные требования:
- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **PostgreSQL:** 15+
- **Redis:** 7+
- **Node.js:** 18+ (для frontend)
- **Python:** 3.11+

## 🏗️ Предварительная подготовка

### 1. Backup текущей системы
```bash
# Создать папку для backup
mkdir -p /backups/$(date +%Y%m%d_%H%M%S)
cd /backups/$(date +%Y%m%d_%H%M%S)

# Backup базы данных
pg_dump -h localhost -U printfarm_user -d printfarm_db | gzip > database_backup.sql.gz

# Backup файлов приложения
tar -czf app_backup.tar.gz /path/to/current/printfarm

# Backup конфигураций
cp /path/to/current/.env ./env_backup
cp /path/to/current/docker-compose.yml ./docker_compose_backup.yml
```

### 2. Проверка ресурсов
```bash
# Проверить место на диске (нужно минимум 5GB)
df -h

# Проверить RAM (нужно минимум 4GB)
free -h

# Проверить состояние Docker
docker system df
docker system prune -f  # Очистить неиспользуемые ресурсы
```

### 3. Создание пользователей и папок
```bash
# Создать пользователя для приложения (если не существует)
sudo useradd -m -s /bin/bash printfarm

# Создать структуру папок
sudo mkdir -p /opt/printfarm/{logs,media,static,backups}
sudo chown -R printfarm:printfarm /opt/printfarm
```

## 📦 Deployment процедура

### Шаг 1: Получение кода v7.0
```bash
# Клонировать репозиторий или обновить
cd /opt/printfarm
git clone https://github.com/your-org/printfarm.git .
# или
git fetch --all
git checkout v7.0
```

### Шаг 2: Настройка окружения
```bash
# Создать .env файл
cp .env.example .env

# Настроить переменные окружения
cat > .env << EOF
# Django
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=super-secure-password
DATABASE_URL=postgresql://printfarm_user:super-secure-password@db:5432/printfarm_db

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад API
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend
REACT_APP_API_URL=http://your-domain.com:8000/api/v1
EOF
```

### Шаг 3: Сборка и запуск контейнеров
```bash
# Остановить старые контейнеры
docker-compose down

# Собрать новые образы
docker-compose build --no-cache

# Запустить сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

### Шаг 4: Инициализация базы данных
```bash
# Применить миграции
docker-compose exec backend python manage.py migrate

# Создать суперпользователя (если нужно)
docker-compose exec backend python manage.py createsuperuser

# Собрать статические файлы
docker-compose exec backend python manage.py collectstatic --noinput
```

### Шаг 5: Проверка функциональности
```bash
# Проверить веб-интерфейс
curl -f http://localhost/ || echo "❌ Frontend недоступен"

# Проверить API
curl -f http://localhost:8000/api/v1/products/ || echo "❌ API недоступен"

# Проверить админку
curl -f http://localhost:8000/admin/ || echo "❌ Admin недоступен"

# Проверить логи
docker-compose logs backend | tail -20
docker-compose logs frontend | tail -20
```

## 🔧 Настройка Nginx (Production)

### Конфигурация nginx.conf:
```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Admin
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Static files
    location /static/ {
        alias /opt/printfarm/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Media files
    location /media/ {
        alias /opt/printfarm/media/;
        expires 7d;
    }
}
```

## 📊 Системы мониторинга

### 1. Логирование
```bash
# Настроить ротацию логов
sudo tee /etc/logrotate.d/printfarm << EOF
/opt/printfarm/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Настроить rsyslog для централизованного логирования
echo "*.* @@log-server:514" >> /etc/rsyslog.conf
systemctl restart rsyslog
```

### 2. Health checks
```bash
# Создать health check скрипт
cat > /opt/printfarm/health_check.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 PrintFarm v7.0 Health Check"

# Frontend check
if curl -f -s http://localhost/ > /dev/null; then
    echo "✅ Frontend: OK"
else
    echo "❌ Frontend: FAIL"
    exit 1
fi

# API check
if curl -f -s http://localhost:8000/api/v1/products/ > /dev/null; then
    echo "✅ API: OK"
else
    echo "❌ API: FAIL"
    exit 1
fi

# Database check
if docker-compose exec -T db pg_isready -U printfarm_user; then
    echo "✅ Database: OK"
else
    echo "❌ Database: FAIL"
    exit 1
fi

# Redis check
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis: OK"
else
    echo "❌ Redis: FAIL"
    exit 1
fi

echo "✅ All systems operational"
EOF

chmod +x /opt/printfarm/health_check.sh
```

### 3. Мониторинг производительности
```bash
# Установить htop для мониторинга ресурсов
sudo apt-get install htop iotop

# Настроить мониторинг Docker контейнеров
cat > /opt/printfarm/monitor_containers.sh << 'EOF'
#!/bin/bash
echo "📊 Container Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
EOF

chmod +x /opt/printfarm/monitor_containers.sh
```

## 🚨 Процедуры экстренного реагирования

### При падении сервисов:
```bash
# Быстрая диагностика
docker-compose ps
docker-compose logs --tail=50

# Перезапуск всех сервисов
docker-compose restart

# Полная перезагрузка
docker-compose down && docker-compose up -d
```

### При проблемах с производительностью:
```bash
# Очистить логи
docker-compose exec backend sh -c "echo '' > /app/logs/django.log"

# Очистить кэш Redis
docker-compose exec redis redis-cli FLUSHALL

# Перезапуск Celery worker
docker-compose restart celery
```

## 📞 Контакты поддержки

- **Production Issues:** DevOps Engineer
- **Application Bugs:** Backend Team Lead  
- **UI/UX Issues:** Frontend Team Lead
- **Business Logic:** Product Owner

## ✅ Post-deployment чек-лист

- [ ] Все контейнеры запущены
- [ ] Frontend доступен на http://your-domain.com
- [ ] API отвечает на http://your-domain.com:8000/api/v1/
- [ ] Админка доступна на http://your-domain.com:8000/admin/
- [ ] Синхронизация МойСклад работает
- [ ] Экспорт Excel функционирует
- [ ] Логи не содержат критических ошибок
- [ ] SSL сертификаты настроены
- [ ] Backup план протестирован
- [ ] Мониторинг настроен
- [ ] Команда уведомлена о деплое

---

**🔐 Безопасность:** Убедитесь, что все пароли и токены изменены с дефолтных значений!  
**📊 Мониторинг:** Следите за производительностью в первые 24 часа после деплоя.