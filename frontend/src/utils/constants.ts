export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api/v1';
export const MEDIA_BASE_URL = process.env.REACT_APP_MEDIA_URL || 'http://127.0.0.1:8000/media/';

export const APP_VERSION = '4.1.8';

export const PRODUCT_TYPES = {
  new: 'Новая позиция',
  old: 'Старая позиция',
  critical: 'Критическая позиция',
} as const;

export const SYNC_STATUSES = {
  pending: 'В процессе',
  success: 'Успешно',
  failed: 'Ошибка',
  partial: 'Частично выполнено',
} as const;

export const PRIORITY_LEVELS = {
  HIGH: 80,
  MEDIUM: 40,
  LOW: 20,
} as const;

export const COLORS = {
  primary: '#06EAFC',
  secondary: '#1E1E1E',
  success: '#00FF88',
  warning: '#FFB800',
  error: '#FF0055',
} as const;