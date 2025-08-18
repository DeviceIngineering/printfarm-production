import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import { 
  AppstoreOutlined, 
  FileTextOutlined, 
  SettingOutlined,
  ShopOutlined
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
      key: '/tochka',
      icon: <ShopOutlined />,
      label: <Link to="/tochka">Точка</Link>,
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
  ];

  return (
    <AntHeader style={{ display: 'flex', alignItems: 'center' }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        marginRight: 'auto' 
      }}>
        <img 
          src="/favicon.ico" 
          alt="PrintFarm Production" 
          style={{ 
            height: 32, 
            width: 32, 
            marginRight: 8 
          }} 
        />
        <Title 
          level={4} 
          style={{ 
            color: 'var(--color-primary)', 
            margin: 0,
            textShadow: 'var(--glow-primary)'
          }}
        >
          PrintFarm Production
        </Title>
      </div>
      
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