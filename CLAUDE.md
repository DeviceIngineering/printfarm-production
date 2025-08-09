# CLAUDE.md - Техническое задание для системы управления производством PrintFarm

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
    article = models.CharField(max_length=255, db_index=True, verbose_name='Артикул из МойСклад')
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Группа товаров
    product_group_id = models.CharField(max_length=36, blank=True)
    product_group_name = models.CharField(max_length=255, blank=True)
    
    # Остатки и продажи (всегда в штуках)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                       verbose_name='Текущий остаток (шт)')
    sales_last_2_months = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                             verbose_name='Продажи за 2 месяца (шт)')
    average_daily_consumption = models.DecimalField(max_digits=10, decimal_places=4, default=0,
                                                   verbose_name='Средний дневной расход (шт/день)')
    
    # Единица измерения (всегда штуки)
    uom = models.CharField(max_length=10, default='шт', editable=False)
    
    # Классификация
    PRODUCT_TYPE_CHOICES = [
        ('new', 'Новая позиция'),
        ('old', 'Старая позиция'),
        ('critical', 'Критическая позиция'),
    ]
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    
    # Расчетные поля
    days_of_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    production_needed = models.DecimalField(max_digits=10, decimal_places=0, default=0,
                                          verbose_name='Требуется произвести (шт)')
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

# Настройки часового пояса
TIME_ZONE = 'Europe/Moscow'
USE_TZ = True

# Единицы измерения
DEFAULT_UOM = 'шт'  # Всегда штуки
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
    
    def parse_product_data(self, raw_product: Dict) -> Dict:
        """Парсинг данных товара из API МойСклад"""
        return {
            'moysklad_id': raw_product.get('id'),
            'article': raw_product.get('article', ''),  # Артикул берется из поля article
            'name': raw_product.get('name'),
            'description': raw_product.get('description', ''),
            'product_group_id': raw_product.get('productFolder', {}).get('meta', {}).get('href', '').split('/')[-1],
            # Все количества в API МойСклад уже в штуках
            'current_stock': raw_product.get('stock', 0),
            'sales_quantity': raw_product.get('quantity', 0),
        }
```

## 7. Алгоритм расчета производства

### 7.1 Классификация товаров
```python
from config.business_constants import (
    NEW_PRODUCT_MIN_STOCK,
    NEW_PRODUCT_MIN_SALES,
    NEW_PRODUCT_STOCK_THRESHOLD
)

@critical_business_logic(version="1.0", description="Классификация товаров согласно ТЗ")
def classify_product(product: Product) -> str:
    """
    КРИТИЧЕСКАЯ ФУНКЦИЯ - НЕ ИЗМЕНЯТЬ!
    Классификация товара по типу согласно бизнес-правилам.
    
    Returns:
        'critical' - критическая позиция (низкий остаток + есть спрос)
        'new' - новая позиция (низкий остаток или низкие продажи)
        'old' - старая позиция (все остальные)
    """
    if product.current_stock < NEW_PRODUCT_MIN_STOCK:
        return 'critical' if product.sales_last_2_months > 0 else 'new'
    elif product.sales_last_2_months < NEW_PRODUCT_MIN_SALES and product.current_stock < NEW_PRODUCT_STOCK_THRESHOLD:
        return 'new'
    else:
        return 'old'
```

### 7.2 Расчет потребности
```python
import math
from decimal import Decimal, ROUND_CEILING
from config.business_constants import (
    NEW_PRODUCT_MIN_STOCK,
    NEW_PRODUCT_TARGET_STOCK,
    OLD_PRODUCT_TARGET_DAYS,
    OLD_PRODUCT_MIN_DAYS
)

@critical_business_logic(version="1.0", description="Расчет потребности в производстве")
def calculate_production_need(product: Product) -> Decimal:
    """
    КРИТИЧЕСКАЯ ФУНКЦИЯ - НЕ ИЗМЕНЯТЬ!
    Расчет количества для производства с округлением вверх.
    Все количества в штуках, округление ВСЕГДА вверх.
    """
    if product.product_type == 'new':
        if product.current_stock < NEW_PRODUCT_MIN_STOCK:
            need = Decimal(str(NEW_PRODUCT_TARGET_STOCK)) - product.current_stock
            return need.quantize(Decimal('1'), rounding=ROUND_CEILING)
        return Decimal('0')
    
    elif product.product_type == 'old':
        target_days = OLD_PRODUCT_TARGET_DAYS  # целевой запас на 15 дней
        target_stock = product.average_daily_consumption * target_days
        
        if product.current_stock < product.average_daily_consumption * OLD_PRODUCT_MIN_DAYS:
            need = target_stock - product.current_stock
            if need > 0:
                # Округляем вверх до целого числа штук
                return need.quantize(Decimal('1'), rounding=ROUND_CEILING)
    
    return Decimal('0')
