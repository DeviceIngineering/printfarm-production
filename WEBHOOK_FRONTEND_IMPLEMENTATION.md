# 🎨 Инструкция по добавлению вкладки Webhook Testing в Planning V2

## ✅ Что уже сделано (Backend + Redux):

1. ✅ **Backend API endpoints** созданы и работают:
   - `GET /api/v1/simpleprint/webhook/events/` - список событий
   - `GET /api/v1/simpleprint/webhook/stats/` - статистика
   - `POST /api/v1/simpleprint/webhook/test-trigger/` - тест webhook
   - `DELETE /api/v1/simpleprint/webhook/events/clear/` - очистка

2. ✅ **Redux slice** создан (`frontend/src/store/webhookSlice.ts`):
   - Thunks: `fetchWebhookEvents`, `fetchWebhookStats`, `triggerTestWebhook`, `clearOldWebhookEvents`
   - Selectors: `selectWebhookEvents`, `selectWebhookStats`, `selectWebhookLoading`, `selectWebhookError`

3. ✅ **Store обновлен** (`frontend/src/store/index.ts`):
   - Добавлен `webhook: webhookReducer`

---

## 📋 Что нужно сделать (Frontend):

### Шаг 1: Создать компонент WebhookTestingTab

**Файл**: `frontend/src/pages/PlanningV2Page/components/WebhookTestingTab/WebhookTestingTab.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Card, Statistic, Row, Col, Table, Space, Tag, message, Select } from 'antd';
import { SyncOutlined, RocketOutlined, DeleteOutlined } from '@ant-design/icons';
import {
  fetchWebhookEvents,
  fetchWebhookStats,
  triggerTestWebhook,
  clearOldWebhookEvents,
  selectWebhookEvents,
  selectWebhookStats,
  selectWebhookLoading,
} from '../../../../store/webhookSlice';
import type { AppDispatch } from '../../../../store';
import type { WebhookEvent } from '../../../../store/webhookSlice';
import './WebhookTestingTab.css';

const { Option } = Select;

export const WebhookTestingTab: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const events = useSelector(selectWebhookEvents);
  const stats = useSelector(selectWebhookStats);
  const loading = useSelector(selectWebhookLoading);

  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh каждые 5 секунд
  useEffect(() => {
    if (autoRefresh) {
      dispatch(fetchWebhookStats());
      dispatch(fetchWebhookEvents({ limit: 20 }));

      const interval = setInterval(() => {
        dispatch(fetchWebhookStats());
        dispatch(fetchWebhookEvents({ limit: 20 }));
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, dispatch]);

  // Начальная загрузка
  useEffect(() => {
    dispatch(fetchWebhookStats());
    dispatch(fetchWebhookEvents({ limit: 20 }));
  }, [dispatch]);

  const handleRefresh = () => {
    dispatch(fetchWebhookStats());
    dispatch(fetchWebhookEvents({ limit: 20 }));
    message.success('Данные обновлены');
  };

  const handleTriggerTest = async (eventType: string) => {
    try {
      await dispatch(triggerTestWebhook(eventType)).unwrap();
      message.success(`Тестовый webhook ${eventType} отправлен`);
      // Обновляем список после отправки
      setTimeout(() => {
        dispatch(fetchWebhookStats());
        dispatch(fetchWebhookEvents({ limit: 20 }));
      }, 500);
    } catch (error) {
      message.error('Ошибка отправки тестового webhook');
    }
  };

  const handleClearOld = async () => {
    try {
      await dispatch(clearOldWebhookEvents(7)).unwrap();
      message.success('Старые события удалены');
      dispatch(fetchWebhookStats());
      dispatch(fetchWebhookEvents({ limit: 20 }));
    } catch (error) {
      message.error('Ошибка удаления событий');
    }
  };

  // Колонки таблицы
  const columns = [
    {
      title: 'Время',
      dataIndex: 'received_at',
      key: 'received_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('ru-RU'),
    },
    {
      title: 'Событие',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 180,
      render: (text: string, record: WebhookEvent) => (
        <Tag color={getEventColor(text)}>{record.event_type_display || text}</Tag>
      ),
    },
    {
      title: 'Printer ID',
      dataIndex: 'printer_id',
      key: 'printer_id',
      width: 150,
      render: (text: string | null) => text || '—',
    },
    {
      title: 'Job ID',
      dataIndex: 'job_id',
      key: 'job_id',
      width: 200,
      render: (text: string | null) => text || '—',
    },
    {
      title: 'Статус',
      dataIndex: 'processed',
      key: 'processed',
      width: 100,
      render: (processed: boolean, record: WebhookEvent) => (
        processed && !record.processing_error ? (
          <Tag color="green">✅ OK</Tag>
        ) : record.processing_error ? (
          <Tag color="red">⚠️ Error</Tag>
        ) : (
          <Tag color="blue">⏳ Pending</Tag>
        )
      ),
    },
  ];

  // Цвет для типа события
  const getEventColor = (eventType: string): string => {
    if (eventType.includes('started')) return 'blue';
    if (eventType.includes('completed')) return 'green';
    if (eventType.includes('failed')) return 'red';
    if (eventType.includes('paused')) return 'orange';
    if (eventType.includes('queue')) return 'purple';
    if (eventType.includes('printer')) return 'cyan';
    return 'default';
  };

  return (
    <div className="webhook-testing-tab">
      {/* Статистика */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Всего событий" value={stats?.total || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Обработано"
              value={stats?.processed || 0}
              suffix={stats?.total ? `/ ${stats.total}` : ''}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="За последний час"
              value={stats?.last_hour || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ошибок"
              value={stats?.errors || 0}
              valueStyle={{ color: stats?.errors ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* События по типам */}
      {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
        <Card title="События по типам" size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            {Object.entries(stats.by_type).map(([type, count]) => (
              <Tag key={type} color={getEventColor(type)}>
                {type}: {count}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      {/* Кнопки управления */}
      <Space style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<SyncOutlined spin={loading} />}
          onClick={handleRefresh}
          loading={loading}
        >
          Обновить
        </Button>

        <Select
          style={{ width: 200 }}
          placeholder="Отправить тест"
          onChange={handleTriggerTest}
          value={undefined}
        >
          <Option value="job.started">job.started</Option>
          <Option value="job.finished">job.finished</Option>
          <Option value="job.failed">job.failed</Option>
          <Option value="printer.state_changed">printer.state_changed</Option>
          <Option value="queue.changed">queue.changed</Option>
        </Select>

        <Button
          danger
          icon={<DeleteOutlined />}
          onClick={handleClearOld}
          disabled={!stats?.total}
        >
          Очистить старые (> 7 дней)
        </Button>

        <Tag color={autoRefresh ? 'green' : 'default'}>
          {autoRefresh ? '🟢 LIVE (обновление каждые 5 сек)' : '⚪ Остановлено'}
        </Tag>
        <Button size="small" onClick={() => setAutoRefresh(!autoRefresh)}>
          {autoRefresh ? 'Остановить' : 'Запустить'}
        </Button>
      </Space>

      {/* Таблица событий */}
      <Table
        columns={columns}
        dataSource={events}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: ['10', '20', '50'] }}
        scroll={{ x: 900, y: 400 }}
        size="small"
        bordered
      />
    </div>
  );
};
```

