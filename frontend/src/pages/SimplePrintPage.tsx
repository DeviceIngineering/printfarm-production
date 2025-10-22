/**
 * SimplePrint Page - Страница с данными SimplePrint
 * Отображает файлы и папки из SimplePrint с возможностью синхронизации
 */

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Table,
  Card,
  Button,
  Input,
  Space,
  Tag,
  Statistic,
  Row,
  Col,
  message,
  Spin,
  Modal,
  Select,
} from 'antd';
import {
  ReloadOutlined,
  SearchOutlined,
  FolderOutlined,
  FileOutlined,
  SyncOutlined,
  CloudServerOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { AppDispatch, RootState } from '../store';
import {
  fetchFiles,
  fetchFolders,
  fetchSyncStats,
  fetchFileStats,
  triggerSync,
  SimplePrintFile,
} from '../store/simpleprintSlice';
import moment from 'moment';

const { Search } = Input;
const { Option } = Select;

const SimplePrintPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files, folders, syncStats, fileStats, loading, syncing, syncError } = useSelector(
    (state: RootState) => state.simpleprint
  );

  const [searchText, setSearchText] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<number | undefined>();
  const [selectedFileType, setSelectedFileType] = useState<string | undefined>();
  const [syncModalVisible, setSyncModalVisible] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    dispatch(fetchFiles());
    dispatch(fetchFolders());
    dispatch(fetchSyncStats());
    dispatch(fetchFileStats());
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    dispatch(fetchFiles({ search: value, folder: selectedFolder, file_type: selectedFileType }));
  };

  const handleFolderChange = (value: number | undefined) => {
    setSelectedFolder(value);
    dispatch(fetchFiles({ search: searchText, folder: value, file_type: selectedFileType }));
  };

  const handleFileTypeChange = (value: string | undefined) => {
    setSelectedFileType(value);
    dispatch(fetchFiles({ search: searchText, folder: selectedFolder, file_type: value }));
  };

  const handleSync = async (fullSync: boolean = false) => {
    try {
      await dispatch(triggerSync({ full_sync: fullSync, force: false })).unwrap();
      message.success('Синхронизация запущена успешно');
      setSyncModalVisible(false);
      // Обновляем данные после синхронизации
      setTimeout(() => {
        loadData();
      }, 2000);
    } catch (error: any) {
      if (error.message?.includes('429')) {
        message.warning('Синхронизация была недавно. Подождите 5 минут.');
      } else {
        message.error(`Ошибка синхронизации: ${error.message || 'Неизвестная ошибка'}`);
      }
    }
  };

  const handleRefresh = () => {
    loadData();
    message.success('Данные обновлены');
  };

  // Форматирование размера файла
  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  // Колонки таблицы
  const columns: ColumnsType<SimplePrintFile> = [
    {
      title: 'Имя файла',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: 300,
      render: (text: string, record: SimplePrintFile) => (
        <Space>
          <FileOutlined style={{ color: '#06EAFC' }} />
          <span style={{ fontWeight: 500 }}>{text}</span>
        </Space>
      ),
    },
    {
      title: 'Папка',
      dataIndex: 'folder_name',
      key: 'folder_name',
      width: 150,
      render: (text: string | null) => (
        text ? (
          <Space>
            <FolderOutlined style={{ color: '#FFB800' }} />
            {text}
          </Space>
        ) : (
          <Tag color="default">Корень</Tag>
        )
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 120,
      render: (text: string) => {
        const colors: { [key: string]: string } = {
          printable: 'green',
          model: 'blue',
          unknown: 'default',
        };
        return <Tag color={colors[text] || 'default'}>{text || 'unknown'}</Tag>;
      },
    },
    {
      title: 'Расширение',
      dataIndex: 'ext',
      key: 'ext',
      width: 100,
      render: (text: string) => <Tag>{text || '-'}</Tag>,
    },
    {
      title: 'Размер',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      sorter: (a, b) => a.size - b.size,
      render: (size: number, record: SimplePrintFile) => (
        <span style={{ fontFamily: 'monospace' }}>{record.size_display}</span>
      ),
    },
    {
      title: 'Дата создания',
      dataIndex: 'created_at_sp',
      key: 'created_at_sp',
      width: 180,
      sorter: (a, b) => moment(a.created_at_sp).unix() - moment(b.created_at_sp).unix(),
      render: (date: string) => moment(date).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Синхронизировано',
      dataIndex: 'last_synced_at',
      key: 'last_synced_at',
      width: 180,
      render: (date: string) => (
        <span style={{ color: '#888' }}>{moment(date).format('DD.MM.YYYY HH:mm')}</span>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Заголовок */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{
          fontSize: '32px',
          fontWeight: 'bold',
          color: '#06EAFC',
          textShadow: '0 0 10px rgba(6, 234, 252, 0.5)',
          marginBottom: '8px'
        }}>
          Данные SimplePrint
        </h1>
        <p style={{ color: '#888', fontSize: '16px' }}>
          Управление файлами и папками из SimplePrint
        </p>
      </div>

      {/* Статистика */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего файлов"
              value={fileStats?.total_files || 0}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#06EAFC' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего папок"
              value={syncStats?.total_folders || 0}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#FFB800' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Общий размер"
              value={fileStats ? formatSize(fileStats.total_size) : '0 B'}
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#00FF88' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Последняя синхронизация"
              value={syncStats?.last_sync ? moment(syncStats.last_sync).fromNow() : 'Никогда'}
              prefix={<SyncOutlined />}
              valueStyle={{ fontSize: '16px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Фильтры и действия */}
      <Card style={{ marginBottom: '16px' }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Search
              placeholder="Поиск файлов..."
              allowClear
              style={{ width: 300 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Select
              placeholder="Выберите папку"
              allowClear
              style={{ width: 200 }}
              onChange={handleFolderChange}
              value={selectedFolder}
            >
              {folders.map((folder) => (
                <Option key={folder.id} value={folder.id}>
                  {folder.name}
                </Option>
              ))}
            </Select>
            <Select
              placeholder="Тип файла"
              allowClear
              style={{ width: 150 }}
              onChange={handleFileTypeChange}
              value={selectedFileType}
            >
              <Option value="printable">Printable</Option>
              <Option value="model">Model</Option>
            </Select>
          </Space>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading}
            >
              Обновить
            </Button>
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={() => setSyncModalVisible(true)}
              loading={syncing}
              style={{
                background: 'linear-gradient(135deg, #06EAFC 0%, #00B8D4 100%)',
                border: 'none',
              }}
            >
              Синхронизация
            </Button>
          </Space>
        </Space>
      </Card>

      {/* Таблица файлов */}
      <Card>
        <Table
          columns={columns}
          dataSource={files}
          rowKey="id"
          loading={loading}
          pagination={{
            defaultPageSize: 50,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total) => `Всего ${total} файлов`,
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* Модальное окно синхронизации */}
      <Modal
        title="Синхронизация с SimplePrint"
        open={syncModalVisible}
        onCancel={() => setSyncModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setSyncModalVisible(false)}>
            Отмена
          </Button>,
          <Button
            key="sync"
            type="default"
            icon={<SyncOutlined />}
            onClick={() => handleSync(false)}
            loading={syncing}
          >
            Обычная синхронизация
          </Button>,
          <Button
            key="fullSync"
            type="primary"
            icon={<SyncOutlined spin={syncing} />}
            onClick={() => handleSync(true)}
            loading={syncing}
            danger
          >
            Полная синхронизация
          </Button>,
        ]}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <p>
            <strong>Обычная синхронизация:</strong> Загружает новые файлы и обновляет существующие.
          </p>
          <p>
            <strong>Полная синхронизация:</strong> Также удаляет файлы, которых больше нет в SimplePrint.
          </p>
          {syncStats?.last_sync && (
            <p style={{ color: '#888' }}>
              Последняя синхронизация: {moment(syncStats.last_sync).format('DD.MM.YYYY HH:mm')}
            </p>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default SimplePrintPage;