```

### 7.3 Приоритизация
```python
from config.business_constants import (
    PRIORITY_CRITICAL_NEW,
    PRIORITY_OLD_LOW_STOCK,
    PRIORITY_NEW_LOW_STOCK,
    PRIORITY_OLD_MEDIUM_STOCK,
    PRIORITY_DEFAULT
)

@critical_business_logic(version="1.0", description="Расчет приоритета производства")
def calculate_priority(product: Product) -> int:
    """
    КРИТИЧЕСКАЯ ФУНКЦИЯ - НЕ ИЗМЕНЯТЬ!
    Расчет приоритета производства (чем выше, тем важнее).
    Приоритеты фиксированы согласно бизнес-правилам.
    """
    if product.product_type == 'critical' and product.current_stock < NEW_PRODUCT_MIN_STOCK:
        return PRIORITY_CRITICAL_NEW  # 100
    elif product.product_type == 'old' and product.days_of_stock < 5:
        return PRIORITY_OLD_LOW_STOCK  # 80
    elif product.product_type == 'new' and product.current_stock < NEW_PRODUCT_MIN_STOCK:
        return PRIORITY_NEW_LOW_STOCK  # 60
    elif product.product_type == 'old' and product.days_of_stock < 10:
        return PRIORITY_OLD_MEDIUM_STOCK  # 40
    else:
        return PRIORITY_DEFAULT  # 20
```

### 7.4 Формирование списка
```python
from decimal import Decimal, ROUND_CEILING
from config.business_constants import (
    ASSORTMENT_THRESHOLD,
    COEFFICIENT_HIGH_PRIORITY,
    COEFFICIENT_MEDIUM_PRIORITY,
    COEFFICIENT_LOW_PRIORITY,
    COEFFICIENT_MIN_PRIORITY
)

@critical_business_logic(version="1.0", description="Формирование списка на производство")
def create_production_list(products: QuerySet) -> ProductionList:
    """
    КРИТИЧЕСКАЯ ФУНКЦИЯ - НЕ ИЗМЕНЯТЬ!
    Формирование финального списка на производство.
    При количестве позиций >= 30 работаем на ассортимент.
    """
    # Сортировка по приоритету
    sorted_products = products.filter(production_needed__gt=0).order_by('-production_priority')
    
    # Если товаров >= 30, работаем на ассортимент
    if sorted_products.count() >= ASSORTMENT_THRESHOLD:
        # Применяем коэффициенты в зависимости от приоритета
        for product in sorted_products:
            if product.production_priority >= 80:
                coefficient = COEFFICIENT_HIGH_PRIORITY  # 1.0
            elif product.production_priority >= 60:
                coefficient = COEFFICIENT_MEDIUM_PRIORITY  # 0.7
            elif product.production_priority >= 40:
                coefficient = COEFFICIENT_LOW_PRIORITY  # 0.5
            else:
                coefficient = COEFFICIENT_MIN_PRIORITY  # 0.3
            
            # Рассчитываем количество и округляем вверх до целых штук
            quantity = product.production_needed * Decimal(str(coefficient))
            product.production_quantity = quantity.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        # Если товаров < 30, производим полную потребность
        for product in sorted_products:
            product.production_quantity = product.production_needed
    
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
from celery.schedules import crontab

# В settings.py
CELERY_BEAT_SCHEDULE = {
    'daily-sync': {
        'task': 'apps.sync.tasks.scheduled_sync',
        'schedule': crontab(hour=0, minute=0),  # 00:00 по московскому времени
        'options': {
            'timezone': 'Europe/Moscow'
        }
    },
}

@celery.task
def scheduled_sync():
    """Ежедневная синхронизация в 00:00 МСК"""
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

