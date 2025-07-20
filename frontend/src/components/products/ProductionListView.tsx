import React, { useEffect } from 'react';
import { Card, Table, Button, Space, Tag, message, Empty, Spin } from 'antd';
import { CalculatorOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { calculateProductionList, fetchProductionList, fetchProductionStats } from '../../store/products';
import { productsApi } from '../../api/products';
import { PRODUCT_TYPES } from '../../utils/constants';

export const ProductionListView: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { productionList, productionStats, loading } = useSelector((state: RootState) => state.products);

  useEffect(() => {
    dispatch(fetchProductionList());
    dispatch(fetchProductionStats());
  }, [dispatch]);

  const handleCalculate = async () => {
    try {
      await dispatch(calculateProductionList({
        min_priority: 20,
        apply_coefficients: true
      })).unwrap();
      message.success('Список производства рассчитан успешно');
    } catch (error) {
      message.error('Ошибка расчета списка производства');
    }
  };

  const handleRefresh = () => {
    dispatch(fetchProductionList());
    dispatch(fetchProductionStats());
  };

  const handleExport = () => {
    try {
      productsApi.exportProductionList();
      message.success('Экспорт начат. Файл загрузится автоматически.');
    } catch (error) {
      message.error('Ошибка при экспорте списка производства');
    }
  };

  const columns = [
    {
      title: '№',
      key: 'index',
      width: 60,
      align: 'center' as const,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: 'Приоритет',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      align: 'center' as const,
    },
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 120,
      render: (type: string) => {
        const color = {
          new: 'blue',
          old: 'green',
          critical: 'red'
        }[type] || 'default';
        
        return <Tag color={color}>{PRODUCT_TYPES[type as keyof typeof PRODUCT_TYPES]}</Tag>;
      },
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      align: 'center' as const,
    },
    {
      title: 'К производству',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 130,
      align: 'center' as const,
      render: (quantity: number) => (
        <span className="font-bold text-blue-600">{Math.ceil(quantity)}</span>
      ),
    },
    {
      title: 'Группа',
      dataIndex: 'group_name',
      key: 'group_name',
      width: 200,
      ellipsis: true,
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      {productionStats && (
        <Card style={{ marginBottom: 24 }}>
          <Space size="large" wrap>
            <div>
              <div style={{ fontSize: 12, color: '#999' }}>Всего товаров требуют производства</div>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {productionStats.total_products_needing_production}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#999' }}>Критический приоритет</div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
                {productionStats.critical_priority_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#999' }}>Высокий приоритет</div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#fa8c16' }}>
                {productionStats.high_priority_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#999' }}>Средний приоритет</div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                {productionStats.medium_priority_count}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#999' }}>Всего единиц к производству</div>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                {productionStats.total_units_needed}
              </div>
            </div>
          </Space>
        </Card>
      )}

      <Card
        title={
          <Space>
            <span>Список на производство</span>
            {productionList && (
              <Tag color="blue">
                от {new Date(productionList.created_at).toLocaleString('ru-RU')}
              </Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<CalculatorOutlined />}
              onClick={handleCalculate}
              type="primary"
              className="btn-primary"
            >
              Рассчитать список
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
            >
              Обновить
            </Button>
            {productionList && (
              <Button 
                icon={<DownloadOutlined />}
                onClick={handleExport}
              >
                Экспорт в Excel
              </Button>
            )}
          </Space>
        }
      >
        {productionList && productionList.items.length > 0 ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <span>Всего позиций: <strong>{productionList.total_items}</strong></span>
                <span>Всего единиц: <strong>{productionList.total_units}</strong></span>
              </Space>
            </div>
            <Table
              columns={columns}
              dataSource={productionList.items}
              rowKey={(record) => `${record.article}-${record.priority}`}
              pagination={false}
              scroll={{ x: 1000, y: 600 }}
              size="middle"
            />
          </>
        ) : (
          <Empty 
            description="Нет данных для отображения"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={handleCalculate}>
              Рассчитать список производства
            </Button>
          </Empty>
        )}
      </Card>
    </div>
  );
};