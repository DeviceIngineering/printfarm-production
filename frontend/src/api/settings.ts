import { apiClient } from './client';

// Типы данных для настроек
export interface SystemInfo {
  version: string;
  build_date: string;
}

export interface SyncSettings {
  sync_enabled: boolean;
  sync_interval_minutes: number;
  sync_interval_display: string;
  warehouse_id: string;
  warehouse_name: string;
  excluded_group_ids: string[];
  excluded_group_names: string[];
  last_sync_at: string | null;
  last_sync_status: string;
  last_sync_message: string;
  next_sync_time: string | null;
  total_syncs: number;
  successful_syncs: number;
  sync_success_rate: number;
}

export interface GeneralSettings {
  default_new_product_stock: number;
  default_target_days: number;
  low_stock_threshold: number;
  products_per_page: number;
  show_images: boolean;
  auto_refresh_interval: number;
}

export interface SettingsSummary {
  system_info: SystemInfo;
  sync_settings: SyncSettings;
  general_settings: GeneralSettings;
  total_products: number;
  last_sync_info: {
    date: string | null;
    status: string;
    total_products: number;
    synced_products: number;
  };
  system_status: {
    sync_enabled: boolean;
    next_sync: string | null;
    database_healthy: boolean;
    api_healthy: boolean;
  };
}

export interface ActionResponse {
  success: boolean;
  message: string;
  [key: string]: any;
}

export interface Warehouse {
  id: string;
  name: string;
  description?: string;
  archived: boolean;
}

export interface WarehousesResponse {
  warehouses: Warehouse[];
  total: number;
}

// API функции
export const settingsApi = {
  // Получить информацию о системе
  getSystemInfo: (): Promise<SystemInfo> =>
    apiClient.get('/settings/system-info/'),

  // Получить сводную информацию
  getSettingsSummary: (): Promise<SettingsSummary> =>
    apiClient.get('/settings/summary/'),

  // Настройки синхронизации
  getSyncSettings: (): Promise<SyncSettings> =>
    apiClient.get('/settings/sync/'),
  
  updateSyncSettings: (data: Partial<SyncSettings>): Promise<SyncSettings> =>
    apiClient.put('/settings/sync/', data),

  // Общие настройки
  getGeneralSettings: (): Promise<GeneralSettings> =>
    apiClient.get('/settings/general/'),
  
  updateGeneralSettings: (data: Partial<GeneralSettings>): Promise<GeneralSettings> =>
    apiClient.put('/settings/general/', data),

  // Действия
  testSyncConnection: (): Promise<ActionResponse> =>
    apiClient.post('/settings/sync/test-connection/'),

  triggerManualSync: (data?: { warehouse_id?: string; excluded_groups?: string[] }): Promise<ActionResponse> =>
    apiClient.post('/settings/sync/trigger-manual/', data || {}),

  // Управление расписанием
  getScheduleStatus: (): Promise<any> =>
    apiClient.get('/settings/schedule/status/'),

  updateSchedule: (data: { interval_minutes: number; enabled: boolean }): Promise<ActionResponse> =>
    apiClient.post('/settings/schedule/update/', data),

  // Получить список складов
  getWarehouses: (): Promise<WarehousesResponse> =>
    apiClient.get('/settings/warehouses/'),
};