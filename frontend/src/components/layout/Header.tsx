import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { 
  AppstoreOutlined, 
  FileTextOutlined, 
  SettingOutlined,
  SyncOutlined,
  PictureOutlined
} from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

export const Header: React.FC = () => {
  const location = useLocation();

  const menuItems = [
    {
      key: '/products',
      icon: <AppstoreOutlined />,
      label: <Link to="/products">Товары</Link>,
    },
    {
      key: '/reports',
      icon: <FileTextOutlined />,
      label: <Link to="/reports">Отчеты</Link>,
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: <Link to="/settings">Настройки</Link>,
    },
    {
      key: '/test-images',
      icon: <PictureOutlined />,
      label: <Link to="/test-images">Тест изображений</Link>,
    },
  ];

  return (
    <AntHeader style={{ display: 'flex', alignItems: 'center' }}>
      <Title 
        level={3} 
        style={{ 
          color: 'var(--color-primary)', 
          margin: 0, 
          marginRight: 'auto',
          textShadow: 'var(--glow-primary)'
        }}
      >
        <SyncOutlined style={{ marginRight: 8 }} />
        PrintFarm Production
      </Title>
      
      <Menu
        theme="dark"
        mode="horizontal"
        selectedKeys={[location.pathname]}
        items={menuItems}
        style={{ 
          minWidth: 0, 
          flex: 1, 
          justifyContent: 'flex-end',
          background: 'transparent'
        }}
      />
    </AntHeader>
  );
};