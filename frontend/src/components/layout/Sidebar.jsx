import { NavLink } from 'react-router-dom';
import { useState, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  Upload, Users, Activity, BarChart3, Network, AlertTriangle, FileText, Zap, Info,
} from 'lucide-react';
import useUploadStore from '../../store/uploadStore';

const navItems = [
  {
    path: '/upload', label: 'Upload Hub', icon: Upload, color: 'text-neon-cyan',
    tooltip: {
      files: ['DEMO', 'DRUG', 'REAC', 'OUTC', 'RPSR', 'THER', 'INDI'],
      desc: 'Ingest and clean raw FAERS quarterly files through the 13-step pipeline with Approve/Reject quality gate.',
    }
  },
  {
    path: '/demographics', label: 'Demographics', icon: Users, color: 'text-pulse-400',
    tooltip: {
      files: ['DEMO', 'RPSR'],
      desc: 'Age-band distribution (ICH E11), sex breakdown, and reporter-source analysis across pediatric cohorts.',
    }
  },
  {
    path: '/adr-analysis', label: 'ADR Analysis', icon: Activity, color: 'text-neon-pink',
    tooltip: {
      files: ['DRUG', 'REAC'],
      desc: 'Drug-ADR co-occurrence heatmaps and frequency tables. Answers: "What are the top side effects of Drug X in children?"',
    }
  },
  {
    path: '/signals', label: 'Signal Detection', icon: BarChart3, color: 'text-neon-amber',
    tooltip: {
      files: ['DRUG', 'REAC', 'DEMO'],
      desc: 'Four-metric disproportionality (PRR, ROR, IC, EBGM) flags drug-ADR pairs occurring more often than expected by chance.',
    }
  },
  {
    path: '/gnn', label: 'GNN Network', icon: Network, color: 'text-neon-purple',
    tooltip: {
      files: ['DRUG', 'REAC', 'DEMO'],
      desc: 'HANConv graph neural network for novel link prediction. Predicts ADRs not yet reported based on graph structure.',
    }
  },
  {
    path: '/outcomes', label: 'Outcomes', icon: AlertTriangle, color: 'text-neon-red',
    tooltip: {
      files: ['OUTC', 'DRUG'],
      desc: 'Severity analysis: Death, Hospitalization, Disability, Life-Threatening outcomes per drug and age band.',
    }
  },
  {
    path: '/reports', label: 'Report Builder', icon: FileText, color: 'text-neon-green',
    tooltip: {
      files: ['All tables'],
      desc: 'Compile charts, signals and insights into a professional PDF dossier for regulatory submission.',
    }
  },
];

function NavItemWithTooltip({ path, label, icon: Icon, color, tooltip }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const itemRef = useRef(null);

  const handleMouseEnter = useCallback(() => {
    if (itemRef.current) {
      const rect = itemRef.current.getBoundingClientRect();
      setTooltipPos({
        top: rect.top,
        left: rect.right + 12,
      });
    }
    setShowTooltip(true);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setShowTooltip(false);
  }, []);

  return (
    <div
      ref={itemRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <NavLink
        to={path}
        className={({ isActive }) =>
          `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
          ${isActive
            ? 'bg-pulse-600/20 text-pulse-300 border border-pulse-500/30 shadow-sm shadow-pulse-500/10'
            : 'text-gray-400 hover:text-gray-200 hover:bg-surface-hover'
          }`
        }
      >
        <Icon className={`w-4.5 h-4.5 ${color} group-hover:scale-110 transition-transform`} size={18} />
        <span>{label}</span>
      </NavLink>

      {/* Tooltip rendered via Portal to escape overflow clipping */}
      {showTooltip && tooltip && createPortal(
        <div
          style={{
            position: 'fixed',
            top: tooltipPos.top,
            left: tooltipPos.left,
            zIndex: 9999,
            width: 264,
          }}
          className="animate-fade-in pointer-events-none"
        >
          <div className="bg-surface-dark/95 backdrop-blur-xl border border-surface-border rounded-xl p-3.5 shadow-2xl shadow-black/40">
            <div className="flex items-center gap-1.5 mb-2">
              <Info className="w-3 h-3 text-pulse-400 flex-shrink-0" />
              <span className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Files Used</span>
            </div>
            <div className="flex flex-wrap gap-1 mb-3">
              {tooltip.files.map(f => (
                <span key={f} className="text-[10px] px-1.5 py-0.5 rounded bg-pulse-600/20 text-pulse-300 border border-pulse-500/30 font-mono">
                  {f}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-gray-300 leading-relaxed">{tooltip.desc}</p>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default function Sidebar() {
  const { loadedQuarters, selectedQuarter } = useUploadStore();
  const quarterCount = loadedQuarters.length;

  return (
    <aside className="w-64 bg-surface-card border-r border-surface-border flex flex-col h-full">
      {/* Logo */}
      <div className="p-6 border-b border-surface-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pulse-500 to-neon-cyan flex items-center justify-center shadow-lg shadow-pulse-500/30">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold gradient-text">PulseTech</h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest">FAERS ADR Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavItemWithTooltip key={item.path} {...item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-surface-border">
        <div className="glass-card p-3 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
            <span className="text-xs text-gray-400">System Status</span>
          </div>
          <p className="text-[11px] text-gray-500">Pediatric Focus - ICH E11</p>
          <p className="text-[11px] text-gray-500">
            {quarterCount > 0
              ? `${quarterCount} quarter${quarterCount > 1 ? 's' : ''} loaded`
              : 'No data loaded'}
            {selectedQuarter !== 'ALL' && (
              <span className="text-pulse-400 ml-1">{selectedQuarter}</span>
            )}
          </p>
        </div>
      </div>
    </aside>
  );
}
