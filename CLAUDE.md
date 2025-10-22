# CLAUDE.md - Техническое задание PrintFarm v4.2.1

## 📋 Текущая версия 4.2.1 (2025-10-22)

### ✅ Активная конфигурация
**Контейнеры factory_v3** (автозапуск `unless-stopped`):
- `factory_v3_nginx` (порт 13000) - внешний доступ
- `factory_v3_backend` (порт 18001) - Django API
- `factory_v3_db` (порт 15433) - PostgreSQL
- `factory_v3_redis` (порт 16380) - Redis для Celery
- `factory_v3_celery` - фоновые задачи
- `factory_v3_celery_beat` - планировщик задач

**Статистика системы:**
- Товары: 668 (новых: 39, старых: 505, критических: 124)
- Производство: 228 позиций на 2154.50 единиц
- Внешний доступ: http://kemomail3.keenetic.pro:13000
- Аутентификация: токен `0a8fee03bca2b530a15b1df44d38b304e3f57484`

### 🎯 Основной функционал
1. **Синхронизация товаров** - интеграция с МойСклад API
2. **Анализ производства** - умный алгоритм расчета потребности
3. **Управление "Точка"** - Excel обработка и дедупликация
4. **SimplePrint интеграция** - синхронизация файлов и папок (NEW in v4.2.1)
5. **Экспорт данных** - стилизованные Excel отчеты

---

## 🚀 SimplePrint Files Integration (v4.2.1)

### Backend реализация
**Модели** (`apps/simpleprint/models.py`):
- `SimplePrintFolder` - иерархия папок
- `SimplePrintFile` - файлы с метаданными
- `SimplePrintSync` - история синхронизаций
- `SimplePrintWebhookEvent` - логирование webhooks

**API Client** (`apps/simpleprint/client.py`):
- Rate limiting: 180 req/min (3 req/sec)
- Retry logic с exponential backoff
- Защита от циклических ссылок (`visited_folders`)
- Graceful degradation при недоступности Redis

**Celery автоматизация**:
- Задача: `simpleprint.scheduled_sync`
- Расписание: каждые 30 минут
- Поддержка полной/инкрементальной синхронизации

### Frontend реализация
**Страница SimplePrint** (`frontend/src/pages/SimplePrintPage.tsx`):
- Статистика: файлы, папки, размер, последняя синхронизация
- Фильтры: поиск, папка, тип файла
- Таблица с колонками: имя, папка, тип, расширение, размер, даты
- Модальное окно синхронизации: обычная/полная
- Пагинация: 50 элементов на странице

**Redux state** (`frontend/src/store/simpleprintSlice.ts`):
- Async thunks: fetchFiles, fetchFolders, fetchSyncStats, triggerSync
- Обработка загрузки и ошибок
- Защита от 429 ошибок (cooldown 5 минут)

### API Endpoints (SimplePrint)
```
GET    /api/v1/simpleprint/files/              # Список файлов
GET    /api/v1/simpleprint/files/stats/        # Статистика файлов
GET    /api/v1/simpleprint/folders/            # Список папок
GET    /api/v1/simpleprint/sync/               # История синхронизаций
POST   /api/v1/simpleprint/sync/trigger/       # Запуск синхронизации
GET    /api/v1/simpleprint/sync/stats/         # Статистика синхронизации
POST   /api/v1/simpleprint/webhook/            # Webhook от SimplePrint
```

### Management команды
```bash
# Обычная синхронизация
python manage.py sync_simpleprint_files

# Полная синхронизация с удалением
python manage.py sync_simpleprint_files --full

# Принудительная синхронизация (игнорировать cooldown)
python manage.py sync_simpleprint_files --force
```

---

## 📚 История версий (краткая)

### v4.2.1 (2025-10-22) - SimplePrint интеграция
- ✅ Полная интеграция SimplePrint Files API
- ✅ Frontend страница с управлением файлами
- ✅ Автоматическая синхронизация каждые 30 минут
- ✅ Webhook поддержка для real-time обновлений

