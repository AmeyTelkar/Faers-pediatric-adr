import { createPortal } from 'react-dom';
import { ShieldOff } from 'lucide-react';

/**
 * Layer 15: License Expiry Lock Screen
 * Full-screen overlay rendered via Portal — cannot be dismissed or bypassed.
 */
export default function LicenseLockScreen() {
  return createPortal(
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 999999,
        background: 'rgba(5, 5, 15, 0.98)',
        backdropFilter: 'blur(20px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'not-allowed',
      }}
      onClickCapture={(e) => e.stopPropagation()}
      onKeyDownCapture={(e) => e.stopPropagation()}
    >
      <div style={{ textAlign: 'center', maxWidth: 480, padding: 40 }}>
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-red-500/10 border border-red-500/30 mb-6 mx-auto" style={{ display: 'flex' }}>
          <ShieldOff className="w-10 h-10 text-red-400" />
        </div>
        <h1 style={{ color: '#ef4444', fontSize: 28, fontWeight: 800, marginBottom: 16, letterSpacing: 1 }}>
          LICENSE EXPIRED
        </h1>
        <p style={{ color: '#9ca3af', fontSize: 14, lineHeight: 1.8, marginBottom: 24 }}>
          This PulseTech license has expired or is invalid.<br />
          All dashboard access has been suspended.
        </p>
        <div style={{
          padding: '16px 24px',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: 12,
          marginBottom: 24,
        }}>
          <p style={{ color: '#a5b4fc', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
            Contact Support
          </p>
          <p style={{ color: '#6366f1', fontSize: 14, fontFamily: 'monospace' }}>
            support@pulsetech-adr.com
          </p>
        </div>
        <p style={{ color: '#374151', fontSize: 10, fontFamily: 'monospace', letterSpacing: 1 }}>
          © 2026 PULSETECH (ANC-031) | MIT VISHWAPRAYAG UNIVERSITY
        </p>
      </div>
    </div>,
    document.body
  );
}
