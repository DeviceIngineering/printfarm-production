# 📁 SimplePrint Files Integration - План реализации

**Дата:** 22 октября 2025
**Версия:** v4.2.1
**Задача:** Интеграция с SimplePrint API для синхронизации G-code файлов

---

## 🎯 Цель

Загрузить и синхронизировать всю информацию о G-code файлах из SimplePrint:
- Получение списка файлов и папок
- Сохранение в локальную базу данных
- Автоматическая синхронизация при изменениях (добавление, изменение, удаление)
- Отслеживание изменений через webhooks

---

## 📊 Информация о SimplePrint API

**Credentials:**
```
API Token: 18f82f78-f45a-46bb-aec8-3792048acccd
User ID: 31471
Company ID: 27286
Base URL: https://api.simplyprint.io/27286/
Rate Limit: 180 requests/min (3 req/sec)
```

**Ключевые endpoints:**
- `GET /files/GetFiles` - список файлов и папок ✅
- `GET /files/GetFolder` - детали папки
- `POST /files/DeleteFiles` - удаление файлов
- `POST /files/DeleteFolders` - удаление папок
- `GET /webhooks` - список webhooks
- `POST /webhooks` - создание webhook

**Аутентификация:**
- Заголовок: `X-API-KEY: 18f82f78-f45a-46bb-aec8-3792048acccd`

---

## 📋 План реализации (5 этапов)

### ЭТАП 1: Настройка и тестирование API (30 мин)

#### Шаг 1.1: Настройка credentials
**Задачи:**
- [ ] Добавить переменные в `.env`:
  ```
  SIMPLEPRINT_API_TOKEN=18f82f78-f45a-46bb-aec8-3792048acccd
  SIMPLEPRINT_USER_ID=31471
  SIMPLEPRINT_COMPANY_ID=27286
  SIMPLEPRINT_BASE_URL=https://api.simplyprint.io/27286/
  SIMPLEPRINT_RATE_LIMIT=180
  ```
- [ ] Добавить конфигурацию в `backend/config/settings/base.py`

**Git commit:**
```
🔧 Config: Add SimplePrint API credentials
```

---

#### Шаг 1.2: Тестовый скрипт подключения
**Задачи:**
- [ ] Создать скрипт `test_simpleprint_connection.py`
- [ ] Проверить подключение к API
- [ ] Получить список файлов (первые 10)
- [ ] Вывести структуру данных
- [ ] Запустить и проверить результат

**Тест:**
```bash
python backend/test_simpleprint_connection.py
```

**Ожидаемый результат:**
- Успешное подключение
- Список файлов получен
- Структура данных понятна

**Логгирование:**
- Статус подключения
- Количество файлов
- Пример структуры файла

**Git commit:**
```
🧪 Test: Add SimplePrint API connection test
```

---

### ЭТАП 2: Django модели (1 час)

#### Шаг 2.1: Создать Django app (если еще не создано)
**Задачи:**
- [ ] Создать или использовать app `simpleprint`
- [ ] Добавить в INSTALLED_APPS

**Git commit:**
```
🎬 Init: Setup SimplePrint app structure
```

---

#### Шаг 2.2: Модели для файлов и папок
**Задачи:**
- [ ] Создать модель `SimplePrintFolder`:
  - simpleprint_id (ID папки в SimplePrint)
  - name (название)
  - parent (связь с родительской папкой, ForeignKey на себя)
  - path (полный путь)
  - created_at, updated_at
  - last_synced_at
- [ ] Создать модель `SimplePrintFile`:
  - simpleprint_id (ID файла/хеш)
  - name (имя файла)
  - folder (ForeignKey на SimplePrintFolder)
  - size (размер в байтах)
  - file_type (тип: gcode, stl, etc)
  - uploaded_at (дата загрузки в SimplePrint)
  - expires_at (дата истечения, если есть)
  - file_hash (MD5/SHA хеш файла)
  - metadata (JSONField для дополнительных данных)
  - created_at, updated_at, last_synced_at
- [ ] Добавить индексы для быстрого поиска
- [ ] Создать миграции
- [ ] Применить миграции

**Тесты:**
- Создание папки
- Создание файла
- Связь файл-папка
- Иерархия папок

**Логгирование:**
- Создание/обновление записей

**Git commit:**
```
💾 Models: Add SimplePrint files and folders models
```

---

### ЭТАП 3: API клиент и синхронизация (2-3 часа)

