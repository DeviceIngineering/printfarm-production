/**
 * Колонки для отфильтрованного списка производства (только товары в Точке)
 * Вынесено в отдельный файл из-за сложности с SimplePrint колонками
 */
import React from 'react';
import { Tag } from 'antd';

/**
 * Функция для форматирования времени печати (секунды -> часы:минуты)
 */
const formatPrintTime = (seconds: number): string => {
  if (!seconds || seconds === 0) return '—';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}ч ${minutes}м`;
  }
  return `${minutes}м`;
};

/**
 * Колонки для отфильтрованного списка производства
 */
export const getFilteredProductionColumns = (
  getColumnSearchProps: any,
  getColumnFilterProps: any,
  filteredProductionData: any[],
  showSimpleprintColumns: boolean
) => {
  // Базовые колонки
  const baseColumns = [
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

  // SimplePrint колонки - показываются только при нажатии "Дополнить из SP"
  const simpleprintColumns = showSimpleprintColumns ? [
    {
      title: 'Время макс',
      dataIndex: 'sp_max_print_time',
      key: 'sp_max_print_time',
      width: 110,
      sorter: (a: any, b: any) => (a.sp_max_print_time || 0) - (b.sp_max_print_time || 0),
      render: (value: number | null, record: any) => {
        if (!value || value === 0) {
          return <span style={{ color: '#999', fontStyle: 'italic' }}>—</span>;
        }

        return (
          <span
            style={{
              color: record.has_sp_data ? '#722ed1' : '#999',
              fontWeight: record.has_sp_data ? 'bold' : 'normal'
            }}
            title={`${value} секунд`}
          >
            {formatPrintTime(value)}
          </span>
        );
      },
    },
    {
      title: 'Кол. макс',
      dataIndex: 'sp_max_quantity',
      key: 'sp_max_quantity',
      width: 100,
      sorter: (a: any, b: any) => (a.sp_max_quantity || 0) - (b.sp_max_quantity || 0),
      render: (value: number | null, record: any) => {
        if (!value || value === 0) {
          return <span style={{ color: '#999', fontStyle: 'italic' }}>—</span>;
        }

        return (
          <span
            style={{
              color: record.has_sp_data ? '#722ed1' : '#999',
              fontWeight: record.has_sp_data ? 'bold' : 'normal'
            }}
          >
            {value} шт
          </span>
        );
      },
    },
  ] : [];

  return [...baseColumns, ...simpleprintColumns];
};
