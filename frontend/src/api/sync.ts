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

export const syncApi = {
  getStatus: (): Promise<SyncStatus> =>
    apiClient.get('/sync/status/'),

  getHistory: (): Promise<SyncHistory[]> =>
    apiClient.get('/sync/history/'),

  getWarehouses: (): Promise<Warehouse[]> =>
    apiClient.get('/sync/warehouses/'),

  getProductGroups: (): Promise<ProductGroup[]> =>
    apiClient.get('/sync/product-groups/'),

  // Settings API
  getProductGroupsFromSettings: (): Promise<{ product_groups: ProductGroup[]; total: number }> =>
    apiClient.get('/settings/product-groups/'),

  startSync: (params: StartSyncParams) =>
    apiClient.post('/sync/start/', params),

  downloadImages: (params?: DownloadImagesParams): Promise<ImageDownloadResult> =>
    apiClient.post('/sync/download-images/', params || {}),

  downloadSpecificImages: (params: DownloadSpecificImagesParams): Promise<ImageDownloadResult> =>
    apiClient.post('/sync/download-specific-images/', params),
};