### Этап 0: Подготовка защитных механизмов (1 день)
1. Создание структуры контрольных файлов в docs/
2. Написание BUSINESS_RULES.md с фиксацией правил
3. Создание business_constants.py
4. Настройка декоратора @critical_business_logic
5. Инициализация CHECKPOINTS.md

### Этап 1: Базовая инфраструктура (2-3 дня)
1. Настройка Docker окружения
2. Создание Django проекта с базовой конфигурацией
3. Настройка PostgreSQL и Redis
4. Базовая настройка React приложения
5. Настройка Nginx для проксирования
6. **Checkpoint 1**: Фиксация базовой инфраструктуры

### Этап 2: Модели и API (3-4 дня)
1. Создание моделей Product, ProductImage, SyncLog
2. Настройка Django REST Framework
3. Базовые CRUD endpoints для товаров
4. Настройка аутентификации (токены)
5. Создание первых immutable тестов для моделей
6. **Checkpoint 2**: Фиксация структуры данных

### Этап 3: Интеграция с МойСклад (4-5 дней)
1. Реализация MoySkladClient
2. Сервис синхронизации товаров
3. Загрузка и сохранение изображений
4. Фоновые задачи Celery для синхронизации
5. Планировщик для ежедневной синхронизации
6. **Checkpoint 3**: Рабочая синхронизация

### Этап 4: Алгоритм расчета производства (3-4 дня)
1. Реализация classify_product() с декоратором @critical_business_logic
2. Реализация calculate_production_need() с ROUND_CEILING
3. Система приоритизации с использованием констант
4. Формирование оптимального списка
5. Полный набор immutable тестов для бизнес-логики
6. **Checkpoint 4**: Критическая бизнес-логика зафиксирована

### Этап 5: Frontend - основные страницы (4-5 дней)
1. Настройка Redux и API клиента
2. Страница товаров с таблицей
3. Компоненты синхронизации
4. Страница производственного списка
5. Применение брендинга PrintFarm
6. **Checkpoint 5**: Базовый UI готов

### Этап 6: Экспорт и отчеты (2-3 дня)
1. Экспорт в Excel (openpyxl)
2. Заглушки для дополнительных отчетов
3. Заглушка для Simple Print API
4. Feature flags для будущих функций

### Этап 7: Оптимизация и тестирование (3-4 дня)
1. Оптимизация запросов к БД
2. Настройка индексов
3. Оптимизация загрузки изображений
4. Тестирование с 10к товаров
5. Проверка всех immutable тестов
6. **Checkpoint 6**: Оптимизированная версия

### Этап 8: Документация и деплой (2 дня)
1. README с инструкцией по запуску
2. Документация API (Swagger/OpenAPI)
3. Настройка production конфигурации
4. Подготовка к переносу на удаленный сервер
5. Финальная проверка всех контрольных точек
6. **Final Checkpoint**: Готово к production

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

### Важные бизнес-правила:
- **Единицы измерения**: Все товары учитываются только в штуках
- **Округление**: Все расчетные количества для производства округляются вверх до целых штук
- **Артикулы**: Берутся напрямую из поля "article" API МойСклад без изменений
- **Часовой пояс**: Все операции и логи ведутся по московскому времени (UTC+3)

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

## 17. Защита бизнес-логики и критического кода

### Структура контрольных файлов
```
project_root/
├── CLAUDE.md                    # Основное ТЗ (этот файл)
├── docs/
│   ├── BUSINESS_RULES.md       # Неизменяемые бизнес-правила
│   ├── IMPLEMENTED_FEATURES.md  # Список реализованных функций
│   ├── API_CONTRACTS.md        # Зафиксированные контракты API
│   ├── CRITICAL_CODE.md        # Критически важный код
│   ├── CHECKPOINTS.md          # Контрольные точки проекта
│   └── BUSINESS_LOGIC_CHANGELOG.md # История изменений бизнес-логики
└── tests/
    └── test_business_logic_immutable.py  # Неизменяемые тесты
```

