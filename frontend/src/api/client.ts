import axios, { AxiosError } from 'axios';
import { API_BASE_URL } from '../utils/constants';

// Production API fallback
const getAPIBaseURL = () => {
  // Try environment variable first
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Production fallback based on window location
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    const port = window.location.port === '8080' ? '8001' : '8000'; // Production backend port
    return `${protocol}//${hostname}:${port}/api/v1`;
  }
  
  return API_BASE_URL;
};

const apiClient = axios.create({
  baseURL: getAPIBaseURL(),
  timeout: 300000, // 5 минут для длительных операций синхронизации
  headers: {
    'Content-Type': 'application/json',
  },
});

// Enhanced error logging for production debugging
const logError = (error: any, context: string) => {
  console.group(`🚨 API Error - ${context}`);
  console.error('URL:', error.config?.url);
  console.error('Method:', error.config?.method?.toUpperCase());
  console.error('Status:', error.response?.status);
  console.error('Data:', error.response?.data);
  console.error('Full Error:', error);
  console.groupEnd();
};

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      // Django REST Framework использует Token auth, не Bearer
      config.headers.Authorization = `Token ${token}`;
    } else {
      // Auto-set demo token for production
      const demoToken = '0a8fee03bca2b530a15b1df44d38b304e3f57484';
      localStorage.setItem('auth_token', demoToken);
      config.headers.Authorization = `Token ${demoToken}`;
      console.warn('🔐 Auto-set demo token for production');
    }
    
    console.log('📡 API Request:', config.method?.toUpperCase(), config.url);
    console.log('🔗 Base URL:', config.baseURL);
    return config;
  },
  (error) => {
    logError(error, 'Request Interceptor');
    return Promise.reject(error);
  }
);

// Enhanced response interceptor with better error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ API Success:', response.config.url, 'Status:', response.status);
    return response.data; // Возвращаем только данные, не весь response
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    const url = error.config?.url;
    
    // Enhanced error logging for production debugging
    logError(error, 'Response');
    
    // Specific error handling
    if (status === 401) {
      console.warn('🔐 Authentication error - checking token');
      const token = localStorage.getItem('auth_token');
      if (!token) {
        const demoToken = '0a8fee03bca2b530a15b1df44d38b304e3f57484';
        localStorage.setItem('auth_token', demoToken);
        console.warn('🔄 Set demo token, reloading...');
        window.location.reload();
      }
    } else if (status === 0 || status === undefined) {
      // Network/CORS errors
      console.error('🌐 Network Error - possible CORS or connectivity issue');
      console.error('Check that backend is running at:', getAPIBaseURL());
    } else if (status >= 500) {
      // Server errors
      console.error('🔥 Server Error - backend might be down or misconfigured');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
export { apiClient };