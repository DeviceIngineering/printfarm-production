# Раздел "Настройки" PrintFarm v3.2

## Обзор

Новый раздел "Настройки" предоставляет централизованное управление всеми параметрами системы PrintFarm, включая информацию о версии, автоматическую синхронизацию по расписанию и общие параметры работы.

## Основные функции

### 1. 📊 Информация о системе
- **Текущая версия** системы (из git tag или commit)
- **Дата сборки** (последний коммит)  
- **Статус компонентов** системы
- **Статистика работы** (количество товаров, синхронизаций)

### 2. 🔄 Настройки синхронизации
- **Автоматическая синхронизация** по расписанию
- **Интервал синхронизации** (кратно 30 минутам: от 30 мин до 24 часов)
- **Выбор склада** для синхронизации
- **Исключение групп товаров** из синхронизации
- **Статистика успешности** синхронизаций
- **Ручной запуск** синхронизации
- **Тест соединения** с МойСклад

### 3. ⚙️ Общие настройки
- **Целевой остаток** для новых товаров (по умолчанию 10)
- **Целевой запас в днях** для старых товаров (по умолчанию 15)
- **Порог низкого остатка** (по умолчанию 5)
- **Количество товаров** на странице (25/50/100/200)
- **Отображение изображений** товаров
- **Автообновление страницы** (отключено/30с/1мин/5мин/10мин)

## API Endpoints

### Системная информация
```
GET /api/v1/settings/system-info/
```
**Ответ:**
```json
{
  "version": "v3.1",
  "build_date": "2025-07-22 03:06:11 +0300"
}
```

### Сводная информация
```
GET /api/v1/settings/summary/
```
**Ответ:**
```json
{
  "system_info": {...},
  "sync_settings": {...},
  "general_settings": {...},
  "total_products": 150,
  "last_sync_info": {
    "date": "2025-07-22T00:00:00Z",
    "status": "success",
    "total_products": 150,
    "synced_products": 145
  },
  "system_status": {
    "sync_enabled": true,
    "next_sync": "2025-07-22T01:00:00Z",
    "database_healthy": true,
    "api_healthy": true
  }
}
```

### Настройки синхронизации
```
GET /api/v1/settings/sync/
PUT /api/v1/settings/sync/
```

**Параметры для обновления:**
```json
{
  "sync_enabled": true,
  "sync_interval_minutes": 60,
  "warehouse_id": "241ed919-a631-11ee-0a80-07a9000bb947",
  "excluded_group_ids": ["group-id-1", "group-id-2"]
}
```

### Действия с синхронизацией
```
POST /api/v1/settings/sync/test-connection/
POST /api/v1/settings/sync/trigger-manual/
```

### Общие настройки
```
GET /api/v1/settings/general/
PUT /api/v1/settings/general/
```

**Параметры:**
```json
{
  "default_new_product_stock": 10,
  "default_target_days": 15,
  "low_stock_threshold": 5,
  "products_per_page": 100,
  "show_images": true,
  "auto_refresh_interval": 0
}
```

### Управление расписанием
```
GET /api/v1/settings/schedule/status/
POST /api/v1/settings/schedule/update/
```

## Модели данных

### SystemInfo
```python
- version (property): Текущая версия из git
- build_date (property): Дата последнего коммита
```

### SyncScheduleSettings  
```python
- sync_enabled: bool = True
- sync_interval_minutes: int = 60 (кратно 30)
- warehouse_id: str
- excluded_group_ids: list
- last_sync_at: datetime
- last_sync_status: str
- total_syncs: int
- successful_syncs: int
- sync_success_rate (property): Процент успешности
```

### GeneralSettings
```python
- default_new_product_stock: int = 10
- default_target_days: int = 15
- low_stock_threshold: int = 5
- products_per_page: int = 100
- show_images: bool = True
- auto_refresh_interval: int = 0
```

## Интеграция с Celery Beat

Система автоматически создает/обновляет задачи в Celery Beat для выполнения синхронизации по расписанию:

```python
# Задача создается автоматически при изменении настроек
PeriodicTask(
    name='sync-moysklad-scheduled',
    task='apps.sync.tasks.scheduled_sync_task',
    interval=IntervalSchedule(every=60, period='MINUTES'),
    enabled=True
)
```

## Команды управления

### Инициализация настроек
```bash
python manage.py init_settings
python manage.py init_settings --reset
python manage.py init_settings --warehouse-id=YOUR_WAREHOUSE_ID
```

### Проверка состояния
```bash
# Django shell
python manage.py shell
>>> from apps.settings.models import *
>>> SystemInfo.get_instance().version
>>> SyncScheduleSettings.get_instance().sync_enabled
```

## Тестирование

### Веб-интерфейс
Откройте `test_settings_frontend.html` в браузере для интерактивного тестирования всех функций.

### API тестирование
```bash
# Получить информацию о системе
curl http://localhost:8000/api/v1/settings/system-info/

# Получить сводку
curl http://localhost:8000/api/v1/settings/summary/

# Тест соединения
curl -X POST http://localhost:8000/api/v1/settings/sync/test-connection/

# Обновить интервал синхронизации
curl -X PUT http://localhost:8000/api/v1/settings/sync/ \
  -H "Content-Type: application/json" \
  -d '{"sync_interval_minutes": 120, "sync_enabled": true}'
```

## Валидация

### Интервал синхронизации
- Должен быть кратен 30 минутам
- Минимум: 30 минут
- Максимум: 1440 минут (24 часа)

### Общие настройки
- `default_new_product_stock`: 1-100
- `default_target_days`: 1-90 дней
- `low_stock_threshold`: 1-50

## Безопасность

- Все модели настроек являются **синглтонами** (только один экземпляр)
- API endpoints используют разрешения из основной конфигурации
- Валидация всех входных параметров
- Логирование всех изменений настроек

## Миграция с предыдущих версий

При первом запуске системы после обновления:

1. Запустить миграции: `python manage.py migrate`
2. Инициализировать настройки: `python manage.py init_settings`
3. Проверить работу API через тестовый интерфейс
4. Настроить желаемые параметры синхронизации

## Интеграция с фронтендом

Фронтенд может получать информацию о системе для отображения:

```javascript
// Получить информацию о версии для footer
const systemInfo = await fetch('/api/v1/settings/system-info/').then(r => r.json());

// Получить настройки для UI
const settings = await fetch('/api/v1/settings/general/').then(r => r.json());

// Обновить размер страницы
await fetch('/api/v1/settings/general/', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({products_per_page: 200})
});
```

## Мониторинг

Система автоматически отслеживает:
- Статус синхронизаций и их успешность
- Время выполнения операций
- Ошибки подключения к МойСклад
- Статистику использования настроек

Данные доступны через endpoint `/api/v1/settings/summary/` для создания дашбордов и отчетов.