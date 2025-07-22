import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Switch, 
  Select, 
 
  Button, 
  Row, 
  Col, 
  Statistic, 
  Tag,
  message,
  Space
} from 'antd';
import { SyncOutlined, CheckCircleOutlined, ExclamationCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { SyncSettings, settingsApi, Warehouse } from '../../api/settings';

interface SyncSettingsCardProps {
  syncSettings: SyncSettings | null;
  loading?: boolean;
  onUpdate?: (settings: SyncSettings) => void;
}

export const SyncSettingsCard: React.FC<SyncSettingsCardProps> = ({ 
  syncSettings, 
  loading = false,
  onUpdate 
}) => {
  const [form] = Form.useForm();
  const [updating, setUpdating] = useState(false);
  const [testing, setTesting] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [warehousesLoading, setWarehousesLoading] = useState(false);

  // Загрузка списка складов
  const loadWarehouses = async () => {
    setWarehousesLoading(true);
    try {
      console.log('🔄 Загрузка складов...');
      const response = await settingsApi.getWarehouses();
      console.log('📦 Ответ API складов:', response);
      
      const warehousesList = response.warehouses || [];
      console.log(`✅ Загружено складов: ${warehousesList.length}`);
      
      setWarehouses(warehousesList);
      
      if (warehousesList.length === 0) {
        message.warning('Список складов пуст');
      }
    } catch (error) {
      console.error('❌ Ошибка загрузки складов:', error);
      const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка';
      message.error(`Ошибка загрузки списка складов: ${errorMessage}`);
      setWarehouses([]); // Устанавливаем пустой массив при ошибке
    } finally {
      setWarehousesLoading(false);
    }
  };

  useEffect(() => {
    loadWarehouses();
  }, []);

  const handleUpdate = async (values: any) => {
    setUpdating(true);
    try {
      const updated = await settingsApi.updateSyncSettings(values);
      message.success('Настройки синхронизации обновлены');
      onUpdate?.(updated);
    } catch (error) {
      message.error('Ошибка обновления настроек');
    } finally {
      setUpdating(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const result = await settingsApi.testSyncConnection();
      if (result.success) {
        message.success('Соединение с МойСклад успешно');
      } else {
        message.error(result.message || 'Ошибка подключения');
      }
    } catch (error) {
      message.error('Ошибка тестирования соединения');
    } finally {
      setTesting(false);
    }
  };

  const handleTriggerSync = async () => {
    setTriggering(true);
    try {
      const result = await settingsApi.triggerManualSync();
      if (result.success) {
        message.success('Синхронизация запущена');
      } else {
        message.error(result.message || 'Ошибка запуска синхронизации');
      }
    } catch (error) {
      message.error('Ошибка запуска синхронизации');
    } finally {
      setTriggering(false);
    }
  };

  const intervalOptions = [
    { value: 30, label: '30 минут' },
    { value: 60, label: '1 час' },
    { value: 90, label: '1.5 часа' },
    { value: 120, label: '2 часа' },
    { value: 180, label: '3 часа' },
    { value: 240, label: '4 часа' },
    { value: 360, label: '6 часов' },
    { value: 720, label: '12 часов' },
    { value: 1440, label: '24 часа' },
  ];

  const getStatusColor = (rate: number) => {
    if (rate >= 90) return 'success';
    if (rate >= 70) return 'warning';
    return 'error';
  };

  return (
    <Card 
      title={
        <span>
          <SyncOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Настройки синхронизации
        </span>
      }
      loading={loading}
      extra={
        <Space>
          <Button 
            icon={<CheckCircleOutlined />}
            onClick={handleTestConnection}
            loading={testing}
            size="small"
          >
            Тест
          </Button>
          <Button 
            icon={<SyncOutlined />}
            onClick={handleTriggerSync}
            loading={triggering}
            size="small"
            type="primary"
          >
            Синхронизация
          </Button>
        </Space>
      }
    >
      {/* Статистика */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Statistic 
            title="Статус" 
            value={syncSettings?.sync_enabled ? 'Включена' : 'Отключена'}
            prefix={
              <Tag color={syncSettings?.sync_enabled ? 'green' : 'red'}>
                {syncSettings?.sync_enabled ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}
              </Tag>
            }
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Интервал" 
            value={syncSettings?.sync_interval_display || 'Не настроен'}
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Всего синхронизаций" 
            value={syncSettings?.total_syncs || 0}
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Успешность" 
            value={`${syncSettings?.sync_success_rate || 0}%`}
            valueStyle={{ color: getStatusColor(syncSettings?.sync_success_rate || 0) === 'success' ? '#3f8600' : 
                                getStatusColor(syncSettings?.sync_success_rate || 0) === 'warning' ? '#cf1322' : '#cf1322' }}
          />
        </Col>
      </Row>

      {/* Форма настроек */}
      <Form
        form={form}
        layout="vertical"
        initialValues={syncSettings || undefined}
        onFinish={handleUpdate}
      >
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item 
              name="sync_enabled" 
              label="Автоматическая синхронизация" 
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item 
              name="sync_interval_minutes" 
              label="Интервал синхронизации"
            >
              <Select options={intervalOptions} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item 
              name="warehouse_id" 
              label="Склад"
              rules={[{ required: true, message: 'Выберите склад' }]}
            >
              <Select 
                placeholder="Выберите склад"
                loading={warehousesLoading}
                showSearch
                optionFilterProp="children"
                filterOption={(input, option) =>
                  (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                }
                notFoundContent={warehousesLoading ? 'Загрузка...' : 'Склады не найдены'}
                dropdownRender={menu => (
                  <>
                    {menu}
                    <div style={{ padding: '8px', borderTop: '1px solid #f0f0f0' }}>
                      <Button 
                        size="small" 
                        type="text" 
                        icon={<ReloadOutlined />}
                        onClick={loadWarehouses}
                        loading={warehousesLoading}
                        block
                      >
                        Обновить список
                      </Button>
                    </div>
                  </>
                )}
              >
                {warehouses && warehouses.map(warehouse => (
                  <Select.Option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name}
                    {warehouse.description && (
                      <span style={{ color: '#999', fontSize: '12px', marginLeft: 8 }}>
                        ({warehouse.description})
                      </span>
                    )}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={updating}
            style={{ background: 'var(--color-primary)' }}
          >
            Сохранить настройки
          </Button>
        </Form.Item>
      </Form>

      {/* Информация о последней синхронизации */}
      {syncSettings?.last_sync_at && (
        <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
          <strong>Последняя синхронизация:</strong> {new Date(syncSettings.last_sync_at).toLocaleString('ru-RU')}
          {syncSettings.last_sync_message && (
            <div style={{ marginTop: 4, color: '#666' }}>
              {syncSettings.last_sync_message}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};