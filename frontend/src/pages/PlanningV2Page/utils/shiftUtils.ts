/**
 * Утилиты для работы со сменами на timeline
 *
 * Смены:
 * - Дневная: 08:00 - 20:00 (12 часов)
 * - Ночная: 20:00 - 08:00 (12 часов)
 *
 * Timeline показывает 5 смен:
 * - 1 прошлая дневная + 1 прошлая ночная
 * - Текущая смена
 * - 2 будущие смены
 */

import { getCurrentTimeGMT3 } from './timeUtils';

export type ShiftType = 'day' | 'night';

export interface Shift {
  type: ShiftType;
  startTime: Date;
  endTime: Date;
  label: string;
  isCurrentShift: boolean;
}

// Константы смен
export const DAY_SHIFT_START_HOUR = 8;      // Дневная смена начинается в 8:00
export const NIGHT_SHIFT_START_HOUR = 20;   // Ночная смена начинается в 20:00
export const SHIFT_DURATION_HOURS = 12;     // Длительность смены 12 часов
export const TIMELINE_TOTAL_HOURS = 60;     // 5 смен × 12 часов
export const CURRENT_TIME_POSITION_PERCENT = 50; // Красная линия по центру

/**
 * Получить тип текущей смены и время её начала
 */
export const getCurrentShiftInfo = (now: Date): { type: ShiftType; startTime: Date } => {
  const hour = now.getHours();

  let shiftStartTime = new Date(now);
  shiftStartTime.setMinutes(0, 0, 0);

  if (hour >= DAY_SHIFT_START_HOUR && hour < NIGHT_SHIFT_START_HOUR) {
    // Дневная смена (8:00 - 20:00)
    shiftStartTime.setHours(DAY_SHIFT_START_HOUR);
    return { type: 'day', startTime: shiftStartTime };
  } else {
    // Ночная смена (20:00 - 08:00)
    if (hour >= NIGHT_SHIFT_START_HOUR) {
      // Сегодня после 20:00
      shiftStartTime.setHours(NIGHT_SHIFT_START_HOUR);
    } else {
      // Сегодня до 8:00 - смена началась вчера
      shiftStartTime.setDate(shiftStartTime.getDate() - 1);
      shiftStartTime.setHours(NIGHT_SHIFT_START_HOUR);
    }
    return { type: 'night', startTime: shiftStartTime };
  }
};

/**
 * Получить начало определенной смены относительно текущей
 * @param offset - смещение от текущей смены (-2 = две смены назад, 0 = текущая, 1 = следующая)
 */
const getShiftStart = (currentShiftStart: Date, currentShiftType: ShiftType, offset: number): Date => {
  const shiftStart = new Date(currentShiftStart);
  const hoursOffset = offset * SHIFT_DURATION_HOURS;
  shiftStart.setHours(shiftStart.getHours() + hoursOffset);
  return shiftStart;
};

/**
 * Определить тип смены по времени начала
 */
const getShiftType = (startTime: Date, currentShiftType: ShiftType, offset: number): ShiftType => {
  // Если offset четный - тот же тип, если нечетный - противоположный
  const totalShifts = offset;
  return (Math.abs(totalShifts) % 2 === 0) ? currentShiftType : (currentShiftType === 'day' ? 'night' : 'day');
};

/**
 * Получить массив из 5 смен для отображения на timeline
 * Порядок: [-2, -1, 0 (текущая), +1, +2]
 */
