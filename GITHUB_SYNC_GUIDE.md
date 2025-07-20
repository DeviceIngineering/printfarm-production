# 🚀 Пошаговая инструкция: Загрузка проекта PrintFarm на GitHub

## 📋 Что вам понадобится:
- Аккаунт на GitHub
- Git установлен локально (уже есть)
- SSH ключ или токен доступа

## 🔐 Шаг 1: Настройка доступа к GitHub

### Вариант A: Через Personal Access Token (рекомендуется)

1. Войдите в ваш GitHub аккаунт
2. Перейдите в Settings → Developer settings → Personal access tokens → Tokens (classic)
3. Нажмите "Generate new token (classic)"
4. Дайте токену имя: "PrintFarm Deploy"
5. Выберите права доступа:
   - ✅ repo (все подпункты)
   - ✅ workflow (если планируете CI/CD)
6. Нажмите "Generate token"
7. **ВАЖНО**: Скопируйте токен сразу! Он больше не будет показан

### Вариант B: Через SSH ключ

```bash
# Проверьте, есть ли у вас SSH ключ
ls -la ~/.ssh/

# Если нет, создайте новый
ssh-keygen -t ed25519 -C "your-email@example.com"

# Скопируйте публичный ключ
cat ~/.ssh/id_ed25519.pub

# Добавьте его в GitHub: Settings → SSH and GPG keys → New SSH key
```

## 📦 Шаг 2: Создание репозитория на GitHub

1. Войдите в GitHub
2. Нажмите "+" → "New repository"
3. Настройки:
   - Repository name: `printfarm-production`
   - Description: "Production management system for PrintFarm with MoySklad integration"
   - Private/Public: выберите по необходимости
   - **НЕ** инициализируйте с README, .gitignore или лицензией
4. Нажмите "Create repository"

## 🔄 Шаг 3: Подготовка локального репозитория

Откройте терминал в папке проекта:

```bash
cd /Users/dim11/Documents/myProjects/Factory_v2

# Проверим статус
git status

# Добавим все файлы, кроме игнорируемых
git add -A

# Создадим коммит
git commit -m "Production ready version 3.0"

# Проверим текущую ветку
git branch
```

## 🌐 Шаг 4: Подключение к GitHub

### Если используете HTTPS с токеном:
```bash
# Добавьте удаленный репозиторий
git remote add origin https://github.com/YOUR_USERNAME/printfarm-production.git

# Проверьте подключение
git remote -v
```

### Если используете SSH:
```bash
# Добавьте удаленный репозиторий
git remote add origin git@github.com:YOUR_USERNAME/printfarm-production.git

# Проверьте подключение
git remote -v
```

## 📤 Шаг 5: Первая отправка на GitHub

```bash
# Переименуем ветку в main (если нужно)
git branch -M main

# Отправим код на GitHub
git push -u origin main
```

### Если используете токен, Git запросит учетные данные:
- Username: ваш GitHub username
- Password: вставьте Personal Access Token (НЕ пароль от аккаунта!)

## 🔒 Шаг 6: Защита чувствительных данных

### Создайте файл .env.example для документации:
```bash
cp .env.production .env.example
```

Отредактируйте .env.example, заменив реальные значения на примеры:
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Database
POSTGRES_PASSWORD=change-this-password

# МойСклад
MOYSKLAD_TOKEN=your-moysklad-token-here
```

### Добавьте и закоммитьте:
```bash
git add .env.example
git commit -m "Add environment example file"
git push
```

## 📝 Шаг 7: Настройка README для GitHub

Создадим README.md для GitHub:

```bash
# Переименуем существующий README
mv README.md PROJECT_README.md

# Создадим новый README для GitHub
cat > README.md << 'EOF'
# PrintFarm Production Management System

Production management system for PrintFarm with MoySklad integration for inventory analysis and optimal production planning.

## 🚀 Features

- ✅ MoySklad synchronization
- ✅ Turnover and stock analysis
- ✅ Automatic production needs calculation
- ✅ Prioritized production list
- ✅ Excel export
- ✅ Docker containerization

## 📋 Requirements

- Docker & Docker Compose
- 2GB+ RAM
- 20GB+ disk space

## 🛠️ Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/printfarm-production.git
cd printfarm-production

# Copy environment configuration
cp .env.example .env

# Edit configuration
nano .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 📖 Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔐 Security Notes

- Change all default passwords
- Update SECRET_KEY in production
- Configure proper ALLOWED_HOSTS
- Use HTTPS in production

## 📄 License

Private repository - All rights reserved
EOF

git add README.md PROJECT_README.md
git commit -m "Update README for GitHub"
git push
```

## 🏷️ Шаг 8: Создание релиза

```bash
# Создайте тег для версии
git tag -a v3.0.0 -m "Version 3.0.0 - Production ready with updated business logic"

# Отправьте тег на GitHub
git push origin v3.0.0
```

В GitHub:
1. Перейдите в Releases → Create a new release
2. Выберите тег v3.0.0
3. Добавьте описание изменений
4. Прикрепите файлы документации если нужно
5. Опубликуйте релиз

## 🔄 Шаг 9: Настройка автоматического деплоя (опционально)

### GitHub Actions для автодеплоя:

```bash
mkdir -p .github/workflows

cat > .github/workflows/deploy.yml << 'EOF'
name: Deploy to Production

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/printfarm
          git pull origin main
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml up -d
          docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
EOF

git add .github/
git commit -m "Add GitHub Actions deploy workflow"
git push
```

## 🎯 Шаг 10: Клонирование на сервер

На вашем production сервере:

```bash
# Если используете HTTPS с токеном
git clone https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/printfarm-production.git /opt/printfarm

# Если используете SSH (нужно добавить deploy key)
git clone git@github.com:YOUR_USERNAME/printfarm-production.git /opt/printfarm

# Перейдите в директорию
cd /opt/printfarm

# Скопируйте production конфигурацию
cp .env.production .env

# Отредактируйте под ваш сервер
nano .env
```

## ✅ Проверочный список

- [ ] Создан Personal Access Token или SSH ключ
- [ ] Создан репозиторий на GitHub
- [ ] Добавлен .gitignore
- [ ] Чувствительные данные не попадают в репозиторий
- [ ] Код отправлен на GitHub
- [ ] Создан .env.example для документации
- [ ] Обновлен README.md
- [ ] Создан тег версии
- [ ] Настроен доступ для сервера

## 🆘 Решение проблем

### "Permission denied (publickey)"
```bash
# Проверьте SSH агент
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Проверьте подключение
ssh -T git@github.com
```

### "remote: Invalid username or password"
- Убедитесь, что используете токен, а не пароль
- Проверьте права доступа токена

### Большие файлы
```bash
# Если есть файлы больше 100MB
git lfs track "*.sqlite3"
git lfs track "media/**"
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

## 📌 Дальнейшие шаги

1. **Настройте GitHub Secrets** для CI/CD:
   - Settings → Secrets → Actions
   - Добавьте: HOST, USERNAME, SSH_KEY

2. **Включите branch protection**:
   - Settings → Branches
   - Защитите main ветку

3. **Настройте webhooks** для уведомлений

4. **Документируйте изменения** в CHANGELOG.md

---

Готово! Теперь ваш проект синхронизирован с GitHub и готов к развертыванию на любом сервере.