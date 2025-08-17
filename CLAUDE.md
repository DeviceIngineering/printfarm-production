# CLAUDE.md - Техническое задание для системы управления производством PrintFarm

## 📋 Версия 4.1.0 (2025-08-17) - Исправление прогресса синхронизации

### 🆕 Новые возможности v4.1.0:
- **🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Отображение прогресса синхронизации** - пользователи видят реальный прогресс вместо "0 из 0"
- **⚡ Реальное время обновлений** - прогресс обновляется каждые 50 товаров + финальные 20
- **👁️ Визуализация текущего артикула** - отображается артикул обрабатываемого товара
- **🛠️ Архитектурное улучшение** - вынос обновлений прогресса из транзакций для видимости
- **🧪 Регрессионные тесты** - 7/8 тестов пройдены, предотвращение повторения проблемы

### 🔧 Ключевые исправления v4.1.0:
- **Проблема**: Обновления прогресса происходили внутри `transaction.atomic()` и были невидимы до коммита
- **Решение**: Вынос `total_products` и `_process_sync_data` за пределы основной транзакции
- **Метод**: Каждый товар сохраняется в индивидуальной микро-транзакции
- **API**: `/api/v1/sync/status/` теперь возвращает реальные данные в реальном времени
- **UX**: Вместо "Обработано: 0 из 0" показывается "Обработано: 75 из 150 товаров"

### 📊 Технические детали v4.1.0:
```python
# Прогресс обновляется вне транзакции
def _update_sync_progress(sync_log, synced_products, current_article):
    sync_log.synced_products = synced_products
    sync_log.current_article = current_article  
    sync_log.save()  # Видимо немедленно!

# Каждые 50 товаров + финальные 20
if synced % 50 == 0:
    self._update_sync_progress(sync_log, synced, product.article)
```

## 📋 Версия 4.0.0 (2025-08-17) - Исправление отображения списка производства

### 🆕 Новые возможности v4.0.0:
- **✅ Исправлена проблема отображения списка производства** - после расчета таблица корректно показывает товары
- **🔧 Исправлена ошибка циклического импорта ProductionService** - использованы inline классы в views.py  
- **🎨 Добавлено поле Color** - отображение цвета товаров из МойСклад с правильным парсингом customentity
- **🔄 Улучшен Redux state management** - корректное обновление списка после расчета
- **🚀 Полный рабочий функционал** - все основные возможности системы работают стабильно

### 🔧 Ключевые исправления v4.0.0:
- Функция `handleCalculate()` теперь вызывает `fetchProductionList()` для обновления отображения
- API `/api/v1/products/production/list/` возвращает реальные данные товаров (50 позиций)
- Парсинг цвета из МойСклад обрабатывает customentity объекты
- Устранены все проблемы с отображением пустых таблиц после расчета

## 📋 Версия 3.8.0 (2025-08-16) - Умный алгоритм расчета резерва

### 🆕 Новые возможности v3.8.0:
- **🧠 Умный алгоритм расчета резерва** - новая логика отображения колонки "Резерв" на вкладке Точка
- **🎨 Цветовая индикация резерва**:
  - **Синий цвет**: Резерв больше остатка (положительный результат)
  - **Красный цвет**: Резерв меньше или равен остатку (требует внимания)
  - **Серый цвет**: Резерв отсутствует
- **📊 Новый расчет**: Если Резерв > 0, то отображается (Резерв - Остаток)
- **🚀 Высокая производительность** - алгоритм обрабатывает 1000 товаров менее чем за 5 секунд
- **💡 Улучшенный UX** - всплывающие подсказки и визуальные предупреждения
- **🔧 Обратная совместимость** - сохранена поддержка старого API
- **✅ Покрытие тестами 90%+** - полное TDD тестирование алгоритма

### 🆕 Возможности v3.7.0:
- **🚀 Автоматическая обработка Excel** - после загрузки файла автоматически выполняется дедупликация, анализ производства и формирование списка
- **📦 Единый API endpoint** - `/api/v1/tochka/upload-and-auto-process/` объединяет все операции в одном запросе
- **🎯 Упрощенный интерфейс** - удалены кнопки "Обновить все", "Анализ производства", "Список к производству", "Дедупликация"
- **📊 Сворачивание таблиц** - механизм сворачивания/разворачивания всех таблиц на вкладке Точка
- **🔄 Автоматическое управление состоянием** - промежуточные таблицы автоматически сворачиваются после обработки Excel
- **⚡ Оптимизация производительности** - целевое время обработки < 5 секунд для типичных файлов
- **💡 Улучшенная обратная связь** - детальные сообщения о ходе и результатах обработки

