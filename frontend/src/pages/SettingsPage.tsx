import React from 'react';
import { Typography, Row, Col, Spin, Alert, Button, Space } from 'antd';
import { SettingOutlined, ReloadOutlined } from '@ant-design/icons';
import { useSettings } from '../hooks/useSettings';
import { SystemInfo } from '../components/settings/SystemInfo';
import { SyncSettingsCard } from '../components/settings/SyncSettingsCard';

const { Title } = Typography;

export const SettingsPage: React.FC = () => {
  const { 
    summary, 
    syncSettings, 
    loading, 
    error, 
    updateSyncSettings,
    refresh 
  } = useSettings();

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Загрузка настроек...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <Alert
          message="Ошибка загрузки настроек"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={refresh}>
              Повторить
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      {/* Заголовок */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>
          <SettingOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Настройки системы
        </Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={refresh}
            loading={loading}
          >
            Обновить
          </Button>
        </Space>
      </div>

      {/* Информация о системе */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <SystemInfo 
            systemInfo={summary?.system_info || null} 
            loading={loading} 
          />
        </Col>
      </Row>

      {/* Настройки синхронизации */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <SyncSettingsCard 
            syncSettings={syncSettings}
            loading={loading}
            onUpdate={updateSyncSettings}
          />
        </Col>
      </Row>

    </div>
  );
};