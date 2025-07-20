import React, { useState, useEffect } from 'react';
import { Card, Button, Space, Alert, Spin, Row, Col, Typography, Image, Tag, Progress } from 'antd';
import { ReloadOutlined, PictureOutlined, DownloadOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const { Title, Text, Paragraph } = Typography;

interface ProductWithImages {
  id: number;
  article: string;
  name: string;
  current_stock: number;
  main_image: string | null;
  images: Array<{
    id: number;
    image: string;
    thumbnail: string;
    is_main: boolean;
  }>;
}

interface ImageSyncProgress {
  total: number;
  completed: number;
  current_product: string;
  errors: number;
}

export const TestImagesPage: React.FC = () => {
  const [products, setProducts] = useState<ProductWithImages[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncingImages, setSyncingImages] = useState(false);
  const [progress, setProgress] = useState<ImageSyncProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProductsWithImages = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Fetching products with images...');
      
      // Запрашиваем товары с изображениями и без них отдельно
      const [withImagesResponse, allProductsResponse] = await Promise.all([
        apiClient.get('/products/', {
          params: {
            page_size: 100,
            ordering: '-last_synced_at',
            has_images: 'true'  // Только товары с изображениями
          }
        }),
        apiClient.get('/products/', {
          params: {
            page_size: 50,
            ordering: '-last_synced_at'
          }
        })
      ]);
      
      const productsWithImages = withImagesResponse.data.results || [];
      const allProducts = allProductsResponse.data.results || [];
      
      console.log('Products with images:', productsWithImages.length);
      console.log('All products (first 50):', allProducts.length);
      
      // Объединяем: сначала товары с изображениями, потом первые товары без изображений
      const combinedProducts = [
        ...productsWithImages,
        ...allProducts.filter((p: ProductWithImages) => !productsWithImages.find((pi: ProductWithImages) => pi.id === p.id)).slice(0, 20)
      ];
      
      console.log('Combined products:', combinedProducts.length);
      setProducts(combinedProducts);
    } catch (err: any) {
      console.error('Products fetch error:', err);
      setError(`Ошибка загрузки товаров: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const syncProductImages = async () => {
    setSyncingImages(true);
    setError(null);
    setProgress({ total: products.length, completed: 0, current_product: '', errors: 0 });

    try {
      for (let i = 0; i < Math.min(products.length, 10); i++) {
        const product = products[i];
        setProgress(prev => prev ? {
          ...prev,
          completed: i,
          current_product: product.name
        } : null);

        try {
          console.log(`Syncing images for product: ${product.article}`);
          await apiClient.post(`/products/${product.id}/sync-images/`);
          
          // Small delay to see progress
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (err) {
          console.error(`Failed to sync images for ${product.article}:`, err);
          setProgress(prev => prev ? { ...prev, errors: prev.errors + 1 } : null);
        }
      }

      // Refresh products after sync
      await fetchProductsWithImages();
      
    } catch (err: any) {
      setError(`Ошибка синхронизации изображений: ${err.message}`);
    } finally {
      setSyncingImages(false);
      setProgress(null);
    }
  };

  const downloadTestImages = async () => {
    setSyncingImages(true);
    setError(null);
    
    try {
      console.log('Starting bulk image download...');
      const response = await apiClient.post('/sync/download-images/', {
        limit: 100  // Увеличили лимит
      });
      
      console.log('Image download response:', response.data);
      await fetchProductsWithImages();
      
    } catch (err: any) {
      console.error('Image download error:', err);
      setError(`Ошибка загрузки изображений: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncingImages(false);
    }
  };

  const downloadSpecificImages = async () => {
    setSyncingImages(true);
    setError(null);
    
    try {
      console.log('Starting specific image download...');
      
      // Загружаем изображения для конкретных товаров, которые мы знаем что имеют изображения
      const articles = ['112-43045', '107-43038', '110-43042', '109-43041', '108-43039'];
      
      const response = await apiClient.post('/sync/download-specific-images/', {
        articles: articles
      });
      
      console.log('Specific image download response:', response.data);
      await fetchProductsWithImages();
      
    } catch (err: any) {
      console.error('Specific image download error:', err);
      setError(`Ошибка загрузки конкретных изображений: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncingImages(false);
    }
  };

  useEffect(() => {
    fetchProductsWithImages();
  }, []);

  const productsWithImages = products.filter(p => p.main_image || (p.images && p.images.length > 0));
  const productsWithoutImages = products.filter(p => !p.main_image && (!p.images || p.images.length === 0));

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>
          <PictureOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Тест изображений товаров
        </Title>
        <Space>
          <Button 
            type="default"
            icon={<DownloadOutlined />} 
            onClick={downloadTestImages}
            loading={syncingImages}
          >
            Загрузить изображения (100)
          </Button>
          <Button 
            type="dashed"
            icon={<PictureOutlined />} 
            onClick={downloadSpecificImages}
            loading={syncingImages}
          >
            Загрузить конкретные
          </Button>
          <Button 
            type="primary"
            icon={<PictureOutlined />} 
            onClick={syncProductImages}
            loading={syncingImages}
          >
            Синхронизировать
          </Button>
          <Button 
            type="default" 
            icon={<ReloadOutlined />} 
            onClick={fetchProductsWithImages}
            loading={loading}
          >
            Обновить
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="Ошибка"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Progress indicator */}
      {progress && (
        <Card style={{ marginBottom: 24 }}>
          <div style={{ textAlign: 'center' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text strong>Синхронизация изображений...</Text>
            </div>
            <div style={{ marginTop: 8 }}>
              <Text>Обрабатывается: {progress.current_product}</Text>
            </div>
            <Progress 
              percent={Math.round((progress.completed / progress.total) * 100)}
              status="active"
              style={{ marginTop: 16 }}
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                {progress.completed} из {progress.total} товаров
                {progress.errors > 0 && ` (ошибок: ${progress.errors})`}
              </Text>
            </div>
          </div>
        </Card>
      )}

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: 'var(--color-primary)', margin: 0 }}>
                {products.length}
              </Title>
              <Text>Всего товаров</Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: 'var(--color-success)', margin: 0 }}>
                {productsWithImages.length}
              </Title>
              <Text>С изображениями</Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: 'var(--color-warning)', margin: 0 }}>
                {productsWithoutImages.length}
              </Title>
              <Text>Без изображений</Text>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Title level={3} style={{ color: 'var(--color-primary)', margin: 0 }}>
                {products.reduce((sum, p) => sum + (p.images?.length || 0), 0)}
              </Title>
              <Text>Всего изображений</Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Products with images */}
      {productsWithImages.length > 0 && (
        <Card title={`Товары с изображениями (${productsWithImages.length})`} style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            {productsWithImages.map(product => (
              <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                <Card
                  size="small"
                  cover={
                    product.main_image ? (
                      <div style={{ height: 200, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                        <Image
                          src={product.main_image}
                          alt={product.name}
                          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'cover' }}
                          preview={true}
                          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                        />
                      </div>
                    ) : product.images && product.images.length > 0 ? (
                      <div style={{ height: 200, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
                        <Image
                          src={product.images[0].image}
                          alt={product.name}
                          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'cover' }}
                          preview={true}
                          fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
                        />
                      </div>
                    ) : (
                      <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f0f0' }}>
                        <PictureOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
                      </div>
                    )
                  }
                >
                  <Card.Meta
                    title={<Text ellipsis style={{ fontWeight: 500 }}>{product.article}</Text>}
                    description={
                      <div>
                        <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: 12 }}>
                          {product.name}
                        </Paragraph>
                        <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Остаток: {product.current_stock}
                          </Text>
                          {product.images && product.images.length > 0 && (
                            <Tag color="green" style={{ fontSize: 10, padding: '2px 6px' }}>
                              {product.images.length} фото
                            </Tag>
                          )}
                        </div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Products without images */}
      {productsWithoutImages.length > 0 && (
        <Card title={`Товары без изображений (${productsWithoutImages.length})`}>
          <Row gutter={[16, 16]}>
            {productsWithoutImages.slice(0, 20).map(product => (
              <Col xs={24} sm={12} md={8} lg={6} key={product.id}>
                <Card size="small">
                  <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#fafafa', marginBottom: 8 }}>
                    <PictureOutlined style={{ fontSize: 32, color: '#d9d9d9' }} />
                  </div>
                  <Card.Meta
                    title={<Text ellipsis style={{ fontWeight: 500, fontSize: 13 }}>{product.article}</Text>}
                    description={
                      <div>
                        <Paragraph ellipsis={{ rows: 2 }} style={{ margin: 0, fontSize: 11 }}>
                          {product.name}
                        </Paragraph>
                        <Text type="secondary" style={{ fontSize: 10 }}>
                          Остаток: {product.current_stock}
                        </Text>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
          {productsWithoutImages.length > 20 && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Text type="secondary">
                ... и еще {productsWithoutImages.length - 20} товаров без изображений
              </Text>
            </div>
          )}
        </Card>
      )}

      {/* Debug Info */}
      <Card title="Отладочная информация" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>API Base URL: {process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}</Text>
          <Text>Загружено товаров: {products.length}</Text>
          <Text>Товаров с изображениями: {productsWithImages.length}</Text>
          <Text>Товаров без изображений: {productsWithoutImages.length}</Text>
          <Text>Время последнего обновления: {new Date().toLocaleString('ru-RU')}</Text>
        </Space>
      </Card>
    </div>
  );
};