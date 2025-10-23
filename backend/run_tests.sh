#!/bin/bash

echo "========================================"
echo "🧪 SimplePrint Tests Suite"
echo "========================================"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для запуска тестов
run_test() {
    local test_file=$1
    local test_name=$2

    echo ""
    echo "========================================"
    echo "🔬 Запуск: $test_name"
    echo "========================================"

    pytest "$test_file" -v -s --tb=short

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $test_name: PASSED${NC}"
    else
        echo -e "${RED}❌ $test_name: FAILED${NC}"
        exit 1
    fi
}

# Проверяем что мы в правильной директории
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Ошибка: manage.py не найден. Запустите из директории backend/${NC}"
    exit 1
fi

# Устанавливаем pytest если не установлен
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest не найден. Устанавливаю...${NC}"
    pip install pytest pytest-django
fi

# Запускаем тесты по порядку
echo ""
echo -e "${YELLOW}📋 План тестирования:${NC}"
echo "1. ✅ Тест API клиента (apps/simpleprint/client.py)"
echo "2. ✅ Тест синхронизации (apps/simpleprint/services.py)"
echo "3. ✅ Тест API endpoints (apps/simpleprint/views.py)"
echo ""

# 1. Тесты клиента
run_test "apps/simpleprint/tests/test_client.py" "API Client Tests"

# 2. Тесты синхронизации
run_test "apps/simpleprint/tests/test_sync.py" "Sync Service Tests"

# 3. Тесты API
run_test "apps/simpleprint/tests/test_api.py" "API Endpoints Tests"

# Итоговый результат
echo ""
echo "========================================"
echo -e "${GREEN}✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!${NC}"
echo "========================================"
echo ""
echo "📊 Результаты:"
echo "   ✓ API Client: OK"
echo "   ✓ Sync Service: OK"
echo "   ✓ API Endpoints: OK"
echo ""
