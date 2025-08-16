import { apiClient } from './client';

// Типы данных для Tochka модуля
export interface ExcelDataItem {
  article: string;
  orders: number;
  row_number?: number;
  has_duplicates?: boolean;
  duplicate_rows?: number[] | null;
}

export interface MergedDataItem extends ExcelDataItem {
  product_name?: string | null;
  current_stock?: number | null;
  sales_last_2_months?: number | null;
  product_type?: string | null;
  production_needed?: number | null;
  production_priority?: number | null;
  product_matched: boolean;
  has_product_data: boolean;
}

export interface FilteredProductionItem {
  article: string;
  product_name: string;
  production_needed: number;
  production_priority: number;
  is_in_tochka: boolean;
  needs_registration: boolean;
}

export interface TochkaProduct {
  id: number;
  article: string;
  name: string;
  product_type: string;
  current_stock: string;
  reserved_stock: string;
  effective_stock: number;
  sales_last_2_months: string;
  production_needed: string;
  production_priority: number;
}

export interface TochkaProductsResponse {
  results: TochkaProduct[];
  count: number;
  next: string | null;
  previous: string | null;
}

export interface TochkaProductionResponse {
  results: TochkaProduct[];
  count: number;
  next: string | null;
  previous: string | null;
}

export interface UploadExcelResponse {
  message: string;
  data: ExcelDataItem[];
  total_records: number;
  unique_articles: number;
}

export interface MergeWithProductsResponse {
  message: string;
  data: MergedDataItem[];
  coverage_rate: string;
  found_products: number;
  total_articles: number;
}

export interface FilteredProductionResponse {
  message: string;
  data: FilteredProductionItem[];
  total_products: number;
  products_in_tochka: number;
  products_need_registration: number;
}

export interface ExportResponse {
  message: string;
  download_url: string;
}

export interface AutoProcessResponse {
  success: boolean;
  processing_time_seconds: number;
  upload_result: {
    message: string;
    data: ExcelDataItem[];
    total_records: number;
    unique_articles: number;
  };
  analysis_result: {
    message: string;
    merged_data: MergedDataItem[];
    coverage_rate: number;
    found_products: number;
    total_articles: number;
  };
  production_result: {
    message: string;
    filtered_production: FilteredProductionItem[];
    total_products: number;
    products_in_tochka: number;
    products_need_registration: number;
  };
  summary: {
    excel_file_processed: boolean;
    analysis_completed: boolean;
    production_list_ready: boolean;
    total_excel_records: number;
    products_found_in_db: number;
    coverage_percentage: number;
    production_items_count: number;
  };
}

// API функции
export const tochkaApi = {
  // Получить товары Точки
  getProducts: (params?: { page?: number; page_size?: number }): Promise<TochkaProductsResponse> =>
    apiClient.get('/tochka/products/', { params }),

  // Получить список на производство
  getProduction: (params?: { page?: number; page_size?: number }): Promise<TochkaProductionResponse> =>
    apiClient.get('/tochka/production/', { params }),

  // Загрузить Excel файл
  uploadExcelFile: (file: File): Promise<UploadExcelResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/tochka/upload-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Объединить Excel данные с товарами (Анализ производства)
  mergeWithProducts: (excelData: ExcelDataItem[]): Promise<MergeWithProductsResponse> =>
    apiClient.post('/tochka/merge-with-products/', {
      excel_data: excelData,
    }),

  // Получить отфильтрованный список производства
  getFilteredProduction: (excelData: ExcelDataItem[]): Promise<FilteredProductionResponse> =>
    apiClient.post('/tochka/filtered-production/', {
      excel_data: excelData,
    }),

  // Экспорт дедуплицированных данных
  exportDeduplicated: (excelData: ExcelDataItem[]): Promise<ExportResponse> =>
    apiClient.post('/tochka/export-deduplicated/', {
      excel_data: excelData,
    }),

  // Экспорт списка производства
  exportProduction: (productionData: FilteredProductionItem[]): Promise<ExportResponse> =>
    apiClient.post('/tochka/export-production/', {
      production_data: productionData,
    }),

  // Автоматическая обработка Excel файла (загрузка + анализ + список производства)
  uploadAndAutoProcess: (file: File): Promise<AutoProcessResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/tochka/upload-and-auto-process/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};