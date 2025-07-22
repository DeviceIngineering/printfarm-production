import React, { useState, useEffect } from 'react';
import { Button, Modal, Form, Select, Checkbox, Space, Tag, Progress, message, Spin } from 'antd';
import { SyncOutlined, LoadingOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { fetchWarehouses, fetchProductGroups, startSync, fetchSyncStatus } from '../../store/sync';

const { Option } = Select;

export const SyncButton: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { warehouses, productGroups, status, loading, warehousesLoading, productGroupsLoading } = useSelector((state: RootState) => state.sync);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [syncInterval, setSyncInterval] = useState<NodeJS.Timer | null>(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState<string>('');
  const [lastExcludedGroups, setLastExcludedGroups] = useState<string[]>([]);

  useEffect(() => {
    // Load warehouses and product groups when component mounts
    console.log('SyncButton mounted, loading data...');
    dispatch(fetchWarehouses());
    dispatch(fetchProductGroups());
    
    // Check sync status
    dispatch(fetchSyncStatus());
    
    // Load saved excluded groups from localStorage
    const savedExcludedGroups = localStorage.getItem('sync_excluded_groups');
    if (savedExcludedGroups) {
      try {
        const groups = JSON.parse(savedExcludedGroups);
        setLastExcludedGroups(groups);
      } catch (error) {
        console.error('Error parsing saved excluded groups:', error);
      }
    }
  }, [dispatch]);

  useEffect(() => {
    console.log('Warehouses updated:', warehouses);
    console.log('Loading state:', warehousesLoading);
  }, [warehouses, warehousesLoading]);

  useEffect(() => {
    // Poll sync status if syncing
    if (status?.is_syncing) {
      const interval = setInterval(() => {
        dispatch(fetchSyncStatus());
      }, 2000);
      setSyncInterval(interval);
    } else if (syncInterval) {
      clearInterval(syncInterval);
      setSyncInterval(null);
    }

    return () => {
      if (syncInterval) {
        clearInterval(syncInterval);
      }
    };
  }, [status?.is_syncing, dispatch]);

  const handleStartSync = async () => {
    try {
      const values = await form.validateFields();
      console.log('Starting sync with values:', values);
      
      // Store selected warehouse name for display
      const warehouse = warehouses.find(w => w.id === values.warehouse_id);
      setSelectedWarehouse(warehouse?.name || '');
      
      // Save excluded groups to localStorage
      const excludedGroups = values.excluded_groups || [];
      localStorage.setItem('sync_excluded_groups', JSON.stringify(excludedGroups));
      setLastExcludedGroups(excludedGroups);
      
      // Start actual sync
      const result = await dispatch(startSync({
        warehouse_id: values.warehouse_id,
        excluded_groups: excludedGroups,
        sync_images: values.sync_images === true // По умолчанию false
      })).unwrap();
      
      console.log('Sync result:', result);
      
      if ((result as any).status === 'success') {
        // Synchronous mode - sync completed
        message.success(`Синхронизация завершена! Загружено ${(result as any).synced_products} из ${(result as any).total_products} товаров.`);
        setModalVisible(false);
        form.resetFields();
        setSelectedWarehouse('');
        
        // Refresh status to update UI
        dispatch(fetchSyncStatus());
      } else {
        // Asynchronous mode - sync started
        message.success('Синхронизация запущена!');
        setModalVisible(false);
        form.resetFields();
        setSelectedWarehouse('');
        
        // Start polling for status
        dispatch(fetchSyncStatus());
      }
    } catch (error: any) {
      console.error('Sync start error:', error);
      message.error(`Ошибка запуска синхронизации: ${error.message || 'Неизвестная ошибка'}`);
    }
  };

  const handleModalOpen = () => {
    setModalVisible(true);
    // Data is already loaded on component mount
    // Only refresh if needed
    if (warehouses.length === 0) {
      dispatch(fetchWarehouses());
    }
    if (productGroups.length === 0) {
      dispatch(fetchProductGroups());
    }
  };

  const renderSyncStatus = () => {
    if (!status?.is_syncing) return null;

    const progress = (status.total_products || 0) > 0 
      ? ((status.synced_products || 0) / (status.total_products || 0)) * 100 
      : 0;

    return (
      <Space direction="vertical" size="small" style={{ minWidth: 300 }}>
        <Space>
          <LoadingOutlined spin />
          <span>Синхронизация товаров...</span>
        </Space>
        <Progress 
          percent={Math.round(progress)} 
          status="active"
          size="small"
          showInfo={false}
        />
        <Space split={<span style={{ color: '#ccc' }}>•</span>}>
          <span><strong>{status.synced_products || 0}</strong> / <strong>{status.total_products || 0}</strong> товаров</span>
          {selectedWarehouse && <span>Склад: {selectedWarehouse}</span>}
          {status.current_article && (
            <span title={`Текущий артикул: ${status.current_article}`}>
              Артикул: <code style={{ fontSize: '11px', background: '#f0f0f0', padding: '1px 3px', borderRadius: '2px' }}>
                {status.current_article}
              </code>
            </span>
          )}
        </Space>
      </Space>
    );
  };

  return (
    <>
      <Space>
        {status?.is_syncing ? (
          renderSyncStatus()
        ) : (
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={handleModalOpen}
            loading={loading}
            className="btn-primary"
          >
            Ручная синхронизация
          </Button>
        )}
        
        {status?.last_sync && !status.is_syncing && (
          <Tag color="blue">
            Последняя: {new Date(status.last_sync).toLocaleString('ru-RU')}
          </Tag>
        )}
      </Space>

      <Modal
        title={
          <Space>
            {loading && <LoadingOutlined spin />}
            {loading ? "Выполняется синхронизация с МойСклад" : "Синхронизация с МойСклад"}
          </Space>
        }
        open={modalVisible}
        onOk={handleStartSync}
        onCancel={() => {
          if (!loading) {
            setModalVisible(false);
            setSelectedWarehouse('');
          }
        }}
        okText={loading ? "Синхронизация..." : "Начать синхронизацию"}
        cancelText={loading ? "Подождите..." : "Отмена"}
        cancelButtonProps={{ disabled: loading }}
        width={600}
        confirmLoading={loading}
        closable={!loading}
        maskClosable={!loading}
      >
        {loading && (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px',
            background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid var(--color-primary)',
            boxShadow: '0 2px 8px rgba(6, 234, 252, 0.1)'
          }}>
            <Spin size="large" style={{ color: 'var(--color-primary)' }} />
            <div style={{ 
              marginTop: '16px', 
              fontSize: '16px', 
              color: '#262626',
              fontWeight: 500
            }}>
              Синхронизация данных с МойСклад
            </div>
            <div style={{ 
              marginTop: '8px', 
              fontSize: '14px', 
              color: '#595959',
              lineHeight: '1.4'
            }}>
              {selectedWarehouse && (
                <div style={{ marginBottom: '4px', fontWeight: 500 }}>
                  Склад: {selectedWarehouse}
                </div>
              )}
              {status?.is_syncing && (
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ fontWeight: 500, color: '#262626' }}>
                    Обработано: {status.synced_products || 0} из {status.total_products || 0} товаров
                  </div>
                  {status.current_article && (
                    <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '2px' }}>
                      Текущий артикул: <code style={{ background: '#f0f0f0', padding: '1px 4px', borderRadius: '2px' }}>
                        {status.current_article}
                      </code>
                    </div>
                  )}
                </div>
              )}
              {!status?.is_syncing && 'Загружаем товары, остатки и данные об оборотах...'}
            </div>
            <div style={{ 
              marginTop: '4px', 
              fontSize: '12px', 
              color: '#8c8c8c'
            }}>
              Обычно занимает 1-3 минуты
            </div>
            
            {/* Animated progress dots */}
            <div style={{ 
              marginTop: '12px',
              display: 'flex',
              justifyContent: 'center',
              gap: '4px'
            }}>
              {[0, 1, 2].map(i => (
                <div
                  key={i}
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: 'var(--color-primary)',
                    animation: `pulse 1.5s ease-in-out ${i * 0.2}s infinite`,
                    opacity: 0.6
                  }}
                />
              ))}
            </div>
          </div>
        )}
        
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            warehouse_id: warehouses.length > 0 ? warehouses[0].id : undefined,
            sync_images: false, // По умолчанию выключено
            excluded_groups: lastExcludedGroups // Восстанавливаем предыдущий выбор
          }}
          key={`${warehouses.length}-${lastExcludedGroups.length}`} // Force re-render when data changes
          style={{ opacity: loading ? 0.6 : 1, pointerEvents: loading ? 'none' : 'auto' }}
        >
          <Form.Item
            name="warehouse_id"
            label="Склад"
            rules={[{ required: true, message: 'Выберите склад' }]}
          >
            <Select 
              placeholder="Выберите склад" 
              loading={warehousesLoading}
              notFoundContent={warehousesLoading ? "Загрузка..." : "Нет данных"}
            >
              {warehouses.map(warehouse => (
                <Option key={warehouse.id} value={warehouse.id}>
                  {warehouse.name} ({warehouse.code})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="excluded_groups"
            label={
              <div>
                Исключить группы товаров
                {productGroups.length > 0 && (
                  <span style={{ fontWeight: 'normal', color: '#666', marginLeft: 8 }}>
                    (найдено: {productGroups.filter(g => !g.archived).length})
                  </span>
                )}
              </div>
            }
          >
            {productGroupsLoading ? (
              <div style={{ color: '#999', fontStyle: 'italic' }}>Загрузка групп товаров...</div>
            ) : productGroups.length === 0 ? (
              <div style={{ color: '#999', fontStyle: 'italic' }}>Группы товаров не найдены</div>
            ) : (
              <Checkbox.Group style={{ width: '100%' }}>
                <Space direction="vertical" style={{ maxHeight: 300, overflowY: 'auto', width: '100%' }}>
                  {productGroups
                    .filter(group => !group.archived) // Показываем только неархивные группы
                    .map(group => (
                      <Checkbox key={group.id} value={group.id}>
                        <div>
                          <div style={{ fontWeight: 500 }}>{group.name}</div>
                          {group.pathName !== group.name && (
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              {group.pathName}
                            </div>
                          )}
                          {group.code && (
                            <div style={{ fontSize: '11px', color: '#999' }}>
                              Код: {group.code}
                            </div>
                          )}
                        </div>
                      </Checkbox>
                    ))}
                </Space>
              </Checkbox.Group>
            )}
          </Form.Item>

          <Form.Item
            name="sync_images"
            valuePropName="checked"
            style={{ marginTop: '20px' }}
          >
            <Checkbox>
              <Space direction="vertical" size={0}>
                <div style={{ fontWeight: 500 }}>
                  Загружать изображения товаров
                </div>
                <div style={{ fontSize: '12px', color: '#666', marginLeft: 0 }}>
                  Изображения будут загружены автоматически для новых товаров (до 100 товаров за раз).
                  <br />
                  Остальные изображения можно загрузить через тестовую страницу изображений.
                </div>
              </Space>
            </Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};