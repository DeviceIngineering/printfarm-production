# 📋 План реализации интеграции SimplePrint

**Дата создания:** 22 октября 2025
**Версия проекта:** v4.2.1
**Задача:** Создать автономную страницу для работы с SimplePrint API с двусторонней интеграцией с вкладкой "Точка"

---

## 🎯 Общая цель

Реализовать полнофункциональную интеграцию с SimplePrint API:
- ✅ Автономная страница для просмотра данных SimplePrint
- ✅ API endpoints для получения и обработки данных
- ✅ Двустороннее взаимодействие с вкладкой "Точка"
- ✅ Полное покрытие тестами
- ✅ Логгирование всех операций
- ✅ Регулярные git коммиты

---

## 📊 Этапы реализации

### **ЭТАП 1: Анализ и проектирование** (1-2 часа)

#### Шаг 1.1: Изучение SimplePrint API
**Задачи:**
- [ ] Изучить документацию SimplePrint API
- [ ] Определить необходимые endpoints
- [ ] Проверить доступные данные (заказы, статусы, товары)
- [ ] Определить лимиты и ограничения API
- [ ] Зафиксировать API credentials в переменных окружения

**Тесты:**
- Тест подключения к SimplePrint API
- Тест получения базовых данных

**Логгирование:**
```python
logger.info("SimplePrint API connection test started")
logger.debug(f"API endpoint: {endpoint}")
logger.info("SimplePrint API connection successful")
```

**Git commit:**
```bash
git commit -m "📝 Docs: Add SimplePrint API research and credentials setup

- Added SimplePrint API documentation
- Configured environment variables
- Added basic connection tests
"
```

---

#### Шаг 1.2: Проектирование архитектуры
**Задачи:**
- [ ] Создать диаграмму взаимодействия компонентов
- [ ] Спроектировать модели данных для SimplePrint
- [ ] Определить API endpoints для frontend
- [ ] Спроектировать механизм синхронизации с "Точка"
- [ ] Создать документ SIMPLEPRINT_ARCHITECTURE.md

**Документация:**
```
backend/apps/simpleprint/
├── models.py           # SimplePrintOrder, SimplePrintProduct
├── serializers.py      # API serializers
├── views.py            # REST API endpoints
├── services.py         # Бизнес-логика
├── client.py           # SimplePrint API client
├── tasks.py            # Celery tasks для синхронизации
└── tests/
    ├── test_models.py
    ├── test_views.py
    ├── test_services.py
    └── test_client.py

frontend/src/pages/SimplePrintPage/
├── SimplePrintPage.tsx
├── components/
│   ├── OrdersTable.tsx
│   ├── OrderDetails.tsx
│   └── SyncButton.tsx
└── __tests__/
```

**Git commit:**
```bash
git commit -m "📐 Design: SimplePrint integration architecture

- Created architecture diagram
- Designed data models
- Planned API endpoints
- Added SIMPLEPRINT_ARCHITECTURE.md
"
```

---

### **ЭТАП 2: Backend - SimplePrint API Client** (2-3 часа)

#### Шаг 2.1: Создание Django app
**Задачи:**
- [ ] Создать Django app `simpleprint`
- [ ] Добавить app в INSTALLED_APPS
- [ ] Создать базовую структуру папок
- [ ] Настроить URL routing

**Команды:**
```bash
cd backend
python manage.py startapp simpleprint
mkdir -p apps/simpleprint/tests
```

**Файл:** `backend/apps/simpleprint/__init__.py`
```python
"""
SimplePrint Integration Module

Модуль для интеграции с SimplePrint API.
Предоставляет функциональность для получения данных о заказах,
статусах печати и синхронизации с системой PrintFarm.
"""

default_app_config = 'apps.simpleprint.apps.SimpleprintConfig'
```

**Тесты:**
```python
# apps/simpleprint/tests/test_app_config.py
def test_app_installed():
    """Проверка что app установлен"""
    assert 'apps.simpleprint' in settings.INSTALLED_APPS
```

**Логгирование:**
```python
import logging

logger = logging.getLogger('simpleprint')
logger.info("SimplePrint app initialized")
```

