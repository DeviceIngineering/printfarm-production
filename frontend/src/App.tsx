import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { ProductsPage } from './pages/ProductsPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { TestWarehousesPage } from './pages/TestWarehousesPage';
import { TestProductGroupsPage } from './pages/TestProductGroupsPage';
import { TestProductsPage } from './pages/TestProductsPage';
import { TestImagesPage } from './pages/TestImagesPage';
import TestPodiumsPage from './pages/TestPodiumsPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ScrollToTop } from './components/common/ScrollToTop';

function App() {
  useEffect(() => {
    // Auto-set token for demo if not exists
    const token = localStorage.getItem('auth_token');
    if (!token) {
      localStorage.setItem('auth_token', '549ebaf641ffa608a26b79a21d72a296c99a02b7');
    }
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
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/test-warehouses" element={<TestWarehousesPage />} />
              <Route path="/test-product-groups" element={<TestProductGroupsPage />} />
              <Route path="/test-products" element={<TestProductsPage />} />
              <Route path="/test-images" element={<TestImagesPage />} />
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