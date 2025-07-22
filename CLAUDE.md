# CLAUDE.md - Техническое задание для системы управления производством PrintFarm

## 📋 Версия 3.1.2 (2025-07-22) - Промежуточный релиз

### 🆕 Новые возможности:
- **Полноценный раздел "Настройки"** с веб-интерфейсом
- **Системная информация**: отображение текущей версии и даты сборки из git
- **Автоматическая синхронизация по расписанию** (кратно 30 минутам: от 30 мин до 24 часов)
- **Управление складами и группами товаров** через API
- **Статистика синхронизаций** и процент успешности
- **Тестирование соединения** с МойСклад одним кликом
- **Ручной запуск синхронизации** через веб-интерфейс
- **Команда инициализации настроек**: `python manage.py init_settings`

### 🔧 API Endpoints (v3.1.2):
- `GET /api/v1/settings/system-info/` - Информация о системе
- `GET /api/v1/settings/summary/` - Сводная информация
- `GET/PUT /api/v1/settings/sync/` - Настройки синхронизации  
- `GET/PUT /api/v1/settings/general/` - Общие настройки
- `POST /api/v1/settings/sync/test-connection/` - Тест соединения
- `POST /api/v1/settings/sync/trigger-manual/` - Ручная синхронизация
- `GET /api/v1/settings/schedule/status/` - Статус расписания
- `POST /api/v1/settings/schedule/update/` - Обновление расписания

### 🗂️ Новые компоненты:
```
backend/apps/settings/          # Новое приложение настроек
├── models.py                   # SystemInfo, SyncScheduleSettings, GeneralSettings
├── serializers.py              # API сериализаторы
├── views.py                    # REST API endpoints
├── services.py                 # Бизнес-логика
├── urls.py                     # URL маршруты
└── management/commands/
    └── init_settings.py        # Команда инициализации

frontend/src/components/settings/  # Компоненты настроек
├── SystemInfo.tsx                  # Информация о системе
├── SyncSettingsCard.tsx           # Настройки синхронизации
└── GeneralSettingsCard.tsx        # Общие настройки

frontend/src/api/settings.ts       # API клиент для настроек
frontend/src/hooks/useSettings.ts  # React hook для настроек
```

### 📦 Команды управления (v3.1.2):
```bash
# Инициализация настроек с параметрами
python manage.py init_settings --warehouse-id=YOUR_ID

# Сброс настроек
python manage.py init_settings --reset

# Проверка статуса через API
curl http://localhost:8000/api/v1/settings/summary/

# Синхронизация с удаленным сервером
./sync_to_remote.sh
```

---

## 1. Обзор проекта

Система управления производством для PrintFarm с интеграцией МойСклад для анализа товарных остатков и формирования оптимального списка товаров на производство.

### Основные функции:
- Синхронизация товаров из МойСклад
- Анализ оборачиваемости и остатков
- Автоматический расчет потребности в производстве
- Формирование приоритизированного списка на производство
- Экспорт данных в Excel

## 2. Технологический стек

### Backend:
- **Framework**: Django 4.2+ с Django REST Framework
- **База данных**: PostgreSQL 15+
- **Кэширование**: Redis (для хранения сессий и кэша)
- **Очереди задач**: Celery + Redis (для фоновых задач)
- **API интеграция**: requests, httpx

### Frontend:
- **Framework**: React 18+
- **UI библиотека**: Ant Design или Material-UI
- **State management**: Redux Toolkit
- **HTTP клиент**: Axios
- **Стилизация**: Tailwind CSS + custom CSS для брендинга

### Инфраструктура:
- **Контейнеризация**: Docker + Docker Compose
- **Веб-сервер**: Nginx (reverse proxy)
- **WSGI сервер**: Gunicorn

## 3. Структура проекта

