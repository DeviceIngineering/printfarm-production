import React from 'react';
import { Badge } from 'antd';
import { TimelinePrinter } from '../../types/printer.types';
import { Shift, calculateShiftPosition, isJobVisible, getShiftHours, getCurrentShiftInfo, getShiftStart, TIMELINE_TOTAL_HOURS, CURRENT_TIME_POSITION_PERCENT } from '../../utils/shiftUtils';
import { JobBlock } from './JobBlock';
import './Timeline.css';

interface PrinterRowProps {
  printer: TimelinePrinter;
  shifts: Shift[];
  currentTime: Date;
  index: number; // Номер принтера для отображения
}

/**
 * Компонент строки принтера на timeline
 *
 * Отображает:
 * - Информацию о принтере (слева)
 * - Фоновые смены (день/ночь)
 * - Блоки заданий на timeline
 */
export const PrinterRow: React.FC<PrinterRowProps> = ({ printer, shifts, currentTime, index }) => {
  // Определить статус принтера на основе заданий
  const getPrinterStatus = (): 'printing' | 'idle' => {
    // Если есть активное задание - printing
    const hasActiveJob = printer.jobs.some(job => job.status === 'printing');
    return hasActiveJob ? 'printing' : 'idle';
  };

  const status = getPrinterStatus();

  // Получить цвет статуса
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'printing':
        return '#52c41a';
      case 'idle':
        return '#999';
      default:
        return '#999';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'printing':
        return 'Печать';
      case 'idle':
        return 'Простой';
      default:
        return status;
    }
  };

  return (
    <div className="timeline-row">
      {/* Фиксированная колонка принтера (слева) */}
      <div className="timeline-printer-column">
        <div className="timeline-printer-info">
          <div className="printer-name-row">
            <span className="printer-name">
              <span style={{ color: '#888', marginRight: '8px' }}>#{index + 1}</span>
              {printer.name}
            </span>
            <Badge
              status={status === 'printing' ? 'processing' : 'default'}
              text={
                <span style={{ color: getStatusColor(status), fontSize: '11px' }}>
                  {getStatusText(status)}
                </span>
              }
            />
          </div>
        </div>
      </div>

      {/* Обертка для скроллируемого трека */}
      <div className="timeline-track-wrapper">
        {/* Трек с заданиями */}
        <div className="timeline-track">
        {/* Красная линия текущего времени - фиксирована по центру */}
        <div
          className="timeline-current-line"
          style={{
            left: `${CURRENT_TIME_POSITION_PERCENT}%`,
          }}
        />

        {/* Фоновые смены */}
        {shifts.map((shift, shiftIndex) => {
          const { left, width } = calculateShiftPosition(shift, currentTime);

          return (
            <div
              key={`shift-${shiftIndex}`}
              className={`shift-background ${shift.type}`}
              style={{
                left: `${left}%`,
                width: `${width}%`,
              }}
            />
          );
        })}

        {/* Часовые колонки с чередующимся фоном */}
        {(() => {
          const { startTime: currentShiftStart } = getCurrentShiftInfo(currentTime);
          const timelineStart = getShiftStart(currentShiftStart, 'day', -2);
          const totalDuration_ms = TIMELINE_TOTAL_HOURS * 60 * 60 * 1000;

          // Ширина одного часа в процентах
          const hourWidth = (1 / TIMELINE_TOTAL_HOURS) * 100;

          return shifts.flatMap((shift, shiftIndex) => {
            const shiftHours = getShiftHours(shift);

            return shiftHours.map((hourTime, hourIndex) => {
              // Рассчитываем позицию часа
              const offset_ms = hourTime.getTime() - timelineStart.getTime();
              const positionPercent = (offset_ms / totalDuration_ms) * 100;

              // Чередуем фон для визуального разделения
              const isEven = (shiftIndex * 12 + hourIndex) % 2 === 0;

              return (
                <React.Fragment key={`hour-${shiftIndex}-${hourIndex}`}>
                  {/* Полутоновый фон часа */}
                  <div
                    className={`timeline-hour-background ${isEven ? 'even' : 'odd'}`}
                    style={{
                      left: `${positionPercent}%`,
                      width: `${hourWidth}%`,
                    }}
                  />
                  {/* Вертикальная линия часа */}
                  <div
                    className="timeline-hour-column"
                    style={{
                      left: `${positionPercent}%`,
                    }}
                  />
                </React.Fragment>
              );
            });
          });
        })()}

        {/* Задания */}
        {printer.jobs.map((job) => {
          // Проверяем видимость задания
          const startTime = new Date(job.started_at);
          const endTime = job.completed_at ? new Date(job.completed_at) : currentTime;

          if (!isJobVisible(startTime, endTime, currentTime)) {
            return null;
          }

          return (
            <JobBlock
              key={job.job_id}
              job={job}
              currentTime={currentTime}
              materialColor={job.material_color}
            />
          );
        })}
        </div>
      </div>
    </div>
  );
};
