# 🧪 Пошаговое тестирование SimplePrint Webhooks

## ✅ Статус проверки

**Дата**: 2025-10-28
**Endpoint**: `http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/`
**Статус**: ✅ **РАБОТАЕТ** - успешно принимает webhooks

---

## 📋 Что уже протестировано

### ✅ Тест 1: Доступность endpoint извне
```bash
curl -X POST http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"webhook_id": 999, "event": "test", "timestamp": 1730121600, "data": {}}'

# Результат: HTTP 200
# {"status":"received","event_type":"unknown","message":"Webhook processed successfully"}
```

### ✅ Тест 2: Прием различных событий SimplePrint
Протестированы события:
- ✅ `job.started` - начало печати
- ✅ `job.finished` - завершение печати
- ✅ `job.failed` - ошибка печати
- ✅ `printer.state_changed` - изменение статуса принтера
- ✅ `queue.changed` - изменение очереди

**Логи сервера подтверждают прием всех событий:**
```
INFO Received webhook: {'webhook_id': 12345, 'event': 'job.started', ...}
INFO Received webhook: {'webhook_id': 12346, 'event': 'job.finished', ...}
INFO Received webhook: {'webhook_id': 12347, 'event': 'job.failed', ...}
INFO Received webhook: {'webhook_id': 12348, 'event': 'printer.state_changed', ...}
INFO Received webhook: {'webhook_id': 12349, 'event': 'queue.changed', ...}
```

---

## 🔧 Настройка webhook в SimplePrint UI

### Шаг 1: Вход в личный кабинет SimplePrint
1. Откройте https://simplyprint.io
2. Войдите с вашими учетными данными

### Шаг 2: Найти раздел Webhooks
Возможные места:
- **Settings → Integrations → Webhooks**
- **Settings → API → Webhooks**
- **Settings → Developer → Webhooks**
- **Company Settings → Webhooks**

### Шаг 3: Создать новый webhook

**Обязательные поля:**

| Поле | Значение |
|------|----------|
| **Name** | `PrintFarm Planning V2 - Events` |
| **URL** | `http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/` |
| **Method** | `POST` |
| **Content-Type** | `application/json` |

**⚠️ ВАЖНО: НЕ путать с admin URL!**
- ❌ НЕПРАВИЛЬНО: `http://kemomail3.keenetic.pro:13000/admin/simpleprint/...`
- ✅ ПРАВИЛЬНО: `http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/`

### Шаг 4: Выбрать события

**Рекомендуемые события для Planning V2:**

#### 🖨️ События принтера:
- ☑️ `printer.online` / `printer.state_changed` - Принтер онлайн
- ☑️ `printer.offline` - Принтер оффлайн

#### 📄 События заданий:
- ☑️ `job.started` - Начало печати
- ☑️ `job.finished` / `job.completed` - Завершение печати
- ☑️ `job.paused` - Пауза печати
- ☑️ `job.resumed` - Возобновление печати
- ☑️ `job.cancelled` - Отмена задания
- ☑️ `job.failed` - Ошибка печати

#### 📊 События прогресса:
- ☑️ `job.progress` - Обновление прогресса (каждые 10% или по времени)

#### 📋 События очереди:
- ☑️ `queue.changed` - Изменение очереди
- ☑️ `queue.item_added` - Добавление в очередь
- ☑️ `queue.item_removed` - Удаление из очереди

**Примечание**: Названия событий могут отличаться в зависимости от версии SimplePrint API. Выберите все доступные события, связанные с принтерами и заданиями.

### Шаг 5: Authentication (опционально)

**Если SimplePrint поддерживает заголовки:**
- Header Name: `X-SP-Token`
- Header Value: `<ваш_секретный_токен>`

**Если не поддерживает:**
- Оставьте поле пустым
- Наш endpoint работает с `AllowAny` (без обязательной аутентификации)

### Шаг 6: Сохранить webhook

Нажмите **"Save"** / **"Create"**

---

## 🧪 Тестирование настроенного webhook

### Тест 1: Отправить тестовое событие из SimplePrint UI

1. В списке webhooks найдите созданный webhook
2. Нажмите **"Test"** / **"Send Test Event"** / **"Trigger Test"**
3. SimplePrint отправит тестовое событие на ваш URL

**Ожидаемый результат:**
- SimplePrint UI показывает: ✅ "Success" или "200 OK"
- Или появляется зеленая галочка

### Тест 2: Проверить логи Django

Сразу после отправки тестового события выполните:

```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'docker logs --tail 50 factory_v3-backend-1 2>&1' | grep -i "webhook"
```

**Ожидаемый вывод:**
```
INFO Received webhook: {'webhook_id': <id>, 'event': '<event_type>', ...}
INFO Webhook processed successfully: <event_type>
```

или (если на сервере старая версия):
```
INFO Received webhook: {'webhook_id': <id>, 'event': '<event_type>', ...}
WARNING Unknown event type: unknown
INFO Webhook processed successfully: unknown
```

### Тест 3: Проверить данные в базе (когда миграции применены)

