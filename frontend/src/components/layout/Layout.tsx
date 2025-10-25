import React from 'react';
import { Layout as AntLayout, Menu, Avatar } from 'antd';
import {
  AppstoreOutlined,
  BarChartOutlined,
  SettingOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  ProjectOutlined,
  ScheduleOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { SyncButton } from '../sync/SyncButton';
import './Layout.css';

const { Header, Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/products',
      icon: <AppstoreOutlined />,
      label: 'Товары',
    },
    {
      key: '/tochka',
      icon: <DatabaseOutlined />,
      label: 'Точка',
    },
    {
      key: '/planning',
      icon: <ProjectOutlined />,
      label: 'Планирование',
    },
    {
      key: '/planningv2',
      icon: <ScheduleOutlined />,
      label: 'Планирование в2',
    },
    {
      key: '/simpleprint',
      icon: <CloudServerOutlined />,
      label: 'SimplePrint',
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
      <Header className="printfarm-header">
        <div className="header-left">
          <div className="printfarm-logo">
            <div className="logo-icon">🏭</div>
            <div className="logo-text">PrintFarm</div>
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
            className="printfarm-menu"
            style={{ flex: 1, marginLeft: '20px' }}
          />
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
  );
};