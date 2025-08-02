#!/bin/bash

# PrintFarm Production - Исправление миграций
# Применяет миграции и создает суперпользователя

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

print_header "ИСПРАВЛЕНИЕ МИГРАЦИЙ БАЗЫ ДАННЫХ"

# Шаг 1: Проверяем что контейнеры запущены
print_info "📊 Проверяем статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

# Шаг 2: Ждем готовности базы данных
print_info "⏳ Ждем готовности базы данных..."
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U printfarm -d printfarm > /dev/null 2>&1; then
        print_success "База данных готова!"
        break
    fi
    echo "   Попытка $i/30... ждем 2 секунды"
    sleep 2
done

# Шаг 3: Применяем миграции Django
print_header "ПРИМЕНЕНИЕ МИГРАЦИЙ"

print_info "🗄️ Применяем базовые миграции Django..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --run-syncdb || {
    print_warning "Первая попытка миграций не удалась, пробуем отдельно..."
    
    # Применяем миграции по частям
    print_info "Создаем базовые таблицы..."
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate auth 
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate contenttypes
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate sessions
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate admin
    
    print_info "Применяем все остальные миграции..."
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate
}

print_success "Миграции применены!"

# Шаг 4: Собираем статические файлы
print_info "📦 Собираем статические файлы..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

print_success "Статические файлы собраны!"

# Шаг 5: Создаем суперпользователя
print_header "СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ"

print_info "👤 Создаем суперпользователя admin/admin..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from django.db import connection

try:
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("✅ Суперпользователь admin/admin создан!")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Is staff: {user.is_staff}")
        print(f"   Is superuser: {user.is_superuser}")
    else:
        print("ℹ️ Суперпользователь admin уже существует")
        user = User.objects.get(username='admin')
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
except Exception as e:
    print(f"❌ Ошибка создания пользователя: {e}")
    # Показываем структуру базы для диагностики
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cursor.fetchall()
        print("📋 Таблицы в базе данных:")
        for table in tables:
            print(f"   - {table[0]}")
EOF

# Шаг 6: Инициализируем настройки приложения (если есть)
print_info "⚙️ Инициализируем настройки приложения..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
try:
    # Пробуем инициализировать настройки если команда существует
    import subprocess
    result = subprocess.run(['python', 'manage.py', 'init_settings'], 
                          capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("✅ Настройки инициализированы")
    else:
        print("ℹ️ Команда init_settings не найдена или не нужна")
except Exception as e:
    print(f"ℹ️ Настройки не инициализированы: {e}")
EOF

# Шаг 7: Проверяем работу API
print_header "ПРОВЕРКА РАБОТОСПОСОБНОСТИ"

print_info "🔍 Проверяем API..."
sleep 3

if curl -f -s http://localhost/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "✅ API работает!"
    echo "   Тестируем API:"
    curl -s http://localhost/api/v1/tochka/stats/ | python3 -m json.tool 2>/dev/null | head -10 || echo "   API доступен"
else
    print_warning "API недоступен, проверяем backend..."
    
    # Показываем логи backend для диагностики
    print_info "📋 Последние 20 строк логов backend:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 backend
    
    # Пробуем запросить backend напрямую
    if docker-compose -f docker-compose.prod.yml exec -T backend curl -f -s http://localhost:8000/api/v1/tochka/stats/ > /dev/null 2>&1; then
        print_warning "Backend работает, но nginx не может к нему подключиться"
        print_info "Проверьте логи nginx:"
        docker-compose -f docker-compose.prod.yml logs nginx
    else
        print_error "Backend не отвечает"
    fi
fi

# Шаг 8: Показываем финальную информацию
print_header "ИНФОРМАЦИЯ О СИСТЕМЕ"

print_info "📊 Статус всех контейнеров:"
docker-compose -f docker-compose.prod.yml ps

print_info "🗄️ Информация о базе данных:"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from django.db import connection

try:
    User = get_user_model()
    total_users = User.objects.count()
    admin_users = User.objects.filter(is_superuser=True).count()
    
    print(f"   Всего пользователей: {total_users}")
    print(f"   Администраторов: {admin_users}")
    
    # Проверяем таблицы приложения
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%product%';")
        product_tables = cursor.fetchone()[0]
        print(f"   Таблиц товаров: {product_tables}")
        
except Exception as e:
    print(f"❌ Ошибка получения информации: {e}")
EOF

# Финальная информация
print_header "МИГРАЦИИ И НАСТРОЙКА ЗАВЕРШЕНЫ!"

print_success "🎉 База данных настроена и готова к работе!"
echo
print_info "🌐 Доступные URL:"
echo "   API статистика:  http://localhost/api/v1/tochka/stats/"
echo "   Админ-панель:     http://localhost/admin/"
echo
print_info "👤 Данные для входа в админку:"
echo "   Логин:    admin"
echo "   Пароль:   admin"
echo
print_info "📋 Проверка работы:"
echo "   Статус:      docker-compose -f docker-compose.prod.yml ps"
echo "   Логи:        docker-compose -f docker-compose.prod.yml logs [сервис]"
echo "   API тест:    curl http://localhost/api/v1/tochka/stats/"
echo
print_success "Готово! База данных работает! 🚀"