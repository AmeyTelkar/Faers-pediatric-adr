/**
 * PulseTech Security Shield (Frontend)
 * Layers: DevTools detection, keyboard shortcuts block, right-click disable, watermark
 * Copyright (c) 2026 PulseTech (ANC-031). All rights reserved.
 */

// ═══════════════════════════════════════════════════════════════════
// Layer 1: DevTools Detection
// ═══════════════════════════════════════════════════════════════════
let devtoolsOpen = false;

function detectDevTools() {
  const threshold = 160;
  const widthDiff = window.outerWidth - window.innerWidth;
  const heightDiff = window.outerHeight - window.innerHeight;

  if (widthDiff > threshold || heightDiff > threshold) {
    if (!devtoolsOpen) {
      devtoolsOpen = true;
      handleDevToolsOpen();
    }
  } else {
    devtoolsOpen = false;
  }
}

function handleDevToolsOpen() {
  // Force logout
  sessionStorage.removeItem('pt_token');
  sessionStorage.removeItem('pt_user');

  // Show warning and redirect
  document.body.innerHTML = `
    <div style="
      position:fixed; inset:0; z-index:999999;
      background: #0a0a0f;
      display:flex; align-items:center; justify-content:center;
      font-family: system-ui, sans-serif;
    ">
      <div style="text-align:center; max-width:500px; padding:40px;">
        <div style="font-size:64px; margin-bottom:20px;">🛡️</div>
        <h1 style="color:#ef4444; font-size:24px; font-weight:800; margin-bottom:12px; letter-spacing:2px;">
          SECURITY VIOLATION
        </h1>
        <p style="color:#9ca3af; font-size:14px; line-height:1.8; margin-bottom:24px;">
          Developer tools detected. Your session has been terminated
          and this incident has been logged.
        </p>
        <p style="color:#6b7280; font-size:11px; font-family:monospace;">
          © 2026 PulseTech (ANC-031) | MIT Vishwaprayag University
        </p>
      </div>
    </div>
  `;
}

// Check every 500ms
setInterval(detectDevTools, 500);

// ═══════════════════════════════════════════════════════════════════
// Layer 2: Disable Right-Click
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  return false;
});

// ═══════════════════════════════════════════════════════════════════
// Layer 3: Block DevTools Keyboard Shortcuts
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('keydown', (e) => {
  // F12
  if (e.key === 'F12') {
    e.preventDefault();
    return false;
  }
  // Ctrl+Shift+I / Ctrl+Shift+J / Ctrl+Shift+C
  if (e.ctrlKey && e.shiftKey && ['I', 'J', 'C'].includes(e.key.toUpperCase())) {
    e.preventDefault();
    return false;
  }
  // Ctrl+U (view source)
  if (e.ctrlKey && e.key.toUpperCase() === 'U') {
    e.preventDefault();
    return false;
  }
  // Ctrl+S (save page)
  if (e.ctrlKey && e.key.toUpperCase() === 'S') {
    e.preventDefault();
    return false;
  }
});

// ═══════════════════════════════════════════════════════════════════
// Layer: Disable text selection on sensitive areas
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('selectstart', (e) => {
  // Allow selection in input/textarea
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  e.preventDefault();
});

// ═══════════════════════════════════════════════════════════════════
// Layer: Disable drag
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('dragstart', (e) => {
  e.preventDefault();
});

// ═══════════════════════════════════════════════════════════════════
// Layer 6: CSS Watermark Overlay (cannot be removed without source)
// ═══════════════════════════════════════════════════════════════════
(function injectWatermark() {
  const style = document.createElement('style');
  style.textContent = `
    body::after {
      content: "EDUCATIONAL USE ONLY — © 2026 PULSETECH (ANC-031) — NOT FOR REDISTRIBUTION";
      position: fixed;
      bottom: 8px;
      right: 12px;
      z-index: 99999;
      pointer-events: none;
      user-select: none;
      font-size: 8px;
      font-family: monospace;
      color: rgba(255,255,255,0.06);
      letter-spacing: 1px;
      font-weight: 600;
    }
    /* Print protection: hide content when printing */
    @media print {
      body * { visibility: hidden !important; }
      body::before {
        visibility: visible !important;
        content: "PRINTING DISABLED — PulseTech (ANC-031) — Educational Use Only";
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-family: monospace;
        color: #000;
        background: #fff;
        z-index: 999999;
      }
    }
  `;
  document.head.appendChild(style);
})();

// ═══════════════════════════════════════════════════════════════════
// Layer 7: Disable Copy/Paste of page content
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('copy', (e) => {
  // Allow copy in input/textarea
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  e.preventDefault();
  if (e.clipboardData) {
    e.clipboardData.setData('text/plain', '© 2026 PulseTech (ANC-031) — Content copying is disabled.');
  }
});

export default {
  init() {
    console.log('[PulseTech] Security shield active — Educational build');
  }
};
