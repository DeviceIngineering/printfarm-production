import React from 'react';
import { Shift, calculateShiftPosition, formatShiftTime } from '../../utils/shiftUtils';
import './Timeline.css';

interface ShiftHeaderProps {
  shifts: Shift[];
  currentTime: Date;
}

/**
 * Компонент шапки timeline с отображением смен (день/ночь)
 *
 * Показывает 5 смен:
 * - Прошлые: дневная + ночная
 * - Текущая (выделена)
 * - Будущие: 2 смены
 */
export const ShiftHeader: React.FC<ShiftHeaderProps> = ({ shifts, currentTime }) => {
  return (
    <div className="timeline-shift-header">
      {/* Лейбл принтера (слева) */}
      <div className="timeline-printer-label">Принтер</div>

      {/* Смены */}
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
    </div>
  );
};
