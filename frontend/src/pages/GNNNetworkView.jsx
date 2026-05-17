import { useState, useEffect, useRef, useMemo } from 'react';
import { Network, Play, Loader2, Maximize2, Minimize2, ZoomIn, ZoomOut, RotateCcw, Info } from 'lucide-react';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const AGE_GROUPS = ['NEONATE', 'INFANT', 'CHILD', 'ADOLESCENT'];
const DRUG_COLOR = '#6366f1';
const ADR_COLOR  = '#f59e0b';
const SIGNAL_EDGE = '#ef4444';
const NORMAL_EDGE = '#4338ca';

/* ---------- seeded PRNG (avoids strict-mode double-run jitter) ---------- */
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export default function GNNNetworkView() {
  const [ageGroup, setAgeGroup] = useState('CHILD');
  const [graphData, setGraphData] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [trainingStatus, setTrainingStatus] = useState({});
  const [viewMode, setViewMode] = useState('classical');
  const [loading, setLoading] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef({ active: false, lastX: 0, lastY: 0 });
  const svgRef = useRef(null);
  const { selectedYear, selectedQuarter, getActiveQuarterFilter } = useUploadStore();

  useEffect(() => { loadGraphData(); loadStatus(); }, [ageGroup, selectedYear, selectedQuarter]);

  const loadGraphData = async () => {
    setLoading(true);
    try {
      const qFilter = getActiveQuarterFilter();
      const res = await api.get(`/gnn/graph-data/${ageGroup}?quarter=${qFilter}`);
      setGraphData(res.data);
      setZoom(1); setPan({ x: 0, y: 0 });
    } catch (err) { console.error(err); }
    setLoading(false);
  };

  const loadStatus = async () => {
    try { 
      const qFilter = getActiveQuarterFilter();
      const res = await api.get(`/gnn/status?quarter=${qFilter}`); 
      setTrainingStatus(res.data); 
    } catch {}
  };

  const handleTrain = async () => {
    try {
      const qFilter = getActiveQuarterFilter();
      const res = await api.post(`/gnn/train/${ageGroup}?epochs=100&quarter=${qFilter}`);
      setTrainingStatus(p => ({ ...p, [ageGroup]: res.data }));
      const predRes = await api.get(`/gnn/predictions/${ageGroup}?top_k=30&quarter=${qFilter}`);
      setPredictions(predRes.data.predictions || []);
    } catch (err) { console.error(err); }
  };

  /* ---------- Force-directed layout — tuned for 50-300 nodes ---------- */
  const VB_W = 1200, VB_H = 900;

  const layout = useMemo(() => {
    if (!graphData?.nodes?.length) return null;
    const { nodes, edges } = graphData;
    const rng = mulberry32(42);
    const pos = {};
    const PAD = 50;

    // Build adjacency for faster lookup
    const adj = {};
    nodes.forEach(n => { adj[n.id] = []; });
    edges.forEach(e => {
      if (adj[e.source]) adj[e.source].push(e.target);
      if (adj[e.target]) adj[e.target].push(e.source);
    });

    // Separate drugs and ADRs for positioning  
    const drugs = nodes.filter(n => n.type === 'drug');
    const adrs  = nodes.filter(n => n.type === 'adr');

    // Initial layout: drugs in inner ring, ADRs in outer ring
    drugs.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(drugs.length, 1);
      const r = Math.min(VB_W, VB_H) * 0.2;
      pos[n.id] = {
        x: VB_W / 2 + r * Math.cos(angle) + (rng() - 0.5) * 20,
        y: VB_H / 2 + r * Math.sin(angle) + (rng() - 0.5) * 20
      };
    });
    adrs.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(adrs.length, 1);
      const r = Math.min(VB_W, VB_H) * 0.38;
      pos[n.id] = {
        x: VB_W / 2 + r * Math.cos(angle) + (rng() - 0.5) * 40,
        y: VB_H / 2 + r * Math.sin(angle) + (rng() - 0.5) * 40
      };
    });

    // Force-directed simulation: tuned parameters
    const ITERS = 300;
    const REPULSION = 35000;
    const SPRING_K = 0.004;
    const CENTER_PULL = 0.003;
    const MIN_DIST = 10;            // prevents divide-by-zero / Infinity
    const MAX_DISPLACEMENT = 15;    // caps per-step movement

    for (let iter = 0; iter < ITERS; iter++) {
      const alpha = 1 - iter / ITERS;
      const cooling = alpha * alpha; // quadratic cooling

      // Accumulate forces then apply (more stable than immediate mutation)
      const forces = {};
      nodes.forEach(n => { forces[n.id] = { x: 0, y: 0 }; });

      // Repulsion (all-pairs, Coulomb-like)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const ni = nodes[i].id, nj = nodes[j].id;
          const a = pos[ni], b = pos[nj];
          if (!a || !b) continue;
          let dx = a.x - b.x, dy = a.y - b.y;
          // Jitter overlapping nodes so they separate
          if (dx === 0 && dy === 0) { dx = (rng() - 0.5) * 2; dy = (rng() - 0.5) * 2; }
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), MIN_DIST);
          const force = (REPULSION / (dist * dist)) * cooling;
          const cappedForce = Math.min(force, MAX_DISPLACEMENT);
          const fx = (dx / dist) * cappedForce, fy = (dy / dist) * cappedForce;
          forces[ni].x += fx;  forces[ni].y += fy;
          forces[nj].x -= fx;  forces[nj].y -= fy;
        }
      }

      // Spring attraction along edges (Hooke-like)
      for (const e of edges) {
        const fi = forces[e.source], fj = forces[e.target];
        const a = pos[e.source], b = pos[e.target];
        if (!a || !b || !fi || !fj) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), MIN_DIST);
        const idealDist = 120;
        const force = (dist - idealDist) * SPRING_K * cooling;
        const cappedForce = Math.min(Math.abs(force), MAX_DISPLACEMENT) * Math.sign(force);
        const fx = (dx / dist) * cappedForce;
        const fy = (dy / dist) * cappedForce;
        fi.x += fx; fi.y += fy;
        fj.x -= fx; fj.y -= fy;
      }

      // Apply forces + centering
      for (const n of nodes) {
        const p = pos[n.id];
        const f = forces[n.id];
        if (!p || !f) continue;
        // Apply accumulated force (capped)
        const mag = Math.sqrt(f.x * f.x + f.y * f.y);
        if (mag > MAX_DISPLACEMENT) {
          f.x = (f.x / mag) * MAX_DISPLACEMENT;
          f.y = (f.y / mag) * MAX_DISPLACEMENT;
        }
        p.x += f.x;
        p.y += f.y;
        // Gentle centering
        p.x += (VB_W / 2 - p.x) * CENTER_PULL;
        p.y += (VB_H / 2 - p.y) * CENTER_PULL;
        // Boundary clamp
        p.x = Math.max(PAD, Math.min(VB_W - PAD, p.x));
        p.y = Math.max(PAD, Math.min(VB_H - PAD, p.y));
        // NaN safety net
        if (!isFinite(p.x)) p.x = VB_W / 2 + (rng() - 0.5) * 100;
        if (!isFinite(p.y)) p.y = VB_H / 2 + (rng() - 0.5) * 100;
      }
    }

    return pos;
  }, [graphData]);

  // Mouse handlers for SVG interaction
  const onMouseDown = (e) => {
    if (e.target.closest('button')) return;
    dragRef.current = { active: true, lastX: e.clientX, lastY: e.clientY };
  };
  const onMouseMove = (e) => {
    if (!dragRef.current?.active) return;
    const dx = e.clientX - dragRef.current.lastX;
    const dy = e.clientY - dragRef.current.lastY;
    dragRef.current.lastX = e.clientX;
    dragRef.current.lastY = e.clientY;
    setPan(p => ({ x: p.x + dx / zoom, y: p.y + dy / zoom }));
  };
  const onMouseUp = () => { if (dragRef.current) dragRef.current.active = false; };
  const onWheel = (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom(z => Math.max(0.2, Math.min(8, z * factor)));
  };
  const resetView = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  const agStatus = trainingStatus[ageGroup];
  const svgH = isFullscreen ? 'calc(100vh - 130px)' : '600px';
  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];
  const drugCount = nodes.filter(n => n.type === 'drug').length;
  const adrCount  = nodes.filter(n => n.type === 'adr').length;
  const signalCount = edges.filter(e => e.is_signal).length;

  const graphPanel = (
    <div className="relative" style={{ height: svgH }}>
      <svg ref={svgRef} width="100%" height="100%"
        viewBox={`0 0 ${VB_W} ${VB_H}`} preserveAspectRatio="xMidYMid meet"
        style={{ background: '#0a0a19', borderRadius: 8, cursor: dragRef.current?.active ? 'grabbing' : 'grab' }}
        onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp}
        onMouseLeave={() => { dragRef.current.active = false; setHoveredNode(null); }}
        onWheel={onWheel}>

        {/* Grid */}
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(99,102,241,0.04)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="bgGlow" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="rgba(99,102,241,0.06)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0)" />
          </radialGradient>
        </defs>
        <rect width={VB_W} height={VB_H} fill="url(#grid)" />
        <rect width={VB_W} height={VB_H} fill="url(#bgGlow)" />

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Edges */}
          {layout && edges.map((e, i) => {
            const a = layout[e.source], b = layout[e.target];
            if (!a || !b) return null;
            const hl = hoveredNode && (e.source === hoveredNode || e.target === hoveredNode);
            const dim = hoveredNode && !hl;
            return (
              <line key={`e-${i}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke={hl ? '#10b981' : e.is_signal ? SIGNAL_EDGE : NORMAL_EDGE}
                strokeWidth={hl ? 2.5 : Math.min(Math.max((e.count || 1) / 10, 0.5), 2.5)}
                opacity={dim ? 0.03 : hl ? 0.9 : e.is_signal ? 0.4 : 0.12}
              />
            );
          })}

          {/* Nodes */}
          {layout && nodes.map((n) => {
            const p = layout[n.id];
            if (!p) return null;
            const isHov = n.id === hoveredNode;
            const isConn = hoveredNode && edges.some(e =>
              (e.source === hoveredNode && e.target === n.id) || (e.target === hoveredNode && e.source === n.id));
            const dim = hoveredNode && !isHov && !isConn;
            const cnt = n.count || 1;
            const sz = Math.max(5, Math.min(Math.sqrt(cnt) * 2, 22));
            const showLabel = isHov || isConn || zoom > 1.5 || nodes.length < 40 || cnt > 50;

            return (
              <g key={`n-${n.id}`}
                onMouseEnter={() => setHoveredNode(n.id)}
                onMouseLeave={() => setHoveredNode(null)}
                opacity={dim ? 0.1 : 1}
                style={{ cursor: 'pointer', transition: 'opacity 0.15s' }}>
                {/* Glow */}
                {isHov && <circle cx={p.x} cy={p.y} r={sz + 10} fill={n.type === 'drug' ? DRUG_COLOR : ADR_COLOR} opacity={0.25} />}
                {/* Node shape */}
                {n.type === 'drug' ? (
                  <circle cx={p.x} cy={p.y} r={isHov ? sz * 1.4 : sz}
                    fill={isHov ? '#818cf8' : isConn ? '#a5b4fc' : DRUG_COLOR}
                    stroke={isHov ? '#c7d2fe' : 'none'} strokeWidth={isHov ? 2 : 0} />
                ) : (
                  <polygon
                    points={`${p.x},${p.y - sz} ${p.x + sz},${p.y} ${p.x},${p.y + sz} ${p.x - sz},${p.y}`}
                    fill={isHov ? '#fbbf24' : isConn ? '#fcd34d' : ADR_COLOR}
                    stroke={isHov ? '#fef3c7' : 'none'} strokeWidth={isHov ? 2 : 0}
                    transform={isHov ? `scale(1.3)` : ''} style={isHov ? { transformOrigin: `${p.x}px ${p.y}px` } : {}} />
                )}
                {/* Label */}
                {showLabel && !dim && (
                  <>
                    <rect x={p.x - 45} y={p.y + sz + 3} width="90" height="16" rx="3" fill="rgba(10,10,25,0.9)" />
                    <text x={p.x} y={p.y + sz + 14} textAnchor="middle" fill={isHov ? '#fff' : '#d1d5db'}
                      fontSize={isHov ? 10 : 8} fontFamily="Inter, system-ui, sans-serif" fontWeight={isHov ? 700 : 400}>
                      {n.id.length > 18 ? n.id.substring(0, 18) + '…' : n.id}
                    </text>
                  </>
                )}
                {/* Tooltip on hover */}
                {isHov && (
                  <g>
                    <rect x={p.x + sz + 10} y={p.y - 40} width="160" height="68" rx="6"
                      fill="#12122aee" stroke="rgba(99,102,241,0.3)" strokeWidth="1" />
                    <text x={p.x + sz + 16} y={p.y - 24} fill={n.type === 'drug' ? '#a5b4fc' : '#fcd34d'}
                      fontSize="10" fontWeight="700" fontFamily="Inter, sans-serif">
                      {n.type === 'drug' ? '💊' : '⚠️'} {n.id.substring(0, 20)}
                    </text>
                    <text x={p.x + sz + 16} y={p.y - 10} fill="#9ca3af" fontSize="9" fontFamily="Inter, sans-serif">
                      Type: {n.type} · Reports: {cnt}
                    </text>
                    <text x={p.x + sz + 16} y={p.y + 3} fill="#9ca3af" fontSize="9" fontFamily="Inter, sans-serif">
                      Connections: {edges.filter(e => e.source === n.id || e.target === n.id).length}
                    </text>
                    <text x={p.x + sz + 16} y={p.y + 16} fill="#ef4444" fontSize="9" fontFamily="Inter, sans-serif">
                      Signals: {edges.filter(e => (e.source === n.id || e.target === n.id) && e.is_signal).length}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>

        {/* Legend (fixed position, not affected by pan/zoom) */}
        <g transform={`translate(14, ${VB_H - 50})`}>
          <rect x="0" y="0" width="280" height="38" rx="6" fill="rgba(10,10,25,0.92)" stroke="rgba(99,102,241,0.15)" />
          <circle cx="20" cy="19" r="7" fill={DRUG_COLOR} />
          <text x="34" y="23" fill="#d1d5db" fontSize="11" fontFamily="Inter, sans-serif">Drug</text>
          <polygon points="95,12 103,19 95,26 87,19" fill={ADR_COLOR} />
          <text x="110" y="23" fill="#d1d5db" fontSize="11" fontFamily="Inter, sans-serif">ADR</text>
          <line x1="155" y1="19" x2="182" y2="19" stroke={SIGNAL_EDGE} strokeWidth="2.5" />
          <text x="188" y="23" fill="#d1d5db" fontSize="11" fontFamily="Inter, sans-serif">Signal</text>
          <line x1="230" y1="19" x2="250" y2="19" stroke={NORMAL_EDGE} strokeWidth="1.5" />
          <text x="255" y="23" fill="#d1d5db" fontSize="11" fontFamily="Inter, sans-serif">Link</text>
        </g>

        {/* Stats footer */}
        <text x={VB_W - 14} y={VB_H - 10} textAnchor="end" fill="#6b7280" fontSize="10" fontFamily="Inter, sans-serif">
          {drugCount} drugs · {adrCount} ADRs · {signalCount} signals · {edges.length} edges
        </text>
      </svg>

      {/* Controls overlay */}
      <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
        <button onClick={() => setIsFullscreen(f => !f)} className="p-2 bg-surface-dark/90 border border-surface-border rounded-lg hover:bg-pulse-600/20" title="Fullscreen">
          {isFullscreen ? <Minimize2 className="w-4 h-4 text-gray-300" /> : <Maximize2 className="w-4 h-4 text-gray-300" />}
        </button>
        <button onClick={() => setZoom(z => Math.min(5, z * 1.3))} className="p-2 bg-surface-dark/90 border border-surface-border rounded-lg hover:bg-pulse-600/20"><ZoomIn className="w-4 h-4 text-gray-300" /></button>
        <button onClick={() => setZoom(z => Math.max(0.3, z / 1.3))} className="p-2 bg-surface-dark/90 border border-surface-border rounded-lg hover:bg-pulse-600/20"><ZoomOut className="w-4 h-4 text-gray-300" /></button>
        <button onClick={resetView} className="p-2 bg-surface-dark/90 border border-surface-border rounded-lg hover:bg-pulse-600/20"><RotateCcw className="w-4 h-4 text-gray-300" /></button>
      </div>
      <div className="absolute bottom-3 left-3 text-[10px] text-gray-500 bg-surface-dark/80 px-2 py-1 rounded z-10">
        {Math.round(zoom * 100)}% · Scroll to zoom · Drag to pan
      </div>
    </div>
  );

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-[#0a0a19] flex flex-col">
        <div className="flex items-center justify-between px-4 py-2 bg-surface-dark border-b border-surface-border">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-semibold text-gray-200">Drug–ADR Network ({ageGroup})</h2>
            <select value={ageGroup} onChange={e => setAgeGroup(e.target.value)} className="select-field w-36 text-xs">
              {AGE_GROUPS.map(ag => <option key={ag} value={ag}>{ag}</option>)}
            </select>
          </div>
          <button onClick={() => setIsFullscreen(false)} className="p-2 hover:bg-surface-hover rounded-lg"><Minimize2 className="w-5 h-5 text-gray-300" /></button>
        </div>
        <div className="flex-1 overflow-hidden p-2">{graphPanel}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div style={{display:'flex', gap:'8px', marginBottom:'12px'}}>
            <span style={{fontSize:'12px', color:'#9CA3AF'}}>
              Showing:
            </span>
            <span style={{fontSize:'12px', fontFamily:'monospace', 
                          background:'#1F2937',
                          padding:'2px 8px', borderRadius:'4px', color:'#93C5FD'}}>
              {selectedYear === 'ALL' ? 'All Years' : selectedYear}
              {' / '}
              {selectedQuarter === 'ALL'
                ? (selectedYear === 'ALL' ? 'All Quarters' : `All ${selectedYear}`)
                : selectedQuarter}
            </span>
          </div>
          <h1 className="text-2xl font-bold gradient-text">GNN Network View</h1>
          <p className="text-sm text-gray-500 mt-1">Heterogeneous Attention Network — Drug-ADR link prediction</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={ageGroup} onChange={e => setAgeGroup(e.target.value)} className="select-field w-40" id="gnn-age-select">
            {AGE_GROUPS.map(ag => <option key={ag} value={ag}>{ag}</option>)}
          </select>
          <div className="flex bg-surface-dark rounded-lg border border-surface-border p-0.5">
            {['classical', 'gnn', 'both'].map(m => (
              <button key={m} onClick={() => setViewMode(m)}
                className={`px-3 py-1.5 text-xs rounded-md transition-all ${viewMode === m ? 'bg-pulse-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}>
                {m === 'classical' ? 'Classical' : m === 'gnn' ? 'GNN Predicted' : 'Both'}
              </button>
            ))}
          </div>
          <button onClick={handleTrain} className="btn-primary flex items-center gap-2" id="train-gnn-btn">
            <Play className="w-4 h-4" /> Train GNN
          </button>
        </div>
      </div>

      {agStatus && (
        <div className={`glass-card p-4 ${agStatus.status === 'completed' ? 'border-neon-green/30' : ''}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-300">
              {agStatus.status === 'completed' ? '✓ Training Complete' : `Status: ${agStatus.status}`}
              {agStatus.status === 'training' && ` — Epoch ${agStatus.epoch}/${agStatus.total_epochs}`}
            </span>
            {agStatus.status === 'completed' && (
              <div className="flex gap-4 text-xs text-gray-400">
                <span>AUC: <span className="text-neon-green font-mono">{agStatus.test_auc}</span></span>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Drug–ADR Network ({ageGroup})</h3>
            <div className="flex items-center gap-1 text-[10px] text-gray-500"><Info className="w-3 h-3" /> Hover · Scroll · Drag</div>
          </div>
          {loading ? (
            <div className="flex items-center justify-center h-[600px]"><Loader2 className="w-10 h-10 animate-spin text-pulse-500" /></div>
          ) : (!graphData || !nodes.length) ? (
            <div className="flex items-center justify-center h-[600px] text-gray-500">
              <div className="text-center"><Network className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No data</p></div>
            </div>
          ) : graphPanel}
        </div>

        <div className="space-y-4">
          <div className="glass-card p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">GNN Novel Predictions</h3>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {predictions.length === 0 ? (
                <p className="text-xs text-gray-500 py-4 text-center">Train GNN to see predictions</p>
              ) : predictions.slice(0, 20).map((p, i) => (
                <div key={i} className="p-2 bg-surface-dark/50 rounded-lg border border-surface-border/50 hover:border-neon-purple/30 transition-colors">
                  <div className="flex items-center justify-between gap-1">
                    <span className="text-xs text-neon-cyan truncate" title={p.drug}>{p.drug}</span>
                    <span className="text-[10px] text-gray-600">→</span>
                    <span className="text-xs text-neon-amber truncate" title={p.adr}>{p.adr}</span>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <div className="w-16 h-1 bg-surface-border rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-neon-purple to-neon-pink rounded-full" style={{ width: `${p.confidence * 100}%` }} />
                    </div>
                    <span className="text-[10px] font-mono text-neon-purple">{(p.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {nodes.length > 0 && (
            <div className="glass-card p-4">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Network Summary</h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-surface-dark/50 p-2 rounded border border-surface-border/40">
                  <div className="text-gray-500">Drug Nodes</div>
                  <div className="text-lg font-bold text-pulse-400">{drugCount}</div>
                </div>
                <div className="bg-surface-dark/50 p-2 rounded border border-surface-border/40">
                  <div className="text-gray-500">ADR Nodes</div>
                  <div className="text-lg font-bold text-neon-amber">{adrCount}</div>
                </div>
                <div className="bg-surface-dark/50 p-2 rounded border border-surface-border/40">
                  <div className="text-gray-500">Total Edges</div>
                  <div className="text-lg font-bold text-gray-300">{edges.length}</div>
                </div>
                <div className="bg-surface-dark/50 p-2 rounded border border-surface-border/40">
                  <div className="text-gray-500">Signal Edges</div>
                  <div className="text-lg font-bold text-red-400">{signalCount}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
