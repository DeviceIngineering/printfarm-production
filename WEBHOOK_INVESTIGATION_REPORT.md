# 🔍 Webhook Investigation Report - SimplePrint Events

**Дата:** 2025-10-28
**Версия:** v4.4.0
**Ветка:** feature/webhook-testing

---

## 📋 Проблема

Пользователь настроил webhook на стороне SimplePrint, но в логах появлялись сообщения:
```
WARNING ⚠️ Unknown event type: test
```

## 🔬 Исследование

### 1. Анализ логов
Обнаружено событие `test` от SimplePrint - стандартное тестовое событие для проверки webhook URL.

### 2. Анализ базы данных
```sql
SELECT event_type, COUNT(*) FROM PrinterWebhookEvent
GROUP BY event_type ORDER BY COUNT(*) DESC;

Результат:
- unknown: 55 событий ❌
- job_started: 24 события ✅
- job_completed: 8 событий ✅
- job_failed: 6 событий ✅
- test: 3 события ❌
```

### 3. Детальный анализ UNKNOWN событий
Выявлены реальные события SimplePrint, которые не были добавлены в маппинг:

```
printer.material_changed:  16 событий
job.done:                  16 событий
job.bed_cleared:           15 событий
queue.add_item:             3 события
test:                       3 события
queue.changed:              1 событие
printer.state_changed:      1 событие
```

---

## ✅ Решение

### Этап 1: Добавление недостающих типов событий в модель

**Файл:** `backend/apps/simpleprint/models.py`

**Добавлено в `EVENT_TYPE_CHOICES`:**
```python
('test', 'Тестовое событие'),
('job_paused', 'Задание приостановлено'),
('job_resumed', 'Задание возобновлено'),
('printer_state_changed', 'Изменение состояния принтера'),
('file_created', 'Файл создан'),
('file_deleted', 'Файл удален'),
```

**Миграция:** `0006_alter_printerwebhookevent_event_type.py`

### Этап 2: Обновление маппинга событий

**Файл:** `backend/apps/simpleprint/views.py`

**Добавлено в `event_mapping`:**
```python
'test': 'test',
'job.done': 'job_completed',
'job.bed_cleared': 'job_completed',
'queue.add_item': 'queue_changed',
'printer.material_changed': 'printer_state_changed',
```

### Этап 3: Исправление обработчика событий

**Проблема:** Метод `_process_webhook_event` выдавал warning для события `test`, т.к. оно не начинается с `job.`, `printer.`, `queue.`, или `file.`

**Решение:**
```python
def _process_webhook_event(self, webhook_event, event: str, data: dict):
    # Тестовое событие от SimplePrint
    if event == 'test':
        logger.info(f"✅ Test webhook received successfully")
        return

    # Остальная логика...
```

---

## 📊 Результаты

### До исправления
```
INFO 📨 Received SimplePrint webhook: event=test
WARNING ⚠️ Unknown event type: test
INFO ✅ Webhook processed successfully: test
```

### После исправления
```
INFO 📨 Received SimplePrint webhook: event=test
INFO ✅ Test webhook received successfully
INFO ✅ Webhook processed successfully: test
```

---

## 📝 Полный список поддерживаемых событий (19 типов)

| SimplePrint Event | Наш Event Type | Описание |
|-------------------|----------------|----------|
| `test` | `test` | Тестовое событие SimplePrint ✅ |
| `job.started` | `job_started` | Печать началась |
| `job.finished` | `job_completed` | Печать завершена |
| `job.done` | `job_completed` | Печать завершена (альт. название) |
| `job.failed` | `job_failed` | Печать провалена |
| `job.paused` | `job_paused` | Печать на паузе |
| `job.resumed` | `job_resumed` | Печать возобновлена |
| `job.bed_cleared` | `job_completed` | Стол очищен (задание завершено) |
| `printer.online` | `printer_online` | Принтер онлайн |
| `printer.offline` | `printer_offline` | Принтер оффлайн |
| `printer.state_changed` | `printer_state_changed` | Изменение состояния |
| `printer.material_changed` | `printer_state_changed` | Изменение материала |
| `queue.changed` | `queue_changed` | Изменения в очереди |
| `queue.add_item` | `queue_changed` | Добавление в очередь (альт.) |
| `queue.item_added` | `queue_changed` | Добавление в очередь |
| `queue.item_deleted` | `queue_changed` | Удаление из очереди |
| `queue.item_moved` | `queue_changed` | Перемещение в очереди |
| `file.created` | `file_created` | Файл создан |
| `file.deleted` | `file_deleted` | Файл удален |

---

## 🔧 Коммиты

```
f2cbc8c - ✨ Feature: Add Webhook Testing functionality - v4.4.0
3b3f50f - 📝 Docs: Update version to v4.4.0 and CHANGELOG
b455808 - 🐛 Fix: Webhook API URLs - remove duplicate /api/v1/ prefix
f40ed73 - 🐛 Fix: Add support for all SimplePrint webhook events
e0e6727 - ✨ Feature: Add all discovered SimplePrint webhook events
```

---

## 🎯 Выводы

1. **SimplePrint использует альтернативные названия событий:**
   - `job.done` вместо `job.finished`
   - `queue.add_item` вместо `queue.item_added`

2. **Реальные события из production:**
   - `printer.material_changed` - самое частое событие (16 раз)
   - `job.bed_cleared` - важное событие завершения работы (15 раз)

3. **Тестовые события:**
   - SimplePrint отправляет `test` событие при настройке webhook
   - Требуется явная обработка, т.к. не подходит под стандартные префиксы

4. **Документация SimplePrint:**
   - Официальная документация webhook событий недоступна или неполная
   - Реальные события можно обнаружить только через анализ production логов

---

## 📌 Рекомендации

1. **Мониторинг:** Периодически проверять `unknown` события в БД для обнаружения новых типов
2. **Логирование:** Оставить детальное логирование webhook payload для отладки
3. **Документация:** Поддерживать актуальность SIMPLEPRINT_WEBHOOK_SETUP.md

---

## 🔗 Связанные файлы

- `backend/apps/simpleprint/models.py` - модели webhook событий
- `backend/apps/simpleprint/views.py` - обработчик webhook
- `backend/apps/simpleprint/migrations/0006_*.py` - миграция типов событий
- `SIMPLEPRINT_WEBHOOK_SETUP.md` - полная документация настройки
- `test_webhook_v2.sh` - скрипт тестирования

---

**Статус:** ✅ Проблема полностью решена
**Production:** ✅ Задеплоено и протестировано
**Backup:** ✅ Создана резервная копия `factory_v3_webhook_complete_*`
