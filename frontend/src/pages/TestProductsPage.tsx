import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Alert, Spin, Tree, Typography, Statistic, Row, Col } from 'antd';
import { ReloadOutlined, AppstoreOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const { Title, Text } = Typography;

interface Product {
  id: number;
  article: string;
  name: string;
  current_stock: number;
  product_type: string;
  production_priority: number;
  days_of_stock: number;
  product_group_name: string;
  created_at: string;
  updated_at: string;
  last_synced_at: string;
}

interface ProductStats {
  total_products: number;
  new_products: number;
  old_products: number;
  critical_products: number;
  products_needing_production: number;
  total_production_units: number;
}

export const TestProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [stats, setStats] = useState<ProductStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Fetching products...');
      console.log('API Base URL:', process.env.REACT_APP_API_URL || '/api/v1');
      console.log('Auth token:', localStorage.getItem('auth_token') ? 'Present' : 'Missing');
      
      const response = await apiClient.get('/products/');
      console.log('Products response status:', response.status);
      console.log('Products response headers:', response.headers);
      console.log('Products response data:', response.data);
      
      const products = response.data.results || response.data || [];
      console.log('Extracted products:', products.length);
      setProducts(products);
    } catch (err: any) {
      console.error('Products fetch error:', err);
      console.error('Error response:', err.response);
      console.error('Error config:', err.config);
      setError(`Ошибка загрузки товаров: ${err.response?.status} - ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      console.log('Fetching product stats...');
      const response = await apiClient.get('/products/stats/');
      console.log('Stats response:', response.data);
      setStats(response.data);
    } catch (err: any) {
      console.error('Stats fetch error:', err);
      setError(`Ошибка загрузки статистики: ${err.response?.data?.detail || err.message}`);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchStats();
  }, []);

  const handleRefresh = () => {
    fetchProducts();
    fetchStats();
  };

  const renderProductTree = () => {
    if (!products.length) return null;

    // Group products by type
    const groupedProducts = products.reduce((acc, product) => {
      const type = product.product_type || 'unknown';
      if (!acc[type]) acc[type] = [];
      acc[type].push(product);
      return acc;
    }, {} as Record<string, Product[]>);

    const treeData = Object.entries(groupedProducts).map(([type, productList]) => ({
      title: `${type} (${productList.length})`,
      key: type,
      children: productList.slice(0, 10).map(product => ({
        title: (
          <div>
            <Text strong>{product.article}</Text> - {product.name.substring(0, 50)}
            {product.name.length > 50 ? '...' : ''}
            <br />
            <Text type="secondary">
              Остаток: {product.current_stock} | 
              Приоритет: {product.production_priority} |
              Группа: {product.product_group_name || 'Не указана'}
            </Text>
          </div>
        ),
        key: `${type}-${product.id}`,
        isLeaf: true,
      }))
    }));

    return <Tree treeData={treeData} defaultExpandAll />;
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>
          <AppstoreOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Тест загрузки товаров
        </Title>
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          onClick={handleRefresh}
          loading={loading}
        >
          Обновить
        </Button>
      </div>

      {error && (
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Statistics */}
      {stats && (
        <Card title="Статистика товаров" style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={4}>
              <Statistic 
                title="Всего товаров" 
                value={stats.total_products} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Новые позиции" 
                value={stats.new_products} 
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Старые позиции" 
                value={stats.old_products} 
                valueStyle={{ color: '#faad14' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Критические" 
                value={stats.critical_products} 
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Нужно произвести" 
                value={stats.products_needing_production} 
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Единиц к производству" 
                value={stats.total_production_units} 
                precision={0}
                valueStyle={{ color: '#eb2f96' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Products List */}
      <Card 
        title={`Список товаров (${products.length})`}
        loading={loading}
        extra={
          <Space>
            <Text type="secondary">Показаны первые 10 товаров в каждой группе</Text>
          </Space>
        }
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Загрузка товаров...</div>
          </div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 50, color: '#999' }}>
            Товары не найдены
          </div>
        ) : (
          renderProductTree()
        )}
      </Card>

      {/* Debug Info */}
      <Card title="Отладочная информация" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>API Base URL: {process.env.REACT_APP_API_URL || '/api/v1'}</Text>
          <Text>Auth Token: {localStorage.getItem('auth_token') ? `Установлен (${localStorage.getItem('auth_token')?.substring(0, 10)}...)` : 'Не установлен'}</Text>
          <Text>Количество загруженных товаров: {products.length}</Text>
          <Text>Время последнего обновления: {new Date().toLocaleString('ru-RU')}</Text>
          <Text>Ошибка: {error || 'Нет'}</Text>
          
          <Button 
            type="default" 
            onClick={() => {
              console.log('Manual API test started');
              fetch('/api/v1/products/', {
                headers: {
                  'Authorization': `Token ${localStorage.getItem('auth_token')}`,
                  'Accept': 'application/json',
                  'Content-Type': 'application/json'
                }
              })
              .then(res => {
                console.log('Direct fetch response:', res.status, res.statusText);
                return res.json();
              })
              .then(data => {
                console.log('Direct fetch data:', data);
                alert(`Прямой запрос успешен! Товаров: ${data.results?.length || data.length || 0}`);
              })
              .catch(err => {
                console.error('Direct fetch error:', err);
                alert(`Ошибка прямого запроса: ${err.message}`);
              });
            }}
          >
            Тест прямого запроса
          </Button>
          
          {products.length > 0 && (
            <details>
              <summary>Первый товар (JSON)</summary>
              <pre style={{ background: '#f5f5f5', padding: 16, overflow: 'auto' }}>
                {JSON.stringify(products[0], null, 2)}
              </pre>
            </details>
          )}
        </Space>
      </Card>
    </div>
  );
};