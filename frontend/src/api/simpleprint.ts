/**
 * SimplePrint API Client
 *
 * API функции для работы с данными принтеров SimplePrint
 */

import apiClient from './client';
import { PrinterSnapshot, PrinterSyncResult, PrinterStats } from '../types/simpleprint.types';

export const simplePrintApi = {
  /**
   * Получить последние снимки всех принтеров
   */
  getPrinters: (): Promise<PrinterSnapshot[]> =>
    apiClient.get('/simpleprint/printers/'),

  /**
   * Запустить ручную синхронизацию принтеров
   */
  syncPrinters: (): Promise<PrinterSyncResult> =>
    apiClient.post('/simpleprint/printers/sync/'),

  /**
   * Получить статистику принтеров
   */
  getStats: (): Promise<PrinterStats> =>
    apiClient.get('/simpleprint/printers/stats/'),
};
