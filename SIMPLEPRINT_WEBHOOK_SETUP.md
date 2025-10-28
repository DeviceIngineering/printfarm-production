# 🔗 SimplePrint Webhook Setup Guide

## Проблема и решение

### ❌ НЕПРАВИЛЬНЫЙ URL (вызывает HTTP 403)
```
http://kemomail3.keenetic.pro:18001/admin/simpleprint/printerwebhookevent/
```
**Почему не работает:**
- Это административная страница Django
- Требует аутентификацию администратора
- Возвращает HTTP 302 (редирект на /admin/login/)
- SimplePrint не может аутентифицироваться в Django Admin

### ✅ ПРАВИЛЬНЫЙ URL для SimplePrint
```
http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/webhook/
```
**Почему работает:**
- API endpoint без требования аутентификации (`AllowAny`)
- Специально создан для приема webhooks от SimplePrint
- Возвращает HTTP 200 OK с JSON ответом
- Сохраняет события в БД для дальнейшего анализа

---

## 📋 Настройка в SimplePrint Panel

### Шаг 1: Откройте SimplePrint Panel
1. Зайдите в SimplePrint Panel (https://simplyprint.io)
2. Войдите в свой аккаунт
3. Перейдите в Settings → Webhooks

### Шаг 2: Создайте новый Webhook
1. Нажмите **"Add Webhook"**
2. Заполните поля:

**Webhook Settings:**
```yaml
Name: PrintFarm Production Webhook
URL: http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/webhook/
Method: POST
Content-Type: application/json
Active: ✓ (включено)
```

**Events (выберите нужные):**
```
✓ job.started         - Печать началась
✓ job.finished        - Печать завершена
✓ job.paused          - Печать на паузе
✓ job.resumed         - Печать возобновлена
✓ job.failed          - Печать провалена
✓ printer.online      - Принтер онлайн
✓ printer.offline     - Принтер оффлайн
✓ queue.item_added    - Добавлен в очередь
✓ queue.item_deleted  - Удален из очереди
✓ queue.item_moved    - Перемещен в очереди
```

**Secret (опционально):**
- Оставьте пустым для простоты
- Или добавьте случайную строку и сохраните в `.env`:
  ```env
  SIMPLEPRINT_WEBHOOK_SECRET=ваш_секретный_токен
  ```

### Шаг 3: Сохраните и протестируйте
1. Нажмите **"Save"**
2. Нажмите **"Test Webhook"** (если доступно)
3. Должен появиться статус "Success" или HTTP 200

---

## 🧪 Тестирование webhook

### Вариант 1: Ручной тест через curl
```bash
curl -X POST "http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/webhook/" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12345,
    "event": "job.started",
    "timestamp": 1698765432,
    "data": {
      "job": {
        "id": 4077363,
        "file_name": "test_model.gcode"
      },
      "printer": {
        "id": 35372,
        "name": "P1S-1"
      }
    }
  }'
```

**Ожидаемый ответ:**
```json
{
  "status": "received",
  "event": "job.started",
  "message": "Webhook processed successfully"
}
```

### Вариант 2: Использовать тестовый скрипт
```bash
cd /Users/dim11/Documents/myProjects/Factory_v3
./test_webhook_v2.sh
```

### Вариант 3: Проверка в SimplePrint UI
1. Откройте вкладку **"🔗 Webhook Testing"** в модальном окне планирования
2. Нажмите кнопку **"Test Webhook"**
3. Проверьте появление события в таблице

---

## 🔍 Проверка работы webhook

### 1. Проверка логов Django
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'docker logs --tail 50 factory_v3-backend-1 | grep webhook'
```

**Ожидаемый вывод:**
```
INFO 📨 Received SimplePrint webhook: event=job.started, webhook_id=12345, timestamp=1698765432
INFO ✅ Webhook processed successfully: job.started
```

### 2. Проверка записей в БД
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  "docker exec factory_v3-backend-1 python manage.py shell -c \"
from apps.simpleprint.models import PrinterWebhookEvent
print(f'Total events: {PrinterWebhookEvent.objects.count()}')
for event in PrinterWebhookEvent.objects.order_by('-received_at')[:5]:
    print(f'{event.received_at}: {event.event_type} - Printer {event.printer_id}')
\""
```

### 3. Проверка через Django Admin
1. Откройте: http://kemomail3.keenetic.pro:18001/admin/
2. Войдите как администратор
3. Перейдите в **SimplePrint → Printer Webhook Events**
4. Должны увидеть список входящих событий

### 4. Проверка через Frontend UI
1. Откройте: http://kemomail3.keenetic.pro:13000/planningv2
2. Нажмите кнопку **"Отладка API"**
3. Перейдите на вкладку **"🔗 Webhook Testing"**
4. Нажмите **"Обновить"**
5. Должны увидеть статистику и список событий

---

## 🛠️ Устранение неполадок

### Проблема: HTTP 403 Forbidden
**Причина:** Используется неправильный URL (admin page)
**Решение:** Используйте `/api/v1/simpleprint/webhook/` вместо `/admin/...`

### Проблема: HTTP 302 Found (редирект)
**Причина:** То же что и выше - admin page
**Решение:** То же - используйте API endpoint

### Проблема: HTTP 401 Unauthorized
**Причина:** Неправильный secret token в header
**Решение:**
- Проверьте что SimplePrint отправляет правильный token в header `X-SP-Token`
- Или удалите `SIMPLEPRINT_WEBHOOK_SECRET` из `.env` чтобы отключить проверку

### Проблема: События не появляются в БД
**Решение:**
1. Проверьте логи backend
2. Убедитесь что SimplePrint отправляет правильный JSON format
3. Проверьте что порт 18001 доступен извне

### Проблема: SimplePrint не может достучаться до webhook
**Решение:**
1. Проверьте firewall на сервере
2. Убедитесь что порт 18001 открыт
3. Проверьте docker port mapping:
   ```bash
   docker ps | grep factory_v3-backend
   ```
   Должно быть: `0.0.0.0:18001->8000/tcp`

---

## 📊 Формат webhook payload от SimplePrint

SimplePrint отправляет следующий формат:

```json
{
  "webhook_id": 12345,
  "event": "job.started",
  "timestamp": 1698765432,
  "data": {
    "job": {
      "id": 4077363,
      "file_name": "model.gcode",
      "file_id": 123456,
      "started_at": 1698765432,
      "estimated_time": 7200,
      "user": {
        "id": 31471,
        "name": "Admin"
      }
    },
    "printer": {
      "id": 35372,
      "name": "P1S-1",
      "state": "printing",
      "online": true
    }
  }
}
```

### Поддерживаемые события

Наш endpoint обрабатывает и маппит следующие события:

| SimplePrint Event | Наш Event Type | Описание |
|-------------------|----------------|-----------|
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
| `printer.state_changed` | `printer_state_changed` | Изменение состояния принтера |
| `printer.material_changed` | `printer_state_changed` | Изменение материала принтера |
| `queue.changed` | `queue_changed` | Изменения в очереди |
| `queue.add_item` | `queue_changed` | Добавление в очередь (альт. название) |
| `queue.item_added` | `queue_changed` | Добавление в очередь |
| `queue.item_deleted` | `queue_changed` | Удаление из очереди |
| `queue.item_moved` | `queue_changed` | Перемещение в очереди |
| `queue.delete_item` | `queue_item_deleted` | 🆕 Элемент очереди удален (v4.4.2) |
| `file.created` | `file_created` | Файл создан |
| `file.deleted` | `file_deleted` | Файл удален |
| `filament.delete` | `filament_deleted` | 🆕 Филамент удален из инвентаря (v4.4.2) |
| `printer.ai_failure_detected` | `ai_failure_detected` | 🆕 AI обнаружил проблему печати (v4.4.2) |
| `printer.ai_failure_false_positive` | `ai_false_positive` | 🆕 AI ложное срабатывание (v4.4.2) |

**Итого поддерживается:** 23 типа событий SimplePrint (обновлено в v4.4.2)

---

## 📝 Management команды

### Регистрация webhooks в SimplePrint
```bash
docker exec factory_v3-backend-1 python manage.py register_webhooks
```

Эта команда автоматически:
1. Подключается к SimplePrint API
2. Создаёт webhook с правильным URL
3. Настраивает все необходимые события
4. Сохраняет webhook_id в настройках

### Очистка старых событий
```bash
docker exec factory_v3-backend-1 python manage.py shell -c "
from apps.simpleprint.models import PrinterWebhookEvent
from datetime import timedelta
from django.utils import timezone
old_date = timezone.now() - timedelta(days=30)
deleted = PrinterWebhookEvent.objects.filter(received_at__lt=old_date).delete()
print(f'Deleted {deleted[0]} old events')
"
```

---

## 🎯 Итоговый чеклист

- [ ] Удалить старый неправильный webhook в SimplePrint Panel
- [ ] Создать новый webhook с URL: `http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/webhook/`
- [ ] Выбрать нужные события (job.started, job.finished, etc.)
- [ ] Протестировать webhook через SimplePrint UI
- [ ] Проверить что события попадают в БД
- [ ] Открыть вкладку "Webhook Testing" в PrintFarm UI
- [ ] Убедиться что события отображаются в таблице

---

**Версия документа:** v4.4.0
**Дата:** 2025-10-28
**Автор:** Claude Code
