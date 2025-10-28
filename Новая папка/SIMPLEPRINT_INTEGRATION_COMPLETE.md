# SimplePrint Files Integration - Завершено ✅

**Дата завершения:** 22 октября 2025
**Версия:** PrintFarm v4.2.1
**Статус:** ✅ Полностью реализовано

---

## 📊 Выполненные этапы

### ✅ Этап 1: Настройка и тестирование API (30 мин)
- [x] Добавлены credentials в `.env` и `settings.py`
- [x] Создан тестовый скрипт `test_simpleprint_connection.py`
- [x] Проверено подключение к SimplePrint API
- [x] Получены данные: 1 файл и 12 папок
- [x] Git commit: `🔧 Config: Add SimplePrint API credentials`

### ✅ Этап 2: Django модели (1 час)
- [x] Создано приложение `apps/simpleprint`
- [x] Модель `SimplePrintFolder` - иерархия папок
- [x] Модель `SimplePrintFile` - файлы с метаданными
- [x] Модель `SimplePrintSync` - история синхронизаций
- [x] Модель `SimplePrintWebhookEvent` - логирование webhooks
- [x] Django admin интерфейс с фильтрами
- [x] Миграции созданы и применены
- [x] Git commit: `💾 Models: Add SimplePrint files and folders models`

### ✅ Этап 3: API клиент и синхронизация (2 часа)
- [x] `SimplePrintFilesClient` с rate limiting (180 req/min)
- [x] Retry логика с exponential backoff
- [x] Защита от циклических ссылок
- [x] `SimplePrintSyncService` для полной синхронизации
- [x] Management команда: `python manage.py sync_simpleprint_files`
- [x] Опциональный Redis кэш
- [x] Git commit: `⚙️ Services: Add SimplePrint files synchronization service`

### ✅ Этап 4: Webhooks (1.5 часа)
- [x] Модель `SimplePrintWebhookEvent` для логирования
- [x] Webhook view для приема событий
- [x] Обработка событий: file_created, file_updated, file_deleted, folder_created, folder_deleted
- [x] URL: `POST /api/v1/simpleprint/webhook/`
- [x] AllowAny permission (SimplePrint не поддерживает webhook auth)
- [x] Git commit: `🔗 Webhook: Add SimplePrint webhook endpoint`

### ✅ Этап 5: REST API и автоматизация (2 часа)
- [x] REST API ViewSets для файлов, папок, синхронизаций
- [x] Serializers с computed fields
- [x] Фильтрация, поиск, сортировка
- [x] Celery задачи для автоматической синхронизации
- [x] Celery Beat расписание (каждые 30 минут)
- [x] Git commit: `🚀 API: Add SimplePrint files REST API and automation`

---

## 📚 API Endpoints

### Files (Файлы)
```
GET    /api/v1/simpleprint/files/              # Список файлов
GET    /api/v1/simpleprint/files/{id}/         # Детали файла
GET    /api/v1/simpleprint/files/stats/        # Статистика файлов
```

**Фильтры:** `folder`, `file_type`, `ext`
**Поиск:** `name`, `simpleprint_id`
**Сортировка:** `name`, `size`, `created_at_sp`, `last_synced_at`

### Folders (Папки)
```
GET    /api/v1/simpleprint/folders/            # Список папок
GET    /api/v1/simpleprint/folders/{id}/       # Детали папки
GET    /api/v1/simpleprint/folders/{id}/files/ # Файлы в папке
```

**Фильтры:** `parent`, `depth`
**Поиск:** `name`, `simpleprint_id`
**Сортировка:** `name`, `depth`, `files_count`, `last_synced_at`

### Sync (Синхронизация)
```
GET    /api/v1/simpleprint/sync/               # История синхронизаций
GET    /api/v1/simpleprint/sync/{id}/          # Детали синхронизации
POST   /api/v1/simpleprint/sync/trigger/       # Запустить синхронизацию
GET    /api/v1/simpleprint/sync/stats/         # Статистика синхронизации
```

**POST /api/v1/simpleprint/sync/trigger/ - Request Body:**
```json
{
  "full_sync": false,  // полная синхронизация с удалением
  "force": false       // игнорировать cooldown 5 минут
}
```

### Webhook
```
POST   /api/v1/simpleprint/webhook/            # Прием событий от SimplePrint
```

---

## 🚀 Использование

### 1. Ручная синхронизация (Management команда)
```bash
# Обычная синхронизация
python manage.py sync_simpleprint_files

# Полная синхронизация с удалением отсутствующих файлов
python manage.py sync_simpleprint_files --full

# Принудительная синхронизация (игнорировать cooldown)
python manage.py sync_simpleprint_files --force
```

### 2. API синхронизация
```bash
# Запустить синхронизацию через API
curl -X POST http://localhost:8000/api/v1/simpleprint/sync/trigger/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": false, "force": false}'

# Получить статистику
curl http://localhost:8000/api/v1/simpleprint/sync/stats/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### 3. Автоматическая синхронизация (Celery)
```bash
# Celery Beat автоматически запускает синхронизацию каждые 30 минут
# Настройка в config/celery.py:

