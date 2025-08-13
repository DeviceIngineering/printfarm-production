import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  Rate,
  Upload,
  message,
  Steps,
  Radio,
  Checkbox,
  Row,
  Col,
  Card,
  Typography,
  Divider,
  Tag,
  Alert
} from 'antd';
import {
  BugOutlined,
  RocketOutlined,
  BulbOutlined,
  MessageOutlined,
  CameraOutlined,
  PaperClipOutlined,
  StarOutlined,
  HeartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload';

// Типизация для Google Analytics
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
  }
}

const { TextArea } = Input;
const { Option } = Select;
const { Step } = Steps;
const { Title, Text } = Typography;

interface FeedbackWidgetProps {
  visible: boolean;
  onClose: () => void;
  userId: string;
  currentPage?: string;
}

interface FeedbackForm {
  type: 'bug' | 'feature' | 'satisfaction' | 'general';
  category?: string;
  title: string;
  description: string;
  severity?: string;
  stepsToReproduce?: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  satisfaction?: {
    overall: number;
    easeOfUse: number;
    performance: number;
    features: number;
    design: number;
  };
  mostLiked?: string;
  mostDisliked?: string;
  suggestions?: string;
  wouldRecommend?: boolean;
  npsScore?: number;
  email?: string;
  allowContact?: boolean;
}

