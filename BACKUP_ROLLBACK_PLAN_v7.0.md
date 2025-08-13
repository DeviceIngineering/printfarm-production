# 🔄 Backup & Rollback Plan для PrintFarm v7.0

**Дата создания:** 13 августа 2025  
**Версия:** v7.0 Production Deployment  
**Ответственный:** DevOps Team

## 📋 Предварительные требования

### Перед деплоем v7.0:
1. ✅ Создать полный backup текущей системы
2. ✅ Протестировать процедуру восстановления
3. ✅ Подготовить rollback скрипты
4. ✅ Уведомить команду о времени деплоя

## 💾 Backup процедуры

### 1. База данных
```bash
# PostgreSQL backup
pg_dump -h localhost -U printfarm_user -d printfarm_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup с сжатием
pg_dump -h localhost -U printfarm_user -d printfarm_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 2. Файлы приложения
```bash
# Backup кода и медиа файлов
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  /path/to/printfarm

# Backup медиа файлов отдельно
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz /path/to/media/
```

### 3. Конфигурация
```bash
# Backup Docker и nginx конфигов
cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
cp nginx.conf nginx.conf.backup.$(date +%Y%m%d_%H%M%S)

# Backup переменных окружения
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

## 🔄 Rollback процедуры

### Автоматический rollback скрипт:
```bash
#!/bin/bash
# rollback_from_v7.0.sh

set -e

BACKUP_DATE=${1:-"latest"}
BACKUP_DIR="/backups"

echo "🔄 Starting rollback from v7.0 to previous version..."

# 1. Остановить сервисы
echo "📛 Stopping services..."
docker-compose down

# 2. Восстановить базу данных
echo "💾 Restoring database..."
if [ "$BACKUP_DATE" = "latest" ]; then
    BACKUP_FILE=$(ls -t $BACKUP_DIR/backup_*.sql.gz | head -1)
else
    BACKUP_FILE="$BACKUP_DIR/backup_${BACKUP_DATE}.sql.gz"
fi

gunzip -c $BACKUP_FILE | psql -h localhost -U printfarm_user -d printfarm_db

# 3. Восстановить код
echo "📁 Restoring application files..."
git checkout main  # Возврат к main ветке
git reset --hard HEAD~5  # Откат на 5 коммитов назад

# 4. Восстановить конфигурацию
echo "⚙️ Restoring configuration..."
if [ -f ".env.backup.${BACKUP_DATE}" ]; then
    cp .env.backup.${BACKUP_DATE} .env
fi

# 5. Перезапустить сервисы
echo "🚀 Restarting services..."
docker-compose up -d

# 6. Проверить статус
echo "🔍 Checking service status..."
sleep 30
curl -f http://localhost/ || echo "❌ Frontend not responding"
curl -f http://localhost:8000/api/v1/products/ || echo "❌ API not responding"

echo "✅ Rollback completed!"
```

### Ручной rollback:

#### Шаг 1: Остановка сервисов
```bash
docker-compose down
# или
sudo systemctl stop printfarm-backend
sudo systemctl stop printfarm-frontend
sudo systemctl stop nginx
```

#### Шаг 2: Восстановление базы данных
```bash
# Выбрать backup файл
ls -la /backups/backup_*.sql.gz

# Восстановить из backup
gunzip -c /backups/backup_20250813_120000.sql.gz | \
  psql -h localhost -U printfarm_user -d printfarm_db
```

#### Шаг 3: Откат кода
```bash
# Вернуться к предыдущей стабильной версии
git checkout main
git reset --hard 8a7ecd7  # Коммит до v7.0

# Или переключиться на предыдущий тег
git checkout v4.6
```

#### Шаг 4: Восстановление конфигурации
```bash
# Восстановить .env
cp .env.backup.20250813_120000 .env

# Восстановить docker-compose.yml
cp docker-compose.yml.backup.20250813_120000 docker-compose.yml
```

#### Шаг 5: Перезапуск
```bash
docker-compose up -d
# или
sudo systemctl start printfarm-backend
sudo systemctl start printfarm-frontend
sudo systemctl start nginx
```

## 🚨 Критические точки отката

### Немедленный откат при:
- ❌ Главная страница недоступна > 5 минут
- ❌ API возвращает 50x ошибки > 50% запросов
- ❌ База данных недоступна
- ❌ Критические функции (синхронизация МойСклад) не работают

### Отложенный откат при:
- ⚠️ Медленная работа (>3 сек загрузка страниц)
- ⚠️ Ошибки в логах > 10% запросов
- ⚠️ Проблемы с экспортом Excel
- ⚠️ Жалобы пользователей на UI/UX

## 🔍 Мониторинг после rollback

### Проверить через 15 минут:
```bash
# Проверка веб-интерфейса
curl -f http://localhost/ && echo "✅ Frontend OK"

# Проверка API
curl -f http://localhost:8000/api/v1/products/ && echo "✅ API OK"

# Проверка базы данных
docker exec -it db psql -U printfarm_user -d printfarm_db -c "SELECT COUNT(*) FROM products_product;"
```

### Проверить через 1 час:
- Нормальная работа синхронизации
- Отсутствие ошибок в логах
- Стабильное время ответа API

## 📞 Контакты экстренного реагирования

- **DevOps Engineer:** [контакт]
- **Backend Developer:** [контакт]  
- **Frontend Developer:** [контакт]
- **Product Owner:** [контакт]

## 📝 Лог rollback операций

| Дата | Время | Причина | Выполнил | Результат |
|------|-------|---------|----------|-----------|
| | | | | |

---

## ⚡ Быстрые команды

### Экстренный rollback (one-liner):
```bash
./rollback_from_v7.0.sh && echo "Rollback completed, check services"
```

### Проверка статуса после rollback:
```bash
curl -s http://localhost/health && curl -s http://localhost:8000/api/v1/health
```

### Восстановление только БД:
```bash
gunzip -c /backups/backup_latest.sql.gz | psql -h localhost -U printfarm_user -d printfarm_db
```

**🔐 Этот план должен быть протестирован на staging окружении перед production deployment!**