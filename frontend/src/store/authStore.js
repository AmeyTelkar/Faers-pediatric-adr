import { create } from 'zustand';
import axios from 'axios';

/**
 * Auth store using sessionStorage (NOT localStorage).
 * sessionStorage is per-tab — closing the tab kills the session.
 * Copying a URL to a new tab forces re-login.
 */
const useAuthStore = create((set, get) => ({
  token: sessionStorage.getItem('pt_token') || null,
  username: sessionStorage.getItem('pt_user') || null,
  isAuthenticated: !!sessionStorage.getItem('pt_token'),
  loginError: null,
  isLoading: false,

  login: async (username, password) => {
    set({ isLoading: true, loginError: null });
    try {
      const res = await axios.post('/api/auth/login', { username, password });
      const { access_token, username: user } = res.data;
      sessionStorage.setItem('pt_token', access_token);
      sessionStorage.setItem('pt_user', user);
      set({ token: access_token, username: user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check credentials.';
      set({ loginError: msg, isLoading: false });
      return false;
    }
  },

  logout: () => {
    sessionStorage.removeItem('pt_token');
    sessionStorage.removeItem('pt_user');
    set({ token: null, username: null, isAuthenticated: false });
  },

  getToken: () => get().token,
}));

export default useAuthStore;
