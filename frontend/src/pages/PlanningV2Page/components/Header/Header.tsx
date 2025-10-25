import React, { useState } from 'react';
import { Space, Tag, Button, Modal, Table } from 'antd';
import { ReloadOutlined, BugOutlined, SettingOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { formatTimeForTimeline, formatDateHeader, getCurrentTimeGMT3 } from '../../utils/timeUtils';
import { Printer } from '../../types/printer.types';
import './Header.css';

interface HeaderProps {
  currentTime: Date;
  printers: Printer[];
}

export const Header: React.FC<HeaderProps> = ({ currentTime, printers }) => {
  const navigate = useNavigate();
  const gmt3Time = getCurrentTimeGMT3();
  const [debugModalVisible, setDebugModalVisible] = useState(false);

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

  const handleRefresh = () => {
    console.log('Refreshing data...');
    // TODO: Обновление данных с сервера
  };

  const handleDebug = () => {
    console.log('Opening API debug modal...');
    setDebugModalVisible(true);
  };

  const handleSettings = () => {
    console.log('Opening settings...');
    // TODO: Открытие модального окна настроек
  };

  const handleBack = () => {
    navigate('/tochka');
  };

  // Подготовка данных для таблицы отладки
  const debugColumns = [
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

  const debugData = printers.map(printer => ({
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
        title="Отладка API - Информация о принтерах"
        open={debugModalVisible}
        onCancel={() => setDebugModalVisible(false)}
        width={1400}
        footer={[
          <Button key="close" type="primary" onClick={() => setDebugModalVisible(false)}>
            Закрыть
          </Button>
        ]}
      >
        <Table
          columns={debugColumns}
          dataSource={debugData}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200, y: 400 }}
          size="small"
          bordered
        />
        <div style={{ marginTop: '16px', padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
          <strong>Сводка:</strong>
          <div>Всего принтеров: {printers.length}</div>
          <div>Печатают: {printers.filter(p => p.status === 'printing').length}</div>
          <div>Простаивают: {printers.filter(p => p.status === 'idle').length}</div>
          <div>Офлайн/Ошибка: {printers.filter(p => p.status === 'error').length}</div>
        </div>
      </Modal>
    </div>
  );
};
