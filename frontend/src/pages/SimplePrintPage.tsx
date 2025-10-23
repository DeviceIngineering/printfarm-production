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
  Checkbox,
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
  checkSyncStatus,
  cancelSync,
  setSyncing,
  SimplePrintFile,
} from '../store/simpleprintSlice';
import moment from 'moment';

const { Search } = Input;
const { Option } = Select;

const SimplePrintPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files, folders, syncStats, fileStats, loading, syncing, syncError, totalFiles } = useSelector(
    (state: RootState) => state.simpleprint
  );

  const [searchText, setSearchText] = useState('');
  const [selectedFolder, setSelectedFolder] = useState<number | undefined>();
  const [selectedFileType, setSelectedFileType] = useState<string | undefined>();
  const [syncModalVisible, setSyncModalVisible] = useState(false);
  const [syncLogs, setSyncLogs] = useState<string[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [forceSync, setForceSync] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [groupByFolder, setGroupByFolder] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    dispatch(fetchFiles({ page: currentPage, page_size: pageSize }));
    dispatch(fetchFolders());
    dispatch(fetchSyncStats());
    dispatch(fetchFileStats());
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    setCurrentPage(1); // Сброс на первую страницу при поиске
    dispatch(fetchFiles({
      search: value,
      folder: selectedFolder,
      file_type: selectedFileType,
      page: 1,
      page_size: pageSize
    }));
  };

  const handleFolderChange = (value: number | undefined) => {
    setSelectedFolder(value);
    setCurrentPage(1); // Сброс на первую страницу при фильтрации
    dispatch(fetchFiles({
      search: searchText,
      folder: value,
      file_type: selectedFileType,
      page: 1,
      page_size: pageSize
    }));
  };

  const handleFileTypeChange = (value: string | undefined) => {
    setSelectedFileType(value);
    setCurrentPage(1); // Сброс на первую страницу при фильтрации
    dispatch(fetchFiles({
      search: searchText,
      folder: selectedFolder,
      file_type: value,
      page: 1,
      page_size: pageSize
    }));
  };

  const handleTableChange = (page: number, newPageSize?: number) => {
    const effectivePageSize = newPageSize || pageSize;
    setCurrentPage(page);
    if (newPageSize) {
      setPageSize(newPageSize);
    }
    dispatch(fetchFiles({
      search: searchText,
      folder: selectedFolder,
      file_type: selectedFileType,
      page: page,
      page_size: effectivePageSize
    }));
  };

  const handleSync = async (fullSync: boolean = false) => {
    try {
      const timestamp = new Date().toLocaleTimeString();
      setSyncLogs([
        `🚀 Запуск синхронизации... [${timestamp}]`,
        `📡 API Request: POST /api/v1/simpleprint/sync/trigger/`,
        `📝 Параметры: full_sync=${fullSync}, force=${forceSync}`,
      ]);

      const result: any = await dispatch(triggerSync({ full_sync: fullSync, force: forceSync })).unwrap();

      setSyncLogs(prev => [
        ...prev,
        `✅ API Response: ${JSON.stringify(result, null, 2)}`,
      ]);

      if (result.status === 'started' && result.task_id) {
        setSyncLogs(prev => [
          ...prev,
          `📋 Задача создана: ${result.task_id}`,
          `⏳ Ожидание начала синхронизации...`,
          `🔄 Запуск polling (интервал: 2 сек)...`,
        ]);
        setCurrentTaskId(result.task_id);
        startPolling(result.task_id);
      }
    } catch (error: any) {
      const timestamp = new Date().toLocaleTimeString();
      const errorDetails = error.response?.data || error.message || 'Неизвестная ошибка';

      setSyncLogs(prev => [
        ...prev,
        `❌ Ошибка API [${timestamp}]`,
        `📋 Статус: ${error.response?.status || 'N/A'}`,
        `📝 Детали: ${JSON.stringify(errorDetails, null, 2)}`,
      ]);

      if (error.response?.status === 429 || error.message?.includes('429')) {
        const errorMsg = error.response?.data?.message || 'Синхронизация была недавно. Подождите 5 минут.';
        message.warning(errorMsg, 5);
        setSyncLogs(prev => [
          ...prev,
          `💡 Подсказка: Включите "Принудительная синхронизация" чтобы запустить без ожидания`,
        ]);
      } else {
        message.error(`Ошибка синхронизации: ${error.message || 'Неизвестная ошибка'}`);
      }
    }
  };

  const handleCancelSync = async () => {
    if (!currentTaskId) {
      message.warning('Нет активной задачи синхронизации');
      return;
    }

    try {
      const timestamp = new Date().toLocaleTimeString();
      setSyncLogs(prev => [
        ...prev,
        `🛑 Отмена синхронизации... [${timestamp}]`,
        `📡 API Request: POST /api/v1/simpleprint/sync/cancel/`,
        `📝 Body: { task_id: "${currentTaskId.substring(0, 8)}..." }`,
      ]);

      await dispatch(cancelSync(currentTaskId)).unwrap();

      // Останавливаем polling
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }

      setSyncLogs(prev => [
        ...prev,
        `✅ Задача синхронизации отменена [${timestamp}]`,
        `🔄 Обновление данных в UI...`,
      ]);

      setCurrentTaskId(null);
      dispatch(setSyncing(false)); // Сбрасываем состояние syncing
      message.success('Синхронизация отменена');

      // Обновляем данные
      loadData();
    } catch (error: any) {
      const timestamp = new Date().toLocaleTimeString();
      setSyncLogs(prev => [
        ...prev,
        `❌ Ошибка отмены [${timestamp}]: ${error.message || 'Неизвестная ошибка'}`,
      ]);
      message.error(`Не удалось отменить синхронизацию: ${error.message}`);
    }
  };

  const startPolling = (taskId: string) => {
    // Очищаем предыдущий интервал если есть
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }

    let pollCount = 0;

    const interval = setInterval(async () => {
      try {
        pollCount++;
        const timestamp = new Date().toLocaleTimeString();

        // Не удаляем предыдущие сообщения - пусть накапливаются

        const statusResult: any = await dispatch(checkSyncStatus(taskId)).unwrap();

        // Логируем полный ответ в консоль для отладки
        console.log('📊 Status Response:', JSON.stringify(statusResult, null, 2));

        // Больше не добавляем эти строки в основной лог
        // т.к. они будут отображаться в отформатированном виде ниже

        // Обновляем логи с прогрессом
        if (statusResult.progress) {
          const { total_files, synced_files, total_folders, synced_folders } = statusResult.progress;

          setSyncLogs(prev => {
            // Сохраняем начальные логи (первые 4 строки после запуска)
            const baseLog = prev.slice(0, 4);

            // Если данные еще загружаются (total = 0)
            if (total_files === 0 && total_folders === 0) {
              return [
                ...baseLog,
                ``,
                `⏳ ФАЗА 1: Загрузка данных из SimplePrint API...`,
                `📡 SimplePrint имеет ограничение: 180 запросов/минуту (3 req/sec)`,
                `⏰ Обычно эта фаза занимает 4-6 минут для 649 папок`,
                ``,
                `📊 Проверка статуса... Polling #${pollCount} в ${timestamp}`,
                `⏱️ Прошло времени: ${Math.floor(pollCount * 2 / 60)} мин ${(pollCount * 2) % 60} сек`,
              ];
            }

            // Данные загружены, показываем счетчик
            const progress = total_files > 0 ? Math.round((synced_files / total_files) * 100) : 0;
            const progressBar = '█'.repeat(Math.floor(progress / 5)) + '░'.repeat(20 - Math.floor(progress / 5));

            return [
              ...baseLog,
              ``,
              `✅ ФАЗА 2: Синхронизация с базой данных`,
              ``,
              `📁 Папки:  ${String(synced_folders).padStart(4)} / ${total_folders}`,
              `📄 Файлы:  ${String(synced_files).padStart(4)} / ${total_files}`,
              ``,
              `[${progressBar}] ${progress}%`,
              ``,
              `📊 Polling #${pollCount} в ${timestamp}`,
            ];
          });
        } else {
          // Если progress отсутствует - показываем предупреждение
          setSyncLogs(prev => [
            ...prev.slice(0, 4),
            `⚠️ API не возвращает данные прогресса`,
            `🔄 Polling #${pollCount} [${timestamp}]`,
            `📊 API State: ${statusResult.state}, Ready: ${statusResult.ready}`,
          ]);
        }

        // Если синхронизация завершена
        if (statusResult.ready) {
          clearInterval(interval);
          setPollingInterval(null);
          setCurrentTaskId(null);
          dispatch(setSyncing(false)); // Сбрасываем состояние syncing

          setSyncLogs(prev => [...prev, `🎉 Задача завершена! Получение финальных данных...`]);

          if (statusResult.sync_log) {
            const logs = [
              `✅ Синхронизация завершена успешно [${timestamp}]`,
              `📁 Всего папок: ${statusResult.sync_log.total_folders}`,
              `📄 Всего файлов: ${statusResult.sync_log.total_files}`,
              `✓ Синхронизировано папок: ${statusResult.sync_log.synced_folders}`,
              `✓ Синхронизировано файлов: ${statusResult.sync_log.synced_files}`,
            ];

            if (statusResult.sync_log.deleted_files > 0) {
              logs.push(`🗑️ Удалено файлов: ${statusResult.sync_log.deleted_files}`);
            }

            const duration = statusResult.sync_log.duration;
            if (duration) {
              logs.push(`⏱️ Длительность: ${Math.round(duration)} сек`);
            }

            logs.push(`🔄 Всего polling запросов: ${pollCount}`);

            setSyncLogs(logs);
            message.success('Синхронизация завершена успешно');

            setSyncLogs(prev => [...prev, `🔄 Обновление данных в UI...`]);
            loadData();
          } else if (statusResult.error) {
            setSyncLogs(prev => [
              ...prev,
              `❌ Ошибка выполнения: ${JSON.stringify(statusResult.error, null, 2)}`,
            ]);
            message.error('Синхронизация завершилась с ошибкой');
          }
        }
      } catch (error: any) {
        const timestamp = new Date().toLocaleTimeString();
        console.error('Polling error:', error);
        setSyncLogs(prev => [
          ...prev,
          `⚠️ Ошибка polling [${timestamp}]: ${error.message}`,
        ]);
      }
    }, 2000); // Проверяем каждые 2 секунды

    setPollingInterval(interval);
  };

  // Очистка интервала при размонтировании
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

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

  // Группировка файлов по папкам
  const getGroupedData = () => {
    if (!groupByFolder) {
      return files;
    }

    // Группируем файлы по folder_name
    const grouped: { [key: string]: SimplePrintFile[] } = {};
    files.forEach(file => {
      const folderKey = file.folder_name || 'Корень';
      if (!grouped[folderKey]) {
        grouped[folderKey] = [];
      }
      grouped[folderKey].push(file);
    });

    // Преобразуем в древовидную структуру
    const result: any[] = [];
    Object.keys(grouped).sort().forEach((folderName, index) => {
      // Добавляем родительскую папку
      result.push({
        id: `folder-${index}`,
        name: folderName,
        folder_name: null,
        ext: '-',
        size: 0,
        size_display: '-',
        created_at_sp: '',
        isFolder: true,
        children: grouped[folderName],
      });
    });

    return result;
  };

  // Функция для форматирования времени печати
  const formatPrintTime = (seconds: number | null): string => {
    if (!seconds) return '—';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}ч ${minutes}м`;
    }
    return `${minutes}м`;
  };

  // Колонки таблицы
  const columns: ColumnsType<any> = [
    {
      title: 'Артикул',
      dataIndex: 'article',
      key: 'article',
      width: 200,
      ellipsis: true,
      render: (article: string | null, record: any) => {
        if (record.isFolder) return null;
        return article ? (
          <Tag color="purple" style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '13px' }}>
            {article}
          </Tag>
        ) : (
          <span style={{ color: '#8c8c8c' }}>—</span>
        );
      },
    },
    {
      title: 'Имя файла',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: 350,
      render: (text: string, record: any) => {
        if (record.isFolder) {
          return (
            <Space>
              <FolderOutlined style={{ color: '#FFB800', fontSize: '16px' }} />
              <span style={{ fontWeight: 600, color: '#FFB800' }}>{text}</span>
            </Space>
          );
        }
        return (
          <Space>
            <FileOutlined style={{ color: '#06EAFC' }} />
            <span style={{ fontWeight: 500 }}>{text}</span>
          </Space>
        );
      },
    },
    {
      title: 'Кол-во',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'center' as const,
      render: (quantity: number | null, record: any) => {
        if (record.isFolder) return null;
        if (!quantity) return <span style={{ color: '#8c8c8c' }}>—</span>;

        // Разные цвета для разных типов количества
        let color = 'green';
        let displayText = '';

        if (quantity === 0.5) {
          // Части изделия (part1, part2...)
          color = 'orange';
          displayText = '½ шт';
        } else if (quantity % 1 !== 0) {
          // Дробное значение (1.5, 2.5, 3.7...)
          color = 'cyan';
          displayText = `${quantity} шт`;
        } else {
          // Целое значение
          color = 'green';
          displayText = `${quantity.toFixed(0)} шт`;
        }

        return (
          <Tag color={color} style={{ fontSize: '14px', fontWeight: 600 }}>
            {displayText}
          </Tag>
        );
      },
    },
    {
      title: 'Время печати',
      dataIndex: 'print_time',
      key: 'print_time',
      width: 130,
      align: 'center' as const,
      render: (printTime: number | null, record: any) => {
        if (record.isFolder) return null;
        return (
          <span style={{ fontFamily: 'monospace', color: printTime ? '#06EAFC' : '#8c8c8c' }}>
            {formatPrintTime(printTime)}
          </span>
        );
      },
    },
    {
      title: 'Папка',
      dataIndex: 'folder_name',
      key: 'folder_name',
      width: 220,
      ellipsis: true,
      render: (text: string | null, record: any) => {
        if (record.isFolder) return null;
        return text ? (
          <Tag color="blue" icon={<FolderOutlined />}>
            {text}
          </Tag>
        ) : (
          <Tag color="default">Корень</Tag>
        );
      },
    },
    {
      title: 'Вес',
      dataIndex: 'weight',
      key: 'weight',
      width: 100,
      align: 'center' as const,
      render: (weight: number | null, record: any) => {
        if (record.isFolder) return null;
        return weight ? (
          <span style={{ fontFamily: 'monospace' }}>
            {weight.toFixed(1)} г
          </span>
        ) : (
          <span style={{ color: '#8c8c8c' }}>—</span>
        );
      },
    },
    {
      title: 'Цвет',
      dataIndex: 'material_color',
      key: 'material_color',
      width: 120,
      render: (color: string | null, record: any) => {
        if (record.isFolder) return null;
        return color ? (
          <Tag color="cyan" style={{ fontWeight: 500 }}>
            {color}
          </Tag>
        ) : (
          <span style={{ color: '#8c8c8c' }}>—</span>
        );
      },
    },
    {
      title: 'Расширение',
      dataIndex: 'ext',
      key: 'ext',
      width: 120,
      render: (text: string, record: any) => {
        if (record.isFolder) return null;
        return <Tag color="cyan">{text || '-'}</Tag>;
      },
    },
    {
      title: 'Размер',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: (size: number, record: any) => {
        if (record.isFolder) return null;
        return <span style={{ fontFamily: 'monospace' }}>{record.size_display}</span>;
      },
    },
    {
      title: 'Дата создания',
      dataIndex: 'created_at_sp',
      key: 'created_at_sp',
      width: 180,
      render: (date: string, record: any) => {
        if (record.isFolder) return null;
        return moment(date).format('DD.MM.YYYY HH:mm');
      },
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
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
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
          <Checkbox
            checked={groupByFolder}
            onChange={(e) => setGroupByFolder(e.target.checked)}
          >
            <span style={{ fontWeight: 500 }}>
              <FolderOutlined style={{ marginRight: '8px', color: '#FFB800' }} />
              Группировать по папкам
            </span>
          </Checkbox>
        </Space>
      </Card>

      {/* Таблица файлов */}
      <Card>
        <Table
          columns={columns}
          dataSource={getGroupedData()}
          rowKey={(record) => record.isFolder ? record.id : `file-${record.id}`}
          loading={loading}
          pagination={groupByFolder ? false : {
            current: currentPage,
            pageSize: pageSize,
            total: totalFiles,
            showSizeChanger: true,
            pageSizeOptions: ['20', '50', '100', '200'],
            showTotal: (total) => `Всего ${total} файлов`,
            onChange: handleTableChange,
            onShowSizeChange: (current, size) => handleTableChange(current, size),
          }}
          expandable={groupByFolder ? {
            defaultExpandAllRows: false,
            indentSize: 30,
          } : undefined}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* Модальное окно синхронизации */}
      <Modal
        title="Синхронизация с SimplePrint"
        open={syncModalVisible}
        closable={!syncing}
        maskClosable={!syncing}
        keyboard={!syncing}
        onCancel={() => {
          if (syncing && currentTaskId) {
            Modal.confirm({
              title: 'Синхронизация в процессе',
              content: 'Синхронизация продолжается в фоновом режиме. Закрыть окно?',
              okText: 'Да, закрыть',
              cancelText: 'Продолжить наблюдение',
              onOk: () => {
                setSyncModalVisible(false);
              },
            });
          } else {
            setSyncModalVisible(false);
          }
        }}
        width={700}
        footer={[
          <Button
            key="close"
            onClick={() => setSyncModalVisible(false)}
            disabled={syncing}
          >
            Закрыть
          </Button>,
          syncing && currentTaskId ? (
            <Button
              key="cancel"
              danger
              onClick={handleCancelSync}
              loading={false}
            >
              Отменить синхронизацию
            </Button>
          ) : null,
          <Button
            key="sync"
            type="default"
            icon={<SyncOutlined />}
            onClick={() => handleSync(false)}
            loading={syncing}
            disabled={syncing}
          >
            Обычная синхронизация
          </Button>,
          <Button
            key="fullSync"
            type="primary"
            icon={<SyncOutlined spin={syncing} />}
            onClick={() => handleSync(true)}
            loading={syncing}
            disabled={syncing}
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

          {/* Опция принудительной синхронизации */}
          <Checkbox
            checked={forceSync}
            onChange={(e) => setForceSync(e.target.checked)}
            disabled={syncing}
          >
            <span style={{ color: '#888' }}>
              Принудительная синхронизация (игнорировать ограничение 5 минут)
            </span>
          </Checkbox>

          {/* Область логов синхронизации */}
          {syncLogs.length > 0 && (
            <Card
              title="Логи синхронизации"
              size="small"
              style={{ marginTop: '16px' }}
              bodyStyle={{
                backgroundColor: '#1E1E1E',
                color: '#00FF88',
                fontFamily: 'monospace',
                fontSize: '13px',
                maxHeight: '300px',
                overflowY: 'auto',
                padding: '12px',
              }}
            >
              {syncLogs.map((log, index) => (
                <div key={index} style={{ marginBottom: '4px' }}>
                  {log}
                </div>
              ))}
              {syncing && (
                <div style={{ marginTop: '8px', color: '#06EAFC' }}>
                  <Spin size="small" style={{ marginRight: '8px' }} />
                  Синхронизация в процессе...
                </div>
              )}
            </Card>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default SimplePrintPage;
