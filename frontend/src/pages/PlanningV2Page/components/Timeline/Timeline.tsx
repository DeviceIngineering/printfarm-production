import React, { useRef, useEffect } from 'react';
import { Badge, Tag, Tooltip } from 'antd';
import { Printer } from '../../types/printer.types';
import {
  getTimelineHours,
  formatTimeForTimeline,
  calculateTimelinePosition,
  calculateTimelineWidth,
  getCurrentTimeGMT3,
} from '../../utils/timeUtils';
import './Timeline.css';

interface TimelineProps {
  printers: Printer[];
  currentTime: Date;
}

export const Timeline: React.FC<TimelineProps> = ({ printers, currentTime }) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [currentTimePosition, setCurrentTimePosition] = React.useState(0);
  const hours = getTimelineHours();

  // Обновление позиции линии времени каждую секунду
  useEffect(() => {
    const updateTimelinePosition = () => {
      const position = calculateTimelinePosition(getCurrentTimeGMT3());
      setCurrentTimePosition(position);
    };

    // Начальная установка
    updateTimelinePosition();

    // Обновление каждую секунду
    const interval = setInterval(updateTimelinePosition, 1000);

    return () => clearInterval(interval);
  }, []);

  // Автоскролл к текущему времени при монтировании
  useEffect(() => {
    if (timelineRef.current) {
      const currentPosition = calculateTimelinePosition(getCurrentTimeGMT3());
      const scrollPosition = (currentPosition / 100) * timelineRef.current.scrollWidth - 400;
      timelineRef.current.scrollLeft = Math.max(0, scrollPosition);
    }
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'printing': return '#52c41a';
      case 'idle': return '#999';
      case 'error': return '#ff4d4f';
      default: return '#999';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'printing': return 'Печать';
      case 'idle': return 'Простой';
      case 'error': return 'Ошибка';
      default: return status;
    }
  };

  const getMaterialColorBg = (color: string) => {
    switch (color) {
      case 'black': return '#4a4a4a'; // Более светлый черный для лучшей видимости
      case 'white': return '#8a8a8a'; // Темно-серый вместо светлого
      case 'other': return '#5b4aae'; // Более темный фиолетовый
      default: return '#5a5a5a'; // Более светлый серый
    }
  };

  return (
    <div className="planning-v2-timeline" ref={timelineRef}>
      {/* Временная шкала */}
      <div className="timeline-header">
        <div className="timeline-printer-label">Принтер</div>
        <div className="timeline-hours">
          {hours.map((hour, index) => {
            const now = getCurrentTimeGMT3();
            const isCurrentHour = hour.getHours() === now.getHours() &&
                                 hour.getDate() === now.getDate();

            return (
              <div
                key={index}
                className={`timeline-hour ${isCurrentHour ? 'current-hour' : ''}`}
              >
                {formatTimeForTimeline(hour)}
              </div>
            );
          })}
        </div>
      </div>

      {/* Строки принтеров */}
      <div className="timeline-body">
        {/* Линия текущего времени - обновляется каждую секунду */}
        <div
          className="timeline-current-line"
          style={{
            left: `${240 + currentTimePosition * 10}px`,
          }}
        />
        {printers.map(printer => (
          <div key={printer.id} className="timeline-row">
            {/* Информация о принтере */}
            <div className="timeline-printer-info">
              <div className="printer-name-row">
                <span className="printer-name">{printer.name}</span>
                <Badge
                  status={printer.status === 'printing' ? 'processing' : printer.status === 'error' ? 'error' : 'default'}
                  text={<span style={{ color: getStatusColor(printer.status), fontSize: '11px' }}>
                    {getStatusText(printer.status)}
                  </span>}
                />
              </div>
              <div className="printer-meta">
                <Tag
                  color={printer.materialColor === 'black' ? 'default' : printer.materialColor === 'white' ? 'blue' : 'purple'}
                  style={{ fontSize: '10px', padding: '0 6px' }}
                >
                  {printer.materialColor === 'black' ? 'Черный' : printer.materialColor === 'white' ? 'Белый' : 'Другой'}
                </Tag>
                {printer.temperature && printer.status === 'printing' && (
                  <span className="printer-temp">{printer.temperature.hotend}°C</span>
                )}
              </div>
            </div>

            {/* Таймлайн принтера */}
            <div
              className="timeline-track"
              onDrop={(e) => {
                e.preventDefault();
                const articleData = e.dataTransfer.getData('article');
                console.log('Dropped on printer:', printer.id, articleData);
                // TODO: Добавить задачу в очередь принтера
              }}
              onDragOver={(e) => e.preventDefault()}
            >
              {/* Текущая задача */}
              {printer.currentTask && (
                <Tooltip
                  title={
                    <div>
                      <div><strong>{printer.currentTask.article}</strong></div>
                      <div>Количество: {printer.currentTask.quantity} шт</div>
                      <div>Прогресс: {printer.currentTask.progress}%</div>
                      <div>Осталось: {printer.currentTask.timeRemaining}</div>
                    </div>
                  }
                >
                  <div
                    className="timeline-task current-task"
                    style={{
                      left: `${(calculateTimelinePosition(printer.currentTask.startTime) / 100) * 5200}px`,
                      width: `${(calculateTimelineWidth(printer.currentTask.startTime, printer.currentTask.endTime) / 100) * 5200}px`,
                      backgroundColor: getMaterialColorBg(printer.materialColor),
                    }}
                  >
                    <div className="task-content">
                      <span className="task-article">{printer.currentTask.article}</span>
                      <span className="task-progress">{printer.currentTask.progress}%</span>
                    </div>
                    <div
                      className="task-progress-bar"
                      style={{ width: `${printer.currentTask.progress}%` }}
                    />
                  </div>
                </Tooltip>
              )}

              {/* Задачи в очереди */}
              {printer.queuedTasks.map((task, index) => (
                <Tooltip
                  key={index}
                  title={
                    <div>
                      <div><strong>{task.article}</strong></div>
                      <div>Количество: {task.quantity} шт</div>
                      <div>Время: {task.timeRemaining}</div>
                    </div>
                  }
                >
                  <div
                    className="timeline-task queued-task"
                    style={{
                      left: `${(calculateTimelinePosition(task.startTime) / 100) * 5200}px`,
                      width: `${(calculateTimelineWidth(task.startTime, task.endTime) / 100) * 5200}px`,
                      backgroundColor: getMaterialColorBg(printer.materialColor),
                    }}
                  >
                    <div className="task-content">
                      <span className="task-article">{task.article}</span>
                      <span className="task-quantity">{task.quantity} шт</span>
                    </div>
                  </div>
                </Tooltip>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