### Критические бизнес-правила (НЕ ИЗМЕНЯТЬ!)
```markdown
## Классификация товаров
- Новая позиция: остаток < 5 ИЛИ (продажи < 10 И остаток < 10)
- Критическая: остаток < 5 И есть спрос
- Старая: все остальные

## Расчет производства
- Новые позиции: минимум 5 шт на складе, производим до 10
- Старые позиции: запас на 15 дней
- ВСЕГДА округляем ВВЕРХ до целых штук
- Единицы измерения ВСЕГДА штуки

## Приоритеты производства (фиксированные)
1. Критические новые (остаток < 5) = 100
2. Старые с остатком < 5 дней = 80
3. Новые с остатком < 5 = 60
4. Старые с остатком < 10 дней = 40
5. Остальные = 20
```

### Маркировка критического кода
```python
# backend/apps/core/decorators.py
def critical_business_logic(version="1.0", description=""):
    """Маркер для критической бизнес-логики - НЕ ИЗМЕНЯТЬ!"""
    def decorator(func):
        func._is_critical = True
        func._version = version
        func._description = description
        # Добавляем строгую проверку при вызове
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Логирование вызова критической функции
            logger.info(f"Critical function called: {func.__name__} v{version}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Файл бизнес-констант
```python
# backend/config/business_constants.py
"""
ФАЙЛ БИЗНЕС-КОНСТАНТ - ИЗМЕНЯТЬ ТОЛЬКО ПОСЛЕ СОГЛАСОВАНИЯ!
Последнее обновление: 2025-01-19
"""

# Пороги для классификации товаров
NEW_PRODUCT_MIN_STOCK = 5
NEW_PRODUCT_MIN_SALES = 10
NEW_PRODUCT_STOCK_THRESHOLD = 10

# Целевые показатели производства
NEW_PRODUCT_TARGET_STOCK = 10
OLD_PRODUCT_TARGET_DAYS = 15
OLD_PRODUCT_MIN_DAYS = 10

# Приоритеты (НЕ ИЗМЕНЯТЬ!)
PRIORITY_CRITICAL_NEW = 100
PRIORITY_OLD_LOW_STOCK = 80
PRIORITY_NEW_LOW_STOCK = 60
PRIORITY_OLD_MEDIUM_STOCK = 40
PRIORITY_DEFAULT = 20

# Коэффициенты для ассортимента
ASSORTMENT_THRESHOLD = 30
COEFFICIENT_HIGH_PRIORITY = 1.0
COEFFICIENT_MEDIUM_PRIORITY = 0.7
COEFFICIENT_LOW_PRIORITY = 0.5
COEFFICIENT_MIN_PRIORITY = 0.3
```

## 18. Стратегии работы с Claude Code

### Шаблон безопасного запроса
```markdown
Контекст проекта: Система управления производством PrintFarm
Основная документация: CLAUDE.md
Бизнес-правила: docs/BUSINESS_RULES.md
Реализованные функции: docs/IMPLEMENTED_FEATURES.md

Задача: [описание задачи]

Ограничения:
1. НЕ изменять функции с декоратором @critical_business_logic
2. Сохранить все существующие API контракты
3. Новый код должен пройти test_business_logic_immutable.py
4. Использовать константы из business_constants.py

Ожидаемый результат:
- [что должно получиться]
- Все immutable тесты проходят
- Бизнес-логика не изменена
```

### Команды для проверки целостности
```bash
# Проверка критических функций
grep -r "@critical_business_logic" backend/

# Запуск неизменяемых тестов
python manage.py test tests.test_business_logic_immutable

# Проверка использования констант
grep -r "NEW_PRODUCT_MIN_STOCK\|OLD_PRODUCT_TARGET_DAYS" backend/ | grep -v "business_constants.py"
```

### Feature flags для новой функциональности
```python
# backend/config/features.py
FEATURES = {
    'use_new_sync_algorithm': False,  # Пока не протестировано
    'enable_auto_production': False,   # В разработке
    'legacy_rounding': False,          # ВСЕГДА False! Используем ROUND_CEILING
    'extended_reports': False,         # Дополнительные отчеты
}
```

## 19. Неизменяемые тесты бизнес-логики

```python
# tests/test_business_logic_immutable.py
"""
КРИТИЧЕСКИЕ ТЕСТЫ БИЗНЕС-ЛОГИКИ
Эти тесты ДОЛЖНЫ всегда проходить!
НЕ ИЗМЕНЯТЬ И НЕ УДАЛЯТЬ!
"""
import unittest
from decimal import Decimal, ROUND_CEILING
from apps.products.services import classify_product, calculate_production_need

