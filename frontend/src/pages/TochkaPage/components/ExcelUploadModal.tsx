/**
 * Модальное окно для загрузки Excel файлов
 */
import React from 'react';
import { Modal, Upload, Spin, Typography } from 'antd';
import { FileExcelOutlined } from '@ant-design/icons';

const { Paragraph } = Typography;

interface ExcelUploadModalProps {
  visible: boolean;
  loading: boolean;
  onCancel: () => void;
  onUpload: (file: File) => Promise<boolean>;
}

export const ExcelUploadModal: React.FC<ExcelUploadModalProps> = ({
  visible,
  loading,
  onCancel,
  onUpload,
}) => {
  return (
    <Modal
      title={
        <span>
          <FileExcelOutlined style={{ marginRight: 8, color: '#52c41a' }} />
          Загрузка Excel файла
        </span>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      <div style={{ padding: '20px 0' }}>
        <Paragraph>
          Выберите Excel файл (.xlsx или .xls) который содержит следующие колонки:
        </Paragraph>
        <ul style={{ marginBottom: 20 }}>
          <li><strong>"Артикул товара"</strong> - артикулы товаров</li>
          <li><strong>"Заказов, шт."</strong> - количество заказов в штуках</li>
        </ul>

        <Upload.Dragger
          name="file"
          multiple={false}
          accept=".xlsx,.xls"
          beforeUpload={onUpload}
          showUploadList={false}
          disabled={loading}
          style={{
            opacity: loading ? 0.6 : 1,
            pointerEvents: loading ? 'none' : 'auto'
          }}
        >
          <p className="ant-upload-drag-icon">
            <FileExcelOutlined
              style={{
                fontSize: 48,
                color: loading ? '#d9d9d9' : '#52c41a'
              }}
            />
          </p>
          <p className="ant-upload-text">
            {loading
              ? 'Автоматическая обработка файла...'
              : 'Нажмите или перетащите Excel файл в эту область'
            }
          </p>
          <p className="ant-upload-hint">
            {loading
              ? 'Анализ и формирование списка производства...'
              : 'Поддерживаются форматы .xlsx и .xls'
            }
          </p>
        </Upload.Dragger>

        {loading && (
          <div style={{ textAlign: 'center', marginTop: 20 }}>
            <Spin />
            <p style={{ marginTop: 10 }}>Автоматическая обработка: дедупликация → анализ → список производства...</p>
          </div>
        )}
      </div>
    </Modal>
  );
};
