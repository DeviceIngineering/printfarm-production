import React from 'react';
import { Layout as AntLayout } from 'antd';
import { Header } from './Header';

const { Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header />
      <Content style={{ padding: '24px' }}>
        {children}
      </Content>
    </AntLayout>
  );
};