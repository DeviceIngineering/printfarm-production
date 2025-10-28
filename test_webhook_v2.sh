#!/bin/bash
# Тестовый скрипт для проверки SimplePrint webhook endpoint v2

echo "🔍 Тестирование SimplePrint Webhook Endpoint"
echo "=============================================="
echo ""

# Правильный URL
CORRECT_URL="http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/webhook/"
WRONG_URL="http://kemomail3.keenetic.pro:18001/admin/simpleprint/printerwebhookevent/"

echo "1️⃣  Тест ПРАВИЛЬНОГО webhook endpoint"
echo "   URL: $CORRECT_URL"
echo ""

curl -X POST "$CORRECT_URL" \
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
  }' && echo ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣  Тест НЕПРАВИЛЬНОГО URL (admin page)"
echo "   URL: $WRONG_URL"
echo ""

curl -I "$WRONG_URL" 2>&1 | head -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📋 ИТОГИ:"
echo ""
echo "✅ ПРАВИЛЬНЫЙ URL для SimplePrint:"
echo "   $CORRECT_URL"
echo ""
echo "❌ НЕПРАВИЛЬНЫЙ URL (вызывает 403):"
echo "   $WRONG_URL"
echo ""
