/**
 * SimplePrint Files Redux Slice
 *
 * State management for SimplePrint file management
 * This is a placeholder implementation to maintain compatibility
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface SimplePrintFile {
  id: number;
  name: string;
  folder_name: string | null;
  ext: string;
  size: number;
  size_display: string;
  created_at_sp: string;
  article: string | null;
  quantity: number | null;
  print_time: number | null;
  weight: number | null;
  material_color: string | null;
}

export interface SimplePrintFolder {
  id: number;
  name: string;
}

export interface SimplePrintSyncStats {
  total_folders: number;
  total_files: number;
  synced_folders: number;
  synced_files: number;
  deleted_files: number;
  last_sync: string | null;
}

export interface SimplePrintFileStats {
  total_files: number;
  total_size: number;
}

interface SimplePrintState {
  files: SimplePrintFile[];
  folders: SimplePrintFolder[];
  syncStats: SimplePrintSyncStats | null;
  fileStats: SimplePrintFileStats | null;
  loading: boolean;
  syncing: boolean;
  syncError: string | null;
  totalFiles: number;
}

const initialState: SimplePrintState = {
  files: [],
  folders: [],
  syncStats: null,
  fileStats: null,
  loading: false,
  syncing: false,
  syncError: null,
  totalFiles: 0,
};

/**
 * Async thunk: Fetch files
 */
export const fetchFiles = createAsyncThunk(
  'simpleprint/fetchFiles',
  async (params?: any) => {
    // TODO: Implement API call
    return { results: [], count: 0 };
  }
);

/**
 * Async thunk: Fetch folders
 */
export const fetchFolders = createAsyncThunk(
  'simpleprint/fetchFolders',
  async () => {
    // TODO: Implement API call
    return [];
  }
);

/**
 * Async thunk: Fetch sync stats
 */
export const fetchSyncStats = createAsyncThunk(
  'simpleprint/fetchSyncStats',
  async () => {
    // TODO: Implement API call
    return null;
  }
);

/**
 * Async thunk: Fetch file stats
 */
export const fetchFileStats = createAsyncThunk(
  'simpleprint/fetchFileStats',
  async () => {
    // TODO: Implement API call
    return null;
  }
);

/**
 * Async thunk: Trigger sync
 */
export const triggerSync = createAsyncThunk(
  'simpleprint/triggerSync',
  async (params: { full_sync: boolean; force: boolean }) => {
    // TODO: Implement API call
    return { status: 'started', task_id: null };
  }
);

/**
 * Async thunk: Check sync status
 */
export const checkSyncStatus = createAsyncThunk(
  'simpleprint/checkSyncStatus',
  async (taskId: string) => {
    // TODO: Implement API call
    return { ready: false, state: 'pending', progress: null };
  }
);

/**
 * Async thunk: Cancel sync
 */
export const cancelSync = createAsyncThunk(
  'simpleprint/cancelSync',
  async (taskId: string) => {
    // TODO: Implement API call
    return { success: true };
  }
);

const simpleprintSlice = createSlice({
  name: 'simpleprint',
  initialState,
  reducers: {
    setSyncing: (state, action: PayloadAction<boolean>) => {
      state.syncing = action.payload;
    },
  },
  extraReducers: (builder) => {
    // fetchFiles
    builder
      .addCase(fetchFiles.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchFiles.fulfilled, (state, action) => {
        state.loading = false;
        state.files = action.payload.results || [];
        state.totalFiles = action.payload.count || 0;
      })
      .addCase(fetchFiles.rejected, (state) => {
        state.loading = false;
      });

    // fetchFolders
    builder
      .addCase(fetchFolders.fulfilled, (state, action) => {
        state.folders = action.payload;
      });

    // fetchSyncStats
    builder
      .addCase(fetchSyncStats.fulfilled, (state, action) => {
        state.syncStats = action.payload;
      });

    // fetchFileStats
    builder
      .addCase(fetchFileStats.fulfilled, (state, action) => {
        state.fileStats = action.payload;
      });

    // triggerSync
    builder
      .addCase(triggerSync.pending, (state) => {
        state.syncing = true;
        state.syncError = null;
      })
      .addCase(triggerSync.fulfilled, (state) => {
        state.syncing = true;
      })
      .addCase(triggerSync.rejected, (state, action) => {
        state.syncing = false;
        state.syncError = action.error.message || 'Failed to trigger sync';
      });

    // cancelSync
    builder
      .addCase(cancelSync.fulfilled, (state) => {
        state.syncing = false;
      });
  },
});

export const { setSyncing } = simpleprintSlice.actions;
export default simpleprintSlice.reducer;
