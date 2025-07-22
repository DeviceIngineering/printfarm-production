import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Switch, 
  Select, 
  Checkbox,
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
import { syncApi, ProductGroup } from '../../api/sync';

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
  const [productGroups, setProductGroups] = useState<ProductGroup[]>([]);
  const [productGroupsLoading, setProductGroupsLoading] = useState(false);

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

  // Загрузка списка групп товаров
  const loadProductGroups = async () => {
    setProductGroupsLoading(true);
    try {
      console.log('🔄 Загрузка групп товаров...');
      const response = await syncApi.getProductGroupsFromSettings();
      console.log('📦 Ответ API групп товаров:', response);
      
      const groupsList = response.product_groups || [];
      console.log(`✅ Загружено групп товаров: ${groupsList.length}`);
      
      setProductGroups(groupsList);
      
      if (groupsList.length === 0) {
        message.warning('Список групп товаров пуст');
      }
    } catch (error) {
      console.error('❌ Ошибка загрузки групп товаров:', error);
      const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка';
      message.error(`Ошибка загрузки списка групп товаров: ${errorMessage}`);
      setProductGroups([]);
    } finally {
      setProductGroupsLoading(false);
    }
  };

  useEffect(() => {
    loadWarehouses();
    loadProductGroups();
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
            title="Следующая синхронизация" 
            value={
              syncSettings?.sync_enabled && syncSettings?.next_sync_time 
                ? new Date(syncSettings.next_sync_time).toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })
                : syncSettings?.sync_enabled 
                  ? 'Рассчитывается...'
                  : 'Отключена'
            }
            valueStyle={{
              fontSize: '14px',
              color: syncSettings?.sync_enabled 
                ? syncSettings?.next_sync_time 
                  ? '#1890ff' 
                  : '#faad14'
                : '#999'
            }}
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

        {/* Исключаемые группы товаров */}
        <Row>
          <Col span={24}>
            <Form.Item 
              name="excluded_group_ids" 
              label={
                <div>
                  Исключить группы товаров из синхронизации
                  {productGroups.length > 0 && (
                    <span style={{ fontWeight: 'normal', color: '#666', marginLeft: 8 }}>
                      (всего групп: {productGroups.length})
                    </span>
                  )}
                </div>
              }
            >
              {productGroupsLoading ? (
                <div style={{ color: '#999', fontStyle: 'italic', padding: '8px 0' }}>Загрузка групп товаров...</div>
              ) : productGroups.length === 0 ? (
                <div style={{ color: '#999', fontStyle: 'italic', padding: '8px 0' }}>
                  Группы товаров не найдены
                  <Button 
                    size="small" 
                    type="link" 
                    icon={<ReloadOutlined />}
                    onClick={loadProductGroups}
                    loading={productGroupsLoading}
                    style={{ padding: '0 8px' }}
                  >
                    Обновить
                  </Button>
                </div>
              ) : (
                <Checkbox.Group style={{ width: '100%' }}>
                  <div style={{ 
                    maxHeight: 300, 
                    overflowY: 'auto', 
                    border: '1px solid #d9d9d9', 
                    borderRadius: '6px',
                    padding: '8px 12px'
                  }}>
                    <Space direction="vertical" style={{ width: '100%' }} size={8}>
                      {productGroups.map(group => (
                        <Checkbox key={group.id} value={group.id}>
                          <div>
                            <div style={{ fontWeight: 500 }}>{group.name}</div>
                            {group.pathName !== group.name && (
                              <div style={{ fontSize: '12px', color: '#666' }}>
                                {group.pathName}
                              </div>
                            )}
                          </div>
                        </Checkbox>
                      ))}
                    </Space>
                  </div>
                </Checkbox.Group>
              )}
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

      {/* Информация о синхронизации */}
      {(syncSettings?.last_sync_at || syncSettings?.next_sync_time) && (
        <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
          {syncSettings.last_sync_at && (
            <div style={{ marginBottom: 8 }}>
              <strong>Последняя синхронизация:</strong> {new Date(syncSettings.last_sync_at).toLocaleString('ru-RU')}
              {syncSettings.last_sync_message && (
                <div style={{ marginTop: 4, color: '#666' }}>
                  {syncSettings.last_sync_message}
                </div>
              )}
            </div>
          )}
          {syncSettings.sync_enabled && syncSettings.next_sync_time && (
            <div>
              <strong>Следующая синхронизация:</strong> {new Date(syncSettings.next_sync_time).toLocaleString('ru-RU')}
              <div style={{ marginTop: 4, color: '#666' }}>
                Интервал: {syncSettings.sync_interval_display}
              </div>
            </div>
          )}
          {syncSettings.sync_enabled && !syncSettings.next_sync_time && (
            <div>
              <strong>Следующая синхронизация:</strong> <span style={{ color: '#faad14' }}>Рассчитывается...</span>
            </div>
          )}
          {!syncSettings.sync_enabled && (
            <div style={{ color: '#999' }}>
              Автоматическая синхронизация отключена
            </div>
          )}
        </div>
      )}
    </Card>
  );
};