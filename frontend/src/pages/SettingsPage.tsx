import React from 'react';
import { Card, Typography } from 'antd';
import { SettingOutlined } from '@ant-design/icons';

const { Title } = Typography;

export const SettingsPage: React.FC = () => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>
        <SettingOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
        Настройки
      </Title>
      
      <Card title="Конфигурация системы">
        <p>Интерфейс настроек находится в разработке.</p>
        <p>Настройки системы управляются через переменные окружения в .env файле.</p>
      </Card>
    </div>
  );
};