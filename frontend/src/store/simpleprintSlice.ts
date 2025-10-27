/**
 * Redux slice для SimplePrint данных
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { apiClient } from '../api/client';

// Types
export interface SimplePrintFile {
  id: number;
  simpleprint_id: string;
  name: string;
  folder: number | null;
  folder_name: string | null;
  ext: string;
  file_type: string;
  size: number;
  size_display: string;
  tags: any;
  gcode_analysis: any;
  print_data: any;
  material_color: string | null;
  print_time: number | null;
  weight: number | null;
  quantity: number | null;
  article: string | null;
  created_at_sp: string;
  last_synced_at: string;
}

export interface SimplePrintFolder {
  id: number;
  simpleprint_id: number;
  name: string;
  depth: number;
  files_count: number;
  folders_count: number;
  last_synced_at: string;
}

export interface SyncStats {
  total_folders: number;
  total_files: number;
  last_sync: string | null;
  last_sync_status: string | null;
  last_sync_duration: number | null;
}

export interface FileStats {
  total_files: number;
  total_size: number;
  by_type: {
    [key: string]: {
      count: number;
      size: number;
    };
  };
}

interface SimplePrintState {
  files: SimplePrintFile[];
  folders: SimplePrintFolder[];
  syncStats: SyncStats | null;
  fileStats: FileStats | null;
  loading: boolean;
  error: string | null;
  syncing: boolean;
  syncError: string | null;
  totalFiles: number; // Общее количество файлов для пагинации
}

const initialState: SimplePrintState = {
  files: [],
  folders: [],
  syncStats: null,
  fileStats: null,
  loading: false,
  error: null,
  syncing: false,
  syncError: null,
  totalFiles: 0,
};

// Async thunks
export const fetchFiles = createAsyncThunk(
  'simpleprint/fetchFiles',
  async (params?: { search?: string; folder?: number; file_type?: string; page?: number; page_size?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.folder) queryParams.append('folder', params.folder.toString());
    if (params?.file_type) queryParams.append('file_type', params.file_type);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const response = await apiClient.get(`/simpleprint/files/?${queryParams.toString()}`);
    return response; // apiClient уже возвращает response.data
  }
);

export const fetchFolders = createAsyncThunk(
  'simpleprint/fetchFolders',
  async () => {
    const response = await apiClient.get('/simpleprint/folders/');
    return response; // apiClient уже возвращает response.data
  }
);

export const fetchSyncStats = createAsyncThunk(
  'simpleprint/fetchSyncStats',
  async () => {
    const response = await apiClient.get('/simpleprint/sync/stats/');
    return response; // apiClient уже возвращает response.data
  }
);

export const fetchFileStats = createAsyncThunk(
  'simpleprint/fetchFileStats',
  async () => {
    const response = await apiClient.get('/simpleprint/files/stats/');
    return response; // apiClient уже возвращает response.data
  }
);

export const triggerSync = createAsyncThunk(
  'simpleprint/triggerSync',
  async (params: { full_sync?: boolean; force?: boolean } = {}) => {
    const response = await apiClient.post('/simpleprint/sync/trigger/', params);
    return response; // apiClient уже возвращает response.data
  }
);

export const checkSyncStatus = createAsyncThunk(
  'simpleprint/checkSyncStatus',
  async (taskId: string) => {
    const response = await apiClient.get(`/simpleprint/sync/status/${taskId}/`);
    return response; // apiClient уже возвращает response.data
  }
);

export const cancelSync = createAsyncThunk(
  'simpleprint/cancelSync',
  async (taskId: string) => {
    const response = await apiClient.post('/simpleprint/sync/cancel/', { task_id: taskId });
    return response; // apiClient уже возвращает response.data
  }
);

// Slice
const simpleprintSlice = createSlice({
  name: 'simpleprint',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.syncError = null;
    },
    setSyncing: (state, action: PayloadAction<boolean>) => {
      state.syncing = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch files
    builder
      .addCase(fetchFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFiles.fulfilled, (state, action: PayloadAction<any>) => {
        state.loading = false;
        state.files = action.payload.results || action.payload;
        state.totalFiles = action.payload.count || (action.payload.results ? action.payload.results.length : action.payload.length);
      })
      .addCase(fetchFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch files';
      });

    // Fetch folders
    builder
      .addCase(fetchFolders.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFolders.fulfilled, (state, action: PayloadAction<any>) => {
        state.loading = false;
        state.folders = action.payload.results || action.payload;
      })
      .addCase(fetchFolders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch folders';
      });

    // Fetch sync stats
    builder
      .addCase(fetchSyncStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSyncStats.fulfilled, (state, action: PayloadAction<any>) => {
        state.loading = false;
        state.syncStats = action.payload;
      })
      .addCase(fetchSyncStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch sync stats';
      });

    // Fetch file stats
    builder
      .addCase(fetchFileStats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchFileStats.fulfilled, (state, action: PayloadAction<any>) => {
        state.loading = false;
        state.fileStats = action.payload;
      })
      .addCase(fetchFileStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch file stats';
      });

    // Trigger sync
    builder
      .addCase(triggerSync.pending, (state) => {
        state.syncing = true;
        state.syncError = null;
      })
      .addCase(triggerSync.fulfilled, (state, action: PayloadAction<any>) => {
        // НЕ сбрасываем syncing - задача продолжает работать
        // syncing будет сброшен при завершении polling
        if (action.payload.status !== 'started') {
          state.syncing = false;
        }
      })
      .addCase(triggerSync.rejected, (state, action) => {
        state.syncing = false;
        state.syncError = action.error.message || 'Failed to trigger sync';
      });

    // Cancel sync
    builder
      .addCase(cancelSync.pending, (state) => {
        // Не меняем syncing при отмене
      })
      .addCase(cancelSync.fulfilled, (state) => {
        state.syncing = false;
      })
      .addCase(cancelSync.rejected, (state) => {
        state.syncing = false;
      });
  },
});

export const { clearError, setSyncing } = simpleprintSlice.actions;
export default simpleprintSlice.reducer;
