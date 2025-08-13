#!/bin/bash
echo "🚀 PRINTFARM v7.0 - DEPLOYMENT VERIFICATION SCRIPT"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_tests=0

check_test() {
    local test_name="$1"
    local command="$2"
    local expected="$3"
    
    ((total_tests++))
    echo -n "Testing: $test_name... "
    
    result=$(eval "$command" 2>/dev/null)
    if [[ "$result" == *"$expected"* ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((success_count++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $result"
        return 1
    fi
}

echo ""
echo "🔍 CRITICAL HOTFIX VERIFICATION"
echo "==============================="

# Test 1: Backend server responding
check_test "Backend server health" \
    "curl -s http://localhost:8000/api/v1/tochka/production/ | head -c 50" \
    '"results"'

# Test 2: Products with reserve in API
check_test "Products with reserve count" \
    "curl -s http://localhost:8000/api/v1/tochka/production/ | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len([p for p in data[\"results\"] if float(p[\"reserved_stock\"]) > 0]))'" \
    "5"

# Test 3: Specific critical product
check_test "Critical product 15-43001R present" \
    "curl -s http://localhost:8000/api/v1/tochka/production/ | grep -o '15-43001R'" \
    "15-43001R"

# Test 4: Reserve amount calculation
check_test "Reserve calculation for 15-43001R" \
    "curl -s http://localhost:8000/api/v1/tochka/production/ | python3 -c 'import json,sys; data=json.load(sys.stdin); p=next(p for p in data[\"results\"] if p[\"article\"]==\"15-43001R\"); print(f\"reserve:{p[\"reserved_stock\"]},production:{p[\"production_needed\"]}\")'" \
    "reserve:800.00,production:800.00"

# Test 5: Database integrity
check_test "Database product count" \
    "cd backend && python3 manage.py shell -c 'from apps.products.models import Product; print(Product.objects.count())' | tail -1" \
    "6"

# Test 6: Critical hotfix tests
check_test "Hotfix tests passing" \
    "cd backend && python3 test_reserve_production_hotfix.py | grep -o 'ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ'" \
    "ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ"

echo ""
echo "📊 VERIFICATION SUMMARY"
echo "====================="
echo -e "Tests passed: ${GREEN}$success_count${NC}/$total_tests"

if [ $success_count -eq $total_tests ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED - DEPLOYMENT READY!${NC}"
    echo ""
    echo "✅ Critical hotfix verified"
    echo "✅ Reserve products visible in production"  
    echo "✅ API endpoints working correctly"
    echo "✅ Business logic functioning"
    echo ""
    echo "🚀 SAFE TO DEPLOY TO TEST SERVER"
    echo ""
    echo "Next steps:"
    echo "1. Deploy to test server"
    echo "2. Run this script on test server"
    echo "3. Verify UI functionality"
    echo "4. Deploy to production if all good"
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ DEPLOYMENT NOT READY${NC}"
    echo ""
    echo "Issues found - review failed tests above"
    echo "Fix issues before deploying"
    
    exit 1
fi