import React from 'react';
import { Shift, calculateShiftPosition, formatShiftTime, getShiftHours, getCurrentShiftInfo, getShiftStart, TIMELINE_TOTAL_HOURS } from '../../utils/shiftUtils';
import './Timeline.css';

interface ShiftHeaderProps {
  shifts: Shift[];
  currentTime: Date;
}

/**
 * Компонент шапки timeline с отображением смен (день/ночь) и часовой сеткой
 *
 * Показывает 5 смен:
 * - Прошлые: дневная + ночная
 * - Текущая (выделена)
 * - Будущие: 2 смены
 *
 * Под каждой сменой отображаются часовые метки (каждый час)
 */
export const ShiftHeader: React.FC<ShiftHeaderProps> = ({ shifts, currentTime }) => {
  // Рассчитываем начало timeline для позиционирования часов
  const { startTime: currentShiftStart } = getCurrentShiftInfo(currentTime);
  const timelineStart = getShiftStart(currentShiftStart, 'day', -2);
  const totalDuration_ms = TIMELINE_TOTAL_HOURS * 60 * 60 * 1000;

  return (
    <div className="timeline-shift-header">
      {/* Лейбл принтера (слева, фиксированный) */}
      <div className="timeline-printer-label">Принтер</div>

      {/* Обертка для скроллируемого контента */}
      <div className="timeline-shifts-wrapper">
        {/* Контейнер со сменами и часами */}
        <div className="timeline-shifts-container">
          {/* Слой смен */}
          <div className="timeline-shifts">
            {shifts.map((shift, index) => {
              const { left, width } = calculateShiftPosition(shift, currentTime);

              return (
                <div
                  key={index}
                  className={`timeline-shift ${shift.type} ${shift.isCurrentShift ? 'current' : ''}`}
                  style={{
                    left: `${left}%`,
                    width: `${width}%`,
                  }}
                >
                  <div className="shift-label">{shift.label}</div>
                  <div className="shift-time">{formatShiftTime(shift)}</div>
                </div>
              );
            })}
          </div>

          {/* Слой часовой сетки */}
          <div className="timeline-hours">
            {shifts.map((shift, shiftIndex) => {
              const shiftHours = getShiftHours(shift);

              return shiftHours.map((hourTime, hourIndex) => {
                // Рассчитываем позицию часа
                const offset_ms = hourTime.getTime() - timelineStart.getTime();
                const positionPercent = (offset_ms / totalDuration_ms) * 100;
                const hour = hourTime.getHours();
                const label = `${hour.toString().padStart(2, '0')}:00`;

                return (
                  <div
                    key={`${shiftIndex}-${hourIndex}`}
                    className="timeline-hour-mark"
                    style={{
                      left: `${positionPercent}%`,
                    }}
                  >
                    <span className="hour-label">{label}</span>
                  </div>
                );
              });
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
