import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('API request error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API response error:', error.response?.data || error.message);

    if (error.response?.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) => api.post('/api/auth/login', { username, password }),
  register: (username, password, email) =>
    api.post('/api/auth/register', { username, password, email }),
  verifyToken: () => api.get('/api/auth/verify'),
  logout: () => Promise.resolve(),
};

export const tabsAPI = {
  getTabs: () => api.get('/api/tabs'),
  createTab: (data) => api.post('/api/tabs', data),
  updateTab: (id, data) => api.put(`/api/tabs/${id}`, data),
  deleteTab: (id) => api.delete(`/api/tabs/${id}`),
  getTabSettings: (id) => api.get(`/api/tabs/${id}/settings`),
};

export const queueAPI = {
  getQueueStatus: () => api.get('/api/queue'),
  addToQueue: (data) => api.post('/api/jobs/add', data),
  getAllJobs: () => api.get('/api/queue/jobs'),
  getJob: (id) => api.get(`/api/jobs/status/${id}`),
  cancelJob: (id) => api.post(`/api/jobs/cancel/${id}`),
  clearCompletedJobs: () => api.post('/api/queue/clear'),
  pauseQueue: () => api.post('/api/queue/pause'),
  resumeQueue: () => api.post('/api/queue/resume'),
};

export const systemAPI = {
  getHealth: () => api.get('/health'),
  getSystemLoad: () => api.get('/api/system/load'),
};

export const filesystemAPI = {
  browse: (path) => api.get('/api/filesystem/browse', { params: { path } }),
  scan: (path) => api.post('/api/filesystem/scan', { path }),
  mkdir: (path, name) => api.post('/api/filesystem/mkdir', { path, name }),
  getCachedContent: (path) => api.get('/api/filesystem/cache', { params: { path } }),
};

export default api;