#### Шаг 3.1: SimplePrint API клиент
**Задачи:**
- [ ] Создать класс `SimplePrintFilesClient` в `backend/apps/simpleprint/client.py`
- [ ] Реализовать методы:
  - `get_files_and_folders()` - получить все файлы и папки
  - `get_folder_details(folder_id)` - детали папки
  - `test_connection()` - проверка подключения
- [ ] Добавить обработку rate limit (3 req/sec)
- [ ] Добавить retry логику
- [ ] Добавить кэширование (5 минут)

**Тесты:**
- Получение списка файлов (mock API)
- Обработка ошибок
- Rate limiting
- Кэширование

**Логгирование:**
- Каждый API запрос
- Rate limit статус
- Ошибки

**Git commit:**
```
✨ Feature: Add SimplePrint files API client
```

---

#### Шаг 3.2: Сервис синхронизации
**Задачи:**
- [ ] Создать класс `SimplePrintSyncService` в `backend/apps/simpleprint/services.py`
- [ ] Реализовать `sync_all_files()`:
  - Получить данные из API
  - Обработать папки (создать/обновить иерархию)
  - Обработать файлы (создать/обновить)
  - Удалить файлы которых нет в SimplePrint
  - Записать статистику синхронизации
- [ ] Добавить модель `SimplePrintSync` для истории:
  - status, started_at, finished_at
  - total_folders, synced_folders
  - total_files, synced_files, deleted_files
  - error_details
- [ ] Реализовать инкрементальную синхронизацию

**Тесты:**
- Полная синхронизация
- Добавление новых файлов
- Обновление существующих
- Удаление отсутствующих
- Обработка ошибок

**Логгирование:**
- Начало/конец синхронизации
- Прогресс (каждые 50 файлов)
- Статистика
- Ошибки

**Git commit:**
```
⚙️ Services: Add files synchronization service
```

---

#### Шаг 3.3: Management команда для синхронизации
**Задачи:**
- [ ] Создать команду `python manage.py sync_simpleprint_files`
- [ ] Добавить параметры:
  - `--full` - полная синхронизация
  - `--force` - принудительная
- [ ] Запустить тест синхронизации
- [ ] Проверить результаты в БД

**Тест:**
```bash
python manage.py sync_simpleprint_files --full
```

**Ожидаемый результат:**
- Все файлы и папки загружены
- Иерархия восстановлена
- Статистика выведена

**Git commit:**
```
🔧 Command: Add sync_simpleprint_files management command
```

---

### ЭТАП 4: Webhooks для отслеживания изменений (1-2 часа)

#### Шаг 4.1: Webhook endpoint
**Задачи:**
- [ ] Создать view `SimplePrintWebhookView` в `backend/apps/simpleprint/views.py`
- [ ] Endpoint: `POST /api/v1/simpleprint/webhook/`
- [ ] Обработка событий:
  - file_created - создан новый файл
  - file_updated - файл обновлен
  - file_deleted - файл удален
  - folder_created - создана папка
  - folder_deleted - папка удалена
- [ ] Валидация webhook (проверка подписи если есть)
- [ ] Запуск синхронизации конкретного файла/папки
- [ ] Логирование всех webhook событий

**Тесты:**
- Обработка разных типов событий
- Валидация данных
- Ошибочные запросы

**Логгирование:**
- Получение webhook
- Тип события
- Результат обработки

**Git commit:**
```
🔗 Webhook: Add SimplePrint webhook endpoint
```

---

#### Шаг 4.2: Регистрация webhook в SimplePrint
**Задачи:**
- [ ] Создать скрипт `setup_simpleprint_webhook.py`
- [ ] Зарегистрировать webhook URL в SimplePrint:
  - URL: `https://your-domain.com/api/v1/simpleprint/webhook/`
  - События: file_created, file_updated, file_deleted, folder_created, folder_deleted
- [ ] Сохранить webhook ID в настройках
- [ ] Протестировать получение событий

**Важно:**
Для локальной разработки использовать ngrok или подобные сервисы для публикации endpoint

**Git commit:**
```
🔗 Webhook: Register webhook in SimplePrint
```

---

### ЭТАП 5: REST API и автоматизация (1-2 часа)

#### Шаг 5.1: REST API endpoints
**Задачи:**
- [ ] Создать `SimplePrintFileViewSet`:
  - `GET /api/v1/simpleprint/files/` - список файлов
  - `GET /api/v1/simpleprint/files/{id}/` - детали файла
  - `GET /api/v1/simpleprint/folders/` - список папок
  - `POST /api/v1/simpleprint/files/sync/` - запуск синхронизации
  - `GET /api/v1/simpleprint/files/stats/` - статистика
- [ ] Добавить фильтрацию (по папке, типу файла)
- [ ] Добавить поиск по имени
- [ ] Добавить пагинацию
- [ ] Создать serializers

