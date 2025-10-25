import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 минут для длительных операций синхронизации
  headers: {
    'Content-Type': 'application/json',
  },
});

// Initialize auth token if not present (for demo environment)
const initializeAuthToken = () => {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    const demoToken = '0a8fee03bca2b530a15b1df44d38b304e3f57484';
    localStorage.setItem('auth_token', demoToken);
    console.log('Demo auth token initialized');
    return demoToken;
  }
  return token;
};

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    // ИСПРАВЛЕНИЕ: Всегда устанавливаем токен, инициализируем если нет
    const token = initializeAuthToken();
    if (token) {
      // Django REST Framework использует Token auth, не Bearer
      config.headers.Authorization = `Token ${token}`;
    }
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.config.url, response.data);
    return response.data; // Возвращаем только data для обратной совместимости
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      // ИСПРАВЛЕНИЕ: Устанавливаем токен и возвращаем ошибку без перезагрузки
      const token = localStorage.getItem('auth_token');
      if (!token) {
        localStorage.setItem('auth_token', '0a8fee03bca2b530a15b1df44d38b304e3f57484');
        console.log('Auth token set due to 401 error');
        // Не перезагружаем страницу, позволяем запросу повториться
      }
    }
    
    // ИСПРАВЛЕНИЕ: Добавляем специальную обработку для sync endpoints
    if (error.response?.status === 503 && error.config?.url?.includes('/sync/')) {
      console.warn('МойСклад API connection issue:', error.response.data);
      // Для endpoint'ов синхронизации возвращаем пустые массивы вместо ошибки
      if (error.config.url.includes('/warehouses/')) {
        return Promise.resolve([]);
      }
      if (error.config.url.includes('/product-groups/')) {
        return Promise.resolve([]);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
export { apiClient };