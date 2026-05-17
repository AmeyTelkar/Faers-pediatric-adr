import { create } from 'zustand';
import api from '../api/client';

const useUploadStore = create((set, get) => ({
  // ── Upload state ─────────────────────────────────────────
  files: {},
  quarter: 'Q1',
  year: 2025,
  taskId: null,
  previewStats: null,
  status: 'idle',
  error: null,
  sessionId: null,

  setFile: (fileType, file) =>
    set((state) => ({
      files: { ...state.files, [fileType]: file },
    })),

  removeFile: (fileType) =>
    set((state) => {
      const files = { ...state.files };
      delete files[fileType];
      return { files };
    }),

  setQuarter: (quarter) => set({ quarter }),
  setYear: (year) => set({ year }),
  setTaskId: (taskId) => set({ taskId }),
  setPreviewStats: (previewStats) => set({ previewStats }),
  setStatus: (status) => set({ status }),
  setError: (error) => set({ error }),
  setSessionId: (sessionId) => set({ sessionId }),

  reset: () =>
    set({
      files: {},
      quarter: 'Q1',
      year: 2025,
      taskId: null,
      previewStats: null,
      status: 'idle',
      error: null,
      sessionId: null,
    }),

  getQuarterString: () => {
    const state = get();
    return `${state.year}${state.quarter}`;
  },

  getFileCount: () => {
    return Object.keys(get().files).length;
  },

  // ── Global Quarter Selection (drives all dashboard pages) ──
  selectedYear: 'ALL',
  selectedQuarter: 'ALL',
  loadedYears: [],
  loadedQuarters: [],

  setSelectedYear: (year) => {
    set({ selectedYear: year });
    // When year changes, reset quarter to ALL
    set({ selectedQuarter: 'ALL' });
  },

  setSelectedQuarter: (q) => set({ selectedQuarter: q }),

  fetchLoadedYears: async () => {
    try {
      const res = await api.get('/demographics/years');
      set({ loadedYears: res.data.years || [] });
    } catch (err) {
      console.error('Failed to fetch years:', err);
    }
  },

  fetchLoadedQuarters: async () => {
    try {
      const res = await api.get('/demographics/quarters');
      set({ loadedQuarters: res.data.quarters || [] });
    } catch (err) {
      console.error('Failed to fetch quarters:', err);
    }
  },

  getActiveQuarterFilter: () => {
    const { selectedYear, selectedQuarter } = get();
    if (selectedYear === 'ALL') return 'ALL';
    if (selectedQuarter === 'ALL') return `${selectedYear}_ALL`;
    return selectedQuarter;
  },

  getQuarterLabel: () => {
    const { selectedYear, selectedQuarter, loadedQuarters } = get();
    if (selectedYear === 'ALL') return 'All Years / All Quarters';
    if (selectedQuarter === 'ALL') return `All Quarters in ${selectedYear}`;
    const q = loadedQuarters.find((q) => q.value === selectedQuarter);
    return q ? q.label : selectedQuarter;
  },
}));

export default useUploadStore;
