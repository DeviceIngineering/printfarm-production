import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Button, Typography, Avatar } from 'antd';
import { 
  AppstoreOutlined, 
  BarChartOutlined, 
  SettingOutlined,
  SyncOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { SyncButton } from '../sync/SyncButton';
import './Layout.css';

const { Header, Sider, Content } = AntLayout;
const { Title } = Typography;

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/products',
      icon: <AppstoreOutlined />,
      label: 'Товары',
    },
    {
      key: '/reports',
      icon: <BarChartOutlined />,
      label: 'Отчеты',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Настройки',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  return (
    <AntLayout className="printfarm-layout" style={{ minHeight: '100vh' }}>
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        className="printfarm-sider"
      >
        <div className="printfarm-logo">
          <div className="logo-icon">🏭</div>
          {!collapsed && <div className="logo-text">PrintFarm</div>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="printfarm-menu"
        />
      </Sider>
      <AntLayout>
        <Header className="printfarm-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="collapse-btn"
            />
            <Title level={4} className="page-title">
              PrintFarm Production System
            </Title>
          </div>
          <div className="header-right">
            <SyncButton />
            <Avatar className="user-avatar">A</Avatar>
          </div>
        </Header>
        <Content className="printfarm-content" style={{ padding: '24px' }}>
          <div className="content-wrapper">
            {children}
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
};