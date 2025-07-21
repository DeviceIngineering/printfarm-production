#!/bin/bash

echo "=== PrintFarm Test Suite ==="
echo ""

# Check if we're in development environment
if [ ! -f .env.local ]; then
    echo "⚠️  Warning: .env.local not found. Creating from template..."
    cp .env.local.example .env.local 2>/dev/null || echo "No template found, please create .env.local"
fi

# Ensure we're using local development settings
cp .env.local .env

echo "1. Installing test dependencies..."
docker-compose run --rm backend pip install -r requirements.txt

echo ""
echo "2. Running database migrations for tests..."
docker-compose run --rm backend python manage.py migrate

echo ""
echo "3. Running unit tests..."
docker-compose run --rm backend python -m pytest apps/products/tests/test_production_algorithm.py -v

echo ""
echo "4. Running API tests..."  
docker-compose run --rm backend python -m pytest apps/products/tests/test_api.py -v

echo ""
echo "5. Running integration tests..."
docker-compose run --rm backend python -m pytest apps/sync/tests/test_moysklad_integration.py -v

echo ""
echo "6. Running full test suite with coverage..."
docker-compose run --rm backend python -m pytest --cov=apps --cov-report=html --cov-report=term-missing

echo ""
echo "=== Test Results Summary ==="
echo "📊 Coverage report generated in backend/htmlcov/index.html"
echo ""

# Optional: Run performance tests
read -p "Run performance tests? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "7. Running performance tests..."
    docker-compose run --rm backend python -m pytest -m slow -v
fi

echo ""
echo "✅ All tests completed!"
echo ""
echo "📝 Tips:"
echo "   - Run specific test file: docker-compose run --rm backend python -m pytest apps/products/tests/test_api.py"
echo "   - Run with verbose output: docker-compose run --rm backend python -m pytest -v"
echo "   - Run only failed tests: docker-compose run --rm backend python -m pytest --lf"
echo "   - Run tests matching pattern: docker-compose run --rm backend python -m pytest -k 'test_production'"