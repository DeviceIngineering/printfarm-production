import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  tochkaApi, 
  TochkaProduct, 
  ExcelDataItem, 
  MergedDataItem, 
  FilteredProductionItem,
  TochkaProductsResponse,
  TochkaProductionResponse,
  UploadExcelResponse,
  MergeWithProductsResponse,
  FilteredProductionResponse,
  ExportResponse,
  AutoProcessResponse
} from '../../api/tochka';

interface TochkaState {
  // Основные данные
  products: TochkaProduct[];
  production: TochkaProduct[];
  
  // Excel данные
  excelData: ExcelDataItem[];
  deduplicatedExcelData: ExcelDataItem[];
  
  // Результаты анализа
  mergedData: MergedDataItem[];
  filteredProductionData: FilteredProductionItem[];
  
  // Статистика
  coverage: {
    rate: string;
    found_products: number;
    total_articles: number;
  } | null;
  
  productionStats: {
    total_products: number;
    products_in_tochka: number;
    products_need_registration: number;
  } | null;
  
  // Состояния загрузки
  loading: {
    products: boolean;
    production: boolean;
    upload: boolean;
    merge: boolean;
    filter: boolean;
    export: boolean;
    autoProcess: boolean;
  };
  
  // Ошибки
  error: string | null;
  
  // Пагинация
  pagination: {
    products: {
      current: number;
      pageSize: number;
      total: number;
    };
    production: {
      current: number;
      pageSize: number;
      total: number;
    };
  };
}

const initialState: TochkaState = {
  products: [],
  production: [],
  excelData: [],
  deduplicatedExcelData: [],
  mergedData: [],
  filteredProductionData: [],
  coverage: null,
  productionStats: null,
  loading: {
    products: false,
    production: false,
    upload: false,
    merge: false,
    filter: false,
    export: false,
    autoProcess: false,
  },
  error: null,
  pagination: {
    products: {
      current: 1,
      pageSize: 20,
      total: 0,
    },
    production: {
      current: 1,
      pageSize: 20,
      total: 0,
    },
  },
};

// Async thunks
export const fetchTochkaProducts = createAsyncThunk(
  'tochka/fetchProducts',
  async (params?: { page?: number; page_size?: number }) => {
    const response = await tochkaApi.getProducts(params);
    return response;
  }
);

export const fetchTochkaProduction = createAsyncThunk(
  'tochka/fetchProduction',
  async (params?: { page?: number; page_size?: number }) => {
    const response = await tochkaApi.getProduction(params);
    return response;
  }
);

export const uploadExcelFile = createAsyncThunk(
  'tochka/uploadExcelFile',
  async (file: File) => {
    const response = await tochkaApi.uploadExcelFile(file);
    return response;
  }
);

export const mergeWithProducts = createAsyncThunk(
  'tochka/mergeWithProducts',
  async (excelData: ExcelDataItem[]) => {
    const response = await tochkaApi.mergeWithProducts(excelData);
    return response;
  }
);

export const getFilteredProduction = createAsyncThunk(
  'tochka/getFilteredProduction',
  async (excelData: ExcelDataItem[]) => {
    const response = await tochkaApi.getFilteredProduction(excelData);
    return response;
  }
);

export const exportDeduplicated = createAsyncThunk(
  'tochka/exportDeduplicated',
  async (excelData: ExcelDataItem[]) => {
    const response = await tochkaApi.exportDeduplicated(excelData);
    return response;
  }
);

export const exportProduction = createAsyncThunk(
  'tochka/exportProduction',
  async (productionData: FilteredProductionItem[]) => {
    const response = await tochkaApi.exportProduction(productionData);
    return response;
  }
);

// Автоматическая обработка Excel файла
export const uploadAndAutoProcess = createAsyncThunk(
  'tochka/uploadAndAutoProcess',
  async (file: File) => {
    const response = await tochkaApi.uploadAndAutoProcess(file);
    return response;
  }
);