```
printfarm-production/
├── docker/
│   ├── django/
│   │   └── Dockerfile
│   ├── nginx/
│   │   ├── Dockerfile
│   │   └── nginx.conf
│   └── postgres/
│       └── init.sql
├── docker-compose.yml
├── docker-compose.prod.yml
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── celery.py
│   ├── apps/
│   │   ├── core/
│   │   │   ├── models.py
│   │   │   ├── utils.py
│   │   │   └── exceptions.py
│   │   ├── products/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   └── urls.py
│   │   ├── sync/
│   │   │   ├── models.py
│   │   │   ├── services.py
│   │   │   ├── tasks.py
│   │   │   └── moysklad_client.py
│   │   ├── reports/
│   │   │   ├── services.py
│   │   │   ├── exporters.py
│   │   │   └── views.py
│   │   └── api/
│   │       ├── v1/
│   │       │   ├── urls.py
│   │       │   └── views.py
│   │       └── authentication.py
│   ├── static/
│   ├── media/
│   │   └── products/
│   └── templates/
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── .env.example
│   ├── public/
│   └── src/
│       ├── index.tsx
│       ├── App.tsx
│       ├── api/
│       │   ├── client.ts
│       │   ├── products.ts
│       │   └── sync.ts
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx
│       │   │   └── Layout.tsx
│       │   ├── products/
│       │   │   ├── ProductTable.tsx
│       │   │   ├── ProductFilters.tsx
│       │   │   └── ProductImage.tsx
│       │   ├── sync/
│       │   │   ├── SyncButton.tsx
│       │   │   ├── SyncModal.tsx
│       │   │   └── SyncProgress.tsx
│       │   └── common/
│       │       ├── LoadingSpinner.tsx
│       │       ├── ErrorBoundary.tsx
│       │       └── ScrollToTop.tsx
│       ├── pages/
│       │   ├── ProductsPage.tsx
│       │   ├── ReportsPage.tsx
│       │   └── SettingsPage.tsx
│       ├── store/
│       │   ├── index.ts
│       │   ├── products/
│       │   └── sync/
│       ├── hooks/
│       │   ├── useProducts.ts
│       │   └── useSync.ts
│       ├── utils/
│       │   ├── constants.ts
│       │   └── helpers.ts
│       └── styles/
│           ├── globals.css
│           └── variables.css
└── README.md
```

## 4. Модели данных

### 4.1 Product (Товар)
```python
class Product(models.Model):
    # Основные поля из МойСклад
    moysklad_id = models.CharField(max_length=36, unique=True, db_index=True)
    article = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Группа товаров
    product_group_id = models.CharField(max_length=36, blank=True)
    product_group_name = models.CharField(max_length=255, blank=True)
    
    # Остатки и продажи
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_last_2_months = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_daily_consumption = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Классификация
    PRODUCT_TYPE_CHOICES = [
        ('new', 'Новая позиция'),
        ('old', 'Старая позиция'),
        ('critical', 'Критическая позиция'),
    ]
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    
    # Расчетные поля
    days_of_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    production_needed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    production_priority = models.IntegerField(default=0)
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True)
    
    class Meta:
        ordering = ['-production_priority', 'article']
        indexes = [
            models.Index(fields=['product_type', 'production_priority']),
            models.Index(fields=['current_stock', 'product_type']),
        ]
```

