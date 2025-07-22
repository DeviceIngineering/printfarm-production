# Решение проблем с доступом с разных IP адресов

## Проблема
Пользователи с разных компьютеров/IP адресов не могут получить доступ к API - не загружаются склады, группы товаров, невозможна синхронизация.

## Причина
CORS (Cross-Origin Resource Sharing) политики Django блокируют запросы с внешних IP адресов.

## Быстрое решение

### На сервере выполните:
```bash
cd /opt/printfarm  # или ваш путь к проекту
./deploy/fix_cors.sh
```

## Ручное решение (если скрипт не сработал)

### 1. Обновите код
```bash
git pull origin main
```

### 2. Остановите сервисы
```bash
docker-compose down
```

### 3. Установите переменную окружения
```bash
export DJANGO_SETTINGS_MODULE="config.settings.server_production"
```

### 4. Создайте файл .env
```bash
echo "DJANGO_SETTINGS_MODULE=config.settings.server_production" > .env
```

### 5. Запустите с новыми настройками
```bash
DJANGO_SETTINGS_MODULE=config.settings.server_production docker-compose up -d --build
```

## Проверка исправления

### Проверка 1: API доступность
```bash
curl -H "Origin: http://example.com" http://localhost:8000/api/v1/settings/system-info/
```
Должен вернуть JSON с информацией о системе.

### Проверка 2: CORS заголовки
```bash
curl -v -H "Origin: http://example.com" -H "Access-Control-Request-Method: GET" -X OPTIONS http://localhost:8000/api/v1/sync/warehouses/
```
В ответе должны быть заголовки:
- `Access-Control-Allow-Origin: http://example.com` или `*`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS, ...`

### Проверка 3: Тест с другого компьютера
1. Откройте http://kemomail3.keenetic.pro:3000/ с другого компьютера
2. Перейдите в "Настройки" 
3. Нажмите "Обновить список" для складов
4. Если появился список складов - проблема решена

## Что изменилось

### В production настройках:
- `CORS_ALLOW_ALL_ORIGINS = True` - разрешены все origins
- `ALLOWED_HOSTS = ['*']` - разрешены все хосты
- Отключены строгие SSL/HTTPS настройки
- Смягчены настройки cookies и CSRF

### Новый файл настроек:
- `backend/config/settings/server_production.py` - специальные настройки для сервера

## Диагностика проблем

### Если по-прежнему не работает:

1. **Проверьте логи Django:**
```bash
docker-compose logs backend | grep -i cors
```

2. **Проверьте файрвол:**
```bash
sudo ufw status
```
Порты 3000 и 8000 должны быть открыты.

3. **Проверьте настройки Docker:**
```bash
docker-compose ps
```
Все контейнеры должны быть "Up".

4. **Проверьте переменные окружения:**
```bash
docker-compose exec backend printenv | grep DJANGO_SETTINGS_MODULE
```
Должно быть: `DJANGO_SETTINGS_MODULE=config.settings.server_production`

## Откат изменений

Если что-то пошло не так, вернитесь к обычным настройкам:
```bash
export DJANGO_SETTINGS_MODULE="config.settings.production"
docker-compose restart backend
```

## Безопасность

⚠️ **Внимание**: Текущие настройки делают API доступным для всех. Для продакшена рекомендуется:
1. Указать конкретные разрешенные origins в `CORS_ALLOWED_ORIGINS`
2. Включить обратно SSL настройки при использовании HTTPS
3. Ограничить `ALLOWED_HOSTS` конкретными доменами

## Контакты

При возникновении проблем:
1. Запустите `./deploy/status.sh` для диагностики
2. Проверьте логи: `docker-compose logs -f backend`
3. Сообщите о проблеме с приложением логов