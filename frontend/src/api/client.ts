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
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // For demo, set the token instead of redirecting
      const token = localStorage.getItem('auth_token');
      if (!token) {
        localStorage.setItem('auth_token', '549ebaf641ffa608a26b79a21d72a296c99a02b7');
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;