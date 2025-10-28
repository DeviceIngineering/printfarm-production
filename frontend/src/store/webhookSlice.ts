/**
 * Redux slice для управления Webhook событиями
 *
 * Включает:
 * - Список webhook событий
 * - Статистику событий
 * - Отправку тестовых webhooks
 * - Очистку старых событий
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const token = localStorage.getItem('auth_token');

// ============================================================================
// Types
// ============================================================================

export interface WebhookEvent {
  id: number;
  event_type: string;
  event_type_display: string;
  printer_id: string | null;
  job_id: string | null;
  payload: any;
  processed: boolean;
  processed_at: string | null;
  processing_error: string | null;
  received_at: string;
}

export interface WebhookStats {
  total: number;
  processed: number;
  errors: number;
  by_type: Record<string, number>;
  last_hour: number;
  last_24h: number;
  last_event_at: string | null;
}

interface WebhookState {
  events: WebhookEvent[];
  stats: WebhookStats | null;
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

// ============================================================================
// Async Thunks
// ============================================================================

/**
 * Получить список webhook событий
 */
export const fetchWebhookEvents = createAsyncThunk(
  'webhook/fetchEvents',
  async (params: { limit?: number; event_type?: string } = {}) => {
    const { limit = 20, event_type } = params;
    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    if (event_type) {
      queryParams.append('event_type', event_type);
    }

    const response = await axios.get(
      `${API_BASE_URL}/simpleprint/webhook/events/?${queryParams}`,
      {
        headers: {
          Authorization: `Token ${token}`,
        },
      }
    );
    return response.data.events;
  }
);

/**
 * Получить статистику webhook событий
 */
export const fetchWebhookStats = createAsyncThunk(
  'webhook/fetchStats',
  async () => {
    const response = await axios.get(
      `${API_BASE_URL}/simpleprint/webhook/stats/`,
      {
        headers: {
          Authorization: `Token ${token}`,
        },
      }
    );
    return response.data;
  }
);

/**
 * Отправить тестовый webhook
 */
export const triggerTestWebhook = createAsyncThunk(
  'webhook/triggerTest',
  async (eventType: string = 'job.started') => {
    const response = await axios.post(
      `${API_BASE_URL}/simpleprint/webhook/test-trigger/`,
      { event_type: eventType },
      {
        headers: {
          Authorization: `Token ${token}`,
        },
      }
    );
    return response.data;
  }
);

/**
 * Очистить старые webhook события
 */
export const clearOldWebhookEvents = createAsyncThunk(
  'webhook/clearOld',
  async (days: number = 7) => {
    const response = await axios.delete(
      `${API_BASE_URL}/simpleprint/webhook/events/clear/?days=${days}`,
      {
        headers: {
          Authorization: `Token ${token}`,
        },
      }
    );
    return response.data;
  }
);

// ============================================================================
// Slice
// ============================================================================

const initialState: WebhookState = {
  events: [],
  stats: null,
  loading: false,
  error: null,
  lastUpdate: null,
};

const webhookSlice = createSlice({
  name: 'webhook',
  initialState,
  reducers: {
    /**
     * Очистить ошибки
     */
    clearError: (state) => {
      state.error = null;
    },

    /**
     * Добавить новое событие (для real-time обновлений через WebSocket)
     */
    addWebhookEvent: (state, action: PayloadAction<WebhookEvent>) => {
      state.events.unshift(action.payload);
      // Ограничиваем список 100 событиями
      if (state.events.length > 100) {
        state.events = state.events.slice(0, 100);
      }
    },
  },
  extraReducers: (builder) => {
    // fetchWebhookEvents
    builder.addCase(fetchWebhookEvents.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchWebhookEvents.fulfilled, (state, action) => {
      state.loading = false;
      state.events = action.payload;
      state.lastUpdate = new Date().toISOString();
    });
    builder.addCase(fetchWebhookEvents.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch webhook events';
    });

    // fetchWebhookStats
    builder.addCase(fetchWebhookStats.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchWebhookStats.fulfilled, (state, action) => {
      state.loading = false;
      state.stats = action.payload;
      state.lastUpdate = new Date().toISOString();
    });
    builder.addCase(fetchWebhookStats.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch webhook stats';
    });

    // triggerTestWebhook
    builder.addCase(triggerTestWebhook.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(triggerTestWebhook.fulfilled, (state) => {
      state.loading = false;
    });
    builder.addCase(triggerTestWebhook.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to trigger test webhook';
    });

    // clearOldWebhookEvents
    builder.addCase(clearOldWebhookEvents.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(clearOldWebhookEvents.fulfilled, (state) => {
      state.loading = false;
    });
    builder.addCase(clearOldWebhookEvents.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to clear old webhook events';
    });
  },
});

export const { clearError, addWebhookEvent } = webhookSlice.actions;

export default webhookSlice.reducer;

// ============================================================================
// Selectors
// ============================================================================

export const selectWebhookEvents = (state: any) => state.webhook.events;
export const selectWebhookStats = (state: any) => state.webhook.stats;
export const selectWebhookLoading = (state: any) => state.webhook.loading;
export const selectWebhookError = (state: any) => state.webhook.error;
export const selectWebhookLastUpdate = (state: any) => state.webhook.lastUpdate;
