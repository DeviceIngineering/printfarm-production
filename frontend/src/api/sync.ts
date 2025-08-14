import apiClient from './client';

export interface SyncStatus {
  is_syncing: boolean;
  sync_id?: number;
  started_at?: string;
  total_products?: number;
  synced_products?: number;
  current_article?: string;
  last_sync?: string;
}

export interface SyncHistory {
  id: number;
  sync_type: 'manual' | 'scheduled';
  status: 'pending' | 'success' | 'failed' | 'partial';
  started_at: string;
  finished_at?: string;
  warehouse_name: string;
  total_products: number;
  synced_products: number;
  failed_products: number;
  success_rate: number;
  duration?: number;
}

export interface Warehouse {
  id: string;
  name: string;
  code: string;
}

export interface ProductGroup {
  id: string;
  name: string;
  pathName: string;
  code?: string;
  archived?: boolean;
  parent?: {
    id: string;
    name: string;
  } | null;
}

export interface StartSyncParams {
  warehouse_id: string;
  excluded_groups?: string[];
  sync_images?: boolean;
}

export interface DownloadImagesParams {
  limit?: number;
}

export interface DownloadSpecificImagesParams {
  articles: string[];
}

export interface ImageDownloadResult {
  message: string;
  synced_products: number;
  total_images: number;
  processed_products?: number;
  remaining_without_images?: number;
}

// Enhanced sync API with better error handling
export const syncApi = {
  getStatus: async (): Promise<SyncStatus> => {
    try {
      return await apiClient.get('/sync/status/');
    } catch (error) {
      console.error('🔄 Failed to get sync status:', error);
      // Return default status if API fails
      return {
        is_syncing: false,
        last_sync: null,
      };
    }
  },

  getHistory: async (): Promise<SyncHistory[]> => {
    try {
      return await apiClient.get('/sync/history/');
    } catch (error) {
      console.error('📊 Failed to get sync history:', error);
      return [];
    }
  },

  getWarehouses: async (): Promise<Warehouse[]> => {
    try {
      console.log('🏭 Fetching warehouses...');
      const warehouses = await apiClient.get('/sync/warehouses/');
      console.log('✅ Warehouses loaded:', warehouses?.length || 0);
      return warehouses || [];
    } catch (error) {
      console.error('🏭 Failed to get warehouses:', error);
      // Try to provide helpful debugging info
      if (error?.response?.status === 0) {
        console.error('🌐 Network error - backend may not be accessible');
        console.error('Check if backend is running and CORS is configured');
      } else if (error?.response?.status === 500) {
        console.error('🔥 Server error - MoySklad API may be down or misconfigured');
      }
      return [];
    }
  },

  getProductGroups: async (): Promise<ProductGroup[]> => {
    try {
      console.log('📂 Fetching product groups...');
      const groups = await apiClient.get('/sync/product-groups/');
      console.log('✅ Product groups loaded:', groups?.length || 0);
      return groups || [];
    } catch (error) {
      console.error('📂 Failed to get product groups:', error);
      // Try to provide helpful debugging info
      if (error?.response?.status === 0) {
        console.error('🌐 Network error - backend may not be accessible');
      } else if (error?.response?.status === 500) {
        console.error('🔥 Server error - MoySklad API may be down or misconfigured');
        console.error('Check MoySklad token and API access');
      }
      return [];
    }
  },

  // Settings API with fallback
  getProductGroupsFromSettings: async (): Promise<{ product_groups: ProductGroup[]; total: number }> => {
    try {
      return await apiClient.get('/settings/product-groups/');
    } catch (error) {
      console.error('⚙️ Failed to get product groups from settings:', error);
      // Fallback to regular sync API
      try {
        const groups = await syncApi.getProductGroups();
        return { product_groups: groups, total: groups.length };
      } catch (fallbackError) {
        console.error('⚙️ Fallback also failed:', fallbackError);
        return { product_groups: [], total: 0 };
      }
    }
  },

  startSync: async (params: StartSyncParams) => {
    try {
      console.log('🚀 Starting sync with params:', params);
      return await apiClient.post('/sync/start/', params);
    } catch (error) {
      console.error('🚀 Failed to start sync:', error);
      throw error; // Re-throw for UI handling
    }
  },

  downloadImages: async (params?: DownloadImagesParams): Promise<ImageDownloadResult> => {
    try {
      return await apiClient.post('/sync/download-images/', params || {});
    } catch (error) {
      console.error('🖼️ Failed to download images:', error);
      return {
        message: 'Failed to download images',
        synced_products: 0,
        total_images: 0,
      };
    }
  },

  downloadSpecificImages: async (params: DownloadSpecificImagesParams): Promise<ImageDownloadResult> => {
    try {
      return await apiClient.post('/sync/download-specific-images/', params);
    } catch (error) {
      console.error('🖼️ Failed to download specific images:', error);
      return {
        message: 'Failed to download specific images',
        synced_products: 0,
        total_images: 0,
      };
    }
  },
};