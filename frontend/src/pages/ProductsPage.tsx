import React, { useEffect, useState } from 'react';
import { Typography, Tabs, Space } from 'antd';
import { AppstoreOutlined, UnorderedListOutlined } from '@ant-design/icons';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchProductStats } from '../store/products';
import { ProductTable } from '../components/products/ProductTable';
import { ProductionListView } from '../components/products/ProductionListView';
import { SyncButton } from '../components/sync/SyncButton';

const { Title } = Typography;
const { TabPane } = Tabs;

export const ProductsPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [activeTab, setActiveTab] = useState('products');
  const { status } = useSelector((state: RootState) => state.sync);

  useEffect(() => {
    dispatch(fetchProductStats());
  }, [dispatch]);

  // Refresh products when sync completes
  useEffect(() => {
    const lastSyncTime = status?.last_sync;
    
    if (status && !status.is_syncing && lastSyncTime) {
      // Check if this is a new sync completion
      const lastSyncTimestamp = new Date(lastSyncTime).getTime();
      const lastCheckTimestamp = localStorage.getItem('lastSyncCheck');
      
      if (!lastCheckTimestamp || lastSyncTimestamp > parseInt(lastCheckTimestamp)) {
        console.log('New sync completed, refreshing product data...');
        
        // Update last check timestamp
        localStorage.setItem('lastSyncCheck', lastSyncTimestamp.toString());
        
        // Refresh product statistics
        dispatch(fetchProductStats());
        
        // Small delay to ensure backend has finished processing all data
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      }
    }
  }, [status?.is_syncing, status?.last_sync, dispatch]);

  // Store auth token for demo
  useEffect(() => {
    const token = '549ebaf641ffa608a26b79a21d72a296c99a02b7';
    localStorage.setItem('auth_token', token);
  }, []);

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2} style={{ margin: 0 }}>
          <AppstoreOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Управление производством
        </Title>
        <SyncButton />
      </div>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
        <TabPane
          tab={
            <Space>
              <AppstoreOutlined />
              <span>Товары</span>
            </Space>
          }
          key="products"
        >
          <ProductTable />
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <UnorderedListOutlined />
              <span>Список на производство</span>
            </Space>
          }
          key="production"
        >
          <ProductionListView />
        </TabPane>
      </Tabs>
    </div>
  );
};