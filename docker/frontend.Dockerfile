# PrintFarm Frontend Dockerfile - v4.1.8
# Multi-stage build для оптимизации

# Stage 1: Dependencies
FROM node:18-alpine as deps
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:18-alpine as builder

ARG REACT_APP_API_URL=http://localhost:18000/api/v1
ARG REACT_APP_VERSION=4.1.8
ARG REACT_APP_ENVIRONMENT=production

ENV REACT_APP_API_URL=${REACT_APP_API_URL}
ENV REACT_APP_VERSION=${REACT_APP_VERSION}
ENV REACT_APP_ENVIRONMENT=${REACT_APP_ENVIRONMENT}

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 3: Production server
FROM node:18-alpine

# Метки
LABEL maintainer="PrintFarm Team"
LABEL version="4.1.8"

# Создаем пользователя
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Устанавливаем serve для обслуживания статики
RUN npm install -g serve

# Копируем build из builder
WORKDIR /app
COPY --from=builder --chown=nextjs:nodejs /app/build ./build
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# Создаем конфигурацию serve
RUN echo '{\n\
  "headers": [\n\
    {\n\
      "source": "**/*",\n\
      "headers": [\n\
        {\n\
          "key": "X-Frame-Options",\n\
          "value": "SAMEORIGIN"\n\
        },\n\
        {\n\
          "key": "X-Content-Type-Options",\n\
          "value": "nosniff"\n\
        },\n\
        {\n\
          "key": "X-XSS-Protection",\n\
          "value": "1; mode=block"\n\
        }\n\
      ]\n\
    }\n\
  ],\n\
  "rewrites": [\n\
    { "source": "/**", "destination": "/index.html" }\n\
  ]\n\
}' > /app/serve.json

USER nextjs

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Запуск приложения
CMD ["serve", "-s", "build", "-l", "3000", "-c", "../serve.json"]