# PrintFarm Production Management System

Система управления производством для PrintFarm с интеграцией МойСклад для анализа товарных остатков и формирования оптимального списка товаров на производство.

## Возможности

- ✅ Синхронизация товаров из МойСклад
- ✅ Анализ оборачиваемости и остатков
- ✅ Автоматический расчет потребности в производстве
- ✅ Формирование приоритизированного списка на производство
- ✅ REST API для всех операций
- ⏳ Экспорт данных в Excel (в разработке)
- ⏳ Веб-интерфейс React (в разработке)

## Технологии

### Backend
- Django 4.2 + Django REST Framework
- PostgreSQL 15
- Redis (кэширование и очереди)
- Celery (фоновые задачи)
- МойСклад API интеграция

### Frontend  
- React 18 + TypeScript
- Redux Toolkit
- Ant Design
- Tailwind CSS

### Инфраструктура
- Docker + Docker Compose
- Nginx (reverse proxy)

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd Factory_v2
cp .env.example .env
cp frontend/.env.example frontend/.env
```

### 2. Настройка переменных окружения

Отредактируйте `.env` файл:

```env
# Django
SECRET_KEY=your-secret-key-change-this
DEBUG=True

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password

# МойСклад (обязательно!)
MOYSKLAD_TOKEN=your-moysklad-token
MOYSKLAD_DEFAULT_WAREHOUSE=your-warehouse-id
```

### 3. Запуск с Docker

```bash
# Сборка и запуск всех сервисов
docker-compose up --build

# В отдельном терминале: создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Применение миграций
docker-compose exec backend python manage.py migrate
```

### 4. Проверка работы

- Backend API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/
- Frontend: http://localhost:3000/ (в разработке)
- Nginx: http://localhost/

## API Документация

### Товары

- `GET /api/v1/products/` - Список товаров с фильтрами
- `GET /api/v1/products/{id}/` - Детали товара
- `GET /api/v1/products/stats/` - Статистика по товарам

**Параметры фильтрации:**
- `search` - поиск по артикулу/названию
- `product_type` - тип товара (new/old/critical)
- `min_stock`, `max_stock` - фильтр по остаткам
- `production_needed=true` - только товары требующие производства

### Синхронизация

- `POST /api/v1/sync/start/` - Запуск синхронизации
- `GET /api/v1/sync/status/` - Статус синхронизации  
- `GET /api/v1/sync/history/` - История синхронизаций
- `GET /api/v1/sync/warehouses/` - Список складов
- `GET /api/v1/sync/product-groups/` - Группы товаров

### Производство

- `POST /api/v1/products/production/calculate/` - Расчет списка производства
- `GET /api/v1/products/production/list/` - Получить список производства
- `GET /api/v1/products/production/stats/` - Статистика производства
- `POST /api/v1/products/production/recalculate/` - Пересчет всех товаров

## Пример использования API

### Запуск синхронизации

```bash
curl -X POST http://localhost:8000/api/v1/sync/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "warehouse_id": "241ed919-a631-11ee-0a80-07a9000bb947",
    "excluded_groups": []
  }'
```

### Расчет списка производства

```bash
curl -X POST http://localhost:8000/api/v1/products/production/calculate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "min_priority": 40,
    "apply_coefficients": true
  }'
```

### Получение списка товаров

```bash
curl "http://localhost:8000/api/v1/products/?production_needed=true&min_priority=60" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Алгоритм классификации товаров

### Типы товаров:
- **Новая позиция**: остаток < 5 шт и продажи за 2 месяца < 10 шт
- **Старая позиция**: остаток >= 5 шт или продажи >= 10 шт  
- **Критическая позиция**: остаток < 5 шт но есть продажи

### Приоритеты производства:
- **100**: Критический товар с остатком < 5
- **80**: Старый товар с запасом < 5 дней
- **60**: Новый товар с остатком < 5
- **40**: Старый товар с запасом < 10 дней
- **20**: Остальные товары

### Расчет количества:
- **Новые товары**: до 10 шт если остаток < 5
- **Старые товары**: до 15 дней запаса если текущий запас < 10 дней

## Разработка

### Запуск backend в режиме разработки

```bash
cd backend
pip install -r requirements.txt
python manage.py runserver
```

### Запуск frontend в режиме разработки

```bash
cd frontend  
npm install
npm start
```

### Запуск Celery worker

```bash
cd backend
celery -A config worker -l info
```

### Запуск Celery beat (планировщик)

```bash
cd backend
celery -A config beat -l info
```

## Структура проекта

```
Factory_v2/
├── docker/              # Docker конфигурации
├── backend/             # Django приложение
│   ├── apps/           # Django приложения
│   │   ├── core/       # Базовые модели и утилиты
│   │   ├── products/   # Модели товаров и производства
│   │   ├── sync/       # Синхронизация с МойСклад
│   │   └── reports/    # Отчеты (заглушки)
│   └── config/         # Настройки Django
├── frontend/           # React приложение (в разработке)
└── docker-compose.yml  # Конфигурация Docker Compose
```

## Статус разработки

### ✅ Завершено
- [x] Docker инфраструктура
- [x] Django модели и миграции
- [x] REST API endpoints
- [x] МойСклад API клиент
- [x] Алгоритм расчета производства
- [x] Celery задачи для синхронизации
- [x] Система приоритизации товаров

### ⏳ В разработке
- [ ] React компоненты
- [ ] Экспорт в Excel
- [ ] Полный веб-интерфейс
- [ ] Аутентификация пользователей

### 📋 Планируется
- [ ] Simple Print API интеграция
- [ ] Расширенные отчеты
- [ ] Система уведомлений
- [ ] Мобильная версия

## Поддержка

Для вопросов и предложений создавайте Issues в репозитории проекта.

## Лицензия

Proprietary - PrintFarm Production Management System