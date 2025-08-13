import React, { useState, useEffect, useRef } from 'react';
import { Typography, Card, Button, Row, Col, Table, Tag, message, Spin, Upload, Modal, Input, Space } from 'antd';
import { 
  ShopOutlined, 
  ReloadOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  FileExcelOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { API_BASE_URL } from '../utils/constants';

const { Title, Paragraph } = Typography;

export const TochkaPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [productsData, setProductsData] = useState<any[]>([]);
  const [productionData, setProductionData] = useState<any[]>([]);
  const [excelData, setExcelData] = useState<any[]>([]);
  const [deduplicatedExcelData, setDeduplicatedExcelData] = useState<any[]>([]);
  const [mergedData, setMergedData] = useState<any[]>([]);
  const [filteredProductionData, setFilteredProductionData] = useState<any[]>([]);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [mergeLoading, setMergeLoading] = useState(false);
  const [filterLoading, setFilterLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [searchedColumn, setSearchedColumn] = useState('');
  const searchInput = useRef<any>(null);

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

  // Функция для загрузки товаров
  const loadProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/tochka/products/`);
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
      const response = await fetch(`${API_BASE_URL}/tochka/production/`);
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


  // Функция для создания дедуплицированных данных из загруженного Excel
  const createDeduplicatedData = (rawData: any[]) => {
    const articleMap = new Map();
    
    // Группируем по артикулам
    rawData.forEach((item) => {
      const article = item.article;
      if (articleMap.has(article)) {
        const existing = articleMap.get(article);
        // Суммируем заказы
        existing.orders += item.orders;
        // Добавляем номер строки к дубликатам
        if (!existing.duplicate_rows) {
          existing.duplicate_rows = [];
        }
        existing.duplicate_rows.push(item.row_number);
        existing.has_duplicates = true;
      } else {
        articleMap.set(article, {
          article: item.article,
          orders: item.orders,
          row_number: item.row_number,
          has_duplicates: false,
          duplicate_rows: []
        });
      }
    });
    
    // Конвертируем Map в массив и сортируем по убыванию заказов
    return Array.from(articleMap.values()).sort((a, b) => b.orders - a.orders);
  };

  // Функция для загрузки Excel файла
  const handleExcelUpload = async (file: File) => {
    setUploadLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_BASE_URL}/tochka/upload-excel/`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setExcelData(data.data || []);
        
        // Создаем дедуплицированные данные из исходных
        const deduplicatedData = createDeduplicatedData(data.data || []);
        setDeduplicatedExcelData(deduplicatedData);
        
        setUploadModalVisible(false);
        
        // Более информативное сообщение о результатах
        const successMessage = data.duplicates_merged > 0 
          ? `${data.message} (${data.duplicates_merged} дубликатов объединено)`
          : data.message;
        
        message.success(successMessage, 5); // Показываем 5 секунд
        
        if (data.duplicates_merged > 0) {
          console.log(`Дедупликация завершена:
            - Исходных записей: ${data.total_raw_records}
            - Уникальных артикулов: ${data.unique_articles}  
            - Дубликатов объединено: ${data.duplicates_merged}
            - Дедуплицированных записей создано: ${deduplicatedData.length}`);
        }
      } else {
        message.error(data.error || 'Ошибка при загрузке файла');
        if (data.available_columns) {
          console.log('Доступные колонки:', data.available_columns);
        }
      }
    } catch (error) {
      message.error('Ошибка подключения к серверу');
    } finally {
      setUploadLoading(false);
    }
    
    return false; // Предотвращаем автоматическую загрузку
  };

  // Функция для объединения Excel данных с товарами
  const handleMergeWithProducts = async () => {
    if (excelData.length === 0) {
      message.warning('Сначала загрузите Excel файл');
      return;
    }

    setMergeLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/tochka/merge-with-products/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          excel_data: excelData
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMergedData(data.data || []);
        message.success(`${data.message} (${data.coverage_rate}% покрытие)`, 5);
        
        console.log(`Анализ производства завершен:
          - Всего товаров к производству: ${data.total_production_needed}
          - Есть в Точке: ${data.products_in_tochka}
          - НЕТ в Точке: ${data.products_not_in_tochka}
          - Процент покрытия: ${data.coverage_rate}%`);
          
        if (data.products_not_in_tochka > 0) {
          message.warning(`Внимание! ${data.products_not_in_tochka} товаров требуют регистрации в Точке!`, 8);
        }
      } else {
        message.error(data.error || 'Ошибка при объединении данных');
      }
    } catch (error) {
      message.error('Ошибка подключения к серверу');
    } finally {
      setMergeLoading(false);
    }
  };

  // Функция для получения отфильтрованного списка производства (только товары есть в Точке)
  const handleGetFilteredProduction = async () => {
    if (excelData.length === 0) {
      message.warning('Сначала загрузите Excel файл');
      return;
    }

    setFilterLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/tochka/filtered-production/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          excel_data: excelData
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setFilteredProductionData(data.data || []);
        message.success(`${data.message} (${data.total_quantity} шт)`, 5);
        
        console.log(`Отфильтрованный список готов:
          - Товаров к производству: ${data.total_items}
          - Общее количество: ${data.total_quantity} шт
          - Исключены товары отсутствующие в Точке`);
      } else {
        message.error(data.error || 'Ошибка при получении списка');
      }
    } catch (error) {
      message.error('Ошибка подключения к серверу');
    } finally {
      setFilterLoading(false);
    }
  };

  // Функция для экспорта дедуплицированных данных Excel
  const handleExportDeduplicatedExcel = async () => {
    if (deduplicatedExcelData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/tochka/export-deduplicated/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: deduplicatedExcelData
        }),
      });

      if (response.ok) {
        // Получаем blob с файлом
        const blob = await response.blob();
        
        // Создаем ссылку для скачивания
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Извлекаем имя файла из заголовков
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'Данные_Excel_без_дублей.xlsx';
        if (contentDisposition) {
          const match = contentDisposition.match(/filename="(.+)"/);
          if (match) filename = match[1];
        }
        
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        message.success('Файл успешно экспортирован');
      } else {
        const errorData = await response.json();
        message.error(errorData.error || 'Ошибка при экспорте');
      }
    } catch (error) {
      message.error('Ошибка подключения к серверу');
    }
  };

  // Функция для экспорта списка к производству
  const handleExportProductionList = async () => {
    if (filteredProductionData.length === 0) {
      message.warning('Нет данных для экспорта');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/tochka/export-production/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: filteredProductionData
        }),
      });

      if (response.ok) {
        // Получаем blob с файлом
        const blob = await response.blob();
        
        // Создаем ссылку для скачивания
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Извлекаем имя файла из заголовков
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'Список_к_производству.xlsx';
        if (contentDisposition) {
          const match = contentDisposition.match(/filename="(.+)"/);
          if (match) filename = match[1];
        }
        
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        message.success('Файл успешно экспортирован');
      } else {
        const errorData = await response.json();
        message.error(errorData.error || 'Ошибка при экспорте');
      }
    } catch (error) {
      message.error('Ошибка подключения к серверу');
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
      sorter: (a: any, b: any) => a.article.localeCompare(b.article),
      ...getColumnSearchProps('article'),
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
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
      sorter: (a: any, b: any) => a.name.localeCompare(b.name),
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
      sorter: (a: any, b: any) => a.product_name.localeCompare(b.product_name),
      render: (name: string) => <span style={{ color: '#1890ff' }}>{name}</span>,
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
      title: 'Продажи 2 мес',
      dataIndex: 'sales_last_2_months',
      key: 'sales_last_2_months',
      width: 110,
      sorter: (a: any, b: any) => a.sales_last_2_months - b.sales_last_2_months,
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
        {excelData.length > 0 && (
          <>
            <Col>
              <Button 
                type="primary"
                icon={<AppstoreOutlined />}
                onClick={handleMergeWithProducts}
                loading={mergeLoading}
                style={{ backgroundColor: '#722ed1', borderColor: '#722ed1' }}
              >
                Анализ производства
              </Button>
            </Col>
            <Col>
              <Button 
                type="default"
                icon={<UnorderedListOutlined />}
                onClick={handleGetFilteredProduction}
                loading={filterLoading}
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' }}
              >
                Список к производству
              </Button>
            </Col>
            <Col>
              <Button 
                type="default"
                icon={<FileExcelOutlined />}
                onClick={() => {
                  const element = document.querySelector('[title*="без дублей"]')?.parentElement?.parentElement;
                  if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  }
                }}
                style={{ backgroundColor: '#13c2c2', borderColor: '#13c2c2', color: 'white' }}
                size="small"
              >
                📊 Дедупликация
              </Button>
            </Col>
          </>
        )}
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
          style={{ marginBottom: 24 }}
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

        {/* Таблица анализа производства */}
        {mergedData.length > 0 && (
          <Card 
            title={`Список на производство с анализом Точки (${mergedData.length} товаров)`}
            extra={
              <div>
                <Tag color="purple">К производству</Tag>
                <Tag color="green">
                  {mergedData.filter((item: any) => item.is_in_tochka).length} есть в Точке
                </Tag>
                <Tag color="red" style={{ fontWeight: 'bold' }}>
                  {mergedData.filter((item: any) => item.needs_registration).length} НЕТ в Точке!
                </Tag>
              </div>
            }
            style={{ marginBottom: 24 }}
          >
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
          </Card>
        )}

        {/* Таблица данных из Excel */}
        {excelData.length > 0 && mergedData.length === 0 && (
          <Card 
            title={`Данные из Excel (${excelData.length} уникальных артикулов)`}
            extra={
              <div>
                <Tag color="green">Артикул + Заказы</Tag>
                {excelData.some((item: any) => item.has_duplicates) && (
                  <Tag color="orange">Дубликаты объединены</Tag>
                )}
              </div>
            }
          >
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
          </Card>
        )}

        {/* Таблица дедуплицированных данных Excel */}
        {deduplicatedExcelData.length > 0 && (
          <Card 
            title={`Данные Excel без дублей (${deduplicatedExcelData.length} уникальных артикулов)`}
            extra={
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
                  style={{ backgroundColor: '#13c2c2', borderColor: '#13c2c2' }}
                >
                  Экспорт в Excel
                </Button>
              </div>
            }
            style={{ marginBottom: 24 }}
          >
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
          </Card>
        )}

        {/* Таблица отфильтрованного списка производства */}
        {filteredProductionData.length > 0 && (
          <Card 
            title={`Список к производству (${filteredProductionData.length} товаров)`}
            extra={
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
                  style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                >
                  Экспорт в Excel
                </Button>
              </div>
            }
            style={{ marginBottom: 24 }}
          >
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
            disabled={uploadLoading}
            style={{ 
              opacity: uploadLoading ? 0.6 : 1,
              pointerEvents: uploadLoading ? 'none' : 'auto'
            }}
          >
            <p className="ant-upload-drag-icon">
              <FileExcelOutlined 
                style={{ 
                  fontSize: 48, 
                  color: uploadLoading ? '#d9d9d9' : '#52c41a' 
                }} 
              />
            </p>
            <p className="ant-upload-text">
              {uploadLoading 
                ? 'Обрабатываем файл...' 
                : 'Нажмите или перетащите Excel файл в эту область'
              }
            </p>
            <p className="ant-upload-hint">
              {uploadLoading 
                ? 'Пожалуйста, подождите...' 
                : 'Поддерживаются форматы .xlsx и .xls'
              }
            </p>
          </Upload.Dragger>
          
          {uploadLoading && (
            <div style={{ textAlign: 'center', marginTop: 20 }}>
              <Spin />
              <p style={{ marginTop: 10 }}>Обработка файла...</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};