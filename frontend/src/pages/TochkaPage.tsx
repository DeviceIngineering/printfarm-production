import React, { useState, useEffect } from 'react';
import { Typography, Card, Button, Row, Col, Table, Tag, message, Spin } from 'antd';
import { 
  ShopOutlined, 
  ReloadOutlined,
  AppstoreOutlined,
  UnorderedListOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

export const TochkaPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [productsData, setProductsData] = useState<any[]>([]);
  const [productionData, setProductionData] = useState<any[]>([]);

  // Функция для загрузки товаров
  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/tochka/products/');
      if (response.ok) {
        const data = await response.json();
        setProductsData(data.results || data);
        message.success('Товары загружены');
      } else {
        message.error('Ошибка загрузки товаров');
      }
    } catch (error) {
      message.error('Ошибка подключения к API');
    } finally {
      setLoading(false);
    }
  };

  // Функция для загрузки списка на производство
  const loadProductionList = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/tochka/production/');
      if (response.ok) {
        const data = await response.json();
        setProductionData(data.results || data);
        message.success('Список на производство загружен');
      } else {
        message.error('Ошибка загрузки списка на производство');
      }
    } catch (error) {
      message.error('Ошибка подключения к API');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка данных при монтировании
  useEffect(() => {
    loadProducts();
  }, []);

  // Колонки для таблицы товаров
  const productColumns = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 100,
      render: (type: string) => {
        const colors: any = {
          'new': 'green',
          'old': 'blue',
          'critical': 'red'
        };
        const labels: any = {
          'new': 'Новый',
          'old': 'Старый',
          'critical': 'Критичный'
        };
        return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>;
      },
    },
    {
      title: 'Продажи за 2 мес',
      dataIndex: 'sales_last_2_months',
      key: 'sales_last_2_months',
      width: 120,
      render: (value: number) => `${value} шт`,
    },
  ];

  // Колонки для таблицы производства
  const productionColumns = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      render: (text: string) => <Tag color="orange">{text}</Tag>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 120,
      render: (value: number) => (
        <span style={{ color: '#f5222d', fontWeight: 'bold' }}>
          {value} шт
        </span>
      ),
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      render: (value: number) => (
        <Tag color={value >= 80 ? 'red' : value >= 60 ? 'orange' : 'blue'}>
          {value}
        </Tag>
      ),
    },
    {
      title: 'Текущий остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 120,
      render: (value: number) => `${value} шт`,
    },
  ];

  return (
    <div style={{ padding: '0 24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ color: 'var(--color-primary)', textShadow: 'var(--glow-primary)' }}>
          <ShopOutlined style={{ marginRight: 8 }} />
          Точка
        </Title>
        <Paragraph>
          Информация о товарах и списке на производство
        </Paragraph>
      </div>

      {/* Кнопки управления */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col>
          <Button 
            type="primary" 
            icon={<AppstoreOutlined />}
            onClick={loadProducts}
            loading={loading}
          >
            Загрузить товары
          </Button>
        </Col>
        <Col>
          <Button 
            icon={<UnorderedListOutlined />}
            onClick={loadProductionList}
            loading={loading}
          >
            Загрузить список на производство
          </Button>
        </Col>
        <Col>
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => {
              loadProducts();
              loadProductionList();
            }}
            loading={loading}
          >
            Обновить все
          </Button>
        </Col>
      </Row>

      <Spin spinning={loading}>
        {/* Таблица товаров */}
        <Card 
          title={`Товары (${productsData.length})`} 
          style={{ marginBottom: 24 }}
          extra={<Tag color="blue">Все товары</Tag>}
        >
          <Table
            dataSource={productsData}
            columns={productColumns}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} из ${total} записей`,
            }}
            scroll={{ x: 800 }}
            size="small"
          />
        </Card>

        {/* Таблица производства */}
        <Card 
          title={`Список на производство (${productionData.length})`}
          extra={<Tag color="red">Требуют производства</Tag>}
        >
          <Table
            dataSource={productionData}
            columns={productionColumns}
            rowKey="id"
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} из ${total} записей`,
            }}
            scroll={{ x: 800 }}
            size="small"
          />
        </Card>
      </Spin>
    </div>
  );
};