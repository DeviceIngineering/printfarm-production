import React, { useState } from 'react';
import { Space, Tag, Button, Modal, Table, Tabs, Spin, Input, Select, Descriptions, message } from 'antd';
import { ReloadOutlined, BugOutlined, SettingOutlined, ArrowLeftOutlined, DownloadOutlined, CopyOutlined, SyncOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { formatTimeForTimeline, formatDateHeader, getCurrentTimeGMT3 } from '../../utils/timeUtils';
import { Printer } from '../../types/printer.types';
import { PrinterSnapshot } from '../../../../types/simpleprint.types';
import './Header.css';

const { TabPane } = Tabs;
const { Search } = Input;

interface HeaderProps {
  currentTime: Date;
  printers: Printer[];
}

export const Header: React.FC<HeaderProps> = ({ currentTime, printers }) => {
  const navigate = useNavigate();
  const gmt3Time = getCurrentTimeGMT3();
  const [debugModalVisible, setDebugModalVisible] = useState(false);
  const [apiDebugData, setApiDebugData] = useState<PrinterSnapshot[] | null>(null);
  const [apiLoading, setApiLoading] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('1');

  // Фильтры для таблиц
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [onlineFilter, setOnlineFilter] = useState<string>('all');
  const [searchText, setSearchText] = useState<string>('');

  // Подсчет готовых/ожидающих принтеров
  const readyPrinters = printers.filter(p => p.status === 'idle').length;
  const totalPrinters = printers.length;

  // Подсчет офлайн принтеров
  const offlinePrinters = printers.filter(p => p.status === 'error').length;

  // Подсчет онлайн принтеров
  const onlinePrinters = printers.filter(p => p.status === 'printing' || p.status === 'idle').length;

  // Поиск ближайшего к завершению принтера
  const getNextFinishTime = (): { minutes: number; seconds: number; printerName: string; printerId: string } | null => {
    const now = currentTime.getTime();
    let minTime = Infinity;
    let closestPrinterName = '';
    let closestPrinterId = '';

    printers.forEach(printer => {
      if (printer.currentTask && printer.status === 'printing') {
        const timeLeft = printer.currentTask.endTime.getTime() - now;
        if (timeLeft > 0 && timeLeft < minTime) {
          minTime = timeLeft;
          closestPrinterName = printer.name;
          closestPrinterId = printer.id;
        }
      }
    });

    if (closestPrinterName && minTime !== Infinity) {
      const totalSeconds = Math.floor(minTime / 1000);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return { minutes, seconds, printerName: closestPrinterName, printerId: closestPrinterId };
    }

    return null;
  };

  const nextFinish = getNextFinishTime();

  // Вспомогательные функции форматирования
  const formatSeconds = (seconds: number | null): string => {
    if (!seconds) return '—';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) return `${hours}ч ${minutes}м ${secs}с`;
    if (minutes > 0) return `${minutes}м ${secs}с`;
    return `${secs}с`;
  };

  const formatDateTime = (isoString: string | null): string => {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString('ru-RU');
  };

  const extractArticle = (filename: string | null): string => {
    if (!filename) return '—';
    const match = filename.match(/^(\d+-\d+)/);
    return match ? match[1] : '—';
  };

  const handleRefresh = () => {
    console.log('Refreshing data...');
    // TODO: Обновление данных с сервера
  };

  const handleDebug = () => {
    console.log('Opening API debug modal...');
    setDebugModalVisible(true);
    // Не загружаем данные автоматически - только открываем модальное окно
  };

  const handleRefreshApiData = async () => {
    setApiLoading(true);
    try {
      const response = await fetch('/api/v1/simpleprint/printers/');
      const data: PrinterSnapshot[] = await response.json();
      setApiDebugData(data);
      setLastUpdateTime(new Date().toLocaleString('ru-RU'));
      console.log('✅ API data loaded:', data.length, 'printers');
      message.success(`Загружено ${data.length} принтеров`);
    } catch (error) {
      console.error('❌ Failed to fetch API data:', error);
      message.error('Ошибка загрузки данных: ' + String(error));
      setApiDebugData(null);
    } finally {
      setApiLoading(false);
    }
  };

  const handleExportCSV = () => {
    if (!apiDebugData) return;

    const headers = ['ID', 'Имя', 'Online', 'State', 'Job File', 'Артикул', '%', 'Слои', 'Прошло (с)', 'Осталось (с)', 'Начало', 'Конец', 'T° сопло', 'T° стол'];
    const rows = apiDebugData.map(p => [
      p.printer_id,
      p.printer_name,
      p.online ? 'Да' : 'Нет',
      p.state,
      p.job_file || '',
      extractArticle(p.job_file),
      p.percentage,
      `${p.current_layer}/${p.max_layer}`,
      p.elapsed_time,
      p.time_remaining_seconds,
      p.job_start_time || '',
      p.job_end_time_estimate || '',
      p.temperature_nozzle || '',
      p.temperature_bed || ''
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `printers_${new Date().toISOString()}.csv`;
    link.click();
    message.success('CSV файл загружен');
  };

  const handleCopyJSON = () => {
    if (!apiDebugData) return;
    navigator.clipboard.writeText(JSON.stringify(apiDebugData, null, 2));
    message.success('JSON скопирован в буфер обмена');
  };

  const handleSettings = () => {
    console.log('Opening settings...');
    // TODO: Открытие модального окна настроек
  };

  const handleBack = () => {
    navigate('/tochka');
  };

  // Колонки для Frontend таблицы (текущие преобразованные данные)
  const frontendColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 100 },
    { title: 'Имя', dataIndex: 'name', key: 'name', width: 120 },
    { title: 'Статус', dataIndex: 'status', key: 'status', width: 100 },
    { title: 'Артикул', dataIndex: 'article', key: 'article', width: 150 },
    { title: 'Прогресс', dataIndex: 'progress', key: 'progress', width: 100 },
    { title: 'Осталось', dataIndex: 'timeRemaining', key: 'timeRemaining', width: 120 },
    { title: 'Начало', dataIndex: 'startTime', key: 'startTime', width: 180 },
    { title: 'Конец', dataIndex: 'endTime', key: 'endTime', width: 180 },
    { title: 'Темп. сопло', dataIndex: 'tempHotend', key: 'tempHotend', width: 120 },
    { title: 'Темп. стол', dataIndex: 'tempBed', key: 'tempBed', width: 120 },
    { title: 'Цвет', dataIndex: 'materialColor', key: 'materialColor', width: 100 },
    { title: 'Очередь', dataIndex: 'queuedTasks', key: 'queuedTasks', width: 100 },
  ];

  const frontendData = printers.map(printer => ({
    key: printer.id,
    id: printer.id,
    name: printer.name,
    status: printer.status,
    article: printer.currentTask?.article || '—',
    progress: printer.currentTask ? `${printer.currentTask.progress}%` : '—',
    timeRemaining: printer.currentTask?.timeRemaining || '—',
    startTime: printer.currentTask ? printer.currentTask.startTime.toLocaleString('ru-RU') : '—',
    endTime: printer.currentTask ? printer.currentTask.endTime.toLocaleString('ru-RU') : '—',
    tempHotend: printer.temperature ? `${printer.temperature.hotend}°C` : '—',
    tempBed: printer.temperature ? `${printer.temperature.bed}°C` : '—',
    materialColor: printer.materialColor,
    queuedTasks: printer.queuedTasks.length,
  }));

  // Колонки для Backend таблицы (детальные данные от API)
  const backendColumns = [
    { title: 'ID', dataIndex: 'printer_id', key: 'printer_id', width: 100, fixed: 'left' as const },
    { title: 'Имя', dataIndex: 'printer_name', key: 'printer_name', width: 120, fixed: 'left' as const },
    {
      title: 'Online',
      dataIndex: 'online',
      key: 'online',
      width: 80,
      render: (val: boolean) => val ? <Tag color="green">✓</Tag> : <Tag color="red">✗</Tag>
    },
    {
      title: 'State',
      dataIndex: 'state',
      key: 'state',
      width: 100,
      render: (val: string) => {
        const colors: Record<string, string> = {
          printing: 'blue',
          idle: 'green',
          offline: 'red',
          paused: 'orange',
          error: 'red'
        };
        return <Tag color={colors[val] || 'default'}>{val}</Tag>;
      }
    },
    { title: 'Job File', dataIndex: 'job_file', key: 'job_file', width: 250, ellipsis: true },
    {
      title: 'Артикул',
      key: 'article',
      width: 120,
      render: (_: any, record: PrinterSnapshot) => extractArticle(record.job_file)
    },
    {
      title: 'Прогресс',
      dataIndex: 'percentage',
      key: 'percentage',
      width: 100,
      render: (val: number) => `${val}%`
    },
    {
      title: 'Слои',
      key: 'layers',
      width: 100,
      render: (_: any, record: PrinterSnapshot) => `${record.current_layer}/${record.max_layer}`
    },
    {
      title: 'Прошло',
      dataIndex: 'elapsed_time',
      key: 'elapsed_time',
      width: 120,
      render: (val: number) => formatSeconds(val)
    },
    {
      title: 'Осталось',
      dataIndex: 'time_remaining_seconds',
      key: 'time_remaining_seconds',
      width: 120,
      render: (val: number) => formatSeconds(val)
    },
    {
      title: 'Начало',
      dataIndex: 'job_start_time',
      key: 'job_start_time',
      width: 180,
      render: (val: string | null) => formatDateTime(val)
    },
    {
      title: 'Конец (ожид)',
      dataIndex: 'job_end_time_estimate',
      key: 'job_end_time_estimate',
      width: 180,
      render: (val: string | null) => formatDateTime(val)
    },
    {
      title: 'T° сопло',
      dataIndex: 'temperature_nozzle',
      key: 'temperature_nozzle',
      width: 100,
      render: (val: number | null) => val ? `${val}°C` : '—'
    },
    {
      title: 'T° стол',
      dataIndex: 'temperature_bed',
      key: 'temperature_bed',
      width: 100,
      render: (val: number | null) => val ? `${val}°C` : '—'
    },
    {
      title: 'Idle',
      dataIndex: 'idle_duration_seconds',
      key: 'idle_duration_seconds',
      width: 120,
      render: (val: number) => val > 0 ? formatSeconds(val) : '—'
    },
  ];

  // Фильтрация Backend данных
  const filteredBackendData = apiDebugData
    ? apiDebugData.filter(p => {
        // Фильтр по статусу
        if (statusFilter !== 'all' && p.state !== statusFilter) return false;
        // Фильтр по online
        if (onlineFilter === 'online' && !p.online) return false;
        if (onlineFilter === 'offline' && p.online) return false;
        // Поиск по имени
        if (searchText && !p.printer_name.toLowerCase().includes(searchText.toLowerCase())) return false;
        return true;
      })
    : [];

  return (
    <div className="planning-v2-header">
      <div className="planning-v2-header-left">
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={handleBack}
          className="back-button"
        >
          Назад
        </Button>
        <h2 className="planning-v2-title">Планирование производства</h2>
        <Tag color="blue" className="planning-v2-date-tag">
          {formatDateHeader(gmt3Time)}
        </Tag>
        <Tag color="cyan" className="planning-v2-time-tag">
          {formatTimeForTimeline(gmt3Time)} GMT+3
        </Tag>
      </div>

      <div className="planning-v2-header-center">
        {/* Виджет 1: Готовые принтеры */}
        <div className="header-widget">
          <div className="widget-label">Принт. готов/ожид.</div>
          <div className="widget-value">
            <span className="widget-number ready">{readyPrinters}</span>
            <span className="widget-separator">/</span>
            <span className="widget-number total">{totalPrinters}</span>
          </div>
        </div>

        {/* Виджет 2: Ближайшее окончание */}
        <div className="header-widget">
          <div className="widget-label">Принт. оконч.</div>
          {nextFinish ? (
            <>
              <div className="widget-value">
                <span className="widget-time">
                  {String(nextFinish.minutes).padStart(2, '0')}:
                  {String(nextFinish.seconds).padStart(2, '0')}
                </span>
              </div>
              <div className="widget-sublabel">{nextFinish.printerId}</div>
            </>
          ) : (
            <div className="widget-value">
              <span className="widget-time no-tasks">--:--</span>
            </div>
          )}
        </div>

        {/* Виджет 3: Офлайн принтеры */}
        <div className="header-widget">
          <div className="widget-label">Принт. оффлайн</div>
          <div className="widget-value">
            <span className="widget-number offline">{offlinePrinters}</span>
            <span className="widget-separator">/</span>
            <span className="widget-number total">{totalPrinters}</span>
          </div>
        </div>

        {/* Виджет 4: Онлайн принтеры */}
        <div className="header-widget">
          <div className="widget-label">Принт. онлайн</div>
          <div className="widget-value">
            <span className="widget-number online">{onlinePrinters}</span>
            <span className="widget-separator">/</span>
            <span className="widget-number total">{totalPrinters}</span>
          </div>
        </div>
      </div>

      <div className="planning-v2-header-right">
        <Space size="middle">
          <Button
            type="default"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
          >
            Обновить
          </Button>
          <Button
            type="primary"
            icon={<BugOutlined />}
            onClick={handleDebug}
          >
            Отладка API
          </Button>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={handleSettings}
          />
        </Space>
      </div>

      {/* Модальное окно отладки */}
      <Modal
        title="Отладка API - Детальная информация о принтерах"
        open={debugModalVisible}
        onCancel={() => setDebugModalVisible(false)}
        width={1600}
        footer={[
          <Button key="close" onClick={() => setDebugModalVisible(false)}>
            Закрыть
          </Button>
        ]}
      >
        {/* Toolbar с кнопками управления */}
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Button
              type="primary"
              icon={<SyncOutlined spin={apiLoading} />}
              onClick={handleRefreshApiData}
              loading={apiLoading}
            >
              Обновить данные
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExportCSV}
              disabled={!apiDebugData}
            >
              Export CSV
            </Button>
            <Button
              icon={<CopyOutlined />}
              onClick={handleCopyJSON}
              disabled={!apiDebugData}
            >
              Copy JSON
            </Button>
          </Space>
          {lastUpdateTime && (
            <Tag color="blue">Последнее обновление: {lastUpdateTime}</Tag>
          )}
        </div>

        {apiLoading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="Загрузка данных из API..." />
          </div>
        )}

        {!apiLoading && (
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            {/* Вкладка 1: Frontend данные */}
            <TabPane tab="Frontend данные" key="1">
              <div style={{ marginBottom: '16px', padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
                <strong>Сводка (Frontend):</strong>
                <div>Всего: {printers.length} | Печатают: {printers.filter(p => p.status === 'printing').length} |
                  Idle: {printers.filter(p => p.status === 'idle').length} |
                  Офлайн: {printers.filter(p => p.status === 'error').length}
                </div>
              </div>
              <Table
                columns={frontendColumns}
                dataSource={frontendData}
                pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ['10', '20', '50'] }}
                scroll={{ x: 1400, y: 500 }}
                size="small"
                bordered
              />
            </TabPane>

            {/* Вкладка 2: Backend данные */}
            <TabPane tab="Backend данные (детально)" key="2">
              {/* Фильтры */}
              <div style={{ marginBottom: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <Select
                  style={{ width: 150 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  placeholder="Статус"
                >
                  <Select.Option value="all">Все статусы</Select.Option>
                  <Select.Option value="printing">Printing</Select.Option>
                  <Select.Option value="idle">Idle</Select.Option>
                  <Select.Option value="offline">Offline</Select.Option>
                  <Select.Option value="paused">Paused</Select.Option>
                  <Select.Option value="error">Error</Select.Option>
                </Select>
                <Select
                  style={{ width: 150 }}
                  value={onlineFilter}
                  onChange={setOnlineFilter}
                  placeholder="Online"
                >
                  <Select.Option value="all">Все</Select.Option>
                  <Select.Option value="online">Online</Select.Option>
                  <Select.Option value="offline">Offline</Select.Option>
                </Select>
                <Search
                  placeholder="Поиск по имени..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: 250 }}
                  allowClear
                />
              </div>

              {apiDebugData ? (
                <>
                  <div style={{ marginBottom: '16px', padding: '12px', background: '#e6f7ff', borderRadius: '4px' }}>
                    <strong>Сводка (Backend API):</strong>
                    <div>
                      Всего: {apiDebugData.length} |
                      Online: {apiDebugData.filter(p => p.online).length} |
                      Печатают: {apiDebugData.filter(p => p.state === 'printing').length} |
                      Idle: {apiDebugData.filter(p => p.state === 'idle').length} |
                      Офлайн: {apiDebugData.filter(p => p.state === 'offline').length}
                    </div>
                    <div>Отфильтровано: {filteredBackendData.length} из {apiDebugData.length}</div>
                  </div>
                  <Table
                    columns={backendColumns}
                    dataSource={filteredBackendData}
                    rowKey="printer_id"
                    pagination={{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'] }}
                    scroll={{ x: 2000, y: 500 }}
                    size="small"
                    bordered
                    expandable={{
                      expandedRowRender: (record: PrinterSnapshot) => (
                        <Descriptions bordered size="small" column={2}>
                          <Descriptions.Item label="DB ID">{record.id}</Descriptions.Item>
                          <Descriptions.Item label="Job ID">{record.job_id || '—'}</Descriptions.Item>
                          <Descriptions.Item label="State Display">{record.state_display}</Descriptions.Item>
                          <Descriptions.Item label="Idle Since">{formatDateTime(record.idle_since)}</Descriptions.Item>
                          <Descriptions.Item label="T° Ambient">{record.temperature_ambient ? `${record.temperature_ambient}°C` : '—'}</Descriptions.Item>
                          <Descriptions.Item label="Created At">{formatDateTime(record.created_at)}</Descriptions.Item>
                          <Descriptions.Item label="Raw JSON" span={2}>
                            <pre style={{ maxHeight: '200px', overflow: 'auto', background: '#f5f5f5', padding: '8px', fontSize: '11px' }}>
                              {JSON.stringify(record, null, 2)}
                            </pre>
                          </Descriptions.Item>
                        </Descriptions>
                      ),
                      rowExpandable: () => true,
                    }}
                  />
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '60px', background: '#fafafa', borderRadius: '4px' }}>
                  <p style={{ fontSize: '16px', color: '#999' }}>Нажмите "Обновить данные" для загрузки информации из API</p>
                </div>
              )}
            </TabPane>

            {/* Вкладка 3: Сравнение */}
            <TabPane tab="Сравнение Frontend vs Backend" key="3">
              <div style={{ padding: '20px', background: '#f0f0f0', borderRadius: '4px' }}>
                <h3>Анализ расхождений</h3>
                {apiDebugData ? (
                  <div>
                    <p>Frontend принтеров: {printers.length}</p>
                    <p>Backend принтеров: {apiDebugData.length}</p>
                    {printers.length !== apiDebugData.length && (
                      <Tag color="red">⚠️ Расхождение в количестве принтеров</Tag>
                    )}
                    {printers.length === apiDebugData.length && (
                      <Tag color="green">✓ Количество принтеров совпадает</Tag>
                    )}
                    <div style={{ marginTop: '20px' }}>
                      <strong>Детальное сравнение:</strong>
                      <ul>
                        <li>Frontend: {printers.filter(p => p.status === 'printing').length} печатают</li>
                        <li>Backend: {apiDebugData.filter(p => p.state === 'printing').length} печатают</li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <p>Загрузите данные Backend для сравнения</p>
                )}
              </div>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};
