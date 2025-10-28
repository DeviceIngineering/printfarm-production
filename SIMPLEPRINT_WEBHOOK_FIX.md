# 🔧 Исправление проблемы "Некорректный URL" в SimplePrint Webhooks

## ❌ Проблема
При попытке добавить webhook в SimplePrint получаете ошибку:
```
"Некорректный URL" или "Invalid URL"
```

---

## ✅ Решения (по приоритету)

### 🥇 Решение 1: Используйте HTTPS с Cloudflare Tunnel (РЕКОМЕНДУЕТСЯ)

SimplePrint **требует HTTPS** для webhooks по соображениям безопасности.

#### Шаг 1: Установите Cloudflare Tunnel на сервере

```bash
# SSH на сервер
ssh -p 2132 printfarm@kemomail3.keenetic.pro

# Скачать cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# Сделать исполняемым
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Проверить установку
cloudflared --version
```

#### Шаг 2: Создайте туннель

```bash
# Запустить туннель (временно, для теста)
cloudflared tunnel --url http://localhost:18001

# Вывод будет примерно такой:
# 2025-10-28T14:32:10Z INF Your quick tunnel is: https://abc-123-xyz.trycloudflare.com
```

#### Шаг 3: Используйте HTTPS URL в SimplePrint

В SimplePrint webhook URL используйте:
```
https://abc-123-xyz.trycloudflare.com/api/v1/simpleprint/webhook/
```

**✅ Преимущества:**
- Бесплатно
- Автоматический HTTPS
- Работает сразу
- Не требует настройки DNS

**⚠️ Минус:**
- Временный URL (меняется при перезапуске)
- Для постоянного туннеля нужна регистрация в Cloudflare

#### Шаг 4: Создайте постоянный туннель (опционально)

```bash
# Авторизация в Cloudflare
cloudflared tunnel login

# Создать туннель с именем
cloudflared tunnel create printfarm-webhook

# Создать конфиг
cat > ~/.cloudflared/config.yml << EOF
url: http://localhost:18001
tunnel: <TUNNEL-ID>
credentials-file: /home/printfarm/.cloudflared/<TUNNEL-ID>.json
EOF

# Запустить как сервис
cloudflared tunnel route dns printfarm-webhook webhook.yourdomain.com
cloudflared tunnel run printfarm-webhook
```

Теперь URL будет постоянным:
```
https://webhook.yourdomain.com/api/v1/simpleprint/webhook/
```

---

### 🥈 Решение 2: Используйте ngrok (быстрый тест)

Если нужно быстро протестировать:

```bash
# Установка ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Запуск туннеля
ngrok http 18001

# Вывод покажет HTTPS URL:
# Forwarding: https://1234-5678-9abc.ngrok-free.app -> http://localhost:18001
```

**URL для SimplePrint:**
```
https://1234-5678-9abc.ngrok-free.app/api/v1/simpleprint/webhook/
```

**⚠️ Минусы:**
- Временный URL (8 часов на бесплатном плане)
- Требует регистрации для постоянного URL
- Лимиты на запросы

---

### 🥉 Решение 3: Настройте SSL на Nginx (для продакшена)

Если у вас есть домен, настройте Let's Encrypt:

#### Шаг 1: Установите Certbot

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

#### Шаг 2: Получите сертификат

```bash
# Если у вас есть домен printfarm.yourdomain.com
sudo certbot --nginx -d printfarm.yourdomain.com
```

#### Шаг 3: Обновите Nginx конфигурацию

```nginx
server {
    listen 443 ssl http2;
    server_name printfarm.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/printfarm.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/printfarm.yourdomain.com/privkey.pem;

    location /api/v1/simpleprint/webhook/ {
        proxy_pass http://factory_v3_backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**URL для SimplePrint:**
```
https://printfarm.yourdomain.com/api/v1/simpleprint/webhook/
```

---

## 🧪 Проверка доступности URL

Перед добавлением в SimplePrint, проверьте доступность:

### Тест 1: Проверка снаружи

```bash
# С локального компьютера (не с сервера!)
curl -X POST https://your-tunnel-url/api/v1/simpleprint/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-SP-Token: test-secret" \
  -d '{
    "webhook_id": 0,
    "event": "test",
    "timestamp": 1234567890,
    "data": {"test": true}
  }'

