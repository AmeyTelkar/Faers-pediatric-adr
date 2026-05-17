import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useState, useEffect } from 'react';
import useAuthStore from './store/authStore';
import { onLicenseLock } from './api/client';
import './security'; // Layer 1-3: DevTools detection, right-click, keyboard blocks
import Sidebar from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';
import LicenseLockScreen from './components/LicenseLockScreen';
import LoginPage from './pages/LoginPage';
import UploadHub from './pages/UploadHub';
import Demographics from './pages/Demographics';
import ADRAnalysis from './pages/ADRAnalysis';
import SignalDetection from './pages/SignalDetection';
import GNNNetworkView from './pages/GNNNetworkView';
import OutcomesSeverity from './pages/OutcomesSeverity';
import ReportBuilder from './pages/ReportBuilder';

/* ── Route guard ────────────────────────────────────────────────── */
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/* ── Layer 5: Copyright Watermark (diagonal, center of screen) ──── */
function Watermark() {
  return (
    <div
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%) rotate(-30deg)',
        zIndex: 9998,
        pointerEvents: 'none',
        opacity: 0.03,
        userSelect: 'none',
        whiteSpace: 'nowrap',
      }}
    >
      <p style={{ fontSize: 28, color: '#fff', fontFamily: 'monospace', letterSpacing: 6, fontWeight: 700 }}>
        PULSETECH ANC-031 • LICENSED COPY
      </p>
    </div>
  );
}

/* ── Dashboard layout ───────────────────────────────────────────── */
function DashboardLayout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 bg-surface-dark">
          <div className="max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
        <div className="h-7 bg-surface-card/50 border-t border-surface-border flex items-center justify-between px-4">
          <p className="text-[9px] text-gray-600 tracking-wide select-none">
            © 2026 PulseTech (ANC-031) | MIT Vishwaprayag University
          </p>
          <p className="text-[9px] text-gray-700 tracking-wide select-none font-mono">
            All Rights Reserved | Unauthorized access is prohibited
          </p>
        </div>
      </div>
    </div>
  );
}

function App() {
  const { isAuthenticated } = useAuthStore();
  const [showLicenseLock, setShowLicenseLock] = useState(false);

  // Layer 15: Listen for license expiry from API
  useEffect(() => {
    onLicenseLock(() => setShowLicenseLock(true));
  }, []);

  return (
    <Router>
      {/* License Lock Screen (cannot be dismissed) */}
      {showLicenseLock && <LicenseLockScreen />}

      {/* Watermark on every page */}
      <Watermark />

      <Routes>
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/upload" replace /> : <LoginPage />}
        />
        <Route path="/" element={<ProtectedRoute><DashboardLayout><UploadHub /></DashboardLayout></ProtectedRoute>} />
        <Route path="/upload" element={<ProtectedRoute><DashboardLayout><UploadHub /></DashboardLayout></ProtectedRoute>} />
        <Route path="/demographics" element={<ProtectedRoute><DashboardLayout><Demographics /></DashboardLayout></ProtectedRoute>} />
        <Route path="/adr-analysis" element={<ProtectedRoute><DashboardLayout><ADRAnalysis /></DashboardLayout></ProtectedRoute>} />
        <Route path="/signals" element={<ProtectedRoute><DashboardLayout><SignalDetection /></DashboardLayout></ProtectedRoute>} />
        <Route path="/gnn" element={<ProtectedRoute><DashboardLayout><GNNNetworkView /></DashboardLayout></ProtectedRoute>} />
        <Route path="/outcomes" element={<ProtectedRoute><DashboardLayout><OutcomesSeverity /></DashboardLayout></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute><DashboardLayout><ReportBuilder /></DashboardLayout></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1a2e',
            color: '#e5e7eb',
            border: '1px solid #2d2d4a',
          },
          success: { iconTheme: { primary: '#10b981', secondary: '#1a1a2e' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#1a1a2e' } },
        }}
      />
    </Router>
  );
}

export default App;