**Git commit:**
```bash
git commit -m "🎬 Init: Create SimplePrint Django app

- Created simpleprint app structure
- Added to INSTALLED_APPS
- Added basic tests
- Added logging configuration
"
```

---

#### Шаг 2.2: SimplePrint API Client
**Задачи:**
- [ ] Создать клиент для SimplePrint API
- [ ] Реализовать методы: get_orders(), get_order_details(), get_statuses()
- [ ] Добавить обработку ошибок и retry логику
- [ ] Добавить rate limiting

**Файл:** `backend/apps/simpleprint/client.py`
```python
import logging
import requests
from typing import List, Dict, Optional
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger('simpleprint.client')


class SimplePrintAPIError(Exception):
    """Base exception for SimplePrint API errors"""
    pass


class SimplePrintClient:
    """
    Клиент для работы с SimplePrint API

    Примеры использования:
        client = SimplePrintClient()
        orders = client.get_orders()
        order = client.get_order_details(order_id)
    """

    def __init__(self):
        self.base_url = settings.SIMPLEPRINT_API_URL
        self.api_key = settings.SIMPLEPRINT_API_KEY
        self.company_id = settings.SIMPLEPRINT_COMPANY_ID
        self.user_id = settings.SIMPLEPRINT_USER_ID
        self.timeout = 30

        # Настройка retry логики
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        logger.info(f"SimplePrint client initialized for company {self.company_id}")

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API запроса"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Выполнить API запрос с логгированием

        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Дополнительные параметры для requests

        Returns:
            Dict: Ответ от API

        Raises:
            SimplePrintAPIError: При ошибке API запроса
        """
        url = f"{self.base_url}/{endpoint}"

        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Request params: {kwargs.get('params', {})}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"API request successful: {method} {endpoint}")
            logger.debug(f"Response data: {data}")

            return data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response: {e.response.text}")
            raise SimplePrintAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error: {e}")
            raise SimplePrintAPIError("API request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise SimplePrintAPIError(f"Request failed: {str(e)}")

    def get_orders(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Получить список заказов

        Args:
            filters: Фильтры для запроса (status, date_from, date_to, etc.)

        Returns:
            List[Dict]: Список заказов
        """
        logger.info("Fetching orders from SimplePrint")

        params = {
            'company_id': self.company_id,
            'user_id': self.user_id,
        }

        if filters:
            params.update(filters)
            logger.debug(f"Applying filters: {filters}")

        data = self._make_request('GET', 'orders', params=params)

        orders = data.get('orders', [])
        logger.info(f"Fetched {len(orders)} orders")

        return orders

    def get_order_details(self, order_id: str) -> Dict:
        """
        Получить детали заказа

        Args:
            order_id: ID заказа

        Returns:
            Dict: Детали заказа
        """
        logger.info(f"Fetching order details: {order_id}")

        data = self._make_request('GET', f'orders/{order_id}')

        logger.info(f"Order details fetched: {order_id}")
        return data

    def get_statuses(self) -> List[Dict]:
        """
        Получить список доступных статусов

        Returns:
            List[Dict]: Список статусов
        """
        logger.info("Fetching order statuses")

        data = self._make_request('GET', 'statuses')

        statuses = data.get('statuses', [])
        logger.info(f"Fetched {len(statuses)} statuses")

        return statuses

    def test_connection(self) -> bool:
        """
        Тест подключения к API

        Returns:
            bool: True если подключение успешно
        """
        logger.info("Testing SimplePrint API connection")

        try:
            self.get_statuses()
            logger.info("Connection test successful")
            return True
        except SimplePrintAPIError as e:
            logger.error(f"Connection test failed: {e}")
            return False
```

