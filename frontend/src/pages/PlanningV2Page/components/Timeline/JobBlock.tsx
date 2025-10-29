import React from 'react';
import { Tooltip } from 'antd';
import { TimelineJob } from '../../types/printer.types';
import { calculateJobPosition, calculateJobWidth } from '../../utils/shiftUtils';
import './Timeline.css';

interface JobBlockProps {
  job: TimelineJob;
  currentTime: Date;
  materialColor: 'black' | 'white' | 'other';
}

/**
 * Компонент отображения одного задания на timeline
 *
 * Цвета блоков:
 * - Темный (#2c5f7c) - завершенные задания (completed)
 * - Светлый зеленый (#52c41a) - активные задания (printing)
 * - Темный красный (#8c4545) - проваленные задания (failed)
 * - Темный желтый (#d4a40c) - отмененные (cancelled)
 */
export const JobBlock: React.FC<JobBlockProps> = ({ job, currentTime, materialColor }) => {
  // Конвертируем ISO строки в Date объекты
  const startTime = new Date(job.started_at);
  const endTime = job.completed_at ? new Date(job.completed_at) : currentTime;

  // Рассчитываем позицию и ширину
  const leftPercent = calculateJobPosition(startTime, currentTime);
  const widthPercent = calculateJobWidth(startTime, endTime);

  // Определяем класс в зависимости от статуса
  const getJobClass = (): string => {
    const classes = ['timeline-job-block'];

    switch (job.status) {
      case 'completed':
        classes.push('job-completed');
        break;
      case 'printing':
        classes.push('job-printing');
        break;
      case 'failed':
        classes.push('job-failed');
        break;
      case 'cancelled':
        classes.push('job-cancelled');
        break;
      default:
        classes.push('job-other');
    }

    return classes.join(' ');
  };

  // Форматируем длительность для отображения
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours === 0) return `${minutes}м`;
    if (minutes === 0) return `${hours}ч`;
    return `${hours}ч ${minutes}м`;
  };

  // Форматируем дату и время
  const formatDateTime = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Получить цвет материала для tooltip
  const getMaterialColorLabel = (color: string): string => {
    switch (color) {
      case 'black':
        return 'Черный';
      case 'white':
        return 'Белый';
      case 'other':
        return 'Другой';
      default:
        return color;
    }
  };

  // Содержимое tooltip
  const tooltipContent = (
    <div className="job-tooltip">
      {job.article && (
        <div>
          <strong>Артикул:</strong> {job.article}
        </div>
      )}
      {!job.article && job.file_name && (
        <div>
          <strong>Файл:</strong> {job.file_name}
        </div>
      )}
      <div>
        <strong>Статус:</strong> {getStatusLabel(job.status)}
      </div>
      <div>
        <strong>Начало:</strong> {formatDateTime(job.started_at)}
      </div>
      {job.completed_at && (
        <div>
          <strong>Окончание:</strong> {formatDateTime(job.completed_at)}
        </div>
      )}
      <div>
        <strong>Длительность:</strong> {formatDuration(job.duration_seconds)}
      </div>
      <div>
        <strong>Цвет пластика:</strong> {getMaterialColorLabel(job.material_color)}
      </div>
      {job.status === 'printing' && (
        <div>
          <strong>Прогресс:</strong> {job.percentage}%
        </div>
      )}
    </div>
  );

  // Если блок очень узкий (< 0.5%), не показываем
  if (widthPercent < 0.5) {
    return null;
  }

  return (
    <Tooltip title={tooltipContent} placement="top">
      <div
        className={getJobClass()}
        style={{
          left: `${leftPercent}%`,
          width: `${widthPercent}%`,
        }}
      >
        {/* Содержимое блока */}
        <div className="job-content">
          {job.article && <span className="job-article">{job.article}</span>}
          {!job.article && job.file_name && (
            <span className="job-filename">{job.file_name.substring(0, 20)}</span>
          )}
          {job.status === 'printing' && <span className="job-progress">{job.percentage}%</span>}
        </div>

        {/* Прогресс бар для активных заданий */}
        {job.status === 'printing' && (
          <div className="job-progress-bar" style={{ width: `${job.percentage}%` }} />
        )}
      </div>
    </Tooltip>
  );
};

// Хелпер для получения текста статуса
const getStatusLabel = (status: string): string => {
  switch (status) {
    case 'printing':
      return 'Печатается';
    case 'completed':
      return 'Завершено';
    case 'failed':
      return 'Ошибка';
    case 'cancelled':
      return 'Отменено';
    case 'queued':
      return 'В очереди';
    default:
      return status;
  }
};
