#!/bin/bash

# 🧪 Скрипт для тестирования SimplePrint Webhook
# Использование: ./test_webhook.sh

WEBHOOK_URL="http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/"

echo "======================================"
echo "🧪 ТЕСТИРОВАНИЕ SIMPLEPRINT WEBHOOK"
echo "======================================"
echo ""
echo "URL: $WEBHOOK_URL"
echo ""

# Тест 1: job.started (начало печати)
echo "1️⃣ Тест: job.started (начало печати)"
echo "--------------------------------------"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12345,
    "event": "job.started",
    "timestamp": 1730121600,
    "data": {
      "job": {
        "id": "job_001",
        "name": "test_model.gcode",
        "started": 1730121600
      },
      "printer": {
        "id": "printer_001",
        "name": "Prusa Mini #1"
      },
      "queue": {
        "id": "queue_001",
        "position": 1
      }
    }
  }' \
  --silent | python3 -m json.tool
echo ""
echo ""

# Тест 2: job.finished (завершение печати)
echo "2️⃣ Тест: job.finished (завершение печати)"
echo "--------------------------------------"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12346,
    "event": "job.finished",
    "timestamp": 1730125200,
    "data": {
      "job": {
        "id": "job_001",
        "name": "test_model.gcode",
        "started": 1730121600,
        "finished": 1730125200,
        "cost": {
          "total": 1.50,
          "filament": 1.20,
          "electricity": 0.30
        },
        "filament_used": 25.5,
        "print_time": 3600
      },
      "printer": {
        "id": "printer_001",
        "name": "Prusa Mini #1"
      }
    }
  }' \
  --silent | python3 -m json.tool
echo ""
echo ""

# Тест 3: job.failed (ошибка печати)
echo "3️⃣ Тест: job.failed (ошибка печати)"
echo "--------------------------------------"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12347,
    "event": "job.failed",
    "timestamp": 1730122800,
    "data": {
      "job": {
        "id": "job_002",
        "name": "failed_print.gcode",
        "started": 1730121600,
        "failed": 1730122800,
        "error": "Filament runout"
      },
      "printer": {
        "id": "printer_002",
        "name": "Prusa Mini #2"
      }
    }
  }' \
  --silent | python3 -m json.tool
echo ""
echo ""

# Тест 4: printer.state_changed (изменение статуса принтера)
echo "4️⃣ Тест: printer.state_changed (изменение статуса)"
echo "--------------------------------------"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12348,
    "event": "printer.state_changed",
    "timestamp": 1730121700,
    "data": {
      "printer": {
        "id": "printer_001",
        "name": "Prusa Mini #1",
        "state": "operational",
        "previous_state": "offline"
      }
    }
  }' \
  --silent | python3 -m json.tool
echo ""
echo ""

# Тест 5: queue.changed (изменение очереди)
echo "5️⃣ Тест: queue.changed (изменение очереди)"
echo "--------------------------------------"
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": 12349,
    "event": "queue.changed",
    "timestamp": 1730121800,
    "data": {
      "printer": {
        "id": "printer_001",
        "name": "Prusa Mini #1"
      },
      "queue": {
        "id": "queue_001",
        "items": [
          {
            "id": "queue_item_001",
            "position": 1,
            "job_id": "job_003",
            "file_name": "next_print.gcode"
          },
          {
            "id": "queue_item_002",
            "position": 2,
            "job_id": "job_004",
            "file_name": "another_print.gcode"
          }
        ]
      }
    }
  }' \
  --silent | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "✅ Все тесты отправлены!"
echo "======================================"
echo ""
echo "📋 Следующие шаги:"
echo "1. Проверить логи Django:"
echo "   ssh -p 2132 printfarm@kemomail3.keenetic.pro 'docker logs --tail 100 factory_v3-backend-1 | grep webhook'"
echo ""
echo "2. Проверить количество записей в БД:"
echo "   docker exec factory_v3-backend-1 python manage.py shell"
echo "   >>> from apps.simpleprint.models import PrinterWebhookEvent"
echo "   >>> PrinterWebhookEvent.objects.count()"
echo ""
echo "3. Настроить webhook в SimplePrint UI:"
echo "   URL: $WEBHOOK_URL"
echo "   Events: job.started, job.finished, job.failed, printer.state_changed, queue.changed"
echo ""
