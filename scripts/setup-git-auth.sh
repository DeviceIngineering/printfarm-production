#!/bin/bash

# Скрипт для настройки Git аутентификации с Personal Access Token

echo "🔑 Настройка Git аутентификации"
echo "================================"

# GitHub Personal Access Token (передается через переменную окружения)
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Ошибка: не задана переменная окружения GITHUB_TOKEN"
    echo "Использование: GITHUB_TOKEN=your_token ./setup-git-auth.sh"
    exit 1
fi
REPO_URL="https://github.com/DeviceIngineering/printfarm-production.git"

# Настройка Git для использования токена
echo "Настройка Git credentials..."

# Для текущего репозитория
git config --local credential.helper store

# Создание файла с credentials
echo "https://DeviceIngineering:$GITHUB_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Альтернативный способ - через git config
git config --local user.name "DeviceEngineering"
git config --local user.email "your-email@example.com"

# Обновление remote URL для использования токена
git remote set-url origin "https://DeviceIngineering:$GITHUB_TOKEN@github.com/DeviceIngineering/printfarm-production.git"

echo "✅ Git аутентификация настроена"
echo "Теперь можно использовать git push без ввода пароля"

# Проверка подключения
echo "Тестирование подключения к GitHub..."
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Подключение к GitHub успешно"
else
    echo "❌ Ошибка подключения к GitHub"
    echo "Проверьте токен и права доступа"
fi