/**
 * SimplePrint API Types
 *
 * TypeScript типы для работы с SimplePrint API принтеров
 */

export interface PrinterSnapshot {
  id: number;
  printer_id: string;
  printer_name: string;
  state: 'printing' | 'idle' | 'offline' | 'paused' | 'error';
  state_display: string;
  online: boolean;

  // Job information
  job_id: string | null;
  job_file: string | null;

  // Progress
  percentage: number;
  current_layer: number;
  max_layer: number;
  elapsed_time: number; // seconds

  // Temperatures
  temperature_nozzle: number | null;
  temperature_bed: number | null;
  temperature_ambient: number | null;

  // Calculated times (ISO datetime strings)
  job_start_time: string | null;
  job_end_time_estimate: string | null;
  idle_since: string | null;

  // Computed fields
  idle_duration_seconds: number;
  time_remaining_seconds: number;

  // Metadata
  created_at: string;
  updated_at: string;
}

export interface PrinterSyncResult {
  synced: number;
  failed: number;
  printers: Array<{
    printer_id: string;
    printer_name: string;
    state: string;
    percentage: number;
  }>;
}

export interface PrinterStats {
  total: number;
  printing: number;
  idle: number;
  offline: number;
  error: number;
  online: number;
}
