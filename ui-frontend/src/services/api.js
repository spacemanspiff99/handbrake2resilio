/**
 * Verified mapping: ui-frontend (axios baseURL) → api-gateway (Flask) → typical success status.
 * Nginx (production): /api/* → api-gateway:8080/api/, /health → :8080/health, /socket.io/ → :8080/socket.io/
 *
 * | Client call (api.js)              | Method | Backend route                          | OK status |
 * |-----------------------------------|--------|----------------------------------------|-----------|
 * | authAPI.login                     | POST   | /api/auth/login                        | 200       |
 * | authAPI.register                  | POST   | /api/auth/register                     | 200       |
 * | authAPI.verifyToken               | GET    | /api/auth/verify                       | 200       |
 * | tabsAPI.getTabs                   | GET    | /api/tabs                              | 200       |
 * | tabsAPI.createTab                 | POST   | /api/tabs                              | 200       |
 * | tabsAPI.updateTab(id)             | PUT    | /api/tabs/<int:tab_id>                 | 200       |
 * | tabsAPI.deleteTab(id)             | DELETE | /api/tabs/<int:tab_id>                 | 200       |
 * | tabsAPI.getTabSettings(id)        | GET    | /api/tabs/<int:tab_id>/settings        | 200       |
 * | queueAPI.getQueueStatus           | GET    | /api/queue                             | 200       |
 * | queueAPI.addToQueue               | POST   | /api/jobs/add                          | 200       |
 * | queueAPI.getAllJobs               | GET    | /api/queue/jobs                        | 200       |
 * | queueAPI.getJob(id)               | GET    | /api/jobs/status/<job_id>             | 200       |
 * | queueAPI.cancelJob(id)            | POST   | /api/jobs/cancel/<job_id>              | 200       |
 * | queueAPI.deleteJob(id)            | DELETE | /api/jobs/<job_id>                     | 200       |
 * | queueAPI.clearCompletedJobs       | POST   | /api/queue/clear                       | 200       |
 * | queueAPI.pauseQueue               | POST   | /api/queue/pause                       | 200       |
 * | queueAPI.resumeQueue              | POST   | /api/queue/resume                      | 200       |
 * | systemAPI.getHealth               | GET    | /health                                | 200       |
 * | systemAPI.getSystemLoad           | GET    | /api/system/load                       | 200       |
 * | filesystemAPI.browse              | GET    | /api/filesystem/browse                 | 200       |
 * | filesystemAPI.scan                | POST   | /api/filesystem/scan                   | 200       |
 * | filesystemAPI.mkdir               | POST   | /api/filesystem/mkdir                  | 200       |
 * | filesystemAPI.getCachedContent    | GET    | /api/filesystem/cache                  | 200 / 404 |
 *
 * Tab `id`: SQLite INTEGER (`tabs.id`); URLs use numeric segments — matches `<int:tab_id>`.
 * Job `id`: UUID string from /api/jobs/add — matches `<job_id>` (string) routes.
 *
 * Other: App.js + index.js POST /api/log-error (fetch, not this module) → 200.
 */
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
  deleteJob: (id) => api.delete(`/api/jobs/${id}`),
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
