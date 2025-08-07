import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 минут для длительных операций синхронизации
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
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
    return response.data; // Возвращаем только данные, не весь response
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      // For demo, set the token instead of redirecting
      const token = localStorage.getItem('auth_token');
      if (!token) {
        localStorage.setItem('auth_token', '0a8fee03bca2b530a15b1df44d38b304e3f57484');
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
export { apiClient };