# Ожидаемый ответ:
# {"status":"received","event_type":"unknown","message":"Webhook processed successfully"}
```

### Тест 2: Проверка в браузере

Откройте в браузере:
```
https://your-tunnel-url/api/v1/simpleprint/webhook/
```

Должны увидеть:
```json
{"detail": "Method \"GET\" not allowed."}
```

Это **НОРМАЛЬНО** - endpoint принимает только POST запросы!

---

## 📝 Настройка в SimplePrint UI

После того, как URL доступен:

### Шаг 1: Откройте SimplePrint
1. https://simplyprint.io → Login
2. Settings → Webhooks
3. Click "Create webhook"

### Шаг 2: Заполните поля

```
Name: PrintFarm Webhook
URL: https://your-tunnel-url/api/v1/simpleprint/webhook/
Secret (optional): leave empty for now
```

### Шаг 3: Выберите события

**Отметьте все нужные события:**
- ☑️ Print Job Started
- ☑️ Print Job Finished
- ☑️ Print Job Paused
- ☑️ Print Job Resumed
- ☑️ Print Job Failed
- ☑️ Queue Item Added
- ☑️ Queue Item Deleted
- ☑️ (другие по необходимости)

### Шаг 4: Сохраните и протестируйте

1. Нажмите **"Save"**
2. Нажмите **"Send test event"**
3. Проверьте логи на сервере:

```bash
# Проверка логов Django
docker logs -f factory_v3_backend | grep webhook

# Ожидаемый вывод:
# Received webhook: {'webhook_id': 123, 'event': 'test', ...}
# ✅ Webhook processed successfully: test
```

---

## 🔍 Troubleshooting

### Проблема: "URL недоступен"

**Проверьте:**
1. Cloudflare tunnel запущен:
   ```bash
   ps aux | grep cloudflared
   ```

2. Backend контейнер работает:
   ```bash
   docker ps | grep factory_v3_backend
   ```

3. Firewall не блокирует:
   ```bash
   sudo ufw status
   # Порт 18001 должен быть открыт
   ```

### Проблема: "Connection timeout"

**Проверьте nginx:**
```bash
docker logs factory_v3_nginx | grep webhook

# Проверьте конфигурацию
docker exec factory_v3_nginx cat /etc/nginx/conf.d/default.conf | grep simpleprint
```

### Проблема: "403 Forbidden"

**Проверьте CORS и permissions:**
```python
# backend/apps/simpleprint/views.py
class SimplePrintWebhookView(APIView):
    permission_classes = [AllowAny]  # Должно быть AllowAny!
```

### Проблема: SimplePrint не принимает URL даже с HTTPS

**Возможные причины:**
1. **Неподдерживаемый порт** - попробуйте без порта (443 для HTTPS)
2. **Подпуть слишком длинный** - упростите до `/webhook`
3. **Домен в blacklist** - используйте другой tunnel

**Альтернативный короткий URL:**
```
https://your-tunnel.ngrok.io/webhook
```

Для этого добавьте в `urls.py`:
```python
# backend/config/urls.py
urlpatterns = [
    # Short webhook URL для SimplePrint
    path('webhook/', SimplePrintWebhookView.as_view(), name='simpleprint-webhook-short'),

    # ... existing patterns
]
```

---

## 📊 Итоговая проверка

После настройки, проверьте:

- [ ] URL доступен извне (curl тест успешен)
- [ ] Webhook сохранен в SimplePrint
- [ ] Тестовое событие получено в логах
- [ ] Событие сохранено в БД:
  ```bash
  docker exec factory_v3_backend python manage.py shell
  >>> from apps.simpleprint.models import SimplePrintWebhookEvent
  >>> SimplePrintWebhookEvent.objects.count()
  # Должно быть > 0
  ```

---

## 🎯 Рекомендованная конфигурация

**Для разработки/тестирования:**
- ✅ Cloudflare Tunnel (временный)
- ✅ ngrok (временный)

**Для продакшена:**
- ✅ Cloudflare Tunnel (постоянный с доменом)
- ✅ Let's Encrypt SSL + Nginx
- ✅ Cloudflare DNS + Proxy

---

## 📞 Дополнительная помощь

Если проблема не решается:

1. **Проверьте SimplePrint документацию:**
   - https://help.simplyprint.io/en/article/all-about-the-webhooks-feature-1g12e5c/

2. **Обратитесь в поддержку SimplePrint:**
   - Email: support@simplyprint.io
   - Укажите: "Cannot save webhook URL, getting 'Invalid URL' error"
   - Приложите скриншот ошибки

3. **Проверьте логи SimplePrint:**
   - В SimplePrint UI может быть раздел "Webhook Logs"
   - Там может быть детальная ошибка

---

**Дата создания:** 2025-10-28
**Версия:** 1.0
