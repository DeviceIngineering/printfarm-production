import React from 'react';
import { Card, Typography } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';

const { Title } = Typography;

export const ReportsPage: React.FC = () => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>
        <FileTextOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
        Отчеты
      </Title>
      
      <Card title="Доступные отчеты">
        <p>Система отчетов находится в разработке.</p>
        <p>API endpoint: GET /api/v1/reports/</p>
      </Card>
    </div>
  );
};