```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro
docker exec -it factory_v3-backend-1 python manage.py shell

# В Django shell:
from apps.simpleprint.models import PrinterWebhookEvent

# Посчитать события
print(f"Всего событий: {PrinterWebhookEvent.objects.count()}")

# Показать последние 5 событий
for event in PrinterWebhookEvent.objects.order_by('-received_at')[:5]:
    print(f"{event.received_at} - {event.event_type} - {event.printer_id}")

# Показать детали последнего события
last = PrinterWebhookEvent.objects.order_by('-received_at').first()
if last:
    print(f"\nПоследнее событие:")
    print(f"  Event: {last.event_type}")
    print(f"  Printer: {last.printer_id}")
    print(f"  Job: {last.job_id}")
    print(f"  Processed: {last.processed}")
    print(f"  Payload: {last.payload}")
```

**Ожидаемый результат:**
- Количество событий > 0
- Последнее событие соответствует тестовому

---

## 🎯 Тест реального события

### Вариант 1: Запустить печать принтера

1. В SimplePrint выберите принтер
2. Запустите любое задание на печать
3. Через несколько секунд SimplePrint отправит `job.started` webhook

### Вариант 2: Изменить очередь

1. Добавьте файл в очередь принтера
2. SimplePrint отправит `queue.changed` webhook

### Проверка:

```bash
# Смотреть логи в реальном времени
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'docker logs -f factory_v3-backend-1 2>&1' | grep -i "webhook"
```

**Ожидаемый вывод:**
```
INFO Received webhook: {'webhook_id': ..., 'event': 'job.started', ...}
```

---

## 📊 Диагностика проблем

### Проблема 1: SimplePrint показывает "Connection failed"

**Проверьте доступность URL извне:**
```bash
curl -X POST http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

**Ожидается**: HTTP 200 с JSON ответом

**Если timeout:**
- Проверьте firewall на роутере
- Проверьте, что порт 13000 открыт
- Проверьте nginx конфигурацию

### Проблема 2: SimplePrint показывает "Invalid URL"

**Причина**: SimplePrint требует HTTPS

**Решение**: См. `SIMPLEPRINT_WEBHOOK_FIX.md`
- Cloudflare Tunnel (рекомендуется)
- ngrok
- Let's Encrypt SSL

### Проблема 3: Webhook приходит, но показывает "Unknown event"

**Причина**: На сервере старая версия views.py

**Проверка:**
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'cat ~/factory_v3/backend/apps/simpleprint/views.py' | grep "event_mapping"
```

**Если не находит `event_mapping`:**
- Код не обновлен на сервере
- Нужно загрузить новую версию `views.py`

**Решение:**
```bash
# Загрузить обновленный views.py
scp -P 2132 backend/apps/simpleprint/views.py \
  printfarm@kemomail3.keenetic.pro:~/factory_v3/backend/apps/simpleprint/

# Перезапустить backend
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  "docker restart factory_v3-backend-1"
```

### Проблема 4: События не сохраняются в БД

**Причина**: Миграции не применены

**Проверка:**
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro
docker exec factory_v3-backend-1 python manage.py showmigrations simpleprint
```

**Решение:**
```bash
# Создать миграции (если нужно)
docker exec factory_v3-backend-1 python manage.py makemigrations simpleprint

# Применить миграции
docker exec factory_v3-backend-1 python manage.py migrate simpleprint
```

---

## ✅ Чеклист успешной настройки

После настройки, проверьте:

- [ ] **URL доступен извне**: `curl` тест возвращает HTTP 200
- [ ] **Webhook создан в SimplePrint UI**
- [ ] **Тестовое событие отправлено** из SimplePrint
- [ ] **Событие видно в логах Django**: `INFO Received webhook`
- [ ] **Миграции применены**: таблица `simpleprint_printerwebhookevent` существует
- [ ] **События сохраняются в БД**: `PrinterWebhookEvent.objects.count() > 0`
- [ ] **Реальное событие получено**: запуск печати → `job.started` в логах

---

## 📞 Дополнительная помощь

### Если SimplePrint не поддерживает webhooks в UI:

1. **Проверьте ваш план подписки**
   - Webhooks могут быть доступны только в платных планах
   - Обратитесь в поддержку SimplePrint

2. **Используйте API для регистрации webhooks**
   ```bash
   docker exec factory_v3-backend-1 \
     python manage.py register_webhooks
   ```

3. **Проверьте документацию SimplePrint**
   - https://simplyprint.io/docs/api/
   - https://help.simplyprint.io/en/article/all-about-the-webhooks-feature-1g12e5c/

### Контакты SimplePrint:
- 📧 Email: support@simplyprint.io
- 💬 Discord: https://discord.gg/simplyprint
- 📖 Docs: https://simplyprint.io/docs/

---

## 🎯 Итоговая проверка

После всех настроек выполните финальный тест:

```bash
# Запустить тестовый скрипт
./test_webhook.sh

# Проверить логи
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'docker logs --tail 100 factory_v3-backend-1' | grep -i "webhook"

# Проверить БД (если миграции применены)
docker exec factory_v3-backend-1 python manage.py shell
>>> from apps.simpleprint.models import PrinterWebhookEvent
>>> print(f"Событий в БД: {PrinterWebhookEvent.objects.count()}")
```

**Если все 3 команды выполнены успешно - webhook работает корректно! ✅**

---

**Версия**: 1.0
**Дата**: 2025-10-28
**Автор**: Claude Code AI