### 4.2 ProductImage (Изображение товара)
```python
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True)
    moysklad_url = models.URLField(max_length=500)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 4.3 SyncLog (Журнал синхронизации)
```python
class SyncLog(models.Model):
    SYNC_TYPE_CHOICES = [
        ('manual', 'Ручная'),
        ('scheduled', 'По расписанию'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'В процессе'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('partial', 'Частично выполнено'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    
    warehouse_id = models.CharField(max_length=36)
    warehouse_name = models.CharField(max_length=255)
    
    excluded_groups = models.JSONField(default=list)
    
    total_products = models.IntegerField(default=0)
    synced_products = models.IntegerField(default=0)
    failed_products = models.IntegerField(default=0)
    
    error_details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
```

### 4.4 ProductionList (Список на производство)
```python
class ProductionList(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, default='system')
    
    total_items = models.IntegerField(default=0)
    total_units = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    export_file = models.FileField(upload_to='exports/', null=True)
    
    class Meta:
        ordering = ['-created_at']

class ProductionListItem(models.Model):
    production_list = models.ForeignKey(ProductionList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    priority = models.IntegerField()
    
    class Meta:
        ordering = ['priority', 'product__article']
```

## 5. API Endpoints

### 5.1 Товары
- `GET /api/v1/products/` - Список товаров с пагинацией и фильтрами
- `GET /api/v1/products/{id}/` - Детали товара
- `GET /api/v1/products/stats/` - Статистика по товарам

### 5.2 Синхронизация
- `POST /api/v1/sync/start/` - Запуск синхронизации
- `GET /api/v1/sync/status/` - Статус текущей синхронизации
- `GET /api/v1/sync/history/` - История синхронизаций
- `GET /api/v1/sync/warehouses/` - Список складов из МойСклад
- `GET /api/v1/sync/product-groups/` - Список групп товаров

### 5.3 Производство
- `POST /api/v1/production/calculate/` - Расчет списка на производство
- `GET /api/v1/production/list/` - Получить список на производство
- `POST /api/v1/production/export/` - Экспорт в Excel

### 5.4 Отчеты (заглушки)
- `GET /api/v1/reports/` - Список доступных отчетов
- `POST /api/v1/reports/{type}/generate/` - Генерация отчета

## 6. Интеграция с МойСклад

### 6.1 Конфигурация
```python
MOYSKLAD_CONFIG = {
    'base_url': 'https://api.moysklad.ru/api/remap/1.2',
    'token': 'f9be4985f5e3488716c040ca52b8e04c7c0f9e0b',
    'default_warehouse_id': '241ed919-a631-11ee-0a80-07a9000bb947',
    'rate_limit': 5,  # запросов в секунду
    'retry_attempts': 3,
    'timeout': 30,
}
```

### 6.2 Клиент для API
```python
class MoySkladClient:
    def get_warehouses(self) -> List[Dict]
    def get_product_groups(self) -> List[Dict]
    def get_stock_report(self, warehouse_id: str, product_group_ids: List[str] = None) -> List[Dict]
    def get_turnover_report(self, warehouse_id: str, date_from: datetime, date_to: datetime) -> List[Dict]
    def get_product_images(self, product_id: str) -> List[Dict]
    def download_image(self, image_url: str) -> bytes
```

## 7. Алгоритм расчета производства

### 7.1 Классификация товаров
```python
def classify_product(product: Product) -> str:
    """Классификация товара по типу"""
    if product.current_stock < 5:
        return 'critical' if product.sales_last_2_months > 0 else 'new'
    elif product.sales_last_2_months < 10 and product.current_stock < 10:
        return 'new'
    else:
        return 'old'
```

### 7.2 Расчет потребности
```python
def calculate_production_need(product: Product) -> Decimal:
    """Расчет количества для производства"""
    if product.product_type == 'new':
        if product.current_stock < 5:
            return Decimal('10') - product.current_stock
        return Decimal('0')
    
    elif product.product_type == 'old':
        target_days = 15  # целевой запас на 15 дней
        target_stock = product.average_daily_consumption * target_days
        
        if product.current_stock < product.average_daily_consumption * 10:
            return max(target_stock - product.current_stock, Decimal('0'))
    
    return Decimal('0')
```

### 7.3 Приоритизация
```python
def calculate_priority(product: Product) -> int:
    """Расчет приоритета производства (чем выше, тем важнее)"""
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

### 7.4 Формирование списка
```python
def create_production_list(products: QuerySet) -> ProductionList:
    """Формирование финального списка на производство"""
    # Сортировка по приоритету
    sorted_products = products.filter(production_needed__gt=0).order_by('-production_priority')
    
    # Если товаров >= 30, работаем на ассортимент
    if sorted_products.count() >= 30:
        # Применяем коэффициенты в зависимости от приоритета
        for product in sorted_products:
            if product.production_priority >= 80:
                coefficient = 1.0  # 100% от потребности
            elif product.production_priority >= 60:
                coefficient = 0.7  # 70% от потребности
            elif product.production_priority >= 40:
                coefficient = 0.5  # 50% от потребности
            else:
                coefficient = 0.3  # 30% от потребности
            
            product.production_quantity = product.production_needed * coefficient
    
    return create_list_from_products(sorted_products)
```

## 8. Frontend компоненты

### 8.1 Таблица товаров
- Виртуализированная таблица для работы с 10к+ записей
- Сортировка по всем колонкам
- Фильтры по типу товара, остаткам, приоритету
- Поиск по артикулу и названию
- Миниатюры изображений с модальным просмотром
- Пагинация по 100 записей

### 8.2 Синхронизация
- Модальное окно с настройками синхронизации
- Выбор склада из выпадающего списка
- Множественный выбор исключаемых групп товаров
- Прогресс-бар с количеством загруженных товаров
- Отображение последней даты синхронизации

### 8.3 Список на производство
- Отображение рассчитанного списка
- Возможность ручной корректировки количества
- Экспорт в Excel одним кликом
- Печать списка

## 9. Фоновые задачи (Celery)

### 9.1 Автоматическая синхронизация
```python
@celery.task
def scheduled_sync():
    """Ежедневная синхронизация в 00:00"""
    sync_service = SyncService()
    sync_service.sync_products(
        warehouse_id=settings.MOYSKLAD_DEFAULT_WAREHOUSE,
        sync_type='scheduled'
    )
```

### 9.2 Загрузка изображений
```python
@celery.task
def download_product_images(product_id: int):
    """Асинхронная загрузка изображений товара"""
    # Загрузка и создание миниатюр
```

## 10. Брендинг и UI

### 10.1 Цветовая схема
```css
:root {
  --color-primary: #06EAFC;
  --color-primary-rgb: 6, 234, 252;
  --color-secondary: #1E1E1E;
  --color-text: #000000;
  --color-background: #FFFFFF;
  --color-success: #00FF88;
  --color-warning: #FFB800;
  --color-error: #FF0055;
}
```

### 10.2 Компоненты UI
- Использовать неоновые эффекты для интерактивных элементов
- Шрифт Arimo для всех текстов
- Градиентные кнопки с hover эффектами
- Плавающая кнопка "Наверх" в правом нижнем углу

## 11. Переменные окружения

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password
DATABASE_URL=postgresql://printfarm_user:secure_password@db:5432/printfarm_db

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Simple Print API (заглушка)
SIMPLEPRINT_API_KEY=your-api-key
SIMPLEPRINT_COMPANY_ID=27286
SIMPLEPRINT_USER_ID=31471
```

## 12. Docker конфигурация

### 12.1 docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    env_file:
      - .env

  celery:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file:
      - .env

  celery-beat:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    command: celery -A config beat -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file:
      - .env

  frontend:
    build:
      context: .
      dockerfile: docker/react/Dockerfile
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - REACT_APP_API_URL=http://localhost:8000/api/v1

  nginx:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile
    ports:
      - "80:80"
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

## 13. Пошаговый план реализации

### Этап 1: Базовая инфраструктура (2-3 дня)
1. Настройка Docker окружения
2. Создание Django проекта с базовой конфигурацией
3. Настройка PostgreSQL и Redis
4. Базовая настройка React приложения
5. Настройка Nginx для проксирования

### Этап 2: Модели и API (3-4 дня)
1. Создание моделей Product, ProductImage, SyncLog
2. Настройка Django REST Framework
3. Базовые CRUD endpoints для товаров
4. Настройка аутентификации (токены)

### Этап 3: Интеграция с МойСклад (4-5 дней)
1. Реализация MoySkladClient
2. Сервис синхронизации товаров
3. Загрузка и сохранение изображений
4. Фоновые задачи Celery для синхронизации
5. Планировщик для ежедневной синхронизации

### Этап 4: Алгоритм расчета производства (3-4 дня)
1. Реализация классификации товаров
2. Расчет потребности в производстве
3. Система приоритизации
4. Формирование оптимального списка

### Этап 5: Frontend - основные страницы (4-5 дней)
1. Настройка Redux и API клиента
2. Страница товаров с таблицей
3. Компоненты синхронизации
4. Страница производственного списка
5. Применение брендинга PrintFarm

### Этап 6: Экспорт и отчеты (2-3 дня)
1. Экспорт в Excel (openpyxl)
2. Заглушки для дополнительных отчетов
3. Заглушка для Simple Print API

### Этап 7: Оптимизация и тестирование (3-4 дня)
1. Оптимизация запросов к БД
2. Настройка индексов
3. Оптимизация загрузки изображений
4. Тестирование с 10к товаров
5. Написание базовых тестов

### Этап 8: Документация и деплой (2 дня)
1. README с инструкцией по запуску
2. Документация API (Swagger/OpenAPI)
3. Настройка production конфигурации
4. Подготовка к переносу на удаленный сервер

## 14. Критерии готовности

### MVP должен включать:
1. ✅ Рабочая синхронизация с МойСклад
2. ✅ Хранение товаров и изображений в БД
3. ✅ Автоматический расчет списка на производство
4. ✅ Веб-интерфейс для просмотра товаров
5. ✅ Экспорт списка производства в Excel
6. ✅ Docker-контейнеры для легкого развертывания
7. ✅ Логирование всех операций синхронизации

### Заглушки для будущего развития:
1. 📌 Simple Print API интеграция
2. 📌 Дополнительные отчеты
3. 📌 Система пользователей и прав
4. 📌 Автоматическое планирование производства

## 15. Примечания для разработки

### Обработка ошибок:
- Все API endpoints должны возвращать структурированные ошибки
- Логирование всех исключений с контекстом
- Graceful degradation при недоступности МойСклад

### Производительность:
- Использовать select_related/prefetch_related для оптимизации запросов
- Кэширование списков складов и групп товаров
- Batch операции при синхронизации
- Lazy loading изображений в таблице

### Безопасность:
- CORS настройки для production
- Rate limiting для API endpoints
- Валидация всех входных данных
- Secure headers через Django middleware

## 16. Команды для работы

### Запуск проекта:
```bash
# Первый запуск
docker-compose up --build

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Применение миграций
docker-compose exec backend python manage.py migrate

# Сбор статики
docker-compose exec backend python manage.py collectstatic --noinput
```

### Полезные команды:
```bash
# Запуск синхронизации вручную
docker-compose exec backend python manage.py sync_products

# Очистка старых логов синхронизации
docker-compose exec backend python manage.py cleanup_sync_logs --days=30

# Экспорт текущего списка производства
docker-compose exec backend python manage.py export_production_list
```

## 🧪 План тестирования v3.1.2 (на 23.07.2025)

### 🎯 Приоритетные тесты:

#### 1. Раздел "Настройки" (Критический)
- [ ] **Системная информация**: корректность отображения версии и даты сборки
- [ ] **Настройки синхронизации**: сохранение/загрузка параметров
- [ ] **Общие настройки**: валидация форм и применение изменений
- [ ] **Тест соединения МойСклад**: корректность проверки API
- [ ] **Ручная синхронизация**: запуск и отображение прогресса
- [ ] **Расписание синхронизации**: настройка интервалов (30мин-24ч)

#### 2. Алгоритм производства (Высокий)
- [ ] **Товар 375-42108** (остаток 2, расход 10): должно быть к производству 8
- [ ] **Товар 381-40801** (остаток 8, расход 2): проверить корректность расчета
- [ ] **Критические товары** (остаток < 5): приоритет 100
- [ ] **Новые товары** (расход ≤ 3, остаток < 10): целевой остаток 10

#### 3. API Endpoints (Средний)
- [ ] `GET /api/v1/settings/system-info/` - возвращает версию v3.1.2
- [ ] `GET /api/v1/settings/summary/` - полная сводка без ошибок
- [ ] `PUT /api/v1/settings/sync/` - обновление настроек синхронизации
- [ ] `POST /api/v1/settings/sync/test-connection/` - тестирование МойСклад
- [ ] `POST /api/v1/settings/schedule/update/` - управление расписанием

#### 4. Frontend компоненты (Средний)
- [ ] **Загрузка настроек**: отсутствие ошибок при загрузке
- [ ] **Формы**: валидация полей и отображение ошибок
- [ ] **Интерактивность**: кнопки, переключатели, селекты
- [ ] **Адаптивность**: корректное отображение на разных экранах

#### 5. Интеграция и производительность (Низкий)
- [ ] **Celery Beat**: создание задач расписания
- [ ] **База данных**: миграции и целостность данных
- [ ] **Логирование**: отсутствие критических ошибок в логах
- [ ] **Память**: отсутствие утечек при длительной работе

### 🐛 Известные области для проверки:

1. **Декораторы**: проверить что исправления @method_decorator работают
2. **Типизация**: TypeScript ошибки в Form initialValues
3. **Экспорты**: правильные импорты apiClient
4. **Синхронизация**: статус и прогресс долгих операций
5. **Расписание**: корректная работа с Celery Beat

### 📋 Чек-лист запуска тестов:

```bash
# 1. Убедиться что сервер запущен
python backend/manage.py runserver

# 2. Проверить статус настроек
curl http://localhost:8000/api/v1/settings/summary/ | python -m json.tool

# 3. Открыть веб-интерфейс
# http://localhost:3000/settings

# 4. Протестировать HTML интерфейс
# Открыть test_settings_frontend.html в браузере

# 5. Проверить инициализацию
python backend/manage.py init_settings --reset
```

### 🚨 Критические проблемы для исправления:
- Любые 500 ошибки в API настроек
- Невозможность сохранения настроек
- Неработающий алгоритм производства
- Ошибки при запуске ручной синхронизации

### ✅ Критерии готовности к v3.2:
- Все критические тесты пройдены
- Веб-интерфейс настроек полностью функционален
- Алгоритм производства работает корректно
- API возвращает корректные данные
- Отсутствуют блокирующие ошибки

---

**Важно**: Это техническое задание является живым документом. При возникновении вопросов или необходимости уточнений, обновляйте этот файл соответствующим образом.