**Тесты:** `backend/apps/simpleprint/tests/test_client.py`
```python
import pytest
from unittest.mock import Mock, patch
from apps.simpleprint.client import SimplePrintClient, SimplePrintAPIError


class TestSimplePrintClient:
    """Тесты для SimplePrint API клиента"""

    @pytest.fixture
    def client(self):
        return SimplePrintClient()

    @patch('apps.simpleprint.client.requests.Session.request')
    def test_get_orders_success(self, mock_request, client):
        """Тест успешного получения заказов"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'orders': [
                {'id': '1', 'status': 'pending'},
                {'id': '2', 'status': 'processing'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        orders = client.get_orders()

        assert len(orders) == 2
        assert orders[0]['id'] == '1'
        mock_request.assert_called_once()

    @patch('apps.simpleprint.client.requests.Session.request')
    def test_get_orders_with_filters(self, mock_request, client):
        """Тест получения заказов с фильтрами"""
        mock_response = Mock()
        mock_response.json.return_value = {'orders': []}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        filters = {'status': 'completed', 'date_from': '2025-01-01'}
        client.get_orders(filters=filters)

        call_kwargs = mock_request.call_args[1]
        assert 'status' in call_kwargs['params']
        assert call_kwargs['params']['status'] == 'completed'

    @patch('apps.simpleprint.client.requests.Session.request')
    def test_api_error_handling(self, mock_request, client):
        """Тест обработки ошибок API"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        with pytest.raises(SimplePrintAPIError):
            client.get_orders()

    @patch('apps.simpleprint.client.requests.Session.request')
    def test_connection_test(self, mock_request, client):
        """Тест проверки подключения"""
        mock_response = Mock()
        mock_response.json.return_value = {'statuses': []}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = client.test_connection()

        assert result is True
```

**Настройки:** `backend/config/settings/base.py`
```python
# SimplePrint API Configuration
SIMPLEPRINT_API_URL = env.str('SIMPLEPRINT_API_URL', default='https://api.simpleprint.ru/v1')
SIMPLEPRINT_API_KEY = env.str('SIMPLEPRINT_API_KEY', default='')
SIMPLEPRINT_COMPANY_ID = env.int('SIMPLEPRINT_COMPANY_ID', default=27286)
SIMPLEPRINT_USER_ID = env.int('SIMPLEPRINT_USER_ID', default=31471)
SIMPLEPRINT_RATE_LIMIT = env.int('SIMPLEPRINT_RATE_LIMIT', default=10)  # requests per second

# Logging
LOGGING['loggers']['simpleprint'] = {
    'handlers': ['console', 'file'],
    'level': 'DEBUG',
    'propagate': False,
}
```

**Git commit:**
```bash
git commit -m "✨ Feature: Add SimplePrint API client

- Created SimplePrintClient with retry logic
- Implemented get_orders, get_order_details, get_statuses
- Added comprehensive error handling
- Added logging for all operations
- Added unit tests (100% coverage)
- Added settings configuration
"
```

---

#### Шаг 2.3: Модели данных
**Задачи:**
- [ ] Создать модель SimplePrintOrder
- [ ] Создать модель SimplePrintSync (история синхронизаций)
- [ ] Добавить связь с Product из основного приложения
- [ ] Создать миграции

**Файл:** `backend/apps/simpleprint/models.py`
```python
import logging
from django.db import models
from django.utils import timezone

logger = logging.getLogger('simpleprint.models')


class SimplePrintOrder(models.Model):
    """
    Заказ из SimplePrint

    Хранит информацию о заказах печати из SimplePrint API
    """

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'В обработке'),
        ('printing', 'Печатается'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    # SimplePrint данные
    simpleprint_id = models.CharField(max_length=100, unique=True, db_index=True)
    order_number = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Товар
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='simpleprint_orders'
    )
    article = models.CharField(max_length=255, db_index=True)
    product_name = models.CharField(max_length=500)

    # Количество и даты
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField()
    completion_date = models.DateTimeField(null=True, blank=True)

    # Дополнительная информация
    customer_name = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    raw_data = models.JSONField(default=dict, help_text="Полные данные из SimplePrint API")

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-order_date', 'simpleprint_id']
        indexes = [
            models.Index(fields=['status', 'order_date']),
            models.Index(fields=['article', 'status']),
        ]
        verbose_name = 'SimplePrint Заказ'
        verbose_name_plural = 'SimplePrint Заказы'

    def __str__(self):
        return f"Order {self.order_number} - {self.product_name}"

    def save(self, *args, **kwargs):
        """Переопределяем save для логгирования"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            logger.info(f"Created new SimplePrint order: {self.simpleprint_id}")
        else:
            logger.debug(f"Updated SimplePrint order: {self.simpleprint_id}")

    def mark_as_synced(self):
        """Отметить заказ как синхронизированный"""
        self.last_synced_at = timezone.now()
        self.save()
        logger.info(f"Order {self.simpleprint_id} marked as synced")


class SimplePrintSync(models.Model):
    """
    История синхронизаций с SimplePrint
    """

    STATUS_CHOICES = [
        ('pending', 'В процессе'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('partial', 'Частично'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    total_orders = models.IntegerField(default=0)
    synced_orders = models.IntegerField(default=0)
    failed_orders = models.IntegerField(default=0)

    filters = models.JSONField(default=dict, help_text="Фильтры использованные при синхронизации")
    error_details = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'SimplePrint Синхронизация'
        verbose_name_plural = 'SimplePrint Синхронизации'

    def __str__(self):
        return f"Sync {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.status}"

    def complete(self, status='success', error_details=''):
        """Завершить синхронизацию"""
        self.status = status
        self.finished_at = timezone.now()
        self.error_details = error_details
        self.save()

        logger.info(f"Sync completed: {self.status}, {self.synced_orders}/{self.total_orders}")
```

