import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Card, Statistic, Row, Col, Table, Space, Tag, message, Select } from 'antd';
import { SyncOutlined, DeleteOutlined } from '@ant-design/icons';
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
    // AI события (v4.4.2)
    if (eventType === 'ai_failure_detected') return 'red';
    if (eventType === 'ai_false_positive') return 'gold';
    // Филамент события (v4.4.2)
    if (eventType === 'filament_deleted') return 'orange';
    // Очередь события (v4.4.2)
    if (eventType === 'queue_item_deleted') return 'volcano';
    // Существующие правила
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
                {`${type}: ${count}`}
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
          Очистить старые
        </Button>

        <Tag color={autoRefresh ? 'green' : 'default'}>
          {autoRefresh ? '🟢 LIVE' : '⚪ Остановлено'}
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