### v4.2.0 (2025-09-06) - Production fixes
- Исправлена проблема с 'dict' object has no attribute 'id'
- Обратная совместимость токенов
- Обновлены скрипты автозапуска

### v4.1.8 (2025-08-19) - Пагинация и экспорт
- Исправлена пагинация таблиц (defaultPageSize)
- Экспорт Excel с blob данными
- TypeScript типизация ExportBlobResponse

### v4.1.4 (2025-08-17) - Фильтры
- Фильтр по цвету в таблице производства
- Автоматическое определение уникальных цветов

### v4.1.0 (2025-08-17) - Прогресс синхронизации
- Реальное время обновлений прогресса
- Визуализация текущего артикула
- Микро-транзакции для видимости прогресса

### v4.0.0 - v3.5.1 - Основные возможности
- Вкладка "Точка" с Excel обработкой
- Умный алгоритм расчета резерва
- Горизонтальное меню навигации
- Redux state persistence

---

## 🏗️ Технологический стек

### Backend
- **Framework**: Django 4.2+ с Django REST Framework
- **Database**: PostgreSQL 15+
- **Cache**: Redis (sessions, Celery broker)
- **Tasks**: Celery + Celery Beat
- **API**: МойСклад API, SimplePrint API

### Frontend
- **Framework**: React 18+ с TypeScript
- **UI**: Ant Design
- **State**: Redux Toolkit
- **HTTP**: Axios
- **Routing**: React Router v6

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Proxy**: Nginx
- **Server**: Gunicorn (WSGI)

---

## 🔌 API Endpoints (актуальные)

### Товары
```
GET    /api/v1/products/                       # Список товаров
GET    /api/v1/products/{id}/                  # Детали товара
GET    /api/v1/products/stats/                 # Статистика
```

### Синхронизация МойСклад
```
POST   /api/v1/sync/start/                     # Запуск синхронизации
GET    /api/v1/sync/status/                    # Статус синхронизации
GET    /api/v1/sync/history/                   # История
GET    /api/v1/sync/warehouses/                # Список складов
```

### Производство
```
POST   /api/v1/production/calculate/           # Расчет списка
GET    /api/v1/production/list/                # Получить список
POST   /api/v1/production/export/              # Экспорт в Excel
```

### Точка (Excel обработка)
```
POST   /api/v1/tochka/upload-excel/            # Загрузка и дедупликация
POST   /api/v1/tochka/merge-with-products/     # Анализ производства
POST   /api/v1/tochka/export-deduplicated/     # Экспорт дедуплицированных
POST   /api/v1/tochka/export-production/       # Экспорт списка производства
```

### Настройки
```
GET    /api/v1/settings/system-info/           # Информация о системе
GET    /api/v1/settings/summary/               # Сводная информация
GET/PUT /api/v1/settings/sync/                 # Настройки синхронизации
POST   /api/v1/settings/sync/test-connection/  # Тест соединения
```

### SimplePrint (NEW)
```
GET    /api/v1/simpleprint/files/              # Список файлов
GET    /api/v1/simpleprint/folders/            # Список папок
POST   /api/v1/simpleprint/sync/trigger/       # Запуск синхронизации
POST   /api/v1/simpleprint/webhook/            # Webhook endpoint
```

---

## 🧮 Ключевые алгоритмы

### 1. Классификация товаров
```python
def classify_product(product: Product) -> str:
    if product.current_stock < 5:
        return 'critical' if product.sales_last_2_months > 0 else 'new'
    elif product.sales_last_2_months < 10 and product.current_stock < 10:
        return 'new'
    else:
        return 'old'
```

### 2. Расчет потребности
```python
def calculate_production_need(product: Product) -> Decimal:
    if product.product_type == 'new':
        if product.current_stock < 5:
            return Decimal('10') - product.current_stock
        return Decimal('0')

    elif product.product_type == 'old':
        target_days = 15
        target_stock = product.average_daily_consumption * target_days

        if product.current_stock < product.average_daily_consumption * 10:
            return max(target_stock - product.current_stock, Decimal('0'))

    return Decimal('0')
```

