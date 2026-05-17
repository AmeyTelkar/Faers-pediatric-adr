import { useState } from 'react';
import { Lock, User, Eye, EyeOff, ShieldCheck, AlertTriangle, Fingerprint } from 'lucide-react';
import useAuthStore from '../store/authStore';

export default function LoginPage() {
  const { login, loginError, isLoading } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await login(username, password);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-dark relative overflow-hidden">

      {/* Subtle background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full opacity-[0.035]"
          style={{ background: 'radial-gradient(circle, #6366f1, transparent 70%)' }} />
      </div>

      <div className="w-full max-w-[420px] mx-4 relative z-10">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-pulse-600/15 border border-pulse-500/25 mb-5">
            <ShieldCheck className="w-7 h-7 text-pulse-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-100">Admin Login</h1>
          <p className="text-xs text-gray-500 mt-1.5">PulseTech FAERS Dashboard</p>
        </div>

        {/* Login card */}
        <div className="glass-card p-7 space-y-6">

          {/* Status bar */}
          <div className="flex items-center justify-between pb-4 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <Fingerprint className="w-3.5 h-3.5 text-pulse-400" />
              <span className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold">Secure Login</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-neon-green" />
              <span className="text-[10px] text-neon-green font-mono">ENCRYPTED</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Admin ID */}
            <div>
              <label className="block text-[11px] text-gray-400 mb-2 uppercase tracking-wider font-semibold">Admin ID</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter Admin ID"
                  className="input-field pl-11 py-3 rounded-xl"
                  autoFocus
                  required
                  id="login-username"
                  autoComplete="off"
                />
              </div>
            </div>

            {/* Security Key */}
            <div>
              <label className="block text-[11px] text-gray-400 mb-2 uppercase tracking-wider font-semibold">Security Key</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter Security Key"
                  className="input-field pl-11 pr-12 py-3 rounded-xl"
                  required
                  id="login-password"
                  autoComplete="off"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-300 transition-colors"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error */}
            {loginError && (
              <div className="flex items-center gap-2.5 p-3 bg-neon-red/10 border border-neon-red/30 rounded-xl animate-fade-in">
                <AlertTriangle className="w-4 h-4 text-neon-red flex-shrink-0" />
                <span className="text-xs text-red-300">{loginError}</span>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="btn-primary w-full py-3 rounded-xl flex items-center justify-center gap-2.5 text-sm font-bold"
              id="login-submit"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  Authorize Access
                </>
              )}
            </button>
          </form>

          {/* Warning */}
          <div className="pt-4 border-t border-surface-border text-center">
            <p className="text-[9px] text-gray-600 font-mono tracking-wide">
              UNAUTHORIZED ACCESS ATTEMPTS ARE LOGGED
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[9px] text-gray-700 mt-5">
          &copy; 2026 PulseTech (ANC-031) | MIT Vishwaprayag University
        </p>
      </div>
    </div>
  );
}
