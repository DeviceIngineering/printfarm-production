/**
 * Таблица отфильтрованного списка производства (только товары в Точке)
 * Включает поддержку SimplePrint данных
 */
import React from 'react';
import { Tag, Button } from 'antd';
import { FileExcelOutlined } from '@ant-design/icons';
import { CollapsibleTableCard } from './CollapsibleTableCard';
import { getFilteredProductionColumns } from '../utils';
import type { TablesCollapsedState } from '../hooks';

interface FilteredProductionTableProps {
  data: any[];
  enrichedData: any[];
  showSimpleprintColumns: boolean;
  collapsed: boolean;
  onToggleCollapse: () => void;
  pageSize: number;
  onPageSizeChange: (size: number) => void;
  onEnrichFromSimplePrint: () => void;
  onExport: () => void;
  exportLoading: boolean;
  getColumnSearchProps: any;
  getColumnFilterProps: any;
}

export const FilteredProductionTable: React.FC<FilteredProductionTableProps> = ({
  data,
  enrichedData,
  showSimpleprintColumns,
  collapsed,
  onToggleCollapse,
  pageSize,
  onPageSizeChange,
  onEnrichFromSimplePrint,
  onExport,
  exportLoading,
  getColumnSearchProps,
  getColumnFilterProps,
}) => {
  if (data.length === 0) {
    return null;
  }

  // Рассчитываем общее количество к производству
  const totalProduction = data.reduce((sum: number, item: any) => {
    const value = parseFloat(item.production_needed) || 0;
    return sum + value;
  }, 0).toFixed(0);

  // Определяем какие данные отображать
  const displayData = showSimpleprintColumns ? enrichedData : data;

  // Получаем колонки
  const columns = getFilteredProductionColumns(
    getColumnSearchProps,
    getColumnFilterProps,
    data,
    showSimpleprintColumns
  );

  // Дополнительные элементы в заголовке
  const extra = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <Tag color="green">✅ Только товары в Точке</Tag>
      <Tag color="blue">{totalProduction} шт всего</Tag>
      {showSimpleprintColumns && (
        <Tag color="purple">📊 Данные SimplePrint загружены</Tag>
      )}
      <Button
        type="default"
        size="small"
        onClick={onEnrichFromSimplePrint}
        disabled={showSimpleprintColumns}
        style={{ borderColor: '#722ed1', color: '#722ed1' }}
      >
        {showSimpleprintColumns ? '✓ Дополнено из SP' : 'Дополнить из SP'}
      </Button>
      <Button
        type="primary"
        size="small"
        icon={<FileExcelOutlined />}
        onClick={onExport}
        loading={exportLoading}
        style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
      >
        Экспорт в Excel
      </Button>
    </div>
  );

  return (
    <CollapsibleTableCard
      title={`Список к производству (${data.length} товаров)`}
      tableKey="filteredProduction"
      collapsed={collapsed}
      onToggleCollapse={onToggleCollapse}
      extra={extra}
      dataSource={displayData}
      columns={columns}
      rowKey={(record, index) => `filtered-${index}`}
      pageSize={pageSize}
      onPageSizeChange={onPageSizeChange}
      scrollX={showSimpleprintColumns ? 1300 : 1000}
      style={{ marginBottom: 24 }}
    />
  );
};
