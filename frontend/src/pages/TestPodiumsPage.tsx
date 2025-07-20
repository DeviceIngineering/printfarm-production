import React, { useState, useEffect } from 'react';
import { Table, Button, Card, Spin, Alert, Statistic, Row, Col, Typography, Space } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import api from '../api/client';

const { Title, Text } = Typography;

interface Product {
  id: number;
  article: string;
  name: string;
  current_stock: number;
  sales_last_2_months: number;
  average_daily_consumption: number;
  product_type: string;
  production_needed: number;
  production_priority: number;
  product_group_name: string;
  days_of_stock: number | null;
  last_synced_at: string;
}

interface MoySkladProduct {
  id: string;
  article: string;
  name: string;
  stock: number;
  folder?: {
    name: string;
    meta: {
      href: string;
    };
  };
}

const TestPodiumsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [moyskladData, setMoyskladData] = useState<MoySkladProduct[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    totalProducts: 0,
    zeroStockProducts: 0,
    withSalesProducts: 0,
    averageStock: 0
  });

  const loadProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      // Загружаем товары из локальной БД с фильтром по группе "Подиумы"
      const response = await api.get('/products/', {
        params: {
          product_group_name: 'Подиумы',
          page_size: 100
        }
      });
      
      const productList = response.data.results || [];
      setProducts(productList);
      
      // Считаем статистику
      const totalProducts = productList.length;
      const zeroStockProducts = productList.filter((p: Product) => p.current_stock === 0).length;
      const withSalesProducts = productList.filter((p: Product) => p.sales_last_2_months > 0).length;
      const averageStock = totalProducts > 0 ? 
        productList.reduce((sum: number, p: Product) => sum + p.current_stock, 0) / totalProducts : 0;
      
      setStats({
        totalProducts,
        zeroStockProducts,
        withSalesProducts,
        averageStock: Math.round(averageStock * 100) / 100
      });
      
    } catch (err: any) {
      setError(`Ошибка загрузки товаров: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadMoySkladData = async () => {
    setSyncLoading(true);
    setError(null);
    try {
      // Получаем группы товаров
      const groupsResponse = await api.get('/sync/product-groups/');
      const groups = groupsResponse.data;
      
      // Находим группу "Подиумы"
      const podiumsGroup = groups.find((g: any) => g.name === 'Подиумы');
      if (!podiumsGroup) {
        setError('Группа "Подиумы" не найдена в МойСклад');
        return;
      }
      
      console.log('Найдена группа Подиумы:', podiumsGroup);
      
      // Получаем склады
      const warehousesResponse = await api.get('/sync/warehouses/');
      const warehouses = warehousesResponse.data;
      const defaultWarehouse = warehouses.find((w: any) => w.id === '241ed919-a631-11ee-0a80-07a9000bb947');
      
      if (!defaultWarehouse) {
        setError('Адресный склад не найден');
        return;
      }
      
      console.log('Используем склад:', defaultWarehouse);
      
      // Тестовый запрос напрямую к бэкенду для получения данных МойСклад
      const testResponse = await api.post('/sync/test-moysklad-data/', {
        warehouse_id: defaultWarehouse.id,
        group_name: 'Подиумы'
      });
      
      setMoyskladData(testResponse.data.products || []);
      
    } catch (err: any) {
      setError(`Ошибка загрузки данных МойСклад: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncLoading(false);
    }
  };

  const syncPodiums = async () => {
    setSyncLoading(true);
    setError(null);
    try {
      // Запускаем синхронизацию только группы "Подиумы"
      const groupsResponse = await api.get('/sync/product-groups/');
      const groups = groupsResponse.data;
      
      // Получаем все группы кроме "Подиумы" для исключения
      const excludedGroups = groups
        .filter((g: any) => g.name !== 'Подиумы')
        .map((g: any) => g.id);
      
      const response = await api.post('/sync/start/', {
        warehouse_id: '241ed919-a631-11ee-0a80-07a9000bb947',
        excluded_groups: excludedGroups,
        sync_images: false
      });
      
      console.log('Синхронизация запущена:', response.data);
      
      // Ждем завершения синхронизации
      let syncCompleted = false;
      let attempts = 0;
      const maxAttempts = 30;
      
      while (!syncCompleted && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        try {
          const statusResponse = await api.get('/sync/status/');
          const status = statusResponse.data;
          
          if (status.status === 'success' || status.status === 'failed') {
            syncCompleted = true;
            if (status.status === 'failed') {
              setError(`Синхронизация завершилась с ошибкой: ${status.error_details}`);
            }
          }
        } catch (statusErr) {
          console.log('Ошибка проверки статуса:', statusErr);
        }
        
        attempts++;
      }
      
      if (syncCompleted) {
        // Перезагружаем товары после синхронизации
        await loadProducts();
      } else {
        setError('Синхронизация не завершилась за разумное время');
      }
      
    } catch (err: any) {
      setError(`Ошибка синхронизации: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const columns: ColumnsType<Product> = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      fixed: 'left',
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      render: (stock: number) => (
        <span className={stock === 0 ? 'text-red-500 font-bold' : 'text-green-600 font-bold'}>
          {stock}
        </span>
      ),
    },
    {
      title: 'Продажи (2 мес)',
      dataIndex: 'sales_last_2_months',
      key: 'sales_last_2_months',
      width: 120,
      render: (sales: number) => (
        <span className={sales > 0 ? 'text-blue-600 font-bold' : 'text-gray-400'}>
          {sales}
        </span>
      ),
    },
    {
      title: 'Ср. расход/день',
      dataIndex: 'average_daily_consumption',
      key: 'average_daily_consumption',
      width: 120,
      render: (consumption: number) => {
        const num = Number(consumption) || 0;
        return num.toFixed(3);
      },
    },
    {
      title: 'Дней запаса',
      dataIndex: 'days_of_stock',
      key: 'days_of_stock',
      width: 100,
      render: (days: number | null) => {
        if (days === null || days === undefined) return '∞';
        const num = Number(days);
        return isNaN(num) ? '∞' : num.toFixed(1);
      },
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 80,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          'new': '🆕',
          'old': '📦',
          'critical': '🚨'
        };
        return typeMap[type] || type;
      },
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 120,
      render: (quantity: number) => {
        const num = Number(quantity) || 0;
        return (
          <span className="font-bold text-blue-600">{Math.ceil(num)}</span>
        );
      },
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      render: (priority: number) => (
        <span className={`font-bold ${priority >= 80 ? 'text-red-500' : priority >= 60 ? 'text-orange-500' : 'text-gray-500'}`}>
          {priority}
        </span>
      ),
    },
    {
      title: 'Последняя синхронизация',
      dataIndex: 'last_synced_at',
      key: 'last_synced_at',
      width: 160,
      render: (date: string) => date ? new Date(date).toLocaleString('ru-RU') : 'Никогда',
    },
  ];

  const moyskladColumns: ColumnsType<MoySkladProduct> = [
    {
      title: 'Артикул (МС)',
      dataIndex: 'article',
      key: 'article',
      width: 120,
    },
    {
      title: 'Название (МС)',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Остаток (МС)',
      dataIndex: 'stock',
      key: 'stock',
      width: 100,
      render: (stock: number) => (
        <span className={stock === 0 ? 'text-red-500 font-bold' : 'text-green-600 font-bold'}>
          {stock}
        </span>
      ),
    },
    {
      title: 'Группа (МС)',
      key: 'folder',
      width: 150,
      render: (record: MoySkladProduct) => record.folder?.name || 'Без группы',
    },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <Title level={2}>🧪 Тестовая страница: Товары группы "Подиумы"</Title>
        <Text type="secondary">
          Эта страница позволяет проверить корректность загрузки и отображения товаров из группы "Подиумы"
        </Text>
      </div>

      {error && (
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          closable
          onClose={() => setError(null)}
          className="mb-4"
        />
      )}

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card>
            <Statistic title="Всего товаров" value={stats.totalProducts} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="С нулевыми остатками" 
              value={stats.zeroStockProducts}
              valueStyle={{ color: stats.zeroStockProducts > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="С продажами" 
              value={stats.withSalesProducts}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic 
              title="Средний остаток" 
              value={stats.averageStock}
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Space className="mb-4">
        <Button 
          type="primary" 
          icon={<ReloadOutlined />} 
          onClick={loadProducts}
          loading={loading}
        >
          Обновить данные из БД
        </Button>
        <Button 
          type="default" 
          icon={<DownloadOutlined />} 
          onClick={loadMoySkladData}
          loading={syncLoading}
        >
          Загрузить данные из МойСклад
        </Button>
        <Button 
          type="primary" 
          danger
          icon={<ReloadOutlined />} 
          onClick={syncPodiums}
          loading={syncLoading}
        >
          Синхронизировать только "Подиумы"
        </Button>
      </Space>

      <Card title="Товары в локальной базе данных" className="mb-6">
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} из ${total} товаров`,
          }}
          scroll={{ x: 1200, y: 400 }}
          size="small"
        />
      </Card>

      {moyskladData.length > 0 && (
        <Card title="Данные из МойСклад (для сравнения)">
          <Table
            columns={moyskladColumns}
            dataSource={moyskladData}
            rowKey="id"
            loading={syncLoading}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} из ${total} товаров из МойСклад`,
            }}
            scroll={{ x: 800, y: 400 }}
            size="small"
          />
        </Card>
      )}
    </div>
  );
};

export default TestPodiumsPage;