import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Alert, Spin, Typography, Space, Tag, Tree } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const { Title, Text } = Typography;

interface ProductGroup {
  id: string;
  name: string;
  pathName: string;
  code?: string;
  archived?: boolean;
  parent?: {
    id: string;
    name: string;
  };
}

interface ApiError {
  error: string;
  type: string;
  detail: string;
}

export const TestProductGroupsPage: React.FC = () => {
  const [productGroups, setProductGroups] = useState<ProductGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [rawResponse, setRawResponse] = useState<any>(null);

  const fetchProductGroups = async () => {
    setLoading(true);
    setError(null);
    setRawResponse(null);
    
    try {
      const response = await apiClient.get('/sync/product-groups/');
      console.log('Raw API response:', response);
      setRawResponse(response.data);
      
      if (Array.isArray(response.data)) {
        setProductGroups(response.data);
      } else if (response.data.error) {
        setError(response.data);
        setProductGroups([]);
      }
    } catch (err: any) {
      console.error('Error fetching product groups:', err);
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
    fetchProductGroups();
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
      title: 'Полный путь',
      dataIndex: 'pathName',
      key: 'pathName',
      render: (text: string) => <Text type="secondary">{text}</Text>
    },
    {
      title: 'Код',
      dataIndex: 'code',
      key: 'code',
      render: (text: string) => text ? <Tag>{text}</Tag> : '-'
    },
    {
      title: 'Родительская группа',
      dataIndex: 'parent',
      key: 'parent',
      render: (parent: any) => parent ? (
        <div>
          <Text strong>{parent.name}</Text>
          <br />
          <Text code type="secondary">{parent.id}</Text>
        </div>
      ) : '-'
    },
    {
      title: 'Архивная',
      dataIndex: 'archived',
      key: 'archived',
      render: (archived: boolean) => archived ? <Tag color="red">Да</Tag> : <Tag color="green">Нет</Tag>
    }
  ];

  // Построение дерева для визуального отображения иерархии
  const buildTree = (groups: ProductGroup[]) => {
    const tree: any[] = [];
    const groupMap = new Map();

    // Создаем мапу всех групп
    groups.forEach(group => {
      groupMap.set(group.id, {
        key: group.id,
        title: `${group.name} (${group.pathName})`,
        children: []
      });
    });

    // Строим дерево
    groups.forEach(group => {
      const node = groupMap.get(group.id);
      if (group.parent && groupMap.has(group.parent.id)) {
        groupMap.get(group.parent.id).children.push(node);
      } else {
        tree.push(node);
      }
    });

    return tree;
  };

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Title level={3} style={{ margin: 0 }}>Тест загрузки групп товаров МойСклад</Title>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={fetchProductGroups}
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
              <p>Загрузка групп товаров из МойСклад...</p>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: 16 }}>
                <Text strong>Найдено групп товаров: </Text>
                <Tag color="blue">{productGroups.length}</Tag>
              </div>
              
              <Table 
                columns={columns}
                dataSource={productGroups}
                rowKey="id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} групп`
                }}
                locale={{
                  emptyText: 'Группы товаров не найдены'
                }}
                scroll={{ x: 1200 }}
              />
            </>
          )}
        </Card>

        {productGroups.length > 0 && (
          <Card title="Иерархия групп товаров">
            <Tree
              treeData={buildTree(productGroups)}
              defaultExpandAll
              showLine={{ showLeafIcon: false }}
            />
          </Card>
        )}

        <Card title="Информация о подключении">
          <Space direction="vertical">
            <Text>
              <strong>API Endpoint:</strong> {apiClient.defaults.baseURL}/sync/product-groups/
            </Text>
            <Text>
              <strong>Token:</strong> {localStorage.getItem('auth_token')?.substring(0, 10)}...
            </Text>
            <Text type="secondary">
              Эта страница делает прямой запрос к API МойСклад через Django backend для получения групп товаров
            </Text>
          </Space>
        </Card>

        {rawResponse && (
          <Card title="Raw Response">
            <details>
              <summary style={{ cursor: 'pointer', userSelect: 'none' }}>
                <Text type="secondary">Показать необработанный ответ API</Text>
              </summary>
              <pre style={{ 
                marginTop: 8, 
                padding: 12, 
                background: '#f5f5f5', 
                borderRadius: 4,
                overflow: 'auto',
                maxHeight: 400
              }}>
                {JSON.stringify(rawResponse, null, 2)}
              </pre>
            </details>
          </Card>
        )}
      </Space>
    </div>
  );
};