/**
 * Определения колонок для всех таблиц TochkaPage
 * Вынесены в отдельный файл для лучшей организации и переиспользования
 */
import React from 'react';
import { Tag } from 'antd';

/**
 * Колонки для таблицы товаров
 */
export const getProductColumns = (getColumnSearchProps: any) => [
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

/**
 * Колонки для таблицы производства
 */
export const getProductionColumns = (getColumnSearchProps: any) => [
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

/**
 * Колонки для таблицы данных из Excel
 */
export const getExcelColumns = () => [
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

/**
 * Колонки для таблицы дедуплицированных данных из Excel
 */
export const getDeduplicatedExcelColumns = (getColumnSearchProps: any) => [
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

/**
 * Колонки для объединенной таблицы производства
 */
export const getMergedColumns = (getColumnSearchProps: any) => [
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

// Продолжение в следующем файле из-за ограничения размера...