class TestCriticalBusinessLogic(unittest.TestCase):
    """Тесты критической бизнес-логики v1.0"""
    
    def test_new_product_classification_low_stock(self):
        """Товар с остатком < 5 должен быть 'new' если нет продаж"""
        product = Mock(current_stock=4, sales_last_2_months=0)
        self.assertEqual(classify_product(product), 'new')
        
    def test_critical_product_classification(self):
        """Товар с остатком < 5 и продажами должен быть 'critical'"""
        product = Mock(current_stock=3, sales_last_2_months=15)
        self.assertEqual(classify_product(product), 'critical')
        
    def test_rounding_always_up(self):
        """Округление ВСЕГДА вверх до целых штук"""
        test_cases = [
            (Decimal('10.1'), Decimal('11')),
            (Decimal('10.9'), Decimal('11')),
            (Decimal('10.0'), Decimal('10')),
            (Decimal('0.1'), Decimal('1')),
        ]
        for input_val, expected in test_cases:
            result = input_val.quantize(Decimal('1'), rounding=ROUND_CEILING)
            self.assertEqual(result, expected)
    
    def test_production_priorities(self):
        """Проверка неизменности приоритетов"""
        from config.business_constants import (
            PRIORITY_CRITICAL_NEW,
            PRIORITY_OLD_LOW_STOCK,
            PRIORITY_NEW_LOW_STOCK
        )
        self.assertEqual(PRIORITY_CRITICAL_NEW, 100)
        self.assertEqual(PRIORITY_OLD_LOW_STOCK, 80)
        self.assertEqual(PRIORITY_NEW_LOW_STOCK, 60)
```

## 20. Контрольные точки и версионирование

### Создание контрольных точек
После завершения каждого критического этапа создавайте контрольную точку:

```bash
# Создание тега с контрольной точкой
git tag -a checkpoint-1-models -m "Базовые модели реализованы и протестированы"
git push origin checkpoint-1-models

# Создание резервной копии критических функций
cp backend/apps/products/services.py docs/backups/services_v1.0.py
```

### Документирование в CHECKPOINTS.md
```markdown
# Контрольные точки проекта

## Checkpoint 1: Базовые модели (2025-01-20)
- ✅ Модель Product с полями из ТЗ
- ✅ Единицы измерения зафиксированы как "шт"
- ✅ Артикулы из поля article МойСклад
- Git tag: checkpoint-1-models
- Commit: abc123...

## Checkpoint 2: Бизнес-логика (2025-01-22)
- ✅ classify_product() согласно ТЗ
- ✅ calculate_production_need() с ROUND_CEILING
- ✅ Приоритеты производства
- ✅ Immutable тесты созданы
- Git tag: checkpoint-2-business-logic
- Commit: def456...
```

## 21. Практические рекомендации для Claude Code

### При каждой новой сессии:
1. Начинайте с указания контекста и ограничений
2. Ссылайтесь на CLAUDE.md и BUSINESS_RULES.md
3. Указывайте какие функции трогать нельзя

### Пример начала сессии:
```markdown
Привет! Работаю над проектом PrintFarm.

Контекст:
- Основное ТЗ: CLAUDE.md
- Критические функции помечены @critical_business_logic
- Константы в business_constants.py менять нельзя
- После изменений запускать test_business_logic_immutable.py

Текущая задача: Добавить пагинацию в API товаров
Файл: backend/apps/products/views.py
```

### Защита от регрессий:
1. **Перед изменением**: сохраните текущую версию критических файлов
2. **После изменения**: запустите immutable тесты
3. **При ошибке**: откатитесь к сохраненной версии

### Эскалация изменений:
- **Безопасные изменения**: UI, новые поля (не влияющие на расчеты), оптимизация запросов
- **Требуют внимания**: изменения в сервисах, новые вычисления
- **Критические (требуют подтверждения)**: любые изменения в функциях расчета, классификации, приоритетов

---

**Важно**: Это техническое задание является живым документом. При возникновении вопросов или необходимости уточнений, обновляйте этот файл соответствующим образом. Все изменения бизнес-логики должны быть задокументированы в BUSINESS_LOGIC_CHANGELOG.md.