# SimplePrint Tests - Инструкция

## 📋 Описание

Полный набор тестов для SimplePrint интеграции с детальной диагностикой каждого компонента.

## 🧪 Структура тестов

### 1. `test_client.py` - Тесты API клиента (5 тестов)

Проверяет работу SimplePrint API клиента (`apps/simpleprint/client.py`):

- **Тест 1**: Инициализация клиента
  - Проверяет наличие всех настроек в `settings.py`
  - Валидирует API token, user_id, company_id, base_url

- **Тест 2**: Подключение к API
  - Тестирует метод `test_connection()`
  - Проверяет GET `/account/Test`

- **Тест 3**: Получение файлов и папок
  - Тестирует `get_files_and_folders()`
  - Проверяет GET `/files/GetFiles`
  - Валидирует структуру ответа

- **Тест 4**: Rate Limiting
  - Проверяет соблюдение лимита 180 req/min
  - Измеряет задержки между запросами

- **Тест 5**: Обработка ошибок
  - Тестирует retry логику (3 попытки)
  - Симулирует 500 Server Error

### 2. `test_sync.py` - Тесты синхронизации (5 тестов)

Проверяет сервис синхронизации (`apps/simpleprint/services.py`):

- **Тест 1**: Создание записи синхронизации
  - Проверяет `SimplePrintSync.objects.create()`
  - Валидирует сохранение в БД

- **Тест 2**: Получение всех данных из API
  - Тестирует `fetch_all_files_and_folders_recursively()`
  - Проверяет парсинг ответа API

- **Тест 3**: Сохранение папок в БД
  - Тестирует `_save_folders_to_db()`
  - Проверяет создание/обновление записей

- **Тест 4**: Сохранение файлов в БД
  - Тестирует `_save_files_to_db()`
  - Проверяет связи с папками (ForeignKey)

- **Тест 5**: Полная синхронизация (E2E)
  - Тестирует `sync_all_files()`
  - Проверяет весь процесс end-to-end

### 3. `test_api.py` - Тесты API endpoints (4 теста)

Проверяет REST API endpoints (`apps/simpleprint/views.py`):

- **Тест 1**: POST `/api/v1/simpleprint/sync/trigger/`
  - Проверяет запуск синхронизации
  - Валидирует ответ 202 ACCEPTED
  - Проверяет вызов Celery task

- **Тест 2**: GET `/api/v1/simpleprint/sync/status/{task_id}/`
  - Проверяет получение статуса задачи
  - Тестирует поля state, ready, result

- **Тест 3**: GET `/api/v1/simpleprint/sync/stats/`
  - Проверяет статистику синхронизации
  - Валидирует total_folders, total_files

- **Тест 4**: GET `/api/v1/simpleprint/files/`
  - Проверяет список файлов
  - Валидирует пагинацию и структуру

## 🚀 Запуск тестов

### Вариант 1: Все тесты (рекомендуется)

```bash
cd backend
./run_tests.sh
```

### Вариант 2: Отдельные тесты

```bash
# Только тесты клиента
pytest apps/simpleprint/tests/test_client.py -v -s

# Только тесты синхронизации
pytest apps/simpleprint/tests/test_sync.py -v -s

# Только тесты API
pytest apps/simpleprint/tests/test_api.py -v -s

# Конкретный тест
pytest apps/simpleprint/tests/test_client.py::TestSimplePrintClient::test_01_client_initialization -v -s
```

### Вариант 3: Запуск с дополнительными опциями

```bash
# С выводом покрытия кода
pytest apps/simpleprint/tests/ -v -s --cov=apps.simpleprint --cov-report=html

# Только быстрые тесты (без integration)
pytest apps/simpleprint/tests/ -v -s -m "not slow"

# С остановкой на первой ошибке
pytest apps/simpleprint/tests/ -v -s -x
```

## 📊 Формат вывода

Каждый тест выводит детальную информацию:

```
================================================================================
🔧 ТЕСТ 1: Инициализация SimplePrint клиента
================================================================================
📋 Конфигурация SimplePrint:
   - API Token: 18f82f78f4... (первые 10 символов)
   - User ID: 31471
   - Company ID: 27286
   - Base URL: https://api.simplyprint.io/27286/
   - Rate Limit: 180 req/min

✅ PASS: Клиент инициализирован корректно
   - API Token: ✓
   - User ID: ✓
   - Company ID: ✓
   - Base URL: ✓
```

При ошибке:

```
❌ FAIL: API вернул success=False. Response: {'status': 'error', 'message': 'Invalid token'}
📍 Файл: backend/apps/simpleprint/client.py
📍 Метод: test_connection()
💡 Возможные причины:
   - Неверный API токен
   - API SimplePrint недоступен
   - Неправильный base_url
```

## 🔍 Диагностика проблем

### Проблема: Тесты не запускаются

```bash
# Установите pytest и зависимости
pip install pytest pytest-django

# Проверьте DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE=config.settings.base

# Проверьте что вы в директории backend
pwd  # должно показать .../Factory_v3/backend
```

### Проблема: Ошибки подключения к БД

```bash
# Запустите PostgreSQL
docker-compose up -d db

# Примените миграции
python manage.py migrate
```

### Проблема: API SimplePrint недоступен

Проверьте настройки в `backend/config/settings/base.py`:

```python
SIMPLEPRINT_CONFIG = {
    'api_token': 'ваш_токен',  # Проверьте корректность
    'user_id': 'ваш_user_id',
    'company_id': 'ваш_company_id',
    'base_url': 'https://api.simplyprint.io/COMPANY_ID/',  # Проверьте URL
}
```

## 📝 Результаты тестов

После запуска всех тестов вы увидите:

```
========================================
✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!
========================================

📊 Результаты:
   ✓ API Client: OK
   ✓ Sync Service: OK
   ✓ API Endpoints: OK
```

## 🛠️ Разработка новых тестов

### Добавление нового теста

1. Создайте новый метод в соответствующем файле:

```python
def test_06_my_new_test(self, client):
    """
    ✅/❌ Тест 6: Описание теста
    Проверяет: что именно тестируется
    """
    print("\n" + "="*80)
    print("🧪 ТЕСТ 6: Название теста")
    print("="*80)

    try:
        # Ваш тест код
        assert condition, "❌ FAIL: Описание проблемы"
        print(f"\n✅ PASS: Тест пройден успешно")

    except AssertionError as e:
        print(f"\n❌ FAIL: {str(e)}")
        print(f"📍 Файл: путь/к/файлу.py")
        print(f"📍 Метод: название_метода()")
        raise
```

2. Запустите новый тест:

```bash
pytest apps/simpleprint/tests/test_client.py::TestSimplePrintClient::test_06_my_new_test -v -s
```

## 🎯 Что тестируется

- ✅ SimplePrint API клиент
- ✅ Подключение к SimplePrint
- ✅ Rate limiting (180 req/min)
- ✅ Retry логика (3 попытки)
- ✅ Парсинг файлов и папок
- ✅ Сохранение в PostgreSQL
- ✅ Связи между моделями (ForeignKey)
- ✅ REST API endpoints
- ✅ Celery tasks
- ✅ Аутентификация (Token Auth)

## 📞 Поддержка

Если тесты не проходят:

1. Проверьте вывод теста - там указан точный файл и строка ошибки
2. Проверьте логи в `backend/logs/django.log`
3. Убедитесь что все сервисы запущены (PostgreSQL, Redis, Celery)
4. Проверьте настройки SimplePrint API в `settings/base.py`

---

**Версия**: 1.0.0
**Последнее обновление**: 2025-10-23
