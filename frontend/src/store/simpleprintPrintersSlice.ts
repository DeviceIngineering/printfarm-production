/**
 * SimplePrint Redux Slice
 *
 * State management для данных принтеров SimplePrint
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { simplePrintApi } from '../api/simpleprint';
import { PrinterSnapshot, PrinterStats } from '../types/simpleprint.types';

interface SimplePrintState {
  printers: PrinterSnapshot[];
  stats: PrinterStats | null;
  loading: boolean;
  error: string | null;
  lastSync: string | null;
}

const initialState: SimplePrintState = {
  printers: [],
  stats: null,
  loading: false,
  error: null,
  lastSync: null,
};

/**
 * Async thunk: Получить список принтеров
 */
export const fetchPrinters = createAsyncThunk(
  'simpleprintPrinters/fetchPrinters',
  async () => {
    return await simplePrintApi.getPrinters();
  }
);

/**
 * Async thunk: Запустить синхронизацию
 */
export const syncPrinters = createAsyncThunk(
  'simpleprintPrinters/syncPrinters',
  async () => {
    const result = await simplePrintApi.syncPrinters();
    // После синхронизации сразу загружаем обновленные данные
    const printers = await simplePrintApi.getPrinters();
    return printers;
  }
);

/**
 * Async thunk: Получить статистику
 */
export const fetchStats = createAsyncThunk(
  'simpleprintPrinters/fetchStats',
  async () => {
    return await simplePrintApi.getStats();
  }
);

const simpleprintSlice = createSlice({
  name: 'simpleprintPrinters',
  initialState,
  reducers: {
    /**
     * Очистить ошибку
     */
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // fetchPrinters
    builder
      .addCase(fetchPrinters.pending, (state) => {
        state.loading = true;
        state.error = null;
        console.log('🔵 fetchPrinters.pending');
      })
      .addCase(fetchPrinters.fulfilled, (state, action: PayloadAction<PrinterSnapshot[]>) => {
        console.log('✅ fetchPrinters.fulfilled - payload:', action.payload);
        state.loading = false;
        state.printers = action.payload || [];
        state.lastSync = new Date().toISOString();
        console.log('✅ State updated - printers count:', state.printers.length);
      })
      .addCase(fetchPrinters.rejected, (state, action) => {
        console.error('❌ fetchPrinters.rejected:', action.error);
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch printers';
      });

    // syncPrinters
    builder
      .addCase(syncPrinters.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(syncPrinters.fulfilled, (state, action: PayloadAction<PrinterSnapshot[]>) => {
        state.loading = false;
        state.printers = action.payload;
        state.lastSync = new Date().toISOString();
      })
      .addCase(syncPrinters.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to sync printers';
      });

    // fetchStats
    builder
      .addCase(fetchStats.pending, (state) => {
        state.error = null;
      })
      .addCase(fetchStats.fulfilled, (state, action: PayloadAction<PrinterStats>) => {
        state.stats = action.payload;
      })
      .addCase(fetchStats.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to fetch stats';
      });
  },
});

export const { clearError } = simpleprintSlice.actions;
export default simpleprintSlice.reducer;