export const FeedbackWidget: React.FC<FeedbackWidgetProps> = ({
  visible,
  onClose,
  userId,
  currentPage
}) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [feedbackType, setFeedbackType] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [browserInfo, setBrowserInfo] = useState<any>({});

  useEffect(() => {
    // Собираем информацию о браузере и системе
    const collectBrowserInfo = () => {
      const info = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screenResolution: `${screen.width}x${screen.height}`,
        viewport: `${window.innerWidth}x${window.innerHeight}`,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        referrer: document.referrer
      };
      setBrowserInfo(info);
    };

    if (visible) {
      collectBrowserInfo();
      form.resetFields();
      setCurrentStep(0);
      setFeedbackType('');
      setFileList([]);
    }
  }, [visible, form]);

  const feedbackTypes = [
    {
      key: 'bug',
      title: 'Сообщить о баге',
      description: 'Нашли ошибку или что-то работает не так?',
      icon: <BugOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />,
      color: '#fff2f0'
    },
    {
      key: 'feature',
      title: 'Предложить улучшение',
      description: 'Есть идея как сделать систему лучше?',
      icon: <BulbOutlined style={{ fontSize: 24, color: '#faad14' }} />,
      color: '#fffbe6'
    },
    {
      key: 'satisfaction',
      title: 'Оценить систему',
      description: 'Поделитесь впечатлениями о работе с системой',
      icon: <StarOutlined style={{ fontSize: 24, color: '#52c41a' }} />,
      color: '#f6ffed'
    },
    {
      key: 'general',
      title: 'Общая обратная связь',
      description: 'Любые другие комментарии или вопросы',
      icon: <MessageOutlined style={{ fontSize: 24, color: '#1890ff' }} />,
      color: '#e6f7ff'
    }
  ];

  const bugCategories = [
    { value: 'ui_ux', label: 'Интерфейс/UX проблема' },
    { value: 'performance', label: 'Медленная работа' },
    { value: 'data_accuracy', label: 'Неточные данные' },
    { value: 'export', label: 'Проблемы с экспортом' },
    { value: 'integration', label: 'Интеграция МойСклад' },
    { value: 'workflow', label: 'Рабочий процесс' },
    { value: 'other', label: 'Другое' }
  ];

  const severityLevels = [
    { value: 'critical', label: 'Критический', color: '#ff4d4f' },
    { value: 'high', label: 'Высокий', color: '#fa8c16' },
    { value: 'medium', label: 'Средний', color: '#faad14' },
    { value: 'low', label: 'Низкий', color: '#52c41a' }
  ];

  const handleTypeSelect = (type: string) => {
    setFeedbackType(type);
    setCurrentStep(1);
    form.setFieldsValue({ type });
  };

  const handleNext = async () => {
    try {
      const fields = getFieldsForStep(currentStep);
      await form.validateFields(fields);
      setCurrentStep(currentStep + 1);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  const getFieldsForStep = (step: number): string[] => {
    switch (feedbackType) {
      case 'bug':
        switch (step) {
          case 1: return ['title', 'category', 'severity'];
          case 2: return ['description', 'stepsToReproduce'];
          case 3: return ['expectedBehavior', 'actualBehavior'];
          default: return [];
        }
      case 'feature':
        switch (step) {
          case 1: return ['title', 'category'];
          case 2: return ['description', 'suggestions'];
          default: return [];
        }
      case 'satisfaction':
        switch (step) {
          case 1: return ['overallSatisfaction', 'easeOfUse', 'performance'];
          case 2: return ['mostLiked', 'mostDisliked'];
          case 3: return ['wouldRecommend', 'npsScore'];
          default: return [];
        }
      case 'general':
        switch (step) {
          case 1: return ['title'];
          case 2: return ['description'];
          default: return [];
        }
      default: return [];
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      const values = await form.validateFields();
      
      // Подготавливаем данные для отправки
      const feedbackData = {
        ...values,
        userId,
        currentPage,
        browserInfo,
        timestamp: new Date().toISOString(),
        attachments: fileList.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type
        }))
      };

      // Отправляем данные
      const response = await fetch('/api/v1/feedback/submit/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(feedbackData)
      });

      if (!response.ok) {
        throw new Error('Ошибка отправки обратной связи');
      }

      // Отправляем файлы если есть
      if (fileList.length > 0) {
        const formData = new FormData();
        fileList.forEach(file => {
          if (file.originFileObj) {
            formData.append('files', file.originFileObj);
          }
        });
        
        const responseData = await response.json();
        formData.append('feedbackId', responseData.id);

        await fetch('/api/v1/feedback/upload/', {
          method: 'POST',
          headers: {
            'Authorization': `Token ${localStorage.getItem('auth_token')}`
          },
          body: formData
        });
      }

      message.success('Спасибо за обратную связь! Мы рассмотрим ваше сообщение.');
      
      // Трекинг для аналитики
      if (window.gtag) {
        window.gtag('event', 'feedback_submitted', {
          feedback_type: feedbackType,
          category: values.category || 'general',
          user_id: userId
        });
      }

      onClose();
    } catch (error) {
      console.error('Ошибка отправки обратной связи:', error);
      message.error('Произошла ошибка при отправке. Попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  };

  const renderTypeSelection = () => (
    <div style={{ textAlign: 'center' }}>
      <Title level={3}>Как мы можем помочь?</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        Выберите тип обратной связи
      </Text>
      
      <Row gutter={[16, 16]}>
        {feedbackTypes.map(type => (
          <Col span={12} key={type.key}>
            <Card
              hoverable
              style={{ 
                backgroundColor: type.color,
                border: feedbackType === type.key ? '2px solid #1890ff' : '1px solid #d9d9d9',
                height: 120
              }}
              bodyStyle={{ padding: 16, textAlign: 'center' }}
              onClick={() => handleTypeSelect(type.key)}
            >
              <div style={{ marginBottom: 8 }}>
                {type.icon}
              </div>
              <Text strong style={{ display: 'block', fontSize: 14 }}>
                {type.title}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {type.description}
              </Text>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );

  const renderBugForm = () => {
    switch (currentStep) {
      case 1:
        return (
          <div>
            <Title level={4}>Основная информация</Title>
            <Form.Item
              name="title"
              label="Краткое описание проблемы"
              rules={[{ required: true, message: 'Введите краткое описание' }]}
            >
              <Input placeholder="Например: Кнопка экспорта не работает в модуле Точка" />
            </Form.Item>
            
            <Form.Item
              name="category"
              label="Категория"
              rules={[{ required: true, message: 'Выберите категорию' }]}
            >
              <Select placeholder="Выберите категорию проблемы">
                {bugCategories.map(cat => (
                  <Option key={cat.value} value={cat.value}>{cat.label}</Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item
              name="severity"
              label="Критичность"
              rules={[{ required: true, message: 'Оцените критичность' }]}
            >
              <Radio.Group>
                {severityLevels.map(level => (
                  <Radio key={level.value} value={level.value}>
                    <Tag color={level.color}>{level.label}</Tag>
                  </Radio>
                ))}
              </Radio.Group>
            </Form.Item>
          </div>
        );
        
      case 2:
        return (
          <div>
            <Title level={4}>Детальное описание</Title>
            <Form.Item
              name="description"
              label="Подробное описание проблемы"
              rules={[{ required: true, message: 'Опишите проблему подробно' }]}
            >
              <TextArea
                rows={4}
                placeholder="Опишите что именно не работает..."
              />
            </Form.Item>
            
            <Form.Item
              name="stepsToReproduce"
              label="Шаги для воспроизведения"
              rules={[{ required: true, message: 'Укажите шаги для воспроизведения' }]}
            >
              <TextArea
                rows={4}
                placeholder="1. Открыл страницу...&#10;2. Нажал на кнопку...&#10;3. Увидел ошибку..."
              />
            </Form.Item>
            
            <Form.Item
              name="frequency"
              label="Как часто возникает?"
            >
              <Select placeholder="Выберите частоту">
                <Option value="always">Всегда</Option>
                <Option value="often">Часто</Option>
                <Option value="sometimes">Иногда</Option>
                <Option value="rarely">Редко</Option>
                <Option value="once">Однократно</Option>
              </Select>
            </Form.Item>
          </div>
        );
        
      case 3:
        return (
          <div>
            <Title level={4}>Ожидания vs Реальность</Title>
            <Form.Item
              name="expectedBehavior"
              label="Что должно было произойти?"
            >
              <TextArea
                rows={3}
                placeholder="Опишите ожидаемое поведение системы..."
              />
            </Form.Item>
            
            <Form.Item
              name="actualBehavior"
              label="Что произошло на самом деле?"
            >
              <TextArea
                rows={3}
                placeholder="Опишите что произошло вместо ожидаемого..."
              />
            </Form.Item>
            
            <Form.Item
              name="screenshot"
              label="Скриншот или файл"
            >
              <Upload
                fileList={fileList}
                onChange={({ fileList }) => setFileList(fileList)}
                beforeUpload={() => false}
                multiple
              >
                <Button icon={<CameraOutlined />}>
                  Прикрепить скриншот или файл
                </Button>
              </Upload>
            </Form.Item>
          </div>
        );
        
      default:
        return null;
    }
  };

  const renderSatisfactionForm = () => {
    switch (currentStep) {
      case 1:
        return (
          <div>
            <Title level={4}>Оцените систему</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              Поставьте оценку от 1 до 5 звезд
            </Text>
            
            <Form.Item
              name={['satisfaction', 'overall']}
              label="Общая удовлетворенность"
              rules={[{ required: true, message: 'Поставьте общую оценку' }]}
            >
              <Rate />
            </Form.Item>
            
            <Form.Item
              name={['satisfaction', 'easeOfUse']}
              label="Простота использования"
              rules={[{ required: true, message: 'Оцените простоту использования' }]}
            >
              <Rate />
            </Form.Item>
            
            <Form.Item
              name={['satisfaction', 'performance']}
              label="Скорость работы"
              rules={[{ required: true, message: 'Оцените скорость работы' }]}
            >
              <Rate />
            </Form.Item>
            
            <Form.Item
              name={['satisfaction', 'features']}
              label="Полнота функций"
            >
              <Rate />
            </Form.Item>
            
            <Form.Item
              name={['satisfaction', 'design']}
              label="Дизайн интерфейса"
            >
              <Rate />
            </Form.Item>
          </div>
        );
        
      case 2:
        return (
          <div>
            <Title level={4}>Что вам нравится/не нравится?</Title>
            
            <Form.Item
              name="mostLiked"
              label="Что больше всего понравилось?"
            >
              <TextArea
                rows={3}
                placeholder="Опишите самые полезные или удобные функции..."
              />
            </Form.Item>
            
            <Form.Item
              name="mostDisliked"
              label="Что больше всего не понравилось?"
            >
              <TextArea
                rows={3}
                placeholder="Что вызывает затруднения или раздражение..."
              />
            </Form.Item>
            
            <Form.Item
              name="suggestions"
              label="Предложения по улучшению"
            >
              <TextArea
                rows={3}
                placeholder="Как можно сделать систему лучше..."
              />
            </Form.Item>
          </div>
        );
        
      case 3:
        return (
          <div>
            <Title level={4}>Рекомендации</Title>
            
            <Form.Item
              name="wouldRecommend"
              label="Порекомендовали бы систему коллегам?"
              rules={[{ required: true, message: 'Выберите ответ' }]}
            >
              <Radio.Group>
                <Radio value={true}>
                  <HeartOutlined style={{ color: '#52c41a' }} /> Да, обязательно
                </Radio>
                <Radio value={false}>
                  Пока нет
                </Radio>
              </Radio.Group>
            </Form.Item>
            
            <Form.Item
              name="npsScore"
              label="Оцените вероятность рекомендации (0-10)"
              rules={[{ required: true, message: 'Поставьте оценку' }]}
            >
              <Rate count={10} />
            </Form.Item>
            
            <Alert
              message="NPS шкала"
              description="0-6: Критики, 7-8: Нейтральные, 9-10: Промоутеры"
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </div>
        );
        
      default:
        return null;
    }
  };

  const renderContactForm = () => (
    <div>
      <Title level={4}>Контактная информация</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
        Оставьте email если хотите получить ответ (необязательно)
      </Text>
      
      <Form.Item
        name="email"
        label="Email для связи"
        rules={[{ type: 'email', message: 'Введите корректный email' }]}
      >
        <Input placeholder="your@email.com" />
      </Form.Item>
      
      <Form.Item
        name="allowContact"
        valuePropName="checked"
      >
        <Checkbox>
          Я согласен на обработку персональных данных и получение ответа по email
        </Checkbox>
      </Form.Item>
    </div>
  );

  const getStepsForType = (type: string) => {
    switch (type) {
      case 'bug':
        return [
          { title: 'Тип', description: 'Выбор типа обратной связи' },
          { title: 'Основное', description: 'Заголовок и категория' },
          { title: 'Детали', description: 'Описание и шаги' },
          { title: 'Ожидания', description: 'Ожидаемое поведение' },
          { title: 'Контакты', description: 'Информация для связи' }
        ];
      case 'satisfaction':
        return [
          { title: 'Тип', description: 'Выбор типа обратной связи' },
          { title: 'Оценки', description: 'Рейтинги по аспектам' },
          { title: 'Комментарии', description: 'Что нравится/не нравится' },
          { title: 'Рекомендации', description: 'NPS и рекомендации' },
          { title: 'Контакты', description: 'Информация для связи' }
        ];
      default:
        return [
          { title: 'Тип', description: 'Выбор типа обратной связи' },
          { title: 'Основное', description: 'Заголовок' },
          { title: 'Детали', description: 'Подробное описание' },
          { title: 'Контакты', description: 'Информация для связи' }
        ];
    }
  };

  const isLastStep = () => {
    const steps = getStepsForType(feedbackType);
    return currentStep === steps.length - 1;
  };

  return (
    <Modal
      title="Обратная связь"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
      destroyOnClose
    >
      {feedbackType && (
        <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}>
          {getStepsForType(feedbackType).map((step, index) => (
            <Step key={index} title={step.title} description={step.description} />
          ))}
        </Steps>
      )}

      <Form form={form} layout="vertical">
        {currentStep === 0 && renderTypeSelection()}
        
        {feedbackType === 'bug' && currentStep > 0 && currentStep < 4 && renderBugForm()}
        {feedbackType === 'satisfaction' && currentStep > 0 && currentStep < 4 && renderSatisfactionForm()}
        
        {((feedbackType === 'feature' || feedbackType === 'general') && currentStep === 1) && (
          <div>
            <Form.Item
              name="title"
              label="Заголовок"
              rules={[{ required: true, message: 'Введите заголовок' }]}
            >
              <Input />
            </Form.Item>
          </div>
        )}
        
        {((feedbackType === 'feature' || feedbackType === 'general') && currentStep === 2) && (
          <div>
            <Form.Item
              name="description"
              label="Описание"
              rules={[{ required: true, message: 'Введите описание' }]}
            >
              <TextArea rows={6} />
            </Form.Item>
          </div>
        )}
        
        {isLastStep() && renderContactForm()}
      </Form>

      {currentStep > 0 && (
        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Button style={{ marginRight: 8 }} onClick={handlePrev}>
            Назад
          </Button>
          
          {!isLastStep() ? (
            <Button type="primary" onClick={handleNext}>
              Далее
            </Button>
          ) : (
            <Button
              type="primary"
              loading={loading}
              onClick={handleSubmit}
              icon={<ThunderboltOutlined />}
            >
              Отправить обратную связь
            </Button>
          )}
        </div>
      )}
    </Modal>
  );
};