**Тесты:** `backend/apps/simpleprint/tests/test_models.py`
```python
import pytest
from django.utils import timezone
from apps.simpleprint.models import SimplePrintOrder, SimplePrintSync
from apps.products.models import Product


@pytest.mark.django_db
class TestSimplePrintOrder:
    """Тесты модели SimplePrintOrder"""

    def test_create_order(self):
        """Тест создания заказа"""
        order = SimplePrintOrder.objects.create(
            simpleprint_id='SP-12345',
            order_number='ORD-001',
            article='TEST-001',
            product_name='Test Product',
            quantity=10,
            order_date=timezone.now()
        )

        assert order.pk is not None
        assert order.status == 'pending'
        assert str(order) == 'Order ORD-001 - Test Product'

    def test_mark_as_synced(self):
        """Тест отметки о синхронизации"""
        order = SimplePrintOrder.objects.create(
            simpleprint_id='SP-12346',
            order_number='ORD-002',
            article='TEST-002',
            product_name='Test Product 2',
            quantity=5,
            order_date=timezone.now()
        )

        assert order.last_synced_at is None

        order.mark_as_synced()

        assert order.last_synced_at is not None


@pytest.mark.django_db
class TestSimplePrintSync:
    """Тесты модели SimplePrintSync"""

    def test_create_sync(self):
        """Тест создания записи синхронизации"""
        sync = SimplePrintSync.objects.create(
            total_orders=100
        )

        assert sync.status == 'pending'
        assert sync.synced_orders == 0

    def test_complete_sync(self):
        """Тест завершения синхронизации"""
        sync = SimplePrintSync.objects.create(
            total_orders=100,
            synced_orders=95
        )

        sync.complete(status='success')

        assert sync.status == 'success'
        assert sync.finished_at is not None
```

**Команды:**
```bash
python manage.py makemigrations simpleprint
python manage.py migrate
```

**Git commit:**
```bash
git commit -m "💾 Models: Add SimplePrint data models

- Created SimplePrintOrder model
- Created SimplePrintSync model
- Added relationship with Product
- Added comprehensive tests
- Added migrations
"
```

---

### **ЭТАП 3: Backend - API Endpoints** (2-3 часа)

#### Шаг 3.1: Сервисы и бизнес-логика
**Задачи:**
- [ ] Создать SimplePrintService
- [ ] Реализовать sync_orders()
- [ ] Реализовать match_with_products()
- [ ] Добавить кеширование данных

