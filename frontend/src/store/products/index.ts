import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { productsApi, Product, ProductDetail, ProductStats, ProductListParams, ProductionList, ProductionStats } from '../../api/products';

interface ProductsState {
  products: Product[];
  currentProduct: ProductDetail | null;
  productStats: ProductStats | null;
  productionList: ProductionList | null;
  productionStats: ProductionStats | null;
  loading: boolean;
  error: string | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  filters: ProductListParams;
}

const initialState: ProductsState = {
  products: [],
  currentProduct: null,
  productStats: null,
  productionList: null,
  productionStats: null,
  loading: false,
  error: null,
  pagination: {
    current: 1,
    pageSize: 100,
    total: 0,
  },
  filters: {},
};

// Async thunks
export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async (params: ProductListParams = {}) => {
    const response = await productsApi.getProducts(params);
    return response;
  }
);

export const fetchProduct = createAsyncThunk(
  'products/fetchProduct',
  async (id: number) => {
    const response = await productsApi.getProduct(id);
    return response;
  }
);

export const fetchProductStats = createAsyncThunk(
  'products/fetchProductStats',
  async () => {
    const response = await productsApi.getProductStats();
    return response;
  }
);

export const calculateProductionList = createAsyncThunk(
  'products/calculateProductionList',
  async (params?: { min_priority?: number; apply_coefficients?: boolean }) => {
    await productsApi.calculateProductionList(params);
    const response = await productsApi.getProductionList();
    return response;
  }
);

export const fetchProductionList = createAsyncThunk(
  'products/fetchProductionList',
  async (listId?: number) => {
    const response = await productsApi.getProductionList(listId);
    return response;
  }
);

export const fetchProductionStats = createAsyncThunk(
  'products/fetchProductionStats',
  async () => {
    const response = await productsApi.getProductionStats();
    return response;
  }
);

export const recalculateProduction = createAsyncThunk(
  'products/recalculateProduction',
  async () => {
    const response = await productsApi.recalculateProduction();
    return response;
  }
);

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<ProductListParams>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {};
    },
    setPagination: (state, action: PayloadAction<{ current: number; pageSize: number }>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch products
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.loading = false;
        // Дополнительная проверка и очистка данных
        const products = action.payload.results || [];
        state.products = products.map(product => ({
          ...product,
          current_stock: product.current_stock ?? 0,
          days_of_stock: product.days_of_stock ?? null,
          production_needed: product.production_needed ?? 0,
          production_priority: product.production_priority ?? 0
        } as Product));
        state.pagination.total = action.payload.count || 0;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch products';
      })
      
      // Fetch product
      .addCase(fetchProduct.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProduct.fulfilled, (state, action) => {
        state.loading = false;
        state.currentProduct = action.payload;
      })
      .addCase(fetchProduct.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch product';
      })
      
      // Fetch product stats
      .addCase(fetchProductStats.fulfilled, (state, action) => {
        state.productStats = action.payload;
      })
      
      // Calculate production list
      .addCase(calculateProductionList.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(calculateProductionList.fulfilled, (state, action) => {
        state.loading = false;
        state.productionList = action.payload;
      })
      .addCase(calculateProductionList.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to calculate production list';
      })
      
      // Fetch production list
      .addCase(fetchProductionList.fulfilled, (state, action) => {
        state.productionList = action.payload;
      })
      
      // Fetch production stats
      .addCase(fetchProductionStats.fulfilled, (state, action) => {
        state.productionStats = action.payload;
      })
      
      // Recalculate production
      .addCase(recalculateProduction.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(recalculateProduction.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(recalculateProduction.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to recalculate production';
      });
  },
});

export const { setFilters, clearFilters, setPagination, clearError } = productsSlice.actions;
export const productsReducer = productsSlice.reducer;