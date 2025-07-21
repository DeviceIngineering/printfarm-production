import React from 'react';
import { Card, Statistic, Row, Col, Tag } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { SystemInfo as SystemInfoType } from '../../api/settings';

interface SystemInfoProps {
  systemInfo: SystemInfoType | null;
  loading?: boolean;
}

export const SystemInfo: React.FC<SystemInfoProps> = ({ systemInfo, loading = false }) => {
  return (
    <Card 
      title={
        <span>
          <InfoCircleOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Информация о системе
        </span>
      }
      loading={loading}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Statistic 
            title="Версия системы" 
            value={systemInfo?.version || 'Неизвестно'}
            prefix={<Tag color="cyan">v</Tag>}
          />
        </Col>
        <Col span={12}>
          <Statistic 
            title="Дата сборки" 
            value={systemInfo?.build_date || 'Неизвестно'}
          />
        </Col>
      </Row>
    </Card>
  );
};