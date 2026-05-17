import axios from 'axios';

// ── License lock state (shared across app) ─────────────────────────
let licenseLocked = false;
const licenseListeners = [];
export const onLicenseLock = (cb) => licenseListeners.push(cb);
export const isLicenseLocked = () => licenseLocked;

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Attach JWT token to every request (from sessionStorage) ────────
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('pt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor ───────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    // Layer 15: License expired → show lock screen
    if (status === 423) {
      licenseLocked = true;
      licenseListeners.forEach((cb) => cb());
      return Promise.reject(error);
    }

    // 401 Unauthorized → force logout
    if (status === 401) {
      sessionStorage.removeItem('pt_token');
      sessionStorage.removeItem('pt_user');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // 429 Rate limited
    if (status === 429) {
      console.warn('[SECURITY] Rate limited by server');
    }

    return Promise.reject(error);
  }
);

export default api;
