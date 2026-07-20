import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
    'Bypass-Tunnel-Reminder': 'true',
    'ngrok-skip-browser-warning': 'true'
  }
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Request timeout. Please try again.'));
    }
    if (!error.response) {
      return Promise.reject(new Error('Network error. Please check your connection.'));
    }
    return Promise.reject(error);
  }
);

export const detectImage = async (file, confThreshold = 0.25) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/api/v1/detect/image?conf=${confThreshold}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const processFrame = async (file, confThreshold = 0.25) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post(`/api/v1/detect/stream/frame?conf=${confThreshold}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/api/v1/health');
  return response.data;
};

export const getModelInfo = async () => {
  const response = await api.get('/api/v1/model/info');
  return response.data;
};

export const exportJSON = async (limit = 1000) => {
  window.open(`/api/v1/export/json?limit=${limit}`, '_blank');
};

export const exportCSV = async (limit = 1000) => {
  window.open(`/api/v1/export/csv?limit=${limit}`, '_blank');
};

export const getHistory = async (limit = 50) => {
  const response = await api.get(`/api/v1/detect/history?limit=${limit}`);
  return response.data;
};

export const clearHistory = async () => {
  const response = await api.post('/api/v1/detect/history/clear');
  return response.data;
};

export default api;