const tochkaSlice = createSlice({
  name: 'tochka',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    
    clearExcelData: (state) => {
      state.excelData = [];
      state.deduplicatedExcelData = [];
      state.mergedData = [];
      state.filteredProductionData = [];
      state.coverage = null;
      state.productionStats = null;
    },
    
    setProductsPagination: (state, action: PayloadAction<{ current: number; pageSize: number }>) => {
      state.pagination.products = { ...state.pagination.products, ...action.payload };
    },
    
    setProductionPagination: (state, action: PayloadAction<{ current: number; pageSize: number }>) => {
      state.pagination.production = { ...state.pagination.production, ...action.payload };
    },
    
    // Функция для создания дедуплицированных данных
    createDeduplicatedData: (state) => {
      if (state.excelData.length === 0) return;
      
      const articleMap = new Map<string, ExcelDataItem>();
      
      state.excelData.forEach((item) => {
        const article = item.article;
        if (articleMap.has(article)) {
          const existing = articleMap.get(article)!;
          existing.orders += item.orders;
          existing.has_duplicates = true;
          existing.duplicate_rows = existing.duplicate_rows || [];
          existing.duplicate_rows.push(item.row_number || 0);
        } else {
          articleMap.set(article, {
            ...item,
            has_duplicates: false,
            duplicate_rows: null,
          });
        }
      });
      
      // Сортируем по убыванию количества заказов
      state.deduplicatedExcelData = Array.from(articleMap.values())
        .sort((a, b) => b.orders - a.orders);
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch products
      .addCase(fetchTochkaProducts.pending, (state) => {
        state.loading.products = true;
        state.error = null;
      })
      .addCase(fetchTochkaProducts.fulfilled, (state, action) => {
        state.loading.products = false;
        state.products = action.payload.results || [];
        state.pagination.products.total = action.payload.count || 0;
      })
      .addCase(fetchTochkaProducts.rejected, (state, action) => {
        state.loading.products = false;
        state.error = action.error.message || 'Failed to fetch products';
      })
      
      // Fetch production
      .addCase(fetchTochkaProduction.pending, (state) => {
        state.loading.production = true;
        state.error = null;
      })
      .addCase(fetchTochkaProduction.fulfilled, (state, action) => {
        state.loading.production = false;
        state.production = action.payload.results || [];
        state.pagination.production.total = action.payload.count || 0;
      })
      .addCase(fetchTochkaProduction.rejected, (state, action) => {
        state.loading.production = false;
        state.error = action.error.message || 'Failed to fetch production';
      })
      
      // Upload Excel file
      .addCase(uploadExcelFile.pending, (state) => {
        state.loading.upload = true;
        state.error = null;
      })
      .addCase(uploadExcelFile.fulfilled, (state, action) => {
        state.loading.upload = false;
        state.excelData = action.payload.data || [];
        // Автоматически создаем дедуплицированные данные
        tochkaSlice.caseReducers.createDeduplicatedData(state);
      })
      .addCase(uploadExcelFile.rejected, (state, action) => {
        state.loading.upload = false;
        state.error = action.error.message || 'Failed to upload Excel file';
      })
      
      // Merge with products
      .addCase(mergeWithProducts.pending, (state) => {
        state.loading.merge = true;
        state.error = null;
      })
      .addCase(mergeWithProducts.fulfilled, (state, action) => {
        state.loading.merge = false;
        state.mergedData = action.payload.data || [];
        state.coverage = {
          rate: action.payload.coverage_rate,
          found_products: action.payload.found_products,
          total_articles: action.payload.total_articles,
        };
      })
      .addCase(mergeWithProducts.rejected, (state, action) => {
        state.loading.merge = false;
        state.error = action.error.message || 'Failed to merge with products';
      })
      
      // Get filtered production
      .addCase(getFilteredProduction.pending, (state) => {
        state.loading.filter = true;
        state.error = null;
      })
      .addCase(getFilteredProduction.fulfilled, (state, action) => {
        state.loading.filter = false;
        state.filteredProductionData = action.payload.data || [];
        state.productionStats = {
          total_products: action.payload.total_products,
          products_in_tochka: action.payload.products_in_tochka,
          products_need_registration: action.payload.products_need_registration,
        };
      })
      .addCase(getFilteredProduction.rejected, (state, action) => {
        state.loading.filter = false;
        state.error = action.error.message || 'Failed to get filtered production';
      })
      
      // Export operations
      .addCase(exportDeduplicated.pending, (state) => {
        state.loading.export = true;
        state.error = null;
      })
      .addCase(exportDeduplicated.fulfilled, (state) => {
        state.loading.export = false;
      })
      .addCase(exportDeduplicated.rejected, (state, action) => {
        state.loading.export = false;
        state.error = action.error.message || 'Failed to export deduplicated data';
      })
      
      .addCase(exportProduction.pending, (state) => {
        state.loading.export = true;
        state.error = null;
      })
      .addCase(exportProduction.fulfilled, (state) => {
        state.loading.export = false;
      })
      .addCase(exportProduction.rejected, (state, action) => {
        state.loading.export = false;
        state.error = action.error.message || 'Failed to export production data';
      })
      
      // Auto process Excel file
      .addCase(uploadAndAutoProcess.pending, (state) => {
        state.loading.autoProcess = true;
        state.error = null;
      })
      .addCase(uploadAndAutoProcess.fulfilled, (state, action) => {
        state.loading.autoProcess = false;
        const { upload_result, analysis_result, production_result } = action.payload;
        
        // Обновляем Excel данные
        state.excelData = upload_result.data;
        state.deduplicatedExcelData = upload_result.data;
        
        // Обновляем результаты анализа
        state.mergedData = analysis_result.merged_data;
        state.coverage = {
          rate: analysis_result.coverage_rate.toString(),
          found_products: analysis_result.found_products,
          total_articles: analysis_result.total_articles,
        };
        
        // Обновляем список производства
        state.filteredProductionData = production_result.filtered_production;
        state.productionStats = {
          total_products: production_result.total_products,
          products_in_tochka: production_result.products_in_tochka,
          products_need_registration: production_result.products_need_registration,
        };
      })
      .addCase(uploadAndAutoProcess.rejected, (state, action) => {
        state.loading.autoProcess = false;
        state.error = action.error.message || 'Failed to auto process Excel file';
      });
  },
});

export const { 
  clearError, 
  clearExcelData, 
  setProductsPagination, 
  setProductionPagination,
  createDeduplicatedData
} = tochkaSlice.actions;

export const tochkaReducer = tochkaSlice.reducer;