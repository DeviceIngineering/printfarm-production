import React from 'react';
import { Space, Tag, Button } from 'antd';
import { ReloadOutlined, SaveOutlined, SettingOutlined, ArrowLeftOutlined } from '@ant-design/icons';
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

  const handleSave = () => {
    console.log('Saving plan...');
    // TODO: Сохранение плана в localStorage или на сервер
  };

  const handleSettings = () => {
    console.log('Opening settings...');
    // TODO: Открытие модального окна настроек
  };

  const handleBack = () => {
    navigate('/tochka');
  };

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
            icon={<SaveOutlined />}
            onClick={handleSave}
          >
            Сохранить план
          </Button>
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={handleSettings}
          />
        </Space>
      </div>
    </div>
  );
};
