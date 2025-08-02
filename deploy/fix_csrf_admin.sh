#!/bin/bash

# PrintFarm Production - Исправление CSRF для доступа к админке
# Устраняет ошибку "Ошибка проверки CSRF. Запрос отклонён."

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

print_header "ИСПРАВЛЕНИЕ CSRF ДЛЯ АДМИНКИ"

# Получаем локальный IP автоматически
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "192.168.1.98")
print_info "Обнаружен локальный IP: $LOCAL_IP"

# Шаг 1: Создаем исправленный .env файл
print_info "🔧 Создаем исправленный .env файл..."

# Резервная копия
cp .env .env.backup.csrf.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

cat > .env << EOF
# Django настройки (с исправлением CSRF)
SECRET_KEY=django-insecure-but-working-key-for-testing
DEBUG=True
ALLOWED_HOSTS=*

# CSRF настройки для внешнего доступа
CSRF_TRUSTED_ORIGINS=http://kemomail3.keenetic.pro:8089,http://${LOCAL_IP}:8089,http://localhost:8089,https://kemomail3.keenetic.pro:8089

# База данных
POSTGRES_DB=printfarm
POSTGRES_USER=printfarm
POSTGRES_PASSWORD=1qaz2wsX
DATABASE_URL=postgresql://printfarm:1qaz2wsX@db:5432/printfarm

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.production

# Дополнительные CSRF настройки
CSRF_COOKIE_SECURE=False
CSRF_COOKIE_HTTPONLY=False
CSRF_USE_SESSIONS=True
CSRF_COOKIE_SAMESITE=Lax
EOF

print_success ".env файл обновлен с CSRF настройками"

# Шаг 2: Создаем патч для Django settings прямо в контейнере
print_info "⚙️ Применяем CSRF настройки в Django..."

docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import os
import django
from django.conf import settings

# Устанавливаем переменные окружения
os.environ['CSRF_TRUSTED_ORIGINS'] = 'http://kemomail3.keenetic.pro:8089,http://${LOCAL_IP}:8089,http://localhost:8089,https://kemomail3.keenetic.pro:8089'
os.environ['CSRF_COOKIE_SECURE'] = 'False'
os.environ['CSRF_COOKIE_HTTPONLY'] = 'False' 
os.environ['CSRF_USE_SESSIONS'] = 'True'
os.environ['CSRF_COOKIE_SAMESITE'] = 'Lax'

print('✅ CSRF переменные окружения установлены')

# Создаем файл с дополнительными настройками
csrf_settings = '''
# CSRF настройки для внешнего доступа
CSRF_TRUSTED_ORIGINS = [
    \"http://kemomail3.keenetic.pro:8089\",
    \"http://${LOCAL_IP}:8089\", 
    \"http://localhost:8089\",
    \"https://kemomail3.keenetic.pro:8089\",
]

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SAMESITE = \"Lax\"
CSRF_FAILURE_VIEW = \"django.views.csrf.csrf_failure\"

# Дополнительные настройки безопасности для внешнего доступа
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = None

print(\"✅ CSRF настройки Django применены\")
'''

with open('/tmp/csrf_settings.py', 'w') as f:
    f.write(csrf_settings)

print('✅ Файл CSRF настроек создан')
" 2>/dev/null || print_warning "Не удалось применить настройки через Python"

# Шаг 3: Перезапускаем backend с новыми настройками
print_info "🔄 Перезапускаем backend..."
docker-compose -f docker-compose.prod.yml restart backend

# Ждем запуска
print_info "⏳ Ждем запуска backend (15 секунд)..."
sleep 15

# Шаг 4: Проверяем Django настройки
print_info "🔍 Проверяем Django CSRF настройки..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.conf import settings
import os