**Файл:** `backend/apps/simpleprint/services.py`
```python
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from .client import SimplePrintClient, SimplePrintAPIError
from .models import SimplePrintOrder, SimplePrintSync
from apps.products.models import Product

logger = logging.getLogger('simpleprint.services')


class SimplePrintService:
    """
    Сервис для работы с SimplePrint данными
    """

    def __init__(self):
        self.client = SimplePrintClient()
        logger.debug("SimplePrintService initialized")

    def sync_orders(self, filters: Optional[Dict] = None) -> SimplePrintSync:
        """
        Синхронизация заказов из SimplePrint

        Args:
            filters: Фильтры для запроса

        Returns:
            SimplePrintSync: Запись о синхронизации
        """
        logger.info("Starting SimplePrint orders synchronization")

        # Создаем запись о синхронизации
        sync_log = SimplePrintSync.objects.create(filters=filters or {})

        try:
            # Получаем заказы из API
            orders_data = self.client.get_orders(filters=filters)
            sync_log.total_orders = len(orders_data)
            sync_log.save()

            logger.info(f"Fetched {len(orders_data)} orders from SimplePrint")

            # Обрабатываем каждый заказ
            synced = 0
            failed = 0

            for order_data in orders_data:
                try:
                    self._process_order(order_data)
                    synced += 1

                    # Обновляем прогресс каждые 10 заказов
                    if synced % 10 == 0:
                        sync_log.synced_orders = synced
                        sync_log.save()
                        logger.debug(f"Sync progress: {synced}/{len(orders_data)}")

                except Exception as e:
                    logger.error(f"Failed to process order {order_data.get('id')}: {e}")
                    failed += 1

            # Завершаем синхронизацию
            sync_log.synced_orders = synced
            sync_log.failed_orders = failed

            if failed == 0:
                sync_log.complete(status='success')
            elif synced > 0:
                sync_log.complete(status='partial', error_details=f'{failed} orders failed')
            else:
                sync_log.complete(status='failed', error_details='All orders failed')

            logger.info(f"Sync completed: {synced} synced, {failed} failed")

            return sync_log

        except SimplePrintAPIError as e:
            logger.error(f"SimplePrint API error: {e}")
            sync_log.complete(status='failed', error_details=str(e))
            raise
        except Exception as e:
            logger.error(f"Unexpected error during sync: {e}")
            sync_log.complete(status='failed', error_details=str(e))
            raise

    @transaction.atomic
    def _process_order(self, order_data: Dict) -> SimplePrintOrder:
        """
        Обработать один заказ

        Args:
            order_data: Данные заказа из API

        Returns:
            SimplePrintOrder: Созданный/обновленный заказ
        """
        simpleprint_id = order_data['id']

        # Пытаемся найти существующий заказ
        order, created = SimplePrintOrder.objects.update_or_create(
            simpleprint_id=simpleprint_id,
            defaults={
                'order_number': order_data.get('order_number', ''),
                'status': order_data.get('status', 'pending'),
                'article': order_data.get('article', ''),
                'product_name': order_data.get('product_name', ''),
                'quantity': Decimal(str(order_data.get('quantity', 0))),
                'order_date': order_data.get('order_date'),
                'completion_date': order_data.get('completion_date'),
                'customer_name': order_data.get('customer', {}).get('name', ''),
                'notes': order_data.get('notes', ''),
                'raw_data': order_data,
                'last_synced_at': timezone.now(),
            }
        )

        if created:
            logger.info(f"Created new order: {simpleprint_id}")
        else:
            logger.debug(f"Updated existing order: {simpleprint_id}")

        # Пытаемся найти соответствующий товар
        self._match_order_with_product(order)

        return order

    def _match_order_with_product(self, order: SimplePrintOrder):
        """
        Связать заказ с товаром из Product

        Args:
            order: SimplePrintOrder
        """
        if order.product:
            return  # Уже связан

        try:
            # Ищем товар по артикулу
            product = Product.objects.filter(article=order.article).first()

            if product:
                order.product = product
                order.save()
                logger.info(f"Matched order {order.simpleprint_id} with product {product.article}")
            else:
                logger.warning(f"No product found for article: {order.article}")

        except Exception as e:
            logger.error(f"Error matching order with product: {e}")

    def get_orders_stats(self) -> Dict:
        """
        Получить статистику по заказам

        Returns:
            Dict: Статистика
        """
        cache_key = 'simpleprint_orders_stats'
        stats = cache.get(cache_key)

        if stats:
            logger.debug("Returning cached stats")
            return stats

        stats = {
            'total': SimplePrintOrder.objects.count(),
            'by_status': {},
            'unmatched_count': SimplePrintOrder.objects.filter(product__isnull=True).count(),
        }

        # Статистика по статусам
        for status, _ in SimplePrintOrder.STATUS_CHOICES:
            count = SimplePrintOrder.objects.filter(status=status).count()
            stats['by_status'][status] = count

        # Кешируем на 5 минут
        cache.set(cache_key, stats, 300)

        logger.info(f"Generated stats: {stats}")
        return stats

    def match_all_orders_with_products(self) -> int:
        """
        Сопоставить все несопоставленные заказы с товарами

        Returns:
            int: Количество сопоставленных заказов
        """
        logger.info("Starting batch matching of orders with products")

        unmatched_orders = SimplePrintOrder.objects.filter(product__isnull=True)
        matched_count = 0

        for order in unmatched_orders:
            self._match_order_with_product(order)
            if order.product:
                matched_count += 1

        logger.info(f"Matched {matched_count} orders with products")
        return matched_count
```

