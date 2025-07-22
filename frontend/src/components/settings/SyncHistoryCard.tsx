import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Tag, 
  Space, 
  Statistic,
  Button,
  Typography
} from 'antd';
import { HistoryOutlined, ReloadOutlined } from '@ant-design/icons';
import { syncApi } from '../../api/sync';

const { Text } = Typography;

interface SyncHistoryItem {
  id: number;
  sync_type: 'manual' | 'scheduled';
  status: 'pending' | 'success' | 'failed' | 'partial';
  started_at: string;
  finished_at?: string;
  warehouse_name: string;
  total_products: number;
  synced_products: number;
  failed_products: number;
  success_rate: number;
  duration?: number;
}

export const SyncHistoryCard: React.FC = () => {
  const [history, setHistory] = useState<SyncHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadSyncHistory = async () => {
    setLoading(true);
    try {
      const data = await syncApi.getHistory();
      console.log('Sync history loaded:', data);
      setHistory(data || []);
    } catch (error) {
      console.error('Failed to load sync history:', error);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSyncHistory();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'partial': return 'orange';
      case 'pending': return 'blue';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success': return 'Успешно';
      case 'failed': return 'Ошибка';
      case 'partial': return 'Частично';
      case 'pending': return 'Выполняется';
      default: return status;
    }
  };

  const getSyncTypeText = (syncType: string) => {
    switch (syncType) {
      case 'manual': return 'Ручная';
      case 'scheduled': return 'По расписанию';
      default: return syncType;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Н/Д';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (minutes > 0) {
      return `${minutes}м ${remainingSeconds}с`;
    }
    return `${remainingSeconds}с`;
  };

  const columns = [
    {
      title: 'Дата и время',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 140,
      render: (startedAt: string, record: SyncHistoryItem) => (
        <div>
          <div style={{ fontWeight: 500 }}>
            {new Date(startedAt).toLocaleDateString('ru-RU')}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {new Date(startedAt).toLocaleTimeString('ru-RU', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
            {record.finished_at && (
              <>
                {' - '}
                {new Date(record.finished_at).toLocaleTimeString('ru-RU', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'sync_type',
      key: 'sync_type',
      width: 110,
      render: (syncType: string) => (
        <Tag color={syncType === 'manual' ? 'blue' : 'green'}>
          {getSyncTypeText(syncType)}
        </Tag>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: 'Товары',
      key: 'products',
      width: 120,
      render: (record: SyncHistoryItem) => (
        <div>
          <div style={{ fontWeight: 500 }}>
            <Text type={record.synced_products === record.total_products ? 'success' : 'warning'}>
              {record.synced_products}
            </Text>
            {' / '}
            <Text>{record.total_products}</Text>
          </div>
          {record.failed_products > 0 && (
            <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
              Ошибок: {record.failed_products}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Успешность',
      dataIndex: 'success_rate',
      key: 'success_rate',
      width: 90,
      render: (rate: number) => (
        <Text type={rate >= 90 ? 'success' : rate >= 70 ? 'warning' : 'danger'}>
          {rate.toFixed(1)}%
        </Text>
      ),
    },
    {
      title: 'Время выполнения',
      dataIndex: 'duration',
      key: 'duration',
      width: 110,
      render: (duration?: number) => (
        <Text style={{ fontSize: '12px' }}>
          {formatDuration(duration)}
        </Text>
      ),
    },
    {
      title: 'Склад',
      dataIndex: 'warehouse_name',
      key: 'warehouse_name',
      ellipsis: true,
      render: (name: string) => (
        <Text style={{ fontSize: '12px' }}>
          {name || 'Не указан'}
        </Text>
      ),
    },
  ];

  // Рассчитываем статистику
  const totalSyncs = history.length;
  const successfulSyncs = history.filter(h => h.status === 'success').length;
  const averageSuccessRate = totalSyncs > 0 
    ? history.reduce((sum, h) => sum + h.success_rate, 0) / totalSyncs 
    : 0;

  const lastSync = history.length > 0 ? history[0] : null;

  return (
    <Card 
      title={
        <Space>
          <HistoryOutlined style={{ color: 'var(--color-primary)' }} />
          <span>История синхронизаций</span>
        </Space>
      }
      extra={
        <Button 
          icon={<ReloadOutlined />}
          onClick={loadSyncHistory}
          loading={loading}
          size="small"
        >
          Обновить
        </Button>
      }
      style={{ marginTop: 24 }}
    >
      {/* Статистика */}
      {totalSyncs > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Space size={32}>
            <Statistic 
              title="Всего синхронизаций" 
              value={totalSyncs}
              valueStyle={{ fontSize: '18px' }}
            />
            <Statistic 
              title="Успешных" 
              value={successfulSyncs}
              suffix={`/ ${totalSyncs}`}
              valueStyle={{ 
                fontSize: '18px',
                color: successfulSyncs === totalSyncs ? '#52c41a' : '#fa8c16'
              }}
            />
            <Statistic 
              title="Средняя успешность" 
              value={averageSuccessRate.toFixed(1)}
              suffix="%"
              valueStyle={{ 
                fontSize: '18px',
                color: averageSuccessRate >= 90 ? '#52c41a' : averageSuccessRate >= 70 ? '#fa8c16' : '#ff4d4f'
              }}
            />
            {lastSync && (
              <Statistic 
                title="Последняя синхронизация" 
                value={new Date(lastSync.started_at).toLocaleString('ru-RU')}
                valueStyle={{ fontSize: '14px' }}
              />
            )}
          </Space>
        </div>
      )}

      {/* Таблица истории */}
      <Table 
        columns={columns}
        dataSource={history}
        rowKey="id"
        size="small"
        loading={loading}
        pagination={{ 
          pageSize: 10,
          showSizeChanger: false,
          showQuickJumper: false,
          showTotal: (total) => `Всего ${total} записей`
        }}
        locale={{
          emptyText: totalSyncs === 0 && !loading ? 'Синхронизации еще не выполнялись' : undefined
        }}
        scroll={{ x: 800 }}
      />
    </Card>
  );
};