import React, { useState } from 'react';
import { 
  Card, 
  Form, 
  InputNumber, 
  Select, 
  Switch, 
  Button, 
  Row, 
  Col,
  message
} from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import { GeneralSettings, settingsApi } from '../../api/settings';

interface GeneralSettingsCardProps {
  generalSettings: GeneralSettings | null;
  loading?: boolean;
  onUpdate?: (settings: GeneralSettings) => void;
}

export const GeneralSettingsCard: React.FC<GeneralSettingsCardProps> = ({ 
  generalSettings, 
  loading = false,
  onUpdate 
}) => {
  const [form] = Form.useForm();
  const [updating, setUpdating] = useState(false);

  const handleUpdate = async (values: any) => {
    setUpdating(true);
    try {
      const updated = await settingsApi.updateGeneralSettings(values);
      message.success('Общие настройки обновлены');
      onUpdate?.(updated);
    } catch (error) {
      message.error('Ошибка обновления настроек');
    } finally {
      setUpdating(false);
    }
  };

  const productsPerPageOptions = [
    { value: 25, label: '25' },
    { value: 50, label: '50' },
    { value: 100, label: '100' },
    { value: 200, label: '200' },
  ];

  const autoRefreshOptions = [
    { value: 0, label: 'Отключено' },
    { value: 30, label: '30 секунд' },
    { value: 60, label: '1 минута' },
    { value: 300, label: '5 минут' },
    { value: 600, label: '10 минут' },
  ];

  return (
    <Card 
      title={
        <span>
          <SettingOutlined style={{ marginRight: 8, color: 'var(--color-primary)' }} />
          Общие настройки
        </span>
      }
      loading={loading}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={generalSettings || undefined}
        onFinish={handleUpdate}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item 
              name="default_new_product_stock" 
              label="Целевой остаток для новых товаров"
              rules={[
                { required: true, message: 'Обязательное поле' },
                { type: 'number', min: 1, max: 100, message: 'Значение должно быть от 1 до 100' }
              ]}
            >
              <InputNumber 
                min={1} 
                max={100} 
                style={{ width: '100%' }}
                addonAfter="шт"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item 
              name="default_target_days" 
              label="Целевой запас в днях"
              rules={[
                { required: true, message: 'Обязательное поле' },
                { type: 'number', min: 1, max: 90, message: 'Значение должно быть от 1 до 90' }
              ]}
            >
              <InputNumber 
                min={1} 
                max={90} 
                style={{ width: '100%' }}
                addonAfter="дн"
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item 
              name="low_stock_threshold" 
              label="Порог низкого остатка"
              rules={[
                { required: true, message: 'Обязательное поле' },
                { type: 'number', min: 1, max: 50, message: 'Значение должно быть от 1 до 50' }
              ]}
            >
              <InputNumber 
                min={1} 
                max={50} 
                style={{ width: '100%' }}
                addonAfter="шт"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item 
              name="products_per_page" 
              label="Товаров на странице"
            >
              <Select options={productsPerPageOptions} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item 
              name="show_images" 
              label="Отображать изображения товаров"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item 
              name="auto_refresh_interval" 
              label="Автообновление страницы"
            >
              <Select options={autoRefreshOptions} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={updating}
            style={{ background: 'var(--color-primary)' }}
          >
            Сохранить настройки
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};