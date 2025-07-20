import apiClient from './client';

export interface Product {
  id: number;
  article: string;
  name: string;
  product_type: 'new' | 'old' | 'critical';
  current_stock: number;
  production_needed: number;
  production_priority: number;
  days_of_stock?: number;
  sales_last_2_months: number;
  average_daily_consumption: number;
  main_image?: string;
  last_synced_at?: string;
}

export interface ProductDetail extends Product {
  moysklad_id: string;
  description: string;
  product_group_id: string;
  product_group_name: string;
  images: ProductImage[];
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: number;
  image: string;
  thumbnail: string;
  moysklad_url: string;
  is_main: boolean;
  created_at: string;
}

export interface ProductStats {
  total_products: number;
  new_products: number;
  old_products: number;
  critical_products: number;
  production_needed_items: number;
  total_production_units: number;
}

export interface ProductListParams {
  page?: number;
  page_size?: number;
  search?: string;
  product_type?: string;
  product_group_id?: string;
  min_stock?: number;
  max_stock?: number;
  min_priority?: number;
  production_needed?: boolean;
  ordering?: string;
}

export interface ProductListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
}

export interface ProductionListItem {
  priority: number;
  article: string;
  name: string;
  current_stock: number;
  quantity: number;
  product_type: string;
  production_priority: number;
  group_name: string;
}

export interface ProductionList {
  id: number;
  created_at: string;
  total_items: number;
  total_units: number;
  items: ProductionListItem[];
}

export interface ProductionStats {
  total_products_needing_production: number;
  critical_priority_count: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  total_units_needed: number;
  by_type: {
    [key: string]: {
      count: number;
      total_needed: number;
    };
  };
}

export const productsApi = {
  // Products
  getProducts: (params?: ProductListParams): Promise<ProductListResponse> =>
    apiClient.get('/products/', { params }).then(res => res.data),

  getProduct: (id: number): Promise<ProductDetail> =>
    apiClient.get(`/products/${id}/`).then(res => res.data),

  getProductStats: (): Promise<ProductStats> =>
    apiClient.get('/products/stats/').then(res => res.data),

  // Production
  calculateProductionList: (params?: { min_priority?: number; apply_coefficients?: boolean }) =>
    apiClient.post('/products/production/calculate/', params).then(res => res.data),

  getProductionList: (listId?: number): Promise<ProductionList> => {
    const url = listId ? `/products/production/list/${listId}/` : '/products/production/list/';
    return apiClient.get(url).then(res => res.data);
  },

  getProductionStats: (): Promise<ProductionStats> =>
    apiClient.get('/products/production/stats/').then(res => res.data),

  recalculateProduction: () =>
    apiClient.post('/products/production/recalculate/').then(res => res.data),

  // Export
  exportProducts: (params?: ProductListParams) => {
    const queryParams = new URLSearchParams();
    
    // Add auth token to query params for file download
    const token = localStorage.getItem('auth_token');
    if (token) {
      queryParams.append('auth_token', token);
    }
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    
    const url = `/reports/export/products/?${queryParams.toString()}`;
    window.open(`${apiClient.defaults.baseURL}${url}`, '_blank');
  },

  exportProductionList: () => {
    const token = localStorage.getItem('auth_token');
    const queryParams = new URLSearchParams();
    if (token) {
      queryParams.append('auth_token', token);
    }
    
    const url = `/reports/export/production-list/?${queryParams.toString()}`;
    window.open(`${apiClient.defaults.baseURL}${url}`, '_blank');
  },
};