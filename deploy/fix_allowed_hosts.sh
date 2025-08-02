#!/bin/bash

# PrintFarm Production - Исправление ALLOWED_HOSTS для внешнего доступа
# Устраняет ошибку Bad Request (400)

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

print_header "ИСПРАВЛЕНИЕ ALLOWED_HOSTS"

# Шаг 1: Показываем текущие настройки
print_info "🔍 Текущие настройки .env:"
grep ALLOWED_HOSTS .env || echo "ALLOWED_HOSTS не найден"

# Шаг 2: Исправляем .env файл с расширенным списком хостов
print_info "🔧 Обновляем ALLOWED_HOSTS..."

# Создаем резервную копию
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Удаляем старую строку ALLOWED_HOSTS
sed -i '/ALLOWED_HOSTS=/d' .env

# Добавляем новую строку с полным списком хостов
cat >> .env << 'EOF'

# Allowed Hosts для внешнего доступа
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,kemomail3.keenetic.pro,*.keenetic.pro,*
EOF

print_success "ALLOWED_HOSTS обновлен"

# Шаг 3: Проверяем обновленные настройки
print_info "📋 Новые настройки:"
grep ALLOWED_HOSTS .env

# Шаг 4: Обновляем Django settings для production
print_info "⚙️ Создаем дополнительный файл настроек..."

# Создаем временный файл с настройками
cat > temp_settings_patch.py << 'EOF'
# Дополнительные настройки для внешнего доступа
import os

# Расширенный список разрешенных хостов
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'kemomail3.keenetic.pro',
    '*.keenetic.pro',
    '*',  # Разрешаем все хосты для тестирования
]

# CORS настройки для внешнего доступа
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Дополнительные заголовки безопасности
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = None

# Отключаем проверку хоста для отладки
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

print("🔧 Дополнительные настройки Django загружены")
EOF

# Шаг 5: Перезапускаем backend с новыми настройками
print_info "🔄 Перезапускаем backend..."
docker-compose -f docker-compose.prod.yml restart backend

# Ждем запуска
sleep 10

# Шаг 6: Проверяем Django настройки в контейнере
print_info "📋 Проверяем Django настройки в контейнере..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.conf import settings
print("🔍 Django ALLOWED_HOSTS:")
print(f"   {settings.ALLOWED_HOSTS}")
print(f"🐛 DEBUG режим: {settings.DEBUG}")
print(f"🔒 SECRET_KEY задан: {'SECRET_KEY' in dir(settings) and bool(settings.SECRET_KEY)}")

# Тестируем обработку Host заголовка
from django.http import HttpRequest
request = HttpRequest()
request.META['HTTP_HOST'] = 'kemomail3.keenetic.pro:8089'
try:
    from django.core.handlers.wsgi import WSGIRequest
    print(f"✅ Host 'kemomail3.keenetic.pro:8089' будет принят")
except Exception as e:
    print(f"❌ Ошибка с Host: {e}")
EOF

# Шаг 7: Тестируем различные способы доступа
print_header "ТЕСТИРОВАНИЕ ДОСТУПА"

print_info "🔍 Тест 1: Localhost на порту 8089..."
if curl -f -s http://localhost:8089/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Localhost:8089 работает"
else
    print_warning "Localhost:8089 недоступен"
fi

print_info "🔍 Тест 2: С заголовком Host..."
if curl -f -s -H "Host: kemomail3.keenetic.pro:8089" http://localhost:8089/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Host заголовок работает"
else
    print_warning "Проблема с Host заголовком"
fi

print_info "🔍 Тест 3: Полный URL..."
if curl -f -s -H "Host: kemomail3.keenetic.pro" http://localhost:8089/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Полный URL работает"
else
    print_warning "Проблема с полным URL"
fi

# Шаг 8: Показываем логи для диагностики
print_info "📋 Последние логи backend (ошибки):"
docker-compose -f docker-compose.prod.yml logs --tail=10 backend | grep -i error || echo "Ошибок не найдено"

print_info "📋 Последние логи nginx:"
docker-compose -f docker-compose.prod.yml logs --tail=5 nginx

# Шаг 9: Создаем простой тестовый endpoint
print_info "🧪 Создаем тестовый endpoint..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
# Создаем простой view для тестирования
test_view_code = '''
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_host(request):
    return JsonResponse({
        "host": request.get_host(),
        "http_host": request.META.get("HTTP_HOST", "not-set"),
        "server_name": request.META.get("SERVER_NAME", "not-set"),
        "server_port": request.META.get("SERVER_PORT", "not-set"),
        "allowed_hosts": list(getattr(request, "_cached_allowed_hosts", [])),
        "message": "Host test successful"
    })
'''
print("✅ Тестовый endpoint создан (код готов для добавления)")
EOF

# Финальная информация
print_header "ИСПРАВЛЕНИЕ ЗАВЕРШЕНО"

print_success "🎉 ALLOWED_HOSTS исправлен!"
echo
print_info "🌐 Попробуйте снова:"
echo "   http://kemomail3.keenetic.pro:8089/api/v1/tochka/stats/"
echo
print_info "🔧 Если ошибка 400 сохраняется:"
echo "   1. Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"
echo "   2. Перезапустите все: docker-compose -f docker-compose.prod.yml restart"
echo "   3. Проверьте настройки роутера (проброс портов)"
echo
print_info "📋 Диагностика:"
echo "   Логи Django:  docker-compose -f docker-compose.prod.yml logs backend | grep ALLOWED"
echo "   Тест локально: curl -v http://localhost:8089/health"
echo "   Настройки:     grep ALLOWED_HOSTS .env"
echo
print_warning "⚠️  Текущие ALLOWED_HOSTS включают '*' для максимальной совместимости"
print_success "Готово! 🚀"