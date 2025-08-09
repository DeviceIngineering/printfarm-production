# Простой Dockerfile для быстрого развертывания

FROM nginx:alpine

# Установка curl для health checks
RUN apk add --no-cache curl

# Создание простой HTML страницы
RUN mkdir -p /usr/share/nginx/html
COPY frontend/public/index.html /usr/share/nginx/html/

# Создание простого React build
RUN mkdir -p /usr/share/nginx/html/static/js /usr/share/nginx/html/static/css

# Простая заглушка для React приложения
RUN echo 'window.React = "PrintFarm Frontend Ready";' > /usr/share/nginx/html/static/js/main.js
RUN echo 'body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #1E1E1E 0%, #06EAFC 100%); color: white; min-height: 100vh; }' > /usr/share/nginx/html/static/css/main.css

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost || exit 1

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"]