### 3. Приоритизация
```python
def calculate_priority(product: Product) -> int:
    if product.product_type == 'critical' and product.current_stock < 5:
        return 100
    elif product.product_type == 'old' and product.days_of_stock < 5:
        return 80
    elif product.product_type == 'new' and product.current_stock < 5:
        return 60
    elif product.product_type == 'old' and product.days_of_stock < 10:
        return 40
    else:
        return 20
```

### 4. Алгоритм резерва (Точка)
```python
def calculate_reserve_display(reserved_stock, current_stock):
    calculated_reserve = reserved_stock - current_stock

    if reserved_stock == 0:
        color = 'gray'
    elif reserved_stock > current_stock:
        color = 'blue'  # Хорошо - избыток резерва
    else:
        color = 'red'   # Внимание - недостаток резерва

    return {
        'calculated_reserve': calculated_reserve,
        'color': color,
        'display_text': f"{reserved_stock} → {calculated_reserve} шт"
    }
```

### 5. Дедупликация Excel
```python
def deduplicate_excel_data(raw_data):
    article_dict = {}

    for item in raw_data:
        article = item['article']
        if article in article_dict:
            article_dict[article]['orders'] += item['orders']
            article_dict[article]['duplicate_rows'].append(item['row_number'])
        else:
            article_dict[article] = {
                'article': article,
                'orders': item['orders'],
                'row_number': item['row_number'],
                'duplicate_rows': []
            }

    return sorted(article_dict.values(), key=lambda x: x['orders'], reverse=True)
```

---

## 🎨 Брендинг PrintFarm

### Цветовая схема
```css
:root {
  --color-primary: #06EAFC;        /* Неоновый бирюзовый */
  --color-secondary: #1E1E1E;      /* Темный фон */
  --color-success: #00FF88;        /* Зеленый успех */
  --color-warning: #FFB800;        /* Желтый предупреждение */
  --color-error: #FF0055;          /* Красный ошибка */
}
```

### UI компоненты
- Шрифт: **Arimo**
- Эффекты: неоновое свечение на hover
- Кнопки: градиентные с анимацией
- Таблицы: виртуализация для 10k+ записей

---

## 🐳 Docker развертывание

### Активные контейнеры (factory_v3)
```yaml
services:
  nginx:
    image: nginx:alpine
    ports: ["13000:80"]
    restart: unless-stopped

  backend:
    build: ./docker/django
    ports: ["18001:8000"]
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    ports: ["15433:5432"]
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports: ["16380:6379"]
    restart: unless-stopped

  celery:
    build: ./docker/django
    command: celery -A config worker -l info
    restart: unless-stopped

  celery_beat:
    build: ./docker/django
    command: celery -A config beat -l info
    restart: unless-stopped
```

### Переменные окружения
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,kemomail3.keenetic.pro

# PostgreSQL
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://factory_v3_redis:6379/0

# МойСклад
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# SimplePrint
SIMPLEPRINT_API_TOKEN=18f82f78-f45a-46bb-aec8-3792048acccd
SIMPLEPRINT_USER_ID=31471
SIMPLEPRINT_COMPANY_ID=27286
SIMPLEPRINT_BASE_URL=https://api.simplyprint.io/27286/
SIMPLEPRINT_RATE_LIMIT=180
```

---

## 🛠️ Команды для работы

### Docker управление
```bash
# Запуск всех контейнеров
docker-compose -p factory_v3 up -d

# Остановка
docker-compose -p factory_v3 down

# Просмотр логов
docker-compose -p factory_v3 logs -f backend

# Перезапуск backend
docker-compose -p factory_v3 restart backend

# Проверка статуса
docker ps --filter name=factory_v3
```

### Django команды
```bash
# Применение миграций
docker exec factory_v3_backend python manage.py migrate

# Создание суперпользователя
docker exec -it factory_v3_backend python manage.py createsuperuser

# Сбор статики
docker exec factory_v3_backend python manage.py collectstatic --noinput

# Инициализация настроек
docker exec factory_v3_backend python manage.py init_settings --warehouse-id=YOUR_ID
```

### Синхронизация
```bash
# МойСклад синхронизация
docker exec factory_v3_backend python manage.py sync_products

