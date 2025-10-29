/**
 * Типы для принтеров и заданий печати
 */

export type PrinterStatus = 'printing' | 'idle' | 'error';
export type MaterialColor = 'black' | 'white' | 'other';
export type JobStatus = 'queued' | 'printing' | 'completed' | 'cancelled' | 'failed';

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

// === Timeline Types ===

/**
 * Задание для timeline (из API /api/v1/simpleprint/timeline-jobs/)
 */
export interface TimelineJob {
  job_id: string;
  article: string | null;
  file_name: string;
  status: JobStatus;
  percentage: number;
  started_at: string; // ISO datetime string
  completed_at: string | null;
  duration_seconds: number;
  material_color: MaterialColor;
}

/**
 * Принтер с заданиями для timeline
 */
export interface TimelinePrinter {
  id: string;
  name: string;
  jobs: TimelineJob[];
}

/**
 * Ответ API для timeline-jobs
 */
export interface TimelineJobsResponse {
  printers: TimelinePrinter[];
}
