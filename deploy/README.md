# PrintFarm Production - Скрипты развертывания

Набор скриптов для автоматического обновления и управления PrintFarm Production на удаленном сервере.

## 🚀 Быстрое обновление (основной сценарий)

```bash
# 1. Подключиться к серверу
ssh user@your-server.com

# 2. Перейти в директорию проекта
cd /path/to/printfarm-production

# 3. Сделать скрипт исполняемым (только первый раз)
chmod +x deploy/update.sh

# 4. Запустить обновление
./deploy/update.sh
```

Скрипт автоматически:
- ✅ Создаст бэкап базы данных
- ✅ Остановит сервисы
- ✅ Загрузит последние изменения из Git
- ✅ Пересоберет Docker образы
- ✅ Применит миграции базы данных
- ✅ Соберет статические файлы
- ✅ Запустит все сервисы
- ✅ Проверит работоспособность

## 📊 Проверка состояния системы

```bash
# Быстрая проверка всех сервисов
./deploy/status.sh
```

Показывает:
- Версию системы
- Статус всех контейнеров
- Доступность API и Frontend
- Состояние базы данных и Redis
- Использование ресурсов

## 🔄 Откат к предыдущей версии

Если что-то пошло не так после обновления:

```bash
# Откат к предыдущему коммиту
./deploy/rollback.sh ed9ab7b

# Или к определенной версии
./deploy/rollback.sh v3.1.3
```

## 💾 Восстановление из бэкапа

```bash
# Просмотр доступных бэкапов
ls -la backups/*/database.sql

# Восстановление из конкретного бэкапа
./deploy/restore.sh backups/20250722_112905/database.sql
```

## 📁 Структура скриптов

```
deploy/
├── README.md           # Эта инструкция
├── update.sh          # Основной скрипт обновления
├── rollback.sh        # Откат к предыдущей версии
├── restore.sh         # Восстановление БД из бэкапа
└── status.sh          # Проверка состояния системы
```

## ⚙️ Системные требования

- Docker и Docker Compose
- Git
- curl (для проверок)
- Права доступа к файлам проекта

## 🔧 Ручные команды (если нужны)

```bash
# Остановка всех сервисов
docker-compose down

# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Применение только миграций
docker-compose run --rm backend python manage.py migrate

# Создание суперпользователя
docker-compose run --rm backend python manage.py createsuperuser

# Ручное создание бэкапа БД
docker-compose exec -T db pg_dump -U printfarm_user printfarm_db > backup.sql
```

## 🆘 Решение проблем

### Проблема: "Контейнер не запускается"
```bash
# Просмотр подробных логов
docker-compose logs [service_name]

# Пересборка образа
docker-compose build --no-cache [service_name]
```

### Проблема: "Ошибки миграций"
```bash
# Откат миграций
docker-compose run --rm backend python manage.py migrate [app_name] [migration_number]

# Или восстановление из бэкапа
./deploy/restore.sh backups/latest/database.sql
```

### Проблема: "Недостаточно места на диске"
```bash
# Очистка Docker
docker system prune -a -f
docker volume prune -f

# Удаление старых бэкапов (старше 30 дней)
find backups -type f -mtime +30 -delete
```

## 📞 Поддержка

При возникновении проблем:

1. Запустите `./deploy/status.sh` для диагностики
2. Проверьте логи: `docker-compose logs -f`
3. При критических ошибках: `./deploy/rollback.sh [commit_hash]`

## 🔐 Безопасность

- Все скрипты создают бэкапы перед изменениями
- Бэкапы сохраняются в папке `backups/` с timestamp
- Скрипт отката позволяет быстро вернуться к рабочей версии
- Проверки работоспособности на каждом шаге

---

**PrintFarm Production v3.1.4**  
Автоматизированное развертывание и управление 🚀