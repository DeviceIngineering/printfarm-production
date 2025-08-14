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

// Enhanced API functions with robust error handling
export const settingsApi = {
  // Получить информацию о системе
  getSystemInfo: async (): Promise<SystemInfo> => {
    try {
      console.log('🔧 Fetching system info...');
      const info = await apiClient.get('/settings/system-info/');
      console.log('✅ System info loaded:', info);
      return info;
    } catch (error) {
      console.error('🔧 Failed to get system info:', error);
      // Return fallback system info
      return {
        version: 'v3.3.4',
        build_date: 'Unknown',
      };
    }
  },

  // Получить сводную информацию
  getSettingsSummary: async (): Promise<SettingsSummary> => {
    try {
      console.log('📊 Fetching settings summary...');
      const summary = await apiClient.get('/settings/summary/');
      console.log('✅ Settings summary loaded');
      return summary;
    } catch (error) {
      console.error('📊 Failed to get settings summary:', error);
      // Return fallback summary
      const fallbackSystemInfo = await settingsApi.getSystemInfo();
      return {
        system_info: fallbackSystemInfo,
        sync_settings: {
          sync_enabled: false,
          sync_interval_minutes: 60,
          sync_interval_display: '1 час',
          warehouse_id: '',
          warehouse_name: '',
          excluded_group_ids: [],
          excluded_group_names: [],
          last_sync_at: null,
          last_sync_status: 'never',
          last_sync_message: '',
          next_sync_time: null,
          total_syncs: 0,
          successful_syncs: 0,
          sync_success_rate: 0,
        },
        general_settings: {
          default_new_product_stock: 10,
          default_target_days: 15,
          low_stock_threshold: 5,
          products_per_page: 100,
          show_images: true,
          auto_refresh_interval: 30,
        },
        total_products: 0,
        last_sync_info: {
          date: null,
          status: 'never',
          total_products: 0,
          synced_products: 0,
        },
        system_status: {
          sync_enabled: false,
          next_sync: null,
          database_healthy: false,
          api_healthy: false,
        },
      };
    }
  },

  // Настройки синхронизации
  getSyncSettings: async (): Promise<SyncSettings> => {
    try {
      return await apiClient.get('/settings/sync/');
    } catch (error) {
      console.error('🔄 Failed to get sync settings:', error);
      throw error;
    }
  },
  
  updateSyncSettings: async (data: Partial<SyncSettings>): Promise<SyncSettings> => {
    try {
      return await apiClient.put('/settings/sync/', data);
    } catch (error) {
      console.error('🔄 Failed to update sync settings:', error);
      throw error;
    }
  },

  // Общие настройки
  getGeneralSettings: async (): Promise<GeneralSettings> => {
    try {
      return await apiClient.get('/settings/general/');
    } catch (error) {
      console.error('⚙️ Failed to get general settings:', error);
      throw error;
    }
  },
  
  updateGeneralSettings: async (data: Partial<GeneralSettings>): Promise<GeneralSettings> => {
    try {
      return await apiClient.put('/settings/general/', data);
    } catch (error) {
      console.error('⚙️ Failed to update general settings:', error);
      throw error;
    }
  },

  // Действия
  testSyncConnection: async (): Promise<ActionResponse> => {
    try {
      console.log('🔗 Testing MoySklad connection...');
      const result = await apiClient.post('/settings/sync/test-connection/');
      console.log('✅ Connection test result:', result);
      return result;
    } catch (error) {
      console.error('🔗 Connection test failed:', error);
      return {
        success: false,
        message: 'Не удалось подключиться к МойСклад. Проверьте настройки API.',
      };
    }
  },

  triggerManualSync: async (data?: { warehouse_id?: string; excluded_groups?: string[] }): Promise<ActionResponse> => {
    try {
      console.log('🚀 Triggering manual sync...', data);
      return await apiClient.post('/settings/sync/trigger-manual/', data || {});
    } catch (error) {
      console.error('🚀 Manual sync failed:', error);
      return {
        success: false,
        message: 'Не удалось запустить синхронизацию',
      };
    }
  },

  // Управление расписанием
  getScheduleStatus: async (): Promise<any> => {
    try {
      return await apiClient.get('/settings/schedule/status/');
    } catch (error) {
      console.error('📅 Failed to get schedule status:', error);
      return {
        enabled: false,
        next_run: null,
      };
    }
  },

  updateSchedule: async (data: { interval_minutes: number; enabled: boolean }): Promise<ActionResponse> => {
    try {
      return await apiClient.post('/settings/schedule/update/', data);
    } catch (error) {
      console.error('📅 Failed to update schedule:', error);
      return {
        success: false,
        message: 'Не удалось обновить расписание',
      };
    }
  },

  // Получить список складов
  getWarehouses: async (): Promise<WarehousesResponse> => {
    try {
      console.log('🏭 Fetching warehouses from settings...');
      const result = await apiClient.get('/settings/warehouses/');
      console.log('✅ Settings warehouses loaded:', result?.total || 0);
      return result;
    } catch (error) {
      console.error('🏭 Failed to get warehouses from settings:', error);
      return {
        warehouses: [],
        total: 0,
      };
    }
  },
};