import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Bell, Settings, CalendarDays, ChevronDown, LogOut } from 'lucide-react';
import { useEffect } from 'react';
import useUploadStore from '../../store/uploadStore';
import useAuthStore from '../../store/authStore';

const titleMap = {
  '/': 'Upload Hub',
  '/upload': 'Upload Hub',
  '/demographics': 'Demographics Analysis',
  '/adr-analysis': 'ADR Analysis',
  '/signals': 'Signal Detection',
  '/gnn': 'GNN Network View',
  '/outcomes': 'Outcomes & Severity',
  '/reports': 'Report Builder',
};

function YearQuarterSelector() {
  const {
    selectedYear, selectedQuarter, loadedYears, loadedQuarters,
    setSelectedYear, setSelectedQuarter,
    fetchLoadedYears, fetchLoadedQuarters
  } = useUploadStore();

  useEffect(() => {
    fetchLoadedYears();
    fetchLoadedQuarters();
  }, []);

  const availableQuarters = selectedYear === 'ALL'
    ? loadedQuarters
    : loadedQuarters.filter(q => q.value.startsWith(String(selectedYear)));

  const totalLoaded = loadedQuarters.length;

  return (
    <div className="flex items-center gap-2">
      <CalendarDays className="w-4 h-4 text-gray-500" />
      
      {/* YEAR SELECTOR */}
      <div className="relative">
        <select
          value={selectedYear}
          onChange={(e) => {
            const val = e.target.value === 'ALL' ? 'ALL' : parseInt(e.target.value);
            setSelectedYear(val);
          }}
          className="appearance-none bg-surface-dark border border-surface-border rounded-lg pl-3 pr-8 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-pulse-500 focus:ring-1 focus:ring-pulse-500/30 cursor-pointer min-w-[100px] transition-all"
        >
          <option value="ALL">All Years</option>
          {loadedYears.map(y => (
            <option key={y.year} value={y.year}>
              {y.year}  ({y.quarter_count}Q)
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" />
      </div>

      <span className="text-gray-500 text-sm">/</span>

      {/* QUARTER SELECTOR */}
      <div className="relative">
        <select
          value={selectedQuarter}
          onChange={(e) => setSelectedQuarter(e.target.value)}
          className="appearance-none bg-surface-dark border border-surface-border rounded-lg pl-3 pr-8 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-pulse-500 focus:ring-1 focus:ring-pulse-500/30 cursor-pointer min-w-[160px] transition-all"
        >
          <option value="ALL">
            {selectedYear === 'ALL' ? 'All Quarters' : `All ${selectedYear}`}
          </option>
          {availableQuarters.map((q) => (
            <option key={q.value} value={q.value}>
              {q.label}  ({q.patients?.toLocaleString()} pts)
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" />
      </div>

      <span
        className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-semibold tracking-wide bg-pulse-600/20 text-pulse-300 border border-pulse-500/30`}
      >
        {totalLoaded}Q
      </span>
    </div>
  );
}

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const title = titleMap[location.pathname] || 'Dashboard';
  const { username, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-surface-card/80 backdrop-blur-md border-b border-surface-border flex items-center justify-between px-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-100">{title}</h2>
        <p className="text-xs text-gray-500">Pediatric Pharmacovigilance Analytics</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Quarter Selector */}
        <YearQuarterSelector />

        {/* Divider */}
        <div className="w-px h-6 bg-surface-border" />

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search drugs, ADRs..."
            className="pl-10 pr-4 py-2 w-56 bg-surface-dark border border-surface-border rounded-lg text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-pulse-500 focus:ring-1 focus:ring-pulse-500/30 transition-all"
          />
        </div>

        <button className="p-2 rounded-lg hover:bg-surface-hover transition-colors relative" id="notifications-btn">
          <Bell className="w-5 h-5 text-gray-400" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-neon-cyan rounded-full" />
        </button>

        <button className="p-2 rounded-lg hover:bg-surface-hover transition-colors" id="settings-btn">
          <Settings className="w-5 h-5 text-gray-400" />
        </button>

        {/* Admin user + Logout */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pulse-500 to-neon-purple flex items-center justify-center">
            <span className="text-xs font-bold text-white">{(username || 'A')[0].toUpperCase()}</span>
          </div>
          <span className="text-xs text-gray-400 hidden lg:block">{username || 'Admin'}</span>
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg hover:bg-red-500/20 transition-colors group" title="Logout"
            id="logout-btn"
          >
            <LogOut className="w-4 h-4 text-gray-500 group-hover:text-red-400 transition-colors" />
          </button>
        </div>
      </div>
    </header>
  );
}
