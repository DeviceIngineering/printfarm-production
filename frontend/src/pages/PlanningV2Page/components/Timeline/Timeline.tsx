import React, { useEffect, useState } from 'react';
import { Spin, Alert } from 'antd';
import { TimelinePrinter } from '../../types/printer.types';
import { getTimelineShifts } from '../../utils/shiftUtils';
import { getCurrentTimeGMT3 } from '../../utils/timeUtils';
import { ShiftHeader } from './ShiftHeader';
import { PrinterRow } from './PrinterRow';
import { API_BASE_URL } from '../../../../utils/constants';
import './Timeline.css';

interface TimelineProps {
  // Пропсы не нужны - загружаем данные внутри компонента
}

/**
 * Главный компонент Timeline со сменами
 *
 * Особенности:
 * - Показывает 5 смен (2 прошлые, текущая, 2 будущие)
 * - Красная линия текущего времени фиксирована по центру (50%)
 * - Смены и задания плавно двигаются влево с течением времени
 * - Обновление данных каждую минуту
 * - Автоматическое обновление по webhook событиям (TODO)
 */
export const Timeline: React.FC<TimelineProps> = () => {
  const [currentTime, setCurrentTime] = useState(getCurrentTimeGMT3());
  const [printers, setPrinters] = useState<TimelinePrinter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [hasRecentUpdates, setHasRecentUpdates] = useState(false);

  const shifts = getTimelineShifts(currentTime);

  // Загрузка данных из API
  const fetchTimelineData = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No auth token found');
      }

      const response = await fetch(`${API_BASE_URL}/simpleprint/timeline-live-jobs/`, {
        headers: {
          Authorization: `Token ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      setPrinters(data.printers || []);
      setError(null);

      // Обработка webhook обновлений
      if (data.has_updates) {
        console.log('📢 Webhook updates detected - data refreshed');
        setHasRecentUpdates(true);
        // Сбросить флаг через 2 минуты
        setTimeout(() => setHasRecentUpdates(false), 120000);
      }

      if (data.timestamp) {
        setLastUpdate(data.timestamp);
      }
    } catch (err) {
      console.error('Failed to fetch timeline data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Обновление текущего времени каждую секунду
  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(getCurrentTimeGMT3());
    }, 1000);

    return () => clearInterval(timeInterval);
  }, []);

  // Загрузка данных при монтировании
  useEffect(() => {
    fetchTimelineData();
  }, []);

  // Обновление данных: каждую минуту обычно, каждые 10 секунд при недавних обновлениях
  useEffect(() => {
    const interval = hasRecentUpdates ? 10000 : 60000; // 10 сек или 60 сек

    const dataInterval = setInterval(() => {
      fetchTimelineData();
    }, interval);

    return () => clearInterval(dataInterval);
  }, [hasRecentUpdates]); // Пересоздаем интервал при изменении флага

  // Синхронизация горизонтального скролла между header и body
  useEffect(() => {
    const headerWrapper = document.querySelector('.timeline-shifts-wrapper');
    const bodyScrollWrapper = document.querySelector('.timeline-body-scroll-wrapper');
    const trackWrappers = document.querySelectorAll('.timeline-track-wrapper');

    if (!headerWrapper || !bodyScrollWrapper) return;

    // Синхронизация: header -> body scroll и треки (через margin compensation)
    const headerScrollHandler = () => {
      const scrollLeft = (headerWrapper as Element).scrollLeft;
      (bodyScrollWrapper as Element).scrollLeft = scrollLeft;
      trackWrappers.forEach(wrapper => {
        // Компенсируем padding-left при скролле
        (wrapper as HTMLElement).style.transform = `translateX(-${scrollLeft}px)`;
      });
    };

    // Синхронизация: body scroll -> header и треки
    const bodyScrollHandler = () => {
      const scrollLeft = (bodyScrollWrapper as Element).scrollLeft;
      (headerWrapper as Element).scrollLeft = scrollLeft;
      trackWrappers.forEach(wrapper => {
        (wrapper as HTMLElement).style.transform = `translateX(-${scrollLeft}px)`;
      });
    };

    headerWrapper.addEventListener('scroll', headerScrollHandler);
    bodyScrollWrapper.addEventListener('scroll', bodyScrollHandler);

    return () => {
      headerWrapper.removeEventListener('scroll', headerScrollHandler);
      bodyScrollWrapper.removeEventListener('scroll', bodyScrollHandler);
    };
  }, [printers.length]); // Re-sync when printers change

  // TODO: Подписка на webhook события для real-time обновлений
  // useEffect(() => {
  //   const handleWebhookUpdate = (event: any) => {
  //     if (event.type === 'job_started' || event.type === 'job_completed') {
  //       fetchTimelineData();
  //     }
  //   };
  //
  //   // Подписка на WebSocket или EventSource
  //   return () => {
  //     // Отписка
  //   };
  // }, []);

  if (loading) {
    return (
      <div className="timeline-loading">
        <Spin size="large" tip="Загрузка timeline..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="timeline-error">
        <Alert
          message="Ошибка загрузки данных"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  if (printers.length === 0) {
    return (
      <div className="timeline-empty">
        <Alert
          message="Нет данных"
          description="Нет заданий для отображения за последние 60 часов"
          type="info"
          showIcon
        />
      </div>
    );
  }

  return (
    <div className="planning-v2-timeline">
      {/* Шапка со сменами */}
      <ShiftHeader shifts={shifts} currentTime={currentTime} />

      {/* Строки принтеров */}
      <div className="timeline-body">
        {/* Контейнер со строками (вертикальный скролл) */}
        <div className="timeline-body-rows">
          {printers.map((printer, index) => (
            <PrinterRow
              key={printer.id}
              printer={printer}
              shifts={shifts}
              currentTime={currentTime}
              index={index}
            />
          ))}
        </div>

        {/* Общий горизонтальный скролл внизу */}
        <div className="timeline-body-scroll-wrapper">
          <div className="timeline-scroll-content" style={{ width: '300%', height: '1px' }} />
        </div>
      </div>

      {/* Информация о последнем обновлении */}
      <div className="timeline-footer">
        <span className="timeline-update-info">
          Последнее обновление: {currentTime.toLocaleTimeString('ru-RU')}
          {hasRecentUpdates && (
            <span style={{ marginLeft: '12px', color: '#52c41a', fontWeight: 'bold' }}>
              🔄 Real-time обновления активны
            </span>
          )}
        </span>
        <span className="timeline-printers-count">
          Принтеров: {printers.length} | Заданий: {printers.reduce((sum, p) => sum + p.jobs.length, 0)}
        </span>
      </div>
    </div>
  );
};