'simpleprint-sync-30min': {
    'task': 'simpleprint.scheduled_sync',
    'schedule': 60.0 * 30.0,  # 30 minutes
}

# Запуск Celery Beat
celery -A config beat -l info
```

### 4. Просмотр данных
```bash
# Список файлов
curl http://localhost:8000/api/v1/simpleprint/files/ \
  -H "Authorization: Token YOUR_TOKEN"

# Поиск файлов
curl "http://localhost:8000/api/v1/simpleprint/files/?search=gcode&file_type=printable" \
  -H "Authorization: Token YOUR_TOKEN"

# Статистика файлов
curl http://localhost:8000/api/v1/simpleprint/files/stats/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

## 🗄️ Модели данных

### SimplePrintFolder
```python
- simpleprint_id: int (unique)
- name: str
- parent: FK (self)
- depth: int
- files_count: int
- folders_count: int
- created_at_sp, created_at, updated_at, last_synced_at
```

### SimplePrintFile
```python
- simpleprint_id: str (unique)
- name: str
- folder: FK (SimplePrintFolder)
- ext, file_type, size
- tags: JSON (materials, nozzle)
- print_data: JSON (statistics)
- cost_data: JSON
- gcode_analysis: JSON (estimate, filament, temps)
- created_at_sp, created_at, updated_at, last_synced_at
```

### SimplePrintSync
```python
- status: pending/success/failed/partial
- started_at, finished_at
- total_folders, synced_folders
- total_files, synced_files, deleted_files
- error_details
```

### SimplePrintWebhookEvent
```python
- event_type: file_created/file_updated/file_deleted/...
- payload: JSON
- processed: bool
- processed_at
- processing_error
```

---

## ⚙️ Конфигурация

### .env файл
```env
SIMPLEPRINT_API_TOKEN=18f82f78-f45a-46bb-aec8-3792048acccd
SIMPLEPRINT_USER_ID=31471
SIMPLEPRINT_COMPANY_ID=27286
SIMPLEPRINT_BASE_URL=https://api.simplyprint.io/27286/
SIMPLEPRINT_RATE_LIMIT=180
```

### settings.py
```python
SIMPLEPRINT_CONFIG = {
    'api_token': config('SIMPLEPRINT_API_TOKEN', default=''),
    'user_id': config('SIMPLEPRINT_USER_ID', default='31471'),
    'company_id': config('SIMPLEPRINT_COMPANY_ID', default='27286'),
    'base_url': config('SIMPLEPRINT_BASE_URL', default='https://api.simplyprint.io/27286/'),
    'rate_limit': config('SIMPLEPRINT_RATE_LIMIT', default=180, cast=int),
}
```

---

## 🔧 Особенности реализации

### Rate Limiting
- API ограничение: 180 req/min = 3 req/sec
- Автоматическая задержка между запросами
- Защита от превышения лимитов

### Retry Logic
- 3 попытки для каждого запроса
- Exponential backoff: 1s, 2s, 4s
- Retry только для серверных ошибок (5xx)

### Защита от циклов
- Tracking посещенных папок
- Предотвращение бесконечной рекурсии

### Кэширование
- Redis кэш на 5 минут (опционально)
- Graceful degradation если Redis недоступен

### Cooldown
- 5 минут между синхронизациями
- Можно обойти через `force=true`

---

## 📊 Статистика реализации

**Всего файлов создано/изменено:** ~20 файлов
**Строк кода:** ~2500 строк
**Git коммитов:** 5 коммитов
**Время реализации:** ~6.5 часов
**API endpoints:** 13 endpoints

---

## 🎯 Дальнейшее развитие

### Возможные улучшения:
1. **Frontend страница** - визуализация файлов и папок
2. **Webhook регистрация** - автоматическая регистрация webhook в SimplePrint
3. **Инкрементальная синхронизация** - синхронизация только измененных файлов
4. **Связь с Product** - автоматическое сопоставление файлов с товарами по артикулу
5. **Thumbnail preview** - предпросмотр изображений файлов
6. **Batch операции** - массовое удаление, перемещение файлов
7. **Export/Import** - экспорт списка файлов в Excel

---

## 📝 Примечания

1. **Первая синхронизация** может занять 10-20 минут для ~700 папок
2. **Webhooks** требуют публичный URL (ngrok для локальной разработки)
3. **Celery Beat** должен быть запущен для автоматической синхронизации
4. **Redis** опционален, но рекомендуется для production

---

## ✅ Проверка работоспособности

```bash
# 1. Проверить подключение к API
python backend/test_simpleprint_connection.py

# 2. Запустить синхронизацию
python manage.py sync_simpleprint_files

# 3. Проверить данные в БД
python manage.py shell
>>> from apps.simpleprint.models import SimplePrintFile, SimplePrintFolder
>>> SimplePrintFolder.objects.count()  # Количество папок
>>> SimplePrintFile.objects.count()     # Количество файлов

# 4. Проверить API endpoint
curl http://localhost:8000/api/v1/simpleprint/sync/stats/ \
  -H "Authorization: Token YOUR_TOKEN"
```

---

**Интеграция SimplePrint Files успешно завершена! 🎉**