# SimplePrint синхронизация
docker exec factory_v3_backend python manage.py sync_simpleprint_files

# Полная SimplePrint синхронизация
docker exec factory_v3_backend python manage.py sync_simpleprint_files --full

# Принудительная синхронизация (игнорировать cooldown)
docker exec factory_v3_backend python manage.py sync_simpleprint_files --force
```

### Celery задачи
```bash
# Просмотр активных задач
docker exec factory_v3_celery celery -A config inspect active

# Просмотр расписания
docker exec factory_v3_celery_beat celery -A config inspect scheduled

# Очистка очереди
docker exec factory_v3_celery celery -A config purge
```

### Проверка API
```bash
# Статус системы
curl http://localhost:13000/api/v1/settings/summary/ | python -m json.tool

# Статистика товаров
curl http://localhost:13000/api/v1/products/stats/ | python -m json.tool

# SimplePrint статистика
curl http://localhost:13000/api/v1/simpleprint/sync/stats/ | python -m json.tool

# Внешний доступ
curl http://kemomail3.keenetic.pro:13000/api/v1/settings/summary/
```

---

## 📊 Структура базы данных

### Основные модели

**Product** (Товар):
- moysklad_id, article, name
- current_stock, sales_last_2_months
- product_type (new/old/critical)
- production_needed, production_priority

**SyncLog** (Журнал синхронизации):
- sync_type (manual/scheduled)
- status (pending/success/failed/partial)
- total_products, synced_products

**SimplePrintFile** (Файл SimplePrint):
- simpleprint_id, name, ext, file_type
- folder (FK), size, created_at_sp

**SimplePrintFolder** (Папка SimplePrint):
- simpleprint_id, name, parent (self FK)
- depth, files_count, folders_count

---

## 🧪 Тестирование

### Критические тесты

**Алгоритм производства:**
- Товар 375-42108 (остаток 2, расход 10) → производство 8
- Критические товары (остаток < 5) → приоритет 100
- Новые товары (расход ≤ 3, остаток < 10) → целевой остаток 10

**API endpoints:**
- `/api/v1/settings/system-info/` → версия v4.2.1
- `/api/v1/sync/status/` → реальный прогресс синхронизации
- `/api/v1/simpleprint/files/` → список файлов SimplePrint

**Frontend:**
- Пагинация таблиц (defaultPageSize: 50, опции: 20/50/100/200)
- Экспорт Excel с blob данными
- Redux state persistence при навигации

### Запуск тестов
```bash
# Backend unit tests
docker exec factory_v3_backend python manage.py test

# Проверка миграций
docker exec factory_v3_backend python manage.py makemigrations --check

# Проверка системы
docker exec factory_v3_backend python manage.py check
```

---

## 🔒 Безопасность

### Настройки Django
- CORS настроен для production
- Rate limiting для API endpoints
- Валидация всех входных данных
- Secure headers через middleware

### Аутентификация
- Token-based authentication (DRF)
- Активный токен: `0a8fee03bca2b530a15b1df44d38b304e3f57484`
- Webhook SimplePrint: AllowAny (SimplePrint не поддерживает auth)

---

## 📝 Дополнительная документация

### Файлы документации
- `SIMPLEPRINT_INTEGRATION_COMPLETE.md` - Полная документация SimplePrint интеграции
- `SIMPLEPRINT_README.md` - Краткое руководство SimplePrint
- `VERSION` - Текущая версия системы
- `README.md` - Общее описание проекта

### Полезные ссылки
- МойСклад API: https://dev.moysklad.ru/doc/api/remap/1.2/
- SimplePrint API: https://simplyprint.io/docs/api/
- Ant Design: https://ant.design/components/overview/
- Redux Toolkit: https://redux-toolkit.js.org/

---

**Важно**: Это техническое задание является живым документом. При внесении изменений обновляйте соответствующие разделы и версию системы.

**Последнее обновление**: 2025-10-22
**Версия документа**: 4.2.1
