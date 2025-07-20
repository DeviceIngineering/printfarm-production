import React, { useEffect, useState } from 'react';
import { Table, Tag, Space, Button, Input, Select, Card, Statistic, Row, Col, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, PictureOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { fetchProducts, setFilters, setPagination } from '../../store/products';
import { Product, productsApi } from '../../api/products';
import { syncApi } from '../../api/sync';
import { PRIORITY_LEVELS } from '../../utils/constants';
import { ProductImage } from './ProductImage';

const { Search } = Input;
const { Option } = Select;

export const ProductTable: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { products, loading, pagination, filters, productStats } = useSelector((state: RootState) => state.products);
  const { status } = useSelector((state: RootState) => state.sync);
  const [searchText, setSearchText] = useState(filters.search || '');
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const params = {
      ...filters,
      page: pagination.current,
      page_size: pagination.pageSize
    };
    dispatch(fetchProducts(params));
  }, [dispatch, filters, pagination.current, pagination.pageSize]);

  // Очистка таймера при размонтировании компонента
  useEffect(() => {
    return () => {
      if (searchTimer) {
        clearTimeout(searchTimer);
      }
    };
  }, [searchTimer]);

  // Refresh products when sync completes
  useEffect(() => {
    if (status && !status.is_syncing && status.last_sync) {
      // Small delay to ensure backend has finished processing
      setTimeout(() => {
        dispatch(fetchProducts(filters));
      }, 1000);
    }
  }, [status?.is_syncing, dispatch, filters]);

  const handleSearch = (value: string) => {
    dispatch(setFilters({ ...filters, search: value }));
  };

  const handleSearchChange = (value: string) => {
    setSearchText(value);
    
    // Очистить предыдущий таймер
    if (searchTimer) {
      clearTimeout(searchTimer);
    }
    
    // Установить новый таймер для поиска с задержкой
    const timer = setTimeout(() => {
      dispatch(setFilters({ ...filters, search: value }));
    }, 500); // Задержка 500мс для оптимизации
    
    setSearchTimer(timer);
  };

  const handleFilterChange = (key: string, value: any) => {
    dispatch(setFilters({ ...filters, [key]: value }));
  };

  const handleTableChange = (newPagination: any, newFilters: any, sorter: any) => {
    const newPaginationData = {
      current: newPagination.current || 1,
      pageSize: newPagination.pageSize || 100
    };
    
    dispatch(setPagination(newPaginationData));
    
    // Формируем параметр сортировки
    const ordering = sorter?.field && sorter?.order ? 
      `${sorter.order === 'descend' ? '-' : ''}${sorter.field}` : 
      undefined;
    
    // Обновляем фильтры с новой сортировкой
    const updatedFilters = {
      ...filters,
      page: newPaginationData.current,
      page_size: newPaginationData.pageSize,
      ordering: ordering
    };
    
    // Сохраняем сортировку в состоянии фильтров
    dispatch(setFilters(updatedFilters));
    
    // Выполняем запрос с обновленными фильтрами
    dispatch(fetchProducts(updatedFilters));
  };

  const handleRefresh = () => {
    dispatch(fetchProducts(filters));
    message.success('Данные обновлены');
  };

  const handleExport = () => {
    message.loading('Подготовка экспорта...');
    productsApi.exportProducts(filters);
    setTimeout(() => {
      message.success('Экспорт начат. Файл загрузится автоматически.');
    }, 1000);
  };

  const handleDownloadImages = async () => {
    try {
      message.loading('Загрузка изображений...', 0);
      const result = await syncApi.downloadImages({ limit: 50 });
      message.destroy();
      
      if (result.synced_products > 0) {
        message.success(`Загружено изображений для ${result.synced_products} товаров (${result.total_images} файлов)`);
        // Обновить данные после загрузки изображений
        dispatch(fetchProducts(filters));
      } else {
        message.info('Нет товаров без изображений для загрузки');
      }
    } catch (error: any) {
      message.destroy();
      message.error(`Ошибка загрузки изображений: ${error.response?.data?.error || error.message}`);
    }
  };

  const columns = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      fixed: 'left' as const,
      sorter: true,
    },
    {
      title: 'Изображение',
      dataIndex: 'main_image',
      key: 'main_image',
      width: 80,
      render: (image: string, record: Product) => (
        <ProductImage src={image} article={record.article} />
      ),
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      ellipsis: true,
      sorter: true,
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 50,
      align: 'center' as const,
      sorter: true,
      render: (type: string) => {
        const typeConfig = {
          new: { symbol: '✨', color: 'blue', tooltip: 'Новая позиция' },
          old: { symbol: '✅', color: 'green', tooltip: 'Старая позиция' },
          critical: { symbol: '🔥', color: 'red', tooltip: 'Критическая позиция' }
        }[type] || { symbol: '❓', color: 'default', tooltip: 'Неизвестный тип' };
        
        return (
          <span 
            title={typeConfig.tooltip}
            style={{ 
              fontSize: '16px', 
              cursor: 'help',
              display: 'inline-block'
            }}
          >
            {typeConfig.symbol}
          </span>
        );
      },
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      align: 'center' as const,
      sorter: true,
      render: (stock: number | null | string) => {
        if (stock === null || stock === undefined || stock === '') return '-';
        
        const numericStock = typeof stock === 'string' ? parseFloat(stock) : stock;
        if (isNaN(numericStock)) return '-';
        
        return (
          <span className={numericStock < 5 ? 'text-red-600 font-bold' : ''}>
            {numericStock}
          </span>
        );
      },
    },
    {
      title: 'Расход за 2 мес.',
      dataIndex: 'sales_last_2_months',
      key: 'sales_last_2_months',
      width: 130,
      align: 'center' as const,
      sorter: true,
      render: (sales: number | null | string) => {
        if (sales === null || sales === undefined || sales === '') return '-';
        
        const numericSales = typeof sales === 'string' ? parseFloat(sales) : sales;
        if (isNaN(numericSales)) return '-';
        
        return (
          <span className={numericSales > 0 ? 'text-green-600' : 'text-gray-500'}>
            {numericSales.toFixed(0)}
          </span>
        );
      },
    },
    {
      title: 'Ср. расход/день',
      dataIndex: 'average_daily_consumption',
      key: 'average_daily_consumption',
      width: 120,
      align: 'center' as const,
      sorter: true,
      render: (consumption: number | null | string) => {
        if (consumption === null || consumption === undefined || consumption === '') return '-';
        
        const numericConsumption = typeof consumption === 'string' ? parseFloat(consumption) : consumption;
        if (isNaN(numericConsumption)) return '-';
        
        return (
          <span className={numericConsumption > 1 ? 'text-blue-600' : 'text-gray-600'}>
            {numericConsumption.toFixed(2)}
          </span>
        );
      },
    },
    {
      title: 'Дней остатка',
      dataIndex: 'days_of_stock',
      key: 'days_of_stock',
      width: 120,
      align: 'center' as const,
      sorter: true,
      render: (days: number | null | string) => {
        if (days === null || days === undefined || days === '') return '-';
        
        // Преобразуем в число если это строка
        const numericDays = typeof days === 'string' ? parseFloat(days) : days;
        
        if (isNaN(numericDays)) return '-';
        
        const color = numericDays < 5 ? 'red' : numericDays < 10 ? 'orange' : 'green';
        return <Tag color={color}>{numericDays.toFixed(1)}</Tag>;
      },
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 130,
      align: 'center' as const,
      sorter: true,
      render: (needed: number | null | string) => {
        if (needed === null || needed === undefined || needed === '' || needed === 0) return '-';
        
        const numericNeeded = typeof needed === 'string' ? parseFloat(needed) : needed;
        if (isNaN(numericNeeded) || numericNeeded === 0) return '-';
        
        return <span className="font-bold text-blue-600">{Math.ceil(numericNeeded)}</span>;
      },
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      align: 'center' as const,
      sorter: true,
      render: (priority: number | null | string) => {
        if (priority === null || priority === undefined || priority === '') return '-';
        
        const numericPriority = typeof priority === 'string' ? parseFloat(priority) : priority;
        if (isNaN(numericPriority)) return '-';
        
        let priorityClass = 'priority-low';
        if (numericPriority >= PRIORITY_LEVELS.HIGH) priorityClass = 'priority-high';
        else if (numericPriority >= PRIORITY_LEVELS.MEDIUM) priorityClass = 'priority-medium';
        
        return (
          <Space>
            <span className={`priority-indicator ${priorityClass}`} />
            <span>{priority}</span>
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      {productStats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={4}>
            <Card>
              <Statistic title="Всего товаров" value={productStats.total_products} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="Новые позиции" 
                value={productStats.new_products} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="Старые позиции" 
                value={productStats.old_products} 
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="Критические" 
                value={productStats.critical_products} 
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="Требуют производства" 
                value={productStats.production_needed_items} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic 
                title="Всего к производству" 
                value={productStats.total_production_units} 
                precision={0}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card>
        <Space style={{ marginBottom: 16 }} wrap>
          <Search
            placeholder="Поиск по артикулу или названию"
            onSearch={handleSearch}
            style={{ width: 300 }}
            value={searchText}
            onChange={e => handleSearchChange(e.target.value)}
            allowClear
          />
          
          <Select
            placeholder="Тип товара"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => handleFilterChange('product_type', value)}
          >
            <Option value="new">Новые</Option>
            <Option value="old">Старые</Option>
            <Option value="critical">Критические</Option>
          </Select>
          
          <Select
            placeholder="Приоритет"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => handleFilterChange('min_priority', value)}
          >
            <Option value={20}>Низкий (20+)</Option>
            <Option value={40}>Средний (40+)</Option>
            <Option value={60}>Высокий (60+)</Option>
            <Option value={80}>Критический (80+)</Option>
          </Select>
          
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
          >
            Обновить
          </Button>
          
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleExport}
          >
            Экспорт в Excel
          </Button>
          
          <Button
            icon={<PictureOutlined />}
            onClick={handleDownloadImages}
          >
            Загрузить изображения
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} товаров`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1580, y: 600 }}
          size="middle"
        />
      </Card>
    </div>
  );
};