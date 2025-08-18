import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ProductsPage } from './pages/ProductsPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { TochkaPage } from './pages/TochkaPage';
import { TestWarehousesPage } from './pages/TestWarehousesPage';
import { TestProductGroupsPage } from './pages/TestProductGroupsPage';
import { TestProductsPage } from './pages/TestProductsPage';
import TestPodiumsPage from './pages/TestPodiumsPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ScrollToTop } from './components/common/ScrollToTop';

function App() {
  useEffect(() => {
    console.log('App component mounted');
    // Force clear old token and set new one
    localStorage.removeItem('auth_token');
    localStorage.setItem('auth_token', '0a8fee03bca2b530a15b1df44d38b304e3f57484');
    console.log('Token updated to:', localStorage.getItem('auth_token'));
  }, []);

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <Layout>
            <Routes>
              <Route path="/" element={<ProductsPage />} />
              <Route path="/products" element={<ProductsPage />} />
              <Route path="/tochka" element={<TochkaPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/test-warehouses" element={<TestWarehousesPage />} />
              <Route path="/test-product-groups" element={<TestProductGroupsPage />} />
              <Route path="/test-products" element={<TestProductsPage />} />
              <Route path="/test-podiums" element={<TestPodiumsPage />} />
            </Routes>
            <ScrollToTop />
          </Layout>
        } />
      </Routes>
    </ErrorBoundary>
  );
}

export default App;