---

### Шаг 2: Создать CSS (опционально)

**Файл**: `frontend/src/pages/PlanningV2Page/components/WebhookTestingTab/WebhookTestingTab.css`

```css
.webhook-testing-tab {
  padding: 0;
}

.webhook-testing-tab .ant-statistic-title {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.webhook-testing-tab .ant-statistic-content {
  font-size: 20px;
  font-weight: 600;
}
```

---

### Шаг 3: Добавить в Header.tsx

**Файл**: `frontend/src/pages/PlanningV2Page/components/Header/Header.tsx`

**3.1. Добавить импорт вверху файла:**

```typescript
import { WebhookTestingTab } from '../WebhookTestingTab/WebhookTestingTab';
```

**3.2. Добавить 4-ю вкладку после key="3" (строка ~588):**

```typescript
            </TabPane>

            {/* Вкладка 4: Webhook Testing */}
            <TabPane tab="🔗 Webhook Testing" key="4">
              <WebhookTestingTab />
            </TabPane>

          </Tabs>
```

---

### Шаг 4: Собрать и развернуть Frontend

```bash
# В директории frontend/
npm run build

# Создать архив
cd /Users/dim11/Documents/myProjects/Factory_v3
tar -czf /tmp/frontend-build.tar.gz -C frontend/build .

# Загрузить на сервер
scp -P 2132 /tmp/frontend-build.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/

# Развернуть (SSH на сервер)
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
docker cp /tmp/frontend-build.tar.gz factory_v3-nginx-1:/tmp/ &&
docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-build.tar.gz' &&
docker restart factory_v3-nginx-1
"

# Очистить временный файл
rm /tmp/frontend-build.tar.gz
```

---

## 🧪 Тестирование

После развертывания:

1. Открыть http://kemomail3.keenetic.pro:13000/planning-v2
2. Нажать кнопку "Отладка API" (иконка Bug)
3. Перейти на вкладку "🔗 Webhook Testing"
4. Проверить:
   - ✅ Статистика загружается
   - ✅ Таблица событий отображается
   - ✅ Auto-refresh работает (данные обновляются каждые 5 сек)
   - ✅ Кнопка "Обновить" работает
   - ✅ Dropdown "Отправить тест" работает
   - ✅ Кнопка "Очистить старые" работает

---

## 📊 Что будет работать:

### Статистика (обновляется каждые 5 сек):
- Всего событий: 8
- Обработано: 8/8
- За последний час: 8
- Ошибок: 0

### События по типам:
- job_started: 2
- job_completed: 1
- job_failed: 1
- printer_state_changed: 1
- queue_changed: 1

### Таблица последних 20 событий:
| Время | Событие | Printer ID | Job ID | Статус |
|-------|---------|------------|--------|--------|
| 28.10.2025 11:28:17 | queue_changed | — | — | ✅ OK |
| 28.10.2025 11:28:11 | printer_state_changed | — | — | ✅ OK |
| ... | ... | ... | ... | ... |

### Функции:
- **Обновить** - ручное обновление данных
- **Отправить тест** - отправка тестового webhook (выбор типа)
- **Очистить старые** - удаление событий старше 7 дней
- **LIVE** - автоматическое обновление каждые 5 секунд

---

## 🎯 Итоговый чеклист:

- [x] Backend API endpoints созданы и работают
- [x] Redux slice создан и подключен к store
- [ ] Компонент WebhookTestingTab создан
- [ ] Компонент добавлен в Header.tsx
- [ ] Frontend собран и развернут
- [ ] Тестирование в браузере

---

**Статус**: Backend готов (100%), Frontend требует финальной сборки и развертывания.

**Время на завершение**: ~30-60 минут (создание компонента + сборка + деплой)