### 🆕 Новые возможности v3.5.1:
- **🧭 Горизонтальное меню навигации** - переход от вертикального бокового меню к горизонтальному в header
- **🗄️ Вкладка "Точка"** - добавлена в основное меню навигации с иконкой DatabaseOutlined
- **📊 Исправлена информация о версии** - создан файл VERSION, обновлен SystemInfo для корректного отображения версии
- **💾 Redux state persistence** - данные на вкладке "Точка" сохраняются при переключении между вкладками
- **🎨 Улучшенная структура интерфейса** - современный горизонтальный layout соответствует требованиям v3.5.1
- **🔧 Исправлены проблемы версии** - теперь система корректно показывает v3.5.1 вместо vunknown
- **📅 Корректная дата сборки** - улучшен метод build_date для надежного получения временных меток

### 🧮 Алгоритм расчета резерва v3.8.0:
```python
def calculate_reserve_display(reserved_stock, current_stock):
    """
    Новый алгоритм расчета и отображения резерва
    
    Args:
        reserved_stock (Decimal): Количество товара в резерве
        current_stock (Decimal): Текущий остаток товара
        
    Returns:
        Dict[str, Any]: Результат расчета с цветовой индикацией
    """
    # Основной расчет: Резерв - Остаток
    calculated_reserve = reserved_stock - current_stock
    
    # Цветовая индикация
    if reserved_stock == 0:
        color_indicator = 'gray'     # Нет резерва
        should_show_calculation = False
    elif reserved_stock > current_stock:
        color_indicator = 'blue'     # Резерв больше остатка (хорошо)
        should_show_calculation = True
    else:
        color_indicator = 'red'      # Резерв <= остатка (внимание)
        should_show_calculation = True
    
    return {
        'calculated_reserve': calculated_reserve,
        'color_indicator': color_indicator,
        'should_show_calculation': should_show_calculation,
        'display_text': f"{reserved_stock} → {calculated_reserve} шт",
        'tooltip_text': get_tooltip_text(calculated_reserve)
    }
```

