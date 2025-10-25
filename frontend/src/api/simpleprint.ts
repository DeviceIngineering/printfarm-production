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
  getPrinters: async (): Promise<PrinterSnapshot[]> => {
    const response = await apiClient.get<PrinterSnapshot[]>('/simpleprint/printers/');
    return response.data;
  },

  /**
   * Запустить ручную синхронизацию принтеров
   */
  syncPrinters: async (): Promise<PrinterSyncResult> => {
    const response = await apiClient.post<PrinterSyncResult>('/simpleprint/printers/sync/');
    return response.data;
  },

  /**
   * Получить статистику принтеров
   */
  getStats: async (): Promise<PrinterStats> => {
    const response = await apiClient.get<PrinterStats>('/simpleprint/printers/stats/');
    return response.data;
  },
};
