import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { syncApi, SyncStatus, SyncHistory, Warehouse, ProductGroup, StartSyncParams } from '../../api/sync';

interface SyncState {
  status: SyncStatus | null;
  history: SyncHistory[];
  warehouses: Warehouse[];
  productGroups: ProductGroup[];
  loading: boolean;
  warehousesLoading: boolean;
  productGroupsLoading: boolean;
  error: string | null;
}

const initialState: SyncState = {
  status: null,
  history: [],
  warehouses: [],
  productGroups: [],
  loading: false,
  warehousesLoading: false,
  productGroupsLoading: false,
  error: null,
};

// Async thunks
export const fetchSyncStatus = createAsyncThunk(
  'sync/fetchStatus',
  async () => {
    const response = await syncApi.getStatus();
    return response;
  }
);

export const fetchSyncHistory = createAsyncThunk(
  'sync/fetchHistory',
  async () => {
    const response = await syncApi.getHistory();
    return response;
  }
);

export const fetchWarehouses = createAsyncThunk(
  'sync/fetchWarehouses',
  async () => {
    console.log('Fetching warehouses...');
    const response = await syncApi.getWarehouses();
    console.log('Warehouses response:', response);
    return response;
  }
);

export const fetchProductGroups = createAsyncThunk(
  'sync/fetchProductGroups',
  async () => {
    const response = await syncApi.getProductGroups();
    return response;
  }
);

export const startSync = createAsyncThunk(
  'sync/startSync',
  async (params: StartSyncParams) => {
    const response = await syncApi.startSync(params);
    return response;
  }
);

const syncSlice = createSlice({
  name: 'sync',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch sync status
      .addCase(fetchSyncStatus.fulfilled, (state, action) => {
        state.status = action.payload;
      })
      
      // Fetch sync history
      .addCase(fetchSyncHistory.fulfilled, (state, action) => {
        state.history = action.payload;
      })
      
      // Fetch warehouses
      .addCase(fetchWarehouses.pending, (state) => {
        state.warehousesLoading = true;
        state.error = null;
      })
      .addCase(fetchWarehouses.fulfilled, (state, action) => {
        state.warehouses = action.payload;
        state.warehousesLoading = false;
      })
      .addCase(fetchWarehouses.rejected, (state, action) => {
        state.warehousesLoading = false;
        state.error = action.error.message || 'Failed to fetch warehouses';
      })
      
      // Fetch product groups
      .addCase(fetchProductGroups.pending, (state) => {
        state.productGroupsLoading = true;
        state.error = null;
      })
      .addCase(fetchProductGroups.fulfilled, (state, action) => {
        state.productGroups = action.payload;
        state.productGroupsLoading = false;
      })
      .addCase(fetchProductGroups.rejected, (state, action) => {
        state.productGroupsLoading = false;
        state.error = action.error.message || 'Failed to fetch product groups';
      })
      
      // Start sync
      .addCase(startSync.pending, (state) => {
        state.loading = true;
        state.error = null;
        // Set syncing status to true when starting
        if (state.status) {
          state.status.is_syncing = true;
        } else {
          state.status = { is_syncing: true };
        }
      })
      .addCase(startSync.fulfilled, (state, action) => {
        state.loading = false;
        // Update status based on response
        if (action.payload.status === 'success') {
          // Sync completed successfully (synchronous mode)
          state.status = {
            is_syncing: false,
            last_sync: new Date().toISOString(),
            total_products: action.payload.total_products,
            synced_products: action.payload.synced_products
          };
        } else {
          // Async mode - keep syncing true
          state.status = {
            is_syncing: true,
            sync_id: action.payload.sync_id,
            started_at: new Date().toISOString()
          };
        }
      })
      .addCase(startSync.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to start sync';
        // Reset syncing status on error
        if (state.status) {
          state.status.is_syncing = false;
        }
      });
  },
});

export const { clearError } = syncSlice.actions;
export const syncReducer = syncSlice.reducer;