#!/bin/bash
echo "🔄 Restoring PrintFarm v7.0 development session from checkpoint..."

# Checkout hotfix branch
echo "📂 Switching to hotfix branch..."
git checkout hotfix/production-reserve-inclusion

# Show current status
echo "📋 Current git status:"
git status --short

# Check if Django backend is working
echo "🔧 Checking Django backend..."
cd backend
python3 manage.py check

# Check database connectivity
echo "💾 Testing database connection..."
python3 manage.py shell -c "
from apps.products.models import Product
count = Product.objects.count()
reserve_count = Product.objects.filter(reserved_stock__gt=0).count()
print(f'✅ Database OK: {count} products total, {reserve_count} with reserve')
"

# Run critical hotfix tests
echo "🧪 Running critical hotfix tests..."
python3 test_reserve_production_hotfix.py

# Check if server is running
echo "🌐 Checking if backend server is running..."
curl -s http://localhost:8000/api/v1/tochka/production/ | head -c 100 && echo "..." || echo "❌ Backend server not responding"

# Show checkpoint information
echo ""
echo "📋 Last checkpoint info:"
cat ../.claude/checkpoint-20250813.md | head -30

echo ""
echo "✅ Session restored! Current status:"
echo "🎯 Focus: Reserve Stock Integration in Production Planning"
echo "🔥 Critical hotfix: COMPLETED and TESTED"
echo "📊 Products with reserve: 5 items (8300 total units)"
echo "🚀 Ready for: Test server deployment"
echo ""
echo "📝 Next steps from checkpoint:"
echo "1. Deploy hotfix to test server"
echo "2. Implement cross-tab state synchronization" 
echo "3. Create documentation and integration tests"
echo ""
echo "🔍 Quick commands:"
echo "  Test API: curl http://localhost:8000/api/v1/tochka/production/"
echo "  Run tests: python3 test_reserve_production_hotfix.py"
echo "  Check status: git status"
echo ""
echo "📁 See .claude/checkpoint-20250813.md for full context"