**Тесты:** `backend/apps/simpleprint/tests/test_services.py`
```python
import pytest
from unittest.mock import Mock, patch
from apps.simpleprint.services import SimplePrintService
from apps.simpleprint.models import SimplePrintOrder, SimplePrintSync
from apps.products.models import Product


@pytest.mark.django_db
class TestSimplePrintService:
    """Тесты SimplePrintService"""

    @pytest.fixture
    def service(self):
        return SimplePrintService()

    @pytest.fixture
    def mock_orders_data(self):
        return [
            {
                'id': 'SP-001',
                'order_number': 'ORD-001',
                'status': 'pending',
                'article': 'TEST-001',
                'product_name': 'Test Product 1',
                'quantity': 10,
                'order_date': '2025-10-01T10:00:00Z',
            },
            {
                'id': 'SP-002',
                'order_number': 'ORD-002',
                'status': 'processing',
                'article': 'TEST-002',
                'product_name': 'Test Product 2',
                'quantity': 5,
                'order_date': '2025-10-02T11:00:00Z',
            }
        ]

    @patch('apps.simpleprint.services.SimplePrintClient.get_orders')
    def test_sync_orders_success(self, mock_get_orders, service, mock_orders_data):
        """Тест успешной синхронизации"""
        mock_get_orders.return_value = mock_orders_data

        sync_log = service.sync_orders()

        assert sync_log.status == 'success'
        assert sync_log.total_orders == 2
        assert sync_log.synced_orders == 2
        assert sync_log.failed_orders == 0

        # Проверяем что заказы созданы
        assert SimplePrintOrder.objects.count() == 2

    @pytest.mark.django_db
    def test_match_order_with_product(self, service):
        """Тест сопоставления заказа с товаром"""
        # Создаем товар
        product = Product.objects.create(
            moysklad_id='MS-001',
            article='TEST-001',
            name='Test Product'
        )

        # Создаем заказ
        order = SimplePrintOrder.objects.create(
            simpleprint_id='SP-001',
            order_number='ORD-001',
            article='TEST-001',
            product_name='Test Product',
            quantity=10
        )

        # Сопоставляем
        service._match_order_with_product(order)

        order.refresh_from_db()
        assert order.product == product

    def test_get_orders_stats(self, service):
        """Тест получения статистики"""
        # Создаем несколько заказов
        SimplePrintOrder.objects.create(
            simpleprint_id='SP-001',
            order_number='ORD-001',
            status='pending',
            article='TEST-001',
            quantity=10
        )
        SimplePrintOrder.objects.create(
            simpleprint_id='SP-002',
            order_number='ORD-002',
            status='completed',
            article='TEST-002',
            quantity=5
        )

        stats = service.get_orders_stats()

        assert stats['total'] == 2
        assert stats['by_status']['pending'] == 1
        assert stats['by_status']['completed'] == 1
```

**Git commit:**
```bash
git commit -m "⚙️ Services: Add SimplePrint business logic

- Created SimplePrintService
- Implemented sync_orders with progress tracking
- Implemented product matching logic
- Added caching for statistics
- Added comprehensive tests
- Added detailed logging
"
```

---

*Продолжение плана в следующей части...*

**Примечание:** Это первая часть подробного плана. План включает еще 4 этапа:
- Этап 3.2-3.3: REST API endpoints
- Этап 4: Frontend - автономная страница
- Этап 5: Интеграция с вкладкой "Точка"
- Этап 6: Финальное тестирование и документация

Каждый этап включает детальные инструкции, код, тесты и git коммиты.