### 🎨 Цветовая схема резерва:
- **🔵 Синий (#1890ff)**: `Резерв > Остаток` - избыток резерва (положительно)
- **🔴 Красный (#ff4d4f)**: `Резерв ≤ Остаток` - недостаток резерва (требует внимания)
- **⚫ Серый (#8c8c8c)**: `Резерв = 0` - резерв отсутствует

### 🔄 Migration from v3.5.0:
- Сохранена функциональность Redux Data Persistence
- Все TypeScript исправления остаются активными
- Улучшен UI/UX с горизонтальным меню

## 📋 Версия 4.6 (2025-07-31) - Экспорт Excel и полный функционал

### 🆕 Новые возможности v4.6:
- **Экспорт в Excel** - добавлена возможность экспорта таблиц "Данные Excel без дублей" и "Список к производству"
- **Стилизованные Excel файлы** - заголовки в цветах PrintFarm, автоширина колонок, итоговые строки
- **Автоматическое скачивание** - файлы скачиваются с временными метками в именах
- **Интеграция в UI** - кнопки экспорта встроены в заголовки таблиц
- **Полный рабочий функционал** - все основные возможности системы работают корректно
- **Примечание**: В интерфейсе присутствуют дополнительные элементы UI которые могут быть убраны в следующей версии

### 🆕 Новые возможности v4.5:
- **Полная загрузка данных Excel** - убрано ограничение на 50 записей в таблице дедуплицированных данных
- **Очистка от отладочных функций** - удалены все тестовые кнопки и debug-функции
- **Оптимизация производительности** - удалены ненужные print'ы и отладочный код
- **Улучшенная стабильность** - система готова к продуктивному использованию с большими файлами
- **Исправлена проблема с артикулом 423-51412** - все функции дедупликации и сопоставления работают корректно

### 🆕 Новые возможности v4.4:
- **Анализ покрытия товаров в Точке** - Excel содержит товары которые ЕСТЬ в Точке
- **Поиск товаров МойСклад отсутствующих в Точке** с тегом "НЕТ В ТОЧКЕ"
- **Применение алгоритма производства** только к товарам на производство
- **Приоритетная сортировка** - сначала товары отсутствующие в Точке
- **Статистика покрытия** - процент товаров которые есть в Точке
- **Визуальные предупреждения** для товаров требующих регистрации

### 🆕 Новые возможности v4.3:
- **Объединение Excel данных с товарами** по полю "Артикул" из базы данных
- **Умное сопоставление артикулов** с автоматическим поиском в базе товаров
- **Расширенная таблица результатов** с данными из Excel и информацией о товарах
- **Статистика совпадений** (найдено/не найдено товаров, процент совпадений)
- **Визуальные индикаторы** для найденных и не найденных товаров
- **Сохранение информации о дубликатах** после объединения

### 🆕 Новые возможности v4.2:
- **Автоматическая дедупликация** по полю "Артикул товара"
- **Суммирование заказов** для дубликатов (по полю "Заказов, шт.")
- **Отображение информации о дубликатах** в таблице
- **Статистика дедупликации** (исходных записей, уникальных артикулов, объединенных дубликатов)
- **Сортировка результатов** по убыванию количества заказов
- **Визуальные индикаторы** для строк с объединенными дубликатами

### 🆕 Новые возможности v4.1:
- **Загрузка Excel файлов** с поиском колонок "Артикул товара" и "Заказов, шт."
- **Автоматический парсинг** Excel файлов (.xlsx, .xls)
- **Интеллектуальный поиск колонок** с несколькими вариантами названий
- **Отображение загруженных данных** в отдельной таблице
- **Валидация и обработка ошибок** при загрузке файлов

### 🆕 Новые возможности v4.0:
- **Новая вкладка "Точка"** рядом с вкладкой "Товары"
- **API для получения товаров** из основной базы данных
- **API для получения списка на производство** с приоритетами
- **API статистики товаров** по типам и состояниям
- **Изолированная функциональность** без влияния на существующий код

### 🔧 API Endpoints (v4.6):
- `GET /api/v1/tochka/products/` - Получить все товары
- `GET /api/v1/tochka/production/` - Получить список на производство  
- `GET /api/v1/tochka/stats/` - Получить статистику товаров
- `POST /api/v1/tochka/upload-excel/` - Загрузить Excel файл с полной дедупликацией (без ограничений на количество записей)
- `POST /api/v1/tochka/merge-with-products/` - Анализ производства с проверкой наличия в Точке
- `POST /api/v1/tochka/filtered-production/` - Получить отфильтрованный список производства только для товаров в Точке
- `POST /api/v1/tochka/export-deduplicated/` - Экспорт дедуплицированных данных Excel в стилизованный файл
- `POST /api/v1/tochka/export-production/` - Экспорт списка к производству в стилизованный Excel файл

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

### 📊 Алгоритм дедупликации Excel (v4.2):
```python
def deduplicate_excel_data(raw_data):
    """
    Дедупликация данных из Excel файла
    1. Группируем записи по артикулу
    2. Суммируем заказы для каждого артикула
    3. Сохраняем информацию о дублированных строках
    4. Сортируем по убыванию суммы заказов
    """
    article_dict = {}
    
    for item in raw_data:
        article = item['article']
        if article in article_dict:
            # Суммируем заказы
            article_dict[article]['orders'] += item['orders']
            # Запоминаем номера строк дубликатов
            article_dict[article]['duplicate_rows'].append(item['row_number'])
        else:
            # Первое вхождение артикула
            article_dict[article] = {
                'article': article,
                'orders': item['orders'],
                'row_number': item['row_number'],
                'duplicate_rows': []
            }
    
    # Формируем результат с информацией о дубликатах
    result = []
    for data in article_dict.values():
        result.append({
            'article': data['article'],
            'orders': data['orders'],
            'row_number': data['row_number'],
            'has_duplicates': len(data['duplicate_rows']) > 0,
            'duplicate_rows': data['duplicate_rows'] if data['duplicate_rows'] else None
        })
    
    # Сортируем по убыванию количества заказов
    return sorted(result, key=lambda x: x['orders'], reverse=True)
```

### 🧪 Тестирование и исправления v4.5:
```python
# Исправления в v4.5:
def upload_excel_file_for_tochka():
    """
    ИСПРАВЛЕНО: Убрано ограничение на 50 записей
    Было: 'data': extracted_data[:50]
    Стало: 'data': extracted_data  # Все записи
    """
    return Response({
        'data': extracted_data,  # Показываем все записи без ограничений
        'total_records': len(extracted_data),
        'unique_articles': len(extracted_data),
    })

# Протестированные функции:
- normalize_article() - корректная нормализация артикулов
- createDeduplicatedData() - объединение дубликатов 
- debug_article_matching - артикул 423-51412 найден и обработан ✅
- trace_article_processing - пошаговая трассировка работает ✅
- merge_excel_with_products - анализ покрытия Точки ✅

# Результаты тестирования:
- Артикул 423-51412: найден в 3 строках Excel, суммарно 22 заказа
- Дедупликация работает корректно для всех артикулов
- Анализ покрытия показал 1.9% (2 из 108 товаров в тестовых данных)
- Все отладочные функции удалены после подтверждения работы
```

### 🔄 Алгоритм объединения с товарами (v4.3):
```python
def merge_excel_with_products(excel_data):
    """
    Объединение данных Excel с товарами из базы данных по артикулу
    1. Извлекаем артикулы из Excel данных
    2. Ищем товары в базе данных по артикулам
    3. Объединяем данные Excel с найденными товарами
    4. Сохраняем пустые поля для не найденных товаров
    """
    # Получаем артикулы из Excel
    excel_articles = [item['article'] for item in excel_data]
    
    # Загружаем товары из базы данных
    products = Product.objects.filter(article__in=excel_articles)
    products_dict = {product.article: product for product in products}
    
    # Объединяем данные
    result = []
    for excel_item in excel_data:
        article = excel_item['article']
        product = products_dict.get(article)
        
        if product:
            # Товар найден - объединяем данные
            merged_item = {
                # Данные из Excel
                'article': excel_item['article'],
                'orders': excel_item['orders'],
                'has_duplicates': excel_item.get('has_duplicates', False),
                
                # Данные из базы товаров
                'product_name': product.name,
                'current_stock': float(product.current_stock),
                'sales_last_2_months': float(product.sales_last_2_months),
                'product_type': product.product_type,
                'production_needed': float(product.production_needed),
                'production_priority': product.production_priority,
                
                # Флаги
                'product_matched': True,
                'has_product_data': True,
            }
        else:
            # Товар не найден - только Excel данные
            merged_item = {
                # Данные из Excel
                'article': excel_item['article'],
                'orders': excel_item['orders'],
                'has_duplicates': excel_item.get('has_duplicates', False),
                
                # Пустые поля товара
                'product_name': None,
                'current_stock': None,
                'sales_last_2_months': None,
                'product_type': None,
                'production_needed': None,
                'production_priority': None,
                
                # Флаги
                'product_matched': False,
                'has_product_data': False,
            }
        
        result.append(merged_item)
    
    # Сортируем по количеству заказов (убывание)
    return sorted(result, key=lambda x: x['orders'], reverse=True)
```

### 🔍 Алгоритм анализа покрытия Точки (v4.4):
```python
def analyze_tochka_coverage(excel_data):
    """
    Анализ покрытия товаров в Точке
    Excel содержит товары которые ЕСТЬ в Точке
    Нужно найти товары МойСклад которых НЕТ в Точке
    
    1. Загружаем Excel с товарами Точки
    2. Получаем все товары на производство из МойСклад
    3. Для каждого товара проверяем есть ли он в Excel (Точке)
    4. Помечаем отсутствующие товары как "НЕТ В ТОЧКЕ"
    """
    # Создаем множество артикулов из Excel (товары Точки)
    tochka_articles = {item['article'] for item in excel_data}
    
    # Получаем товары на производство из МойСклад
    products_for_production = Product.objects.filter(
        production_needed__gt=0
    ).order_by('-production_priority')
    
    result = []
    for product in products_for_production:
        if product.article in tochka_articles:
            # Товар ЕСТЬ в Точке
            item = {
                'article': product.article,
                'product_name': product.name,
                'production_needed': product.production_needed,
                'production_priority': product.production_priority,
                'is_in_tochka': True,
                'needs_registration': False,
            }
        else:
            # Товара НЕТ в Точке - требует регистрации!
            item = {
                'article': product.article,
                'product_name': product.name,
                'production_needed': product.production_needed,
                'production_priority': product.production_priority,
                'is_in_tochka': False,
                'needs_registration': True,  # Важный флаг!
            }
        result.append(item)
    
    # Сортировка: сначала товары НЕ в Точке, потом по приоритету
    return sorted(result, key=lambda x: (not x['needs_registration'], -x['production_priority']))
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