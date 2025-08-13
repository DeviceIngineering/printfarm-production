#!/bin/bash

# Скрипт проверки TypeScript ошибок перед деплоем
# Предотвращает выкатывание кода с блокирующими ошибками типизации

set -e

echo "🔍 Checking TypeScript compilation errors..."

cd "$(dirname "$0")/../frontend"

# Устанавливаем зависимости если нужно
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Проверка TypeScript компиляции
echo "⚡ Running TypeScript compiler check..."
npx tsc --noEmit --project tsconfig.json

if [ $? -eq 0 ]; then
    echo "✅ TypeScript compilation: PASSED"
else
    echo "❌ TypeScript compilation: FAILED"
    echo ""
    echo "🚨 CRITICAL: TypeScript compilation errors detected!"
    echo "These errors will block the application from running in production."
    echo ""
    echo "Common fixes:"
    echo "1. Add proper type declarations for external libraries"
    echo "2. Fix Promise/async return type mismatches" 
    echo "3. Add proper error handling with type guards"
    echo "4. Check interface implementations"
    echo ""
    exit 1
fi

# Проверка ESLint (только ошибки, не предупреждения)
echo "🔍 Running ESLint error check..."
npx eslint src --ext .ts,.tsx --max-warnings 50 --format compact

if [ $? -eq 0 ]; then
    echo "✅ ESLint check: PASSED"
else
    echo "⚠️  ESLint found issues (check output above)"
fi

# Проверка тестов аналитики
echo "🧪 Running analytics TypeScript tests..."
npm test -- --testPathPattern=analytics.test.ts --passWithNoTests

if [ $? -eq 0 ]; then
    echo "✅ Analytics TypeScript tests: PASSED"
else
    echo "❌ Analytics TypeScript tests: FAILED"
    exit 1
fi

echo ""
echo "🎉 All TypeScript checks passed!"
echo "✅ Safe to deploy to production"