/**
 * Типы для принтеров и заданий печати
 */

export type PrinterStatus = 'printing' | 'idle' | 'error';
export type MaterialColor = 'black' | 'white' | 'other';

export interface PrintTask {
  article: string;
  quantity: number;
  progress: number; // 0-100%
  timeRemaining: string; // "1ч 20м"
  startTime: Date;
  endTime: Date;
}

export interface Printer {
  id: string; // "P1S-1"
  name: string; // "Принтер 1"
  status: PrinterStatus;
  materialColor: MaterialColor;
  currentTask: PrintTask | null;
  queuedTasks: PrintTask[];
  temperature?: {
    hotend: number;
    bed: number;
  };
}
