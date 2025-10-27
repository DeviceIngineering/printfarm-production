/**
 * Printer Data Mapper
 *
 * Преобразование данных SimplePrint в формат Planning V2
 */

import { PrinterSnapshot } from '../../../types/simpleprint.types';
import { Printer, PrinterStatus, PrintTask, MaterialColor } from '../types/printer.types';

/**
 * Извлечь артикул из имени файла
 * Например: "444-52148_part2_20pcs_14h5m_347g_white.gcode.3mf" → "444-52148"
 */
export function extractArticleFromFilename(filename: string | null): string {
  if (!filename) return '';

  // Паттерн: числа-числа в начале строки
  const match = filename.match(/^(\d+-\d+)/);
  return match ? match[1] : '';
}

/**
 * Преобразовать состояние SimplePrint в наш PrinterStatus
 */
export function mapSimplePrintStateToStatus(state: string): PrinterStatus {
  switch (state) {
    case 'printing':
      return 'printing';
    case 'idle':
      return 'idle';
    case 'offline':
    case 'error':
      return 'error';
    case 'paused':
      return 'idle'; // Paused показываем как idle
    default:
      return 'error';
  }
}

/**
 * Форматировать оставшееся время
 */
function formatTimeRemaining(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}ч ${minutes}м`;
  }
  return `${minutes}м`;
}

/**
 * Преобразовать SimplePrint printer в наш формат Printer
 */
export function mapSimplePrintToPrinter(snapshot: PrinterSnapshot): Printer {
  const status = mapSimplePrintStateToStatus(snapshot.state);

  // Создаем задачу если принтер печатает
  let currentTask: PrintTask | null = null;
  if (snapshot.state === 'printing' && snapshot.job_start_time && snapshot.job_end_time_estimate) {
    // Пытаемся извлечь артикул, если не получается - используем имя файла
    const article = extractArticleFromFilename(snapshot.job_file);
    const displayName = article || snapshot.job_file || 'Неизвестное задание';

    currentTask = {
      article: displayName,
      quantity: 1,  // Не доступно в API
      progress: snapshot.percentage,
      timeRemaining: formatTimeRemaining(snapshot.time_remaining_seconds),
      startTime: new Date(snapshot.job_start_time),
      endTime: new Date(snapshot.job_end_time_estimate),
    };
  }

  return {
    id: snapshot.printer_name, // Используем имя как ID (P1S-2, P1S-3, etc.)
    name: snapshot.printer_name,
    status: status,
    materialColor: 'other' as MaterialColor,  // Не доступно в API
    currentTask: currentTask,
    queuedTasks: [],  // Не доступно в текущей версии API
    temperature: {
      hotend: snapshot.temperature_nozzle || 0,
      bed: snapshot.temperature_bed || 0,
    },
  };
}

/**
 * Преобразовать массив снимков SimplePrint в массив принтеров
 */
export function mapSimplePrintsToPrinters(snapshots: PrinterSnapshot[]): Printer[] {
  // Проверка на undefined или null
  if (!snapshots || !Array.isArray(snapshots)) {
    return [];
  }
  return snapshots.map(mapSimplePrintToPrinter);
}
