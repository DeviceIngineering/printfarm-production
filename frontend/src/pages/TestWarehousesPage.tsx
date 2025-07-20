import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Alert, Spin, Typography, Space, Tag } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const { Title, Text } = Typography;

interface Warehouse {
  id: string;
  name: string;
  code?: string;
  address?: string;
  archived?: boolean;
}

interface ApiError {
  error: string;
  type: string;
  detail: string;
}

export const TestWarehousesPage: React.FC = () => {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [rawResponse, setRawResponse] = useState<any>(null);

  const fetchWarehouses = async () => {
    setLoading(true);
    setError(null);
    setRawResponse(null);
    
    try {
      const response = await apiClient.get('/sync/warehouses/');
      console.log('Raw API response:', response);
      setRawResponse(response.data);
      
      if (Array.isArray(response.data)) {
        setWarehouses(response.data);
      } else if (response.data.error) {
        setError(response.data);
        setWarehouses([]);
      }
    } catch (err: any) {
      console.error('Error fetching warehouses:', err);
      setError({
        error: err.message || 'Unknown error',
        type: 'NetworkError',
        detail: err.response?.data?.detail || 'Failed to connect to API'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 300,
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Код',
      dataIndex: 'code',
      key: 'code',
      render: (text: string) => text ? <Tag>{text}</Tag> : '-'
    },
    {
      title: 'Адрес',
      dataIndex: 'address',
      key: 'address',
      render: (text: string) => text || '-'
    },
    {
      title: 'Архивный',
      dataIndex: 'archived',
      key: 'archived',
      render: (archived: boolean) => archived ? <Tag color="red">Да</Tag> : <Tag color="green">Нет</Tag>
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={3} style={{ margin: 0 }}>Тест загрузки складов МойСклад</Title>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={fetchWarehouses}
              loading={loading}
            >
              Обновить
            </Button>
          </Space>
        </Card>

        {error && (
          <Alert
            message="Ошибка загрузки"
            description={
              <div>
                <p><strong>Тип:</strong> {error.type}</p>
                <p><strong>Сообщение:</strong> {error.error}</p>
                <p><strong>Детали:</strong> {error.detail}</p>
              </div>
            }
            type="error"
            showIcon
          />
        )}

        <Card title="Результат запроса">
          {loading ? (
            <div style={{ textAlign: 'center', padding: '50px 0' }}>
              <Spin size="large" />
              <p>Загрузка складов из МойСклад...</p>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Найдено складов: </Text>
                <Tag color="blue">{warehouses.length}</Tag>
              </div>
              
              <Table 
                columns={columns}
                dataSource={warehouses}
                rowKey="id"
                pagination={false}
                locale={{
                  emptyText: 'Склады не найдены'
                }}
              />

              {rawResponse && (
                <details style={{ marginTop: 24 }}>
                  <summary style={{ cursor: 'pointer', userSelect: 'none' }}>
                    <Text type="secondary">Показать raw response</Text>
                  </summary>
                  <pre style={{ 
                    marginTop: 8, 
                    padding: 12, 
                    background: '#f5f5f5', 
                    borderRadius: 4,
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(rawResponse, null, 2)}
                  </pre>
                </details>
              )}
            </>
          )}
        </Card>

        <Card title="Информация о подключении">
          <Space direction="vertical">
            <Text>
              <strong>API Endpoint:</strong> {apiClient.defaults.baseURL}/sync/warehouses/
            </Text>
            <Text>
              <strong>Token:</strong> {localStorage.getItem('auth_token')?.substring(0, 10)}...
            </Text>
            <Text type="secondary">
              Эта страница делает прямой запрос к API МойСклад через Django backend
            </Text>
          </Space>
        </Card>
      </Space>
    </div>
  );
};