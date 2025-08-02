# 🔧 Исправление ошибки сборки Docker для Production

## ❌ Проблема
При выполнении `docker-compose -f docker-compose.prod.yml build` возникала ошибка:
```
decouple.UndefinedValueError: MOYSKLAD_TOKEN not found. 
Declare it as envvar or define a default value.
```

## ✅ Решение применено

### Что было исправлено:

1. **Переменные окружения теперь имеют дефолтные значения**
   - `backend/config/settings/base.py` - добавлены defaults для MOYSKLAD_TOKEN

2. **collectstatic выполняется при запуске, а не при сборке**
   - Создан `docker/django/entrypoint.prod.sh` 
   - Миграции и сбор статики происходят при старте контейнера

3. **Production Dockerfiles готовы к использованию**
   - `docker/django/Dockerfile.prod` - для Django backend
   - `docker/nginx/Dockerfile.prod` - для Nginx
   - `docker/react/Dockerfile.prod` - для React frontend

## 📋 Как применить исправления на сервере

### Вариант 1: Обновить существующую установку

```bash
# 1. Подключитесь к серверу
ssh printfarm@ваш-сервер

# 2. Перейдите в папку проекта
cd ~/printfarm-production

# 3. Получите последние изменения
git pull origin main

# 4. Пересоберите образы
docker-compose -f docker-compose.prod.yml build --no-cache

# 5. Перезапустите контейнеры
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 6. Проверьте логи
docker-compose -f docker-compose.prod.yml logs backend
```

### Вариант 2: Чистая установка с нуля

```bash
# 1. Удалите старую папку (если есть)
rm -rf ~/printfarm-production

# 2. Клонируйте репозиторий заново
git clone https://github.com/DeviceIngineering/printfarm-production.git
cd printfarm-production

# 3. Создайте .env файл
cp .env.production.example .env
nano .env  # Отредактируйте переменные

# 4. Соберите и запустите
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Создайте суперпользователя
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 🎯 Быстрая проверка работоспособности

```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Должно показать:
#   printfarm_backend_1    Up
#   printfarm_celery_1     Up  
#   printfarm_db_1         Up
#   printfarm_frontend_1   Up
#   printfarm_nginx_1      Up
#   printfarm_redis_1      Up

# Проверить доступность API
curl http://localhost/api/v1/tochka/stats/

# Должен вернуть JSON с статистикой
```

## 📝 Важные изменения в .env файле

Теперь эти переменные **опциональны** (можно не указывать при сборке):
```env
# Эти переменные теперь имеют дефолтные значения
MOYSKLAD_TOKEN=  # Можно оставить пустым при сборке
MOYSKLAD_DEFAULT_WAREHOUSE=  # Можно оставить пустым при сборке
```

Но для работы с МойСклад их нужно заполнить перед запуском!

## 🔄 Если проблема повторяется

1. **Очистите Docker кэш:**
```bash
docker system prune -a
```

2. **Проверьте версию Docker:**
```bash
docker --version  # Должна быть 20.10+
docker-compose --version  # Должна быть 1.29+
```

3. **Убедитесь что .env файл существует:**
```bash
ls -la .env
cat .env | grep MOYSKLAD
```

## ✨ Что нового работает

- ✅ Сборка образов без переменных окружения
- ✅ Автоматические миграции при запуске
- ✅ Автоматический collectstatic при запуске
- ✅ Корректная обработка отсутствующих переменных
- ✅ Production-ready конфигурация

## 📞 Поддержка

Если проблема сохраняется:
1. Запустите диагностику: `./deploy/diagnostics.sh > report.txt`
2. Создайте issue: https://github.com/DeviceIngineering/printfarm-production/issues
3. Приложите файл report.txt

---

*Исправление протестировано и готово к использованию!* 🎉