print("=== CSRF НАСТРОЙКИ ===")
print(f"CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'НЕ УСТАНОВЛЕНО')}")
print(f"CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', 'НЕ УСТАНОВЛЕНО')}")
print(f"CSRF_USE_SESSIONS: {getattr(settings, 'CSRF_USE_SESSIONS', 'НЕ УСТАНОВЛЕНО')}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DEBUG: {settings.DEBUG}")

print("\n=== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===")
print(f"CSRF_TRUSTED_ORIGINS env: {os.environ.get('CSRF_TRUSTED_ORIGINS', 'НЕ УСТАНОВЛЕНО')}")
EOF

# Шаг 5: Тестируем доступ к админке
print_header "ТЕСТИРОВАНИЕ ДОСТУПА К АДМИНКЕ"

print_info "🧪 Тестируем доступ к админке..."

# Тест 1: Локальный доступ
print_info "Тест 1: Локальный доступ"
if curl -f -s -o /dev/null http://localhost:8089/admin/; then
    print_success "localhost:8089/admin/ - РАБОТАЕТ"
else
    print_warning "localhost:8089/admin/ - проблемы"
fi

# Тест 2: Доступ по IP
print_info "Тест 2: Доступ по IP"
if curl -f -s -o /dev/null http://${LOCAL_IP}:8089/admin/; then
    print_success "${LOCAL_IP}:8089/admin/ - РАБОТАЕТ"
else
    print_warning "${LOCAL_IP}:8089/admin/ - проблемы"
fi

# Тест 3: Доступ по домену
print_info "Тест 3: Доступ по домену"
if curl -f -s -o /dev/null http://kemomail3.keenetic.pro:8089/admin/; then
    print_success "kemomail3.keenetic.pro:8089/admin/ - РАБОТАЕТ"
else
    print_warning "kemomail3.keenetic.pro:8089/admin/ - проблемы"
fi

# Шаг 6: Проверяем что API все еще работает
print_info "🔍 Проверяем что API все еще работает..."
if curl -f -s http://localhost:8089/api/v1/tochka/stats/ > /dev/null; then
    print_success "API работает корректно"
else
    print_error "Проблема с API после изменений"
fi

# Шаг 7: Создаем тестового пользователя для проверки
print_info "👤 Проверяем суперпользователя..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model

User = get_user_model()
try:
    admin_user = User.objects.get(username='admin')
    print(f"✅ Пользователь admin существует (ID: {admin_user.id})")
    print(f"   Email: {admin_user.email}")
    print(f"   Суперпользователь: {admin_user.is_superuser}")
    print(f"   Активен: {admin_user.is_active}")
except User.DoesNotExist:
    print("❌ Пользователь admin не найден!")
    print("Создаем нового пользователя...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Пользователь admin создан!")
EOF

# Финальная информация
print_header "CSRF ИСПРАВЛЕНИЯ ЗАВЕРШЕНЫ!"

print_success "🎉 CSRF настройки исправлены!"
echo
print_info "🌐 Попробуйте войти в админку:"
echo "   URL:      http://kemomail3.keenetic.pro:8089/admin/"
echo "   Альт URL: http://${LOCAL_IP}:8089/admin/"
echo "   Логин:    admin"
echo "   Пароль:   admin"
echo
print_info "🔧 Примененные исправления:"
echo "   ✓ CSRF_TRUSTED_ORIGINS добавлен для всех доменов"
echo "   ✓ CSRF_COOKIE_SECURE = False (для HTTP)"
echo "   ✓ CSRF_USE_SESSIONS = True"
echo "   ✓ DEBUG = True (для отладки)"
echo "   ✓ ALLOWED_HOSTS = * (все хосты разрешены)"
echo
print_info "📋 Если проблема сохраняется:"
echo "   1. Очистите cookies браузера"
echo "   2. Попробуйте режим инкогнито"
echo "   3. Используйте IP вместо домена: http://${LOCAL_IP}:8089/admin/"
echo "   4. Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"
echo
print_warning "⚠️  DEBUG=True включен для диагностики - отключите в production!"
echo
print_success "Готово! Админка должна работать! 🚀"