export const getTimelineShifts = (currentTime?: Date): Shift[] => {
  const now = currentTime || getCurrentTimeGMT3();
  const { type: currentType, startTime: currentStart } = getCurrentShiftInfo(now);

  const shifts: Shift[] = [];

  // Генерируем 5 смен: -2, -1, 0, +1, +2
  for (let offset = -2; offset <= 2; offset++) {
    const shiftStart = getShiftStart(currentStart, currentType, offset);
    const shiftEnd = new Date(shiftStart);
    shiftEnd.setHours(shiftEnd.getHours() + SHIFT_DURATION_HOURS);

    const shiftType = getShiftType(shiftStart, currentType, offset);
    const isCurrentShift = offset === 0;

    shifts.push({
      type: shiftType,
      startTime: shiftStart,
      endTime: shiftEnd,
      label: shiftType === 'day' ? 'Дневная смена' : 'Ночная смена',
      isCurrentShift
    });
  }

  return shifts;
};

/**
 * Рассчитать позицию задания на timeline (в процентах, 0-100)
 *
 * @param startTime - время начала задания
 * @param currentTime - текущее время
 * @returns позиция в процентах от начала timeline (0 = начало первой смены, 100 = конец последней смены)
 */
export const calculateJobPosition = (startTime: Date, currentTime: Date): number => {
  const { startTime: currentShiftStart } = getCurrentShiftInfo(currentTime);

  // Начало timeline = начало первой смены (-2 смены от текущей)
  const timelineStart = getShiftStart(currentShiftStart, 'day', -2);
  const timelineStart_ms = timelineStart.getTime();

  // Общая длительность timeline в миллисекундах
  const totalDuration_ms = TIMELINE_TOTAL_HOURS * 60 * 60 * 1000;

  // Смещение задания от начала timeline
  const jobOffset_ms = startTime.getTime() - timelineStart_ms;

  // Позиция в процентах
  const position = (jobOffset_ms / totalDuration_ms) * 100;

  return Math.max(0, Math.min(100, position)); // Ограничиваем 0-100%
};

/**
 * Рассчитать ширину задания на timeline (в процентах)
 *
 * @param startTime - время начала задания
 * @param endTime - время окончания задания
 * @returns ширина в процентах от общей ширины timeline
 */
export const calculateJobWidth = (startTime: Date, endTime: Date): number => {
  const totalDuration_ms = TIMELINE_TOTAL_HOURS * 60 * 60 * 1000;
  const jobDuration_ms = endTime.getTime() - startTime.getTime();

  const width = (jobDuration_ms / totalDuration_ms) * 100;

  return Math.max(0.1, Math.min(100, width)); // Минимум 0.1% для видимости
};

/**
 * Проверить, видно ли задание в текущем диапазоне timeline (5 смен)
 */
export const isJobVisible = (startTime: Date, endTime: Date, currentTime: Date): boolean => {
  const { startTime: currentShiftStart } = getCurrentShiftInfo(currentTime);

  // Диапазон timeline
  const timelineStart = getShiftStart(currentShiftStart, 'day', -2);
  const timelineEnd = getShiftStart(currentShiftStart, 'day', 3); // +3 смены

  // Задание видно если оно пересекается с timeline
  return !(endTime < timelineStart || startTime > timelineEnd);
};

/**
 * Получить позицию смены на timeline (в процентах)
 */
export const calculateShiftPosition = (shift: Shift, currentTime: Date): { left: number; width: number } => {
  const { startTime: currentShiftStart } = getCurrentShiftInfo(currentTime);
  const timelineStart = getShiftStart(currentShiftStart, 'day', -2);
  const totalDuration_ms = TIMELINE_TOTAL_HOURS * 60 * 60 * 1000;

  // Позиция начала смены
  const shiftOffset_ms = shift.startTime.getTime() - timelineStart.getTime();
  const left = (shiftOffset_ms / totalDuration_ms) * 100;

  // Ширина смены
  const shiftDuration_ms = SHIFT_DURATION_HOURS * 60 * 60 * 1000;
  const width = (shiftDuration_ms / totalDuration_ms) * 100;

  return { left, width };
};

/**
 * Форматировать время смены для отображения
 */
export const formatShiftTime = (shift: Shift): string => {
  const hours = shift.startTime.getHours();
  return `${hours.toString().padStart(2, '0')}:00`;
};
