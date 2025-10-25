/**
 * Универсальный компонент карточки таблицы с возможностью сворачивания
 */
import React from 'react';
import { Card, Table, Button } from 'antd';
import { UpOutlined, DownOutlined } from '@ant-design/icons';
import type { TablesCollapsedState } from '../hooks';

interface CollapsibleTableCardProps {
  title: string;
  tableKey: keyof TablesCollapsedState;
  collapsed: boolean;
  onToggleCollapse: () => void;
  extra?: React.ReactNode;
  dataSource: any[];
  columns: any[];
  rowKey: string | ((record: any) => string);
  pageSize: number;
  onPageSizeChange: (size: number) => void;
  scrollX?: number;
  style?: React.CSSProperties;
}

export const CollapsibleTableCard: React.FC<CollapsibleTableCardProps> = ({
  title,
  tableKey,
  collapsed,
  onToggleCollapse,
  extra,
  dataSource,
  columns,
  rowKey,
  pageSize,
  onPageSizeChange,
  scrollX = 800,
  style,
}) => {
  // Создаем заголовок с кнопкой сворачивания
  const cardTitle = (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
      <span>{title}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {extra}
        <Button
          type="text"
          size="small"
          icon={collapsed ? <DownOutlined /> : <UpOutlined />}
          onClick={onToggleCollapse}
          style={{
            padding: '0 4px',
            color: '#1890ff',
            border: 'none'
          }}
          title={collapsed ? 'Развернуть таблицу' : 'Свернуть таблицу'}
        />
      </div>
    </div>
  );

  return (
    <Card
      title={cardTitle}
      style={style}
    >
      {!collapsed && (
        <Table
          dataSource={dataSource}
          columns={columns}
          rowKey={rowKey}
          pagination={{
            defaultPageSize: 20,
            pageSize: pageSize,
            showSizeChanger: true,
            showQuickJumper: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} из ${total} записей`,
            onShowSizeChange: (_current, size) => onPageSizeChange(size),
          }}
          scroll={{ x: scrollX }}
          size="small"
        />
      )}
    </Card>
  );
};
