FROM nginx:alpine

# Установка curl для health checks
RUN apk add --no-cache curl

# Копирование nginx конфигурации
COPY docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Создание директорий для статических файлов
RUN mkdir -p /app/static /app/media

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]