**Тесты:**
- Получение списка
- Фильтрация
- Поиск
- Запуск синхронизации

**Логгирование:**
- API запросы
- Результаты

**Git commit:**
```
🚀 API: Add SimplePrint files REST API
```

---

#### Шаг 5.2: Автоматическая синхронизация (Celery)
**Задачи:**
- [ ] Создать Celery задачу `sync_simpleprint_files_task`
- [ ] Настроить Celery Beat для регулярного запуска:
  - Каждые 30 минут (или настраиваемо)
- [ ] Добавить обработку ошибок
- [ ] Уведомления при ошибках

**Тесты:**
- Запуск задачи
- Обработка ошибок

**Логгирование:**
- Начало/конец задачи
- Результаты

**Git commit:**
```
⏰ Celery: Add scheduled files synchronization
```

---

#### Шаг 5.3: Интеграция с вкладкой "Точка"
**Задачи:**
- [ ] Создать endpoint `GET /api/v1/simpleprint/files/for_tochka/`
- [ ] Вернуть файлы сгруппированные по артикулам
- [ ] Добавить связь SimplePrintFile с Product (по артикулу в имени файла)
- [ ] Добавить отображение на TochkaPage

**Git commit:**
```
🔗 Integration: Connect SimplePrint files with Tochka
```

---

## 📊 Структура базы данных

```
SimplePrintFolder
├── id (PK)
├── simpleprint_id (unique)
├── name
├── parent_id (FK to self)
├── path
├── created_at
├── updated_at
└── last_synced_at

SimplePrintFile
├── id (PK)
├── simpleprint_id (unique)
├── name
├── folder_id (FK to SimplePrintFolder)
├── size
├── file_type
├── uploaded_at
├── expires_at
├── file_hash
├── metadata (JSON)
├── product_id (FK to Product, nullable)
├── created_at
├── updated_at
└── last_synced_at

SimplePrintSync
├── id (PK)
├── status
├── started_at
├── finished_at
├── total_folders
├── synced_folders
├── total_files
├── synced_files
├── deleted_files
└── error_details
```

---

## 🔄 Алгоритм синхронизации

### Полная синхронизация:
1. Получить все папки из SimplePrint API
2. Создать/обновить папки в БД (восстановить иерархию)
3. Получить все файлы из SimplePrint API
4. Для каждого файла:
   - Проверить существует ли в БД
   - Если нет - создать
   - Если есть - обновить если изменился
5. Найти файлы в БД которых нет в SimplePrint - удалить
6. Записать статистику

### Инкрементальная синхронизация (через webhook):
1. Получить событие
2. Обработать изменение (создать/обновить/удалить)
3. Записать в лог

---

## ⏱️ Оценка времени

```
Этап 1: Настройка и тестирование    - 30 мин
Этап 2: Django модели               - 1 час
Этап 3: API клиент и синхронизация  - 2-3 часа
Этап 4: Webhooks                    - 1-2 часа
Этап 5: REST API и автоматизация    - 1-2 часа
```

**Итого: 5.5-8.5 часов**

---

## ✅ Критерии готовности

- [ ] Все файлы и папки загружены из SimplePrint
- [ ] Иерархия папок восстановлена
- [ ] Синхронизация работает (ручная и автоматическая)
- [ ] Webhooks настроены и обрабатываются
- [ ] REST API endpoints работают
- [ ] Тесты написаны и проходят
- [ ] Логгирование работает
- [ ] Celery задача настроена
- [ ] Интеграция с Точкой (опционально)

---

## 🚀 Запуск после реализации

### Первая синхронизация:
```bash
python manage.py sync_simpleprint_files --full
```

### Проверка результатов:
```bash
python manage.py shell
>>> from apps.simpleprint.models import SimplePrintFile, SimplePrintFolder
>>> SimplePrintFolder.objects.count()  # Количество папок
>>> SimplePrintFile.objects.count()     # Количество файлов
```

### API:
```
GET /api/v1/simpleprint/files/
GET /api/v1/simpleprint/files/stats/
POST /api/v1/simpleprint/files/sync/
```

---

## 📝 Примечания

1. **Rate Limiting:** 180 req/min = 3 req/sec. Добавить задержки между запросами.
2. **Webhooks:** Для локальной разработки использовать ngrok
3. **Кэширование:** Кэшировать список файлов на 5 минут
4. **Связь с Product:** Извлекать артикул из имени файла (regex)
5. **Мониторинг:** Логировать все синхронизации и ошибки

---

**Начните с Этапа 1!** 🚀
