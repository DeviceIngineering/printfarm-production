# Multi-stage Dockerfile для React приложения

# Stage 1: Development
FROM node:18-alpine as development

WORKDIR /app

# Копирование package.json и package-lock.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY frontend/ .

# Команда для development
CMD ["npm", "start"]

# Stage 2: Build
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json и package-lock.json
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci --only=production

# Копирование исходного кода
COPY frontend/ .

# Сборка production версии
RUN npm run build

# Stage 3: Production
FROM nginx:alpine as production

# Установка curl для health checks
RUN apk add --no-cache curl

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Копирование nginx конфигурации
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]