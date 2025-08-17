import React, { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Typography, Card, Button, Row, Col, Table, Tag, message, Spin, Upload, Modal, Input, Space } from 'antd';
import { 
  ShopOutlined, 
  ReloadOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  FileExcelOutlined,
  SearchOutlined,
  UpOutlined,
  DownOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../utils/constants';
import { RootState } from '../store';
import {
  fetchTochkaProducts,
  fetchTochkaProduction,
  uploadAndAutoProcess,
  exportDeduplicated,
  exportProduction,
  clearError,
  clearExcelData
} from '../store/tochka';
import type { AppDispatch } from '../store';

const { Title, Paragraph } = Typography;

export const TochkaPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const {
    products: productsData,
    production: productionData,
    excelData,
    deduplicatedExcelData,
    mergedData,
    filteredProductionData,
    coverage,
    productionStats,
    loading,
    error
  } = useSelector((state: RootState) => state.tochka);
  
  // Local UI state
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const searchInput = useRef<any>(null);
  
  // Состояния для сворачивания таблиц
  const [tablesCollapsed, setTablesCollapsed] = useState({
    products: false,
    production: false,
    mergedData: true, // свернуто по умолчанию после обработки
    excelData: true, // свернуто по умолчанию после обработки
    deduplicatedData: true, // свернуто по умолчанию после обработки
    filteredProduction: false // основная таблица результата - развернута
  });

  // Функция поиска для колонок
  const handleSearch = (selectedKeys: any, confirm: any, dataIndex: any) => {
    confirm();
    setSearchText(selectedKeys[0]);
    setSearchedColumn(dataIndex);
  };

  const handleReset = (clearFilters: any) => {
    clearFilters();
    setSearchText('');
  };

  const getColumnSearchProps = (dataIndex: string) => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
      <div style={{ padding: 8 }}>
        <Input
          ref={searchInput}
          placeholder={`Поиск артикула`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => handleSearch(selectedKeys, confirm, dataIndex)}
          style={{ marginBottom: 8, display: 'block' }}
        />
        <Space>
          <Button
            type="primary"
            onClick={() => handleSearch(selectedKeys, confirm, dataIndex)}
            icon={<SearchOutlined />}
            size="small"
            style={{ width: 90 }}
          >
            Найти
          </Button>
          <Button
            onClick={() => clearFilters && handleReset(clearFilters)}
            size="small"
            style={{ width: 90 }}
          >
            Сбросить
          </Button>
        </Space>
      </div>
    ),
    filterIcon: (filtered: boolean) => (
      <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />
    ),
    onFilter: (value: any, record: any) =>
      record[dataIndex]
        ? record[dataIndex].toString().toLowerCase().includes(value.toLowerCase())
        : '',
    onFilterDropdownVisibleChange: (visible: boolean) => {
      if (visible) {
        setTimeout(() => searchInput.current?.select(), 100);
      }
    },
  });

  // Функция для создания фильтра по значениям (для цвета)
  const getColumnFilterProps = (dataIndex: string, data: any[]) => {
    // Получаем уникальные значения из данных
    const uniqueValues = Array.from(new Set(
      data.map(item => {
        const value = item[dataIndex];
        return value || 'Не указан';
      })
    )).sort();

    return {
      filters: uniqueValues.map(value => ({
        text: value,
        value: value === 'Не указан' ? '' : value,
      })),
      onFilter: (value: any, record: any) => {
        const recordValue = record[dataIndex] || '';
        return recordValue === value;
      },
    };
  };

  // Функция для загрузки товаров
  const loadProducts = async () => {
    try {
      await dispatch(fetchTochkaProducts()).unwrap();
      message.success('Товары загружены');
    } catch (error) {
      message.error('Ошибка загрузки товаров');
    }
  };

  // Функция для загрузки списка на производство
  const loadProductionList = async () => {
    try {
      await dispatch(fetchTochkaProduction()).unwrap();
      message.success('Список на производство загружен');
    } catch (error) {
      message.error('Ошибка загрузки списка на производство');
    }
  };



  // Функция для загрузки Excel файла
  const handleExcelUpload = async (file: File) => {
    try {
      const result = await dispatch(uploadAndAutoProcess(file)).unwrap();
      setUploadModalVisible(false);
      
      // Показываем результат автоматической обработки
      const { summary } = result;
      const successMessage = `Файл обработан за ${result.processing_time_seconds.toFixed(1)}с! ` +
        `Найдено товаров: ${summary.products_found_in_db}/${summary.total_excel_records} ` +
        `(${summary.coverage_percentage.toFixed(1)}% покрытие)`;
      
      message.success(successMessage, 8);
      
      console.log('Автоматическая обработка завершена:', {
        'Время обработки': `${result.processing_time_seconds}с`,
        'Excel записей': summary.total_excel_records,
        'Найдено в БД': summary.products_found_in_db,
        'Покрытие': `${summary.coverage_percentage.toFixed(1)}%`,
        'К производству': summary.production_items_count
      });
      
      // После успешной обработки сворачиваем промежуточные таблицы
      setTablesCollapsed(prev => ({
        ...prev,
        mergedData: true,
        excelData: true,
        deduplicatedData: true,
        filteredProduction: false // основная таблица результата остается развернутой
      }));
    } catch (error: any) {
      message.error(error.message || 'Ошибка при обработке файла');
    }
    
    return false; // Предотвращаем автоматическую загрузку
  };

  // Функция для переключения сворачивания таблиц
  const toggleTableCollapse = (tableKey: keyof typeof tablesCollapsed) => {
    setTablesCollapsed(prev => ({
      ...prev,
      [tableKey]: !prev[tableKey]
    }));
  };

  // Вспомогательная функция для создания заголовка карточки с кнопкой сворачивания
  const createCollapsibleTitle = (title: string, tableKey: keyof typeof tablesCollapsed, extra?: React.ReactNode) => {
    const isCollapsed = tablesCollapsed[tableKey];
    return (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
        <span>{title}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {extra}
          <Button
            type="text"
            size="small"
            icon={isCollapsed ? <DownOutlined /> : <UpOutlined />}
            onClick={() => toggleTableCollapse(tableKey)}
            style={{ 
              padding: '0 4px',
              color: '#1890ff',
              border: 'none'
            }}
            title={isCollapsed ? 'Развернуть таблицу' : 'Свернуть таблицу'}
          />
        </div>
      </div>
    );
  };


  // Функция для экспорта дедуплицированных данных Excel
  const handleExportDeduplicatedExcel = async () => {
    if (deduplicatedExcelData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const result = await dispatch(exportDeduplicated(deduplicatedExcelData)).unwrap();
      
      // Создаем ссылку для скачивания
      const link = document.createElement('a');
      link.href = result.download_url;
      link.download = 'Данные_Excel_без_дублей.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success('Файл успешно экспортирован');
    } catch (error: any) {
      message.error(error.message || 'Ошибка при экспорте');
    }
  };

  // Функция для экспорта списка к производству
  const handleExportProductionList = async () => {
    if (filteredProductionData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const result = await dispatch(exportProduction(filteredProductionData)).unwrap();
      
      // Создаем ссылку для скачивания
      const link = document.createElement('a');
      link.href = result.download_url;
      link.download = 'Список_к_производству.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success('Файл успешно экспортирован');
    } catch (error: any) {
      message.error(error.message || 'Ошибка при экспорте');
    }
  };


  // Загрузка данных при монтировании только если они отсутствуют
  useEffect(() => {
    if (productsData.length === 0) {
      loadProducts();
    }
  }, []);
  
  // Очистка ошибок при размонтировании
  useEffect(() => {
    return () => {
      if (error) {
        dispatch(clearError());
      }
    };
  }, [dispatch, error]);

  // Колонки для таблицы товаров
  const productColumns = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      sorter: (a: any, b: any) => a.article.localeCompare(b.article),
      ...getColumnSearchProps('article'),
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      sorter: (a: any, b: any) => {
        const nameA = a.name || '';
        const nameB = b.name || '';
        return nameA.localeCompare(nameB);
      },
      render: (text: string) => text || '-',
    },
    {
      title: 'Цвет',
      dataIndex: 'color',
      key: 'color',
      width: 100,
      sorter: (a: any, b: any) => {
        const colorA = a.color || '';
        const colorB = b.color || '';
        return colorA.localeCompare(colorB);
      },
      render: (color: string) => {
        if (!color) {
          return <span style={{ color: '#999', fontStyle: 'italic' }}>—</span>;
        }
        
        return (
          <Tag 
            style={{ 
              maxWidth: '90px',
              textOverflow: 'ellipsis',
              overflow: 'hidden',
              whiteSpace: 'nowrap'
            }}
            title={color}
          >
            {color}
          </Tag>
        );
      },
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      sorter: (a: any, b: any) => a.current_stock - b.current_stock,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Резерв',
      dataIndex: 'reserved_stock',
      key: 'reserved_stock',
      width: 100,
      sorter: (a: any, b: any) => (a.reserved_stock || 0) - (b.reserved_stock || 0),
      render: (value: number) => (
        <span style={{ 
          color: value > 0 ? '#1890ff' : '#999',
          fontWeight: value > 0 ? 'bold' : 'normal' 
        }}>
          {value || 0} шт
        </span>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 100,
      sorter: (a: any, b: any) => a.product_type.localeCompare(b.product_type),
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
      sorter: (a: any, b: any) => a.sales_last_2_months - b.sales_last_2_months,
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
      sorter: (a: any, b: any) => a.article.localeCompare(b.article),
      ...getColumnSearchProps('article'),
      render: (text: string) => <Tag color="orange">{text}</Tag>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      sorter: (a: any, b: any) => {
        const nameA = a.name || '';
        const nameB = b.name || '';
        return nameA.localeCompare(nameB);
      },
      render: (text: string) => text || '-',
    },
    {
      title: 'Цвет',
      dataIndex: 'color',
      key: 'color',
      width: 100,
      sorter: (a: any, b: any) => {
        const colorA = a.color || '';
        const colorB = b.color || '';
        return colorA.localeCompare(colorB);
      },
      render: (color: string) => {
        if (!color) {
          return <span style={{ color: '#999', fontStyle: 'italic' }}>—</span>;
        }
        
        return (
          <Tag 
            style={{ 
              maxWidth: '90px',
              textOverflow: 'ellipsis',
              overflow: 'hidden',
              whiteSpace: 'nowrap'
            }}
            title={color}
          >
            {color}
          </Tag>
        );
      },
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 120,
      sorter: (a: any, b: any) => a.production_needed - b.production_needed,
      render: (value: number, record: any) => (
        <span style={{ 
          color: '#f5222d', 
          fontWeight: 'bold',
          backgroundColor: record.has_reserve ? '#fff7e6' : 'transparent',
          padding: record.has_reserve ? '2px 6px' : '0',
          borderRadius: record.has_reserve ? '4px' : '0',
          border: record.has_reserve ? '1px dashed #fa8c16' : 'none'
        }}>
          {value} шт
        </span>
      ),
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      sorter: (a: any, b: any) => a.production_priority - b.production_priority,
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
      sorter: (a: any, b: any) => a.current_stock - b.current_stock,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Резерв',
      dataIndex: 'reserved_stock',
      key: 'reserved_stock',
      width: 120,
      sorter: (a: any, b: any) => (a.calculated_reserve || a.reserved_stock || 0) - (b.calculated_reserve || b.reserved_stock || 0),
      render: (value: number, record: any) => {
        // Используем новый алгоритм отображения резерва если доступен
        if (record.reserve_display_text && record.reserve_color) {
          const colorMap = {
            'blue': '#1890ff',    // Синий - резерв больше остатка (хорошо)
            'red': '#ff4d4f',     // Красный - резерв меньше/равен остатку (внимание)
            'gray': '#8c8c8c'     // Серый - нет резерва
          };
          
          return (
            <div>
              <span 
                style={{ 
                  color: colorMap[record.reserve_color as keyof typeof colorMap] || colorMap.gray,
                  fontWeight: record.reserve_needs_attention ? 'bold' : 'normal',
                  fontSize: '12px'
                }}
                title={record.reserve_tooltip || 'Информация о резерве'}
              >
                {record.reserve_display_text}
              </span>
              {record.reserve_needs_attention && (
                <div style={{ 
                  fontSize: '10px', 
                  color: '#ff4d4f',
                  fontWeight: 'bold'
                }}>
                  ⚠ Требует внимания
                </div>
              )}
            </div>
          );
        }
        
        // Fallback к старому отображению
        return (
          <div>
            <span style={{ 
              color: value > 0 ? '#1890ff' : '#999',
              fontWeight: value > 0 ? 'bold' : 'normal' 
            }}>
              {value || 0} шт
            </span>
            {record.reserve_minus_stock !== null && record.reserve_minus_stock !== undefined && (
              <div style={{ fontSize: '10px', color: '#666' }}>
                Резерв-Остаток: {record.reserve_minus_stock > 0 ? '+' : ''}{record.reserve_minus_stock}
              </div>
            )}
          </div>
        );
      },
    },
  ];

  // Колонки для таблицы данных из Excel
  const excelColumns = [
    {
      title: 'Строка',
      dataIndex: 'row_number',
      key: 'row_number',
      width: 80,
      render: (value: number) => <Tag color="purple">#{value}</Tag>,
    },
    {
      title: 'Артикул товара',
      dataIndex: 'article',
      key: 'article',
      width: 150,
      render: (text: string, record: any) => (
        <div>
          <Tag color="green">{text}</Tag>
          {record.has_duplicates && (
            <Tag color="orange" style={{ marginTop: 4, fontSize: '10px' }}>
              Дубликат (строки: {record.duplicate_rows?.join(', ')})
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Заказов, шт.',
      dataIndex: 'orders',
      key: 'orders',
      width: 120,
      render: (value: number, record: any) => (
        <div>
          <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
            {value} шт
          </span>
          {record.has_duplicates && (
            <div style={{ fontSize: '10px', color: '#999' }}>
              Сумма дубликатов
            </div>
          )}
        </div>
      ),
    },
  ];

  // Колонки для таблицы дедуплицированных данных из Excel (только уникальные артикулы)
  const deduplicatedExcelColumns = [
    {
      title: 'Артикул товара',
      dataIndex: 'article',
      key: 'article',
      width: 150,
      ...getColumnSearchProps('article'),
      render: (text: string, record: any) => (
        <div>
          <Tag color="blue">{text}</Tag>
          {record.has_duplicates && (
            <Tag color="orange" style={{ marginLeft: 8, fontSize: '12px' }}>
              Объединен из {record.duplicate_rows ? record.duplicate_rows.length + 1 : 1} строк
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Заказов, шт (сумма)',
      dataIndex: 'orders',
      key: 'orders',
      width: 150,
      sorter: (a: any, b: any) => a.orders - b.orders,
      render: (value: number, record: any) => (
        <div>
          <Tag color="green" style={{ fontSize: '14px', padding: '4px 8px' }}>
            {value} шт
          </Tag>
          {record.duplicate_rows && record.duplicate_rows.length > 0 && (
            <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
              Исходные строки: {[record.row_number, ...record.duplicate_rows].join(', ')}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Статус обработки',
      key: 'status',
      width: 150,
      render: (text: string, record: any) => (
        <div>
          {record.has_duplicates ? (
            <Tag color="orange">Дубликаты объединены</Tag>
          ) : (
            <Tag color="green">Уникальный товар</Tag>
          )}
        </div>
      ),
    },
  ];

  // Колонки для объединенной таблицы производства
  const mergedColumns = [
    {
      title: 'Статус в Точке',
      key: 'tochka_status',
      width: 130,
      fixed: 'left' as const,
      sorter: (a: any, b: any) => {
        // Сортировка: сначала "НЕТ В ТОЧКЕ", потом "Есть в Точке"
        if (a.needs_registration && !b.needs_registration) return -1;
        if (!a.needs_registration && b.needs_registration) return 1;
        return 0;
      },
      render: (record: any) => {
        if (record.needs_registration) {
          return <Tag color="red" style={{ fontWeight: 'bold' }}>НЕТ В ТОЧКЕ</Tag>;
        } else {
          return <Tag color="green">Есть в Точке</Tag>;
        }
      },
    },
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      sorter: (a: any, b: any) => a.article.localeCompare(b.article),
      ...getColumnSearchProps('article'),
      render: (text: string, record: any) => (
        <div>
          <Tag color={record.is_in_tochka ? 'blue' : 'orange'}>{text}</Tag>
          {record.has_duplicates && (
            <Tag color="purple" style={{ marginTop: 4, fontSize: '10px' }}>
              Дубликат в Excel
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Название товара',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 250,
      ellipsis: true,
      sorter: (a: any, b: any) => a.product_name.localeCompare(b.product_name),
      render: (name: string, record: any) => (
        <span style={{ 
          color: record.needs_registration ? '#ff4d4f' : '#1890ff',
          fontWeight: record.needs_registration ? 'bold' : 'normal'
        }}>
          {name}
        </span>
      ),
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 120,
      sorter: (a: any, b: any) => a.production_needed - b.production_needed,
      render: (value: number, record: any) => (
        <span style={{ 
          color: '#f5222d', 
          fontWeight: 'bold',
          fontSize: record.needs_registration ? '14px' : '12px'
        }}>
          {value} шт
        </span>
      ),
    },
    {
      title: 'Заказов в Точке',
      dataIndex: 'orders_in_tochka',
      key: 'orders_in_tochka',
      width: 130,
      sorter: (a: any, b: any) => a.orders_in_tochka - b.orders_in_tochka,
      render: (value: number, record: any) => {
        if (record.is_in_tochka) {
          return (
            <div>
              <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                {value} шт
              </span>
              {record.has_duplicates && (
                <div style={{ fontSize: '10px', color: '#999' }}>
                  Сумма дубликатов
                </div>
              )}
            </div>
          );
        } else {
          return <span style={{ color: '#999' }}>—</span>;
        }
      },
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      sorter: (a: any, b: any) => a.current_stock - b.current_stock,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Продажи 2 мес',
      dataIndex: 'sales_last_2_months',
      key: 'sales_last_2_months',
      width: 110,
      sorter: (a: any, b: any) => a.sales_last_2_months - b.sales_last_2_months,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 90,
      sorter: (a: any, b: any) => a.product_type.localeCompare(b.product_type),
      render: (type: string) => {
        const colors: any = {
          'new': 'green',
          'old': 'blue',
          'critical': 'red'
        };
        const labels: any = {
          'new': 'Новый',
          'old': 'Старый',
          'critical': 'Критич.'
        };
        return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>;
      },
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      sorter: (a: any, b: any) => a.production_priority - b.production_priority,
      render: (value: number) => (
        <Tag color={value >= 80 ? 'red' : value >= 60 ? 'orange' : 'blue'}>
          {value}
        </Tag>
      ),
    },
  ];

  // Колонки для отфильтрованного списка производства (только товары в Точке)
  const filteredProductionColumns = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 120,
      sorter: (a: any, b: any) => a.article.localeCompare(b.article),
      ...getColumnSearchProps('article'),
      render: (text: string) => <Tag color="green">{text}</Tag>,
    },
    {
      title: 'Название товара',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 250,
      ellipsis: true,
      sorter: (a: any, b: any) => {
        const nameA = a.product_name || a.name || '';
        const nameB = b.product_name || b.name || '';
        return nameA.localeCompare(nameB);
      },
      render: (name: string, record: any) => {
        const displayName = name || record.name || '-';
        return <span style={{ color: '#1890ff' }}>{displayName}</span>;
      },
    },
    {
      title: 'К производству',
      dataIndex: 'production_needed',
      key: 'production_needed',
      width: 120,
      sorter: (a: any, b: any) => a.production_needed - b.production_needed,
      render: (value: number, record: any) => (
        <span style={{ 
          color: '#f5222d', 
          fontWeight: 'bold',
          backgroundColor: record.has_reserve ? '#fff7e6' : 'transparent',
          padding: record.has_reserve ? '2px 6px' : '0',
          borderRadius: record.has_reserve ? '4px' : '0',
          border: record.has_reserve ? '1px dashed #fa8c16' : 'none'
        }}>
          {value} шт
        </span>
      ),
    },
    {
      title: 'Резерв',
      dataIndex: 'reserved_stock',
      key: 'reserved_stock',
      width: 100,
      sorter: (a: any, b: any) => (a.reserved_stock || 0) - (b.reserved_stock || 0),
      render: (value: number, record: any) => (
        <div>
          <span style={{ 
            color: value > 0 ? '#1890ff' : '#999',
            fontWeight: value > 0 ? 'bold' : 'normal' 
          }}>
            {value || 0} шт
          </span>
          {record.reserve_minus_stock !== null && record.reserve_minus_stock !== undefined && (
            <div style={{ fontSize: '10px', color: '#666' }}>
              Резерв-Остаток: {record.reserve_minus_stock > 0 ? '+' : ''}{record.reserve_minus_stock}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Заказов в Точке',
      dataIndex: 'orders_in_tochka',
      key: 'orders_in_tochka',
      width: 130,
      sorter: (a: any, b: any) => a.orders_in_tochka - b.orders_in_tochka,
      render: (value: number, record: any) => (
        <div>
          <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
            {value} шт
          </span>
          {record.has_duplicates && (
            <div style={{ fontSize: '10px', color: '#999' }}>
              Сумма дубликатов
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Остаток',
      dataIndex: 'current_stock',
      key: 'current_stock',
      width: 100,
      sorter: (a: any, b: any) => a.current_stock - b.current_stock,
      render: (value: number) => `${value} шт`,
    },
    {
      title: 'Тип',
      dataIndex: 'product_type',
      key: 'product_type',
      width: 90,
      sorter: (a: any, b: any) => a.product_type.localeCompare(b.product_type),
      render: (type: string) => {
        const colors: any = {
          'new': 'green',
          'old': 'blue',
          'critical': 'red'
        };
        const labels: any = {
          'new': 'Новый',
          'old': 'Старый',
          'critical': 'Критич.'
        };
        return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>;
      },
    },
    {
      title: 'Приоритет',
      dataIndex: 'production_priority',
      key: 'production_priority',
      width: 100,
      sorter: (a: any, b: any) => a.production_priority - b.production_priority,
      render: (value: number) => (
        <Tag color={value >= 80 ? 'red' : value >= 60 ? 'orange' : 'blue'}>
          {value}
        </Tag>
      ),
    },
    {
      title: 'Цвет',
      dataIndex: 'color',
      key: 'color',
      width: 100,
      ...getColumnFilterProps('color', filteredProductionData),
      render: (value: string) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div 
            style={{ 
              width: 16, 
              height: 16, 
              backgroundColor: value || '#cccccc',
              border: '1px solid #ddd',
              borderRadius: 2,
              marginRight: 8 
            }}
          />
          {value || 'Не указан'}
        </div>
      ),
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
            loading={loading.products}
          >
            Загрузить товары
          </Button>
        </Col>
        <Col>
          <Button 
            icon={<UnorderedListOutlined />}
            onClick={loadProductionList}
            loading={loading.production}
          >
            Загрузить список на производство
          </Button>
        </Col>
        <Col>
          <Button 
            type="default"
            icon={<FileExcelOutlined />}
            onClick={() => setUploadModalVisible(true)}
            style={{ borderColor: '#52c41a', color: '#52c41a' }}
          >
            Загрузить Excel
          </Button>
        </Col>
      </Row>

      <Spin spinning={loading.products || loading.production || loading.autoProcess || loading.export}>
        {/* Таблица товаров */}
        <Card 
          title={createCollapsibleTitle(
            `Товары (${productsData.length})`, 
            'products',
            <Tag color="blue">Все товары</Tag>
          )}
          style={{ marginBottom: 24 }}
        >
          {!tablesCollapsed.products && (
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
          )}
        </Card>

        {/* Таблица производства */}
        <Card 
          title={createCollapsibleTitle(
            `Список на производство (${productionData.length})`,
            'production',
            <Tag color="red">Требуют производства</Tag>
          )}
          style={{ marginBottom: 24 }}
        >
          {!tablesCollapsed.production && (
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
          )}
        </Card>

        {/* Таблица анализа производства */}
        {mergedData.length > 0 && (
          <Card 
            title={createCollapsibleTitle(
              `Список на производство с анализом Точки (${mergedData.length} товаров)`,
              'mergedData',
              <div>
                <Tag color="purple">К производству</Tag>
                <Tag color="green">
                  {mergedData.filter((item: any) => item.is_in_tochka).length} есть в Точке
                </Tag>
                <Tag color="red" style={{ fontWeight: 'bold' }}>
                  {mergedData.filter((item: any) => item.needs_registration).length} НЕТ в Точке!
                </Tag>
              </div>
            )}
            style={{ marginBottom: 24 }}
          >
            {!tablesCollapsed.mergedData && (
              <Table
                dataSource={mergedData}
                columns={mergedColumns}
                rowKey={(record, index) => `merged-${index}`}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} из ${total} записей`,
                }}
                scroll={{ x: 1000 }}
                size="small"
              />
            )}
          </Card>
        )}

        {/* Таблица данных из Excel */}
        {excelData.length > 0 && mergedData.length === 0 && (
          <Card 
            title={createCollapsibleTitle(
              `Данные из Excel (${excelData.length} уникальных артикулов)`,
              'excelData',
              <div>
                <Tag color="green">Артикул + Заказы</Tag>
                {excelData.some((item: any) => item.has_duplicates) && (
                  <Tag color="orange">Дубликаты объединены</Tag>
                )}
              </div>
            )}
          >
            {!tablesCollapsed.excelData && (
              <Table
                dataSource={excelData}
                columns={excelColumns}
                rowKey={(record, index) => `excel-${index}`}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} из ${total} записей`,
                }}
                scroll={{ x: 400 }}
                size="small"
              />
            )}
          </Card>
        )}

        {/* Таблица дедуплицированных данных Excel */}
        {deduplicatedExcelData.length > 0 && (
          <Card 
            title={createCollapsibleTitle(
              `Данные Excel без дублей (${deduplicatedExcelData.length} уникальных артикулов)`,
              'deduplicatedData',
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Tag color="blue">Дедуплицированные данные</Tag>
                <Tag color="green">
                  {deduplicatedExcelData.reduce((sum: number, item: any) => sum + item.orders, 0)} шт всего
                </Tag>
                <Tag color="orange">
                  {deduplicatedExcelData.filter(item => item.has_duplicates).length} объединений
                </Tag>
                <Button 
                  type="primary"
                  size="small"
                  icon={<FileExcelOutlined />}
                  onClick={handleExportDeduplicatedExcel}
                  loading={loading.export}
                  style={{ backgroundColor: '#13c2c2', borderColor: '#13c2c2' }}
                >
                  Экспорт в Excel
                </Button>
              </div>
            )}
            style={{ marginBottom: 24 }}
          >
            {!tablesCollapsed.deduplicatedData && (
              <Table
                dataSource={deduplicatedExcelData}
                columns={deduplicatedExcelColumns}
                rowKey={(record, index) => `deduplicated-${index}`}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} из ${total} записей`,
                }}
                scroll={{ x: 450 }}
                size="small"
              />
            )}
          </Card>
        )}

        {/* Таблица отфильтрованного списка производства */}
        {filteredProductionData.length > 0 && (
          <Card 
            title={createCollapsibleTitle(
              `Список к производству (${filteredProductionData.length} товаров)`,
              'filteredProduction',
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Tag color="green">✅ Только товары в Точке</Tag>
                <Tag color="blue">
                  {filteredProductionData.reduce((sum: number, item: any) => {
                    const value = parseFloat(item.production_needed) || 0;
                    return sum + value;
                  }, 0).toFixed(0)} шт всего
                </Tag>
                <Button 
                  type="primary"
                  size="small"
                  icon={<FileExcelOutlined />}
                  onClick={handleExportProductionList}
                  loading={loading.export}
                  style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                >
                  Экспорт в Excel
                </Button>
              </div>
            )}
            style={{ marginBottom: 24 }}
          >
            {!tablesCollapsed.filteredProduction && (
              <Table
                dataSource={filteredProductionData}
                columns={filteredProductionColumns}
                rowKey={(record, index) => `filtered-${index}`}
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `${range[0]}-${range[1]} из ${total} записей`,
                }}
                scroll={{ x: 1000 }}
                size="small"
              />
            )}
          </Card>
        )}
      </Spin>

      {/* Модальное окно для загрузки Excel */}
      <Modal
        title={
          <span>
            <FileExcelOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            Загрузка Excel файла
          </span>
        }
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ padding: '20px 0' }}>
          <Paragraph>
            Выберите Excel файл (.xlsx или .xls) который содержит следующие колонки:
          </Paragraph>
          <ul style={{ marginBottom: 20 }}>
            <li><strong>"Артикул товара"</strong> - артикулы товаров</li>
            <li><strong>"Заказов, шт."</strong> - количество заказов в штуках</li>
          </ul>
          
          <Upload.Dragger
            name="file"
            multiple={false}
            accept=".xlsx,.xls"
            beforeUpload={handleExcelUpload}
            showUploadList={false}
            disabled={loading.autoProcess}
            style={{ 
              opacity: loading.autoProcess ? 0.6 : 1,
              pointerEvents: loading.autoProcess ? 'none' : 'auto'
            }}
          >
            <p className="ant-upload-drag-icon">
              <FileExcelOutlined 
                style={{ 
                  fontSize: 48, 
                  color: loading.autoProcess ? '#d9d9d9' : '#52c41a' 
                }} 
              />
            </p>
            <p className="ant-upload-text">
              {loading.autoProcess 
                ? 'Автоматическая обработка файла...' 
                : 'Нажмите или перетащите Excel файл в эту область'
              }
            </p>
            <p className="ant-upload-hint">
              {loading.autoProcess 
                ? 'Анализ и формирование списка производства...' 
                : 'Поддерживаются форматы .xlsx и .xls'
              }
            </p>
          </Upload.Dragger>
          
          {loading.autoProcess && (
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <Spin />
              <p style={{ marginTop: 10 }}>Автоматическая обработка: дедупликация → анализ → список производства...</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};