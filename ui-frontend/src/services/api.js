import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

console.log('🔧 API Service initialized with base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🔧 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    console.log('🔧 Request config:', {
      baseURL: config.baseURL,
      url: config.url,
      method: config.method,
      headers: config.headers
    });
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    console.error('❌ Request error details:', {
      message: error.message,
      code: error.code,
      config: error.config
    });
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    console.log('✅ Response data preview:', JSON.stringify(response.data).substring(0, 200) + '...');
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);
    console.error('❌ Response error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data
    });
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => {
    console.log('🔧 Calling authAPI.login()');
    return api.post('/api/auth/login', { username, password });
  },
  register: (username, password, email) => {
    console.log('🔧 Calling authAPI.register()');
    return api.post('/api/auth/register', { username, password, email });
  },
  verifyToken: () => {
    console.log('🔧 Calling authAPI.verifyToken()');
    return api.get('/api/auth/verify');
  },
  logout: () => {
    console.log('🔧 Calling authAPI.logout()');
    // Client-side only operation usually, but good to have the method structure
    return Promise.resolve();
  }
};

// Tabs API
export const tabsAPI = {
  getTabs: () => {
    console.log('🔧 Calling tabsAPI.getTabs()');
    return api.get('/api/tabs');
  },
  createTab: (data) => {
    console.log('🔧 Calling tabsAPI.createTab() with data:', data);
    return api.post('/api/tabs', data);
  },
  updateTab: (id, data) => {
    console.log('🔧 Calling tabsAPI.updateTab() with id:', id, 'data:', data);
    return api.put(`/api/tabs/${id}`, data);
  },
  deleteTab: (id) => {
    console.log('🔧 Calling tabsAPI.deleteTab() with id:', id);
    return api.delete(`/api/tabs/${id}`);
  },
  getTabSettings: (id) => {
    console.log('🔧 Calling tabsAPI.getTabSettings() with id:', id);
    return api.get(`/api/tabs/${id}/settings`);
  },
};

// Queue API
export const queueAPI = {
  getQueueStatus: () => {
    console.log('🔧 Calling queueAPI.getQueueStatus()');
    return api.get('/api/queue');
  },
  addToQueue: (data) => {
    console.log('🔧 Calling queueAPI.addToQueue() with data:', data);
    return api.post('/api/queue', data);
  },
  getAllJobs: () => {
    console.log('🔧 Calling queueAPI.getAllJobs()');
    return api.get('/api/queue/jobs');
  },
  getJob: (id) => {
    console.log('🔧 Calling queueAPI.getJob() with id:', id);
    return api.get(`/api/queue/jobs/${id}`);
  },
  cancelJob: (id) => {
    console.log('🔧 Calling queueAPI.cancelJob() with id:', id);
    return api.delete(`/api/queue/jobs/${id}`);
  },
  retryJob: (id) => {
    console.log('🔧 Calling queueAPI.retryJob() with id:', id);
    return api.post(`/api/queue/jobs/${id}/retry`);
  },
  clearCompletedJobs: () => {
    console.log('🔧 Calling queueAPI.clearCompletedJobs()');
    return api.post('/api/queue/clear');
  },
  pauseQueue: () => {
    console.log('🔧 Calling queueAPI.pauseQueue()');
    return api.post('/api/queue/pause');
  },
  resumeQueue: () => {
    console.log('🔧 Calling queueAPI.resumeQueue()');
    return api.post('/api/queue/resume');
  },
};

// System API
export const systemAPI = {
  getHealth: () => {
    console.log('🔧 Calling systemAPI.getHealth()');
    return api.get('/api/system/health');
  },
  getSystemLoad: () => {
    console.log('🔧 Calling systemAPI.getSystemLoad()');
    return api.get('/api/system/load');
  },
  getProcesses: () => {
    console.log('🔧 Calling systemAPI.getProcesses()');
    return api.get('/api/system/processes');
  },
  getRecentLogs: () => {
    console.log('🔧 Calling systemAPI.getRecentLogs()');
    return api.get('/api/system/logs');
  },
  getConfig: () => {
    console.log('🔧 Calling systemAPI.getConfig()');
    return api.get('/api/system/config');
  },
  getDiskUsage: () => {
    console.log('🔧 Calling systemAPI.getDiskUsage()');
    return api.get('/api/system/disk');
  },
};

// Content API (placeholder for future implementation)
export const contentAPI = {
  getContent: (tabId) => {
    console.log('🔧 Calling contentAPI.getContent() with tabId:', tabId);
    return api.get(`/api/content/${tabId}`);
  },
  scanContent: () => {
    console.log('🔧 Calling contentAPI.scanContent()');
    return api.post('/api/system/scan');
  },
};

export default api;