import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Treemap } from 'recharts';
import { Activity, Filter } from 'lucide-react';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const COLORS = ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#14b8a6', '#a855f7'];
const AGE_GROUPS = ['NEONATE', 'INFANT', 'CHILD', 'ADOLESCENT'];

export default function ADRAnalysis() {
  const [topPT, setTopPT] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [drugAdrPairs, setDrugAdrPairs] = useState([]);
  const [ageFilter, setAgeFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const { selectedYear, selectedQuarter, getActiveQuarterFilter } = useUploadStore();

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const qFilter = getActiveQuarterFilter();
        const params = new URLSearchParams();
        if (ageFilter) params.set('age_group', ageFilter);
        if (qFilter !== 'ALL') params.set('quarter', qFilter);
        const qs = params.toString() ? `?${params.toString()}` : '';
        const [ptRes, hmRes, pairsRes] = await Promise.all([
          api.get(`/reactions/top-pt${qs}${qs ? '&' : '?'}limit=20`),
          api.get(`/reactions/soc-heatmap?limit=30${qFilter !== 'ALL' ? `&quarter=${qFilter}` : ''}`),
          api.get(`/reactions/drug-adr-pairs${qs}${qs ? '&' : '?'}limit=50`),
        ]);
        setTopPT(ptRes.data);
        setHeatmap(hmRes.data);
        setDrugAdrPairs(pairsRes.data);
      } catch (err) {
        console.error('Failed to load ADR data:', err);
      }
      setLoading(false);
    }
    load();
  }, [ageFilter, selectedYear, selectedQuarter]);

  // Build treemap data from top PT
  const treemapData = topPT.map((item, i) => ({
    name: item.pt_term?.length > 25 ? item.pt_term.substring(0, 25) + '...' : item.pt_term,
    fullName: item.pt_term,
    size: item.count,
    fill: COLORS[i % COLORS.length],
  }));

  // Build heatmap grid
  const heatmapGrid = {};
  heatmap.forEach(({ age_group, pt_term, count }) => {
    if (!heatmapGrid[pt_term]) heatmapGrid[pt_term] = {};
    heatmapGrid[pt_term][age_group] = count;
  });

  const maxCount = Math.max(...heatmap.map(h => h.count), 1);

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const data = payload[0].payload;
    return (
      <div className="bg-surface-card border border-surface-border rounded-lg p-3 shadow-xl">
        <p className="text-sm font-medium text-gray-200">{data.fullName || data.name}</p>
        <p className="text-xs text-neon-cyan mt-1">Count: {data.size?.toLocaleString() || data.count?.toLocaleString()}</p>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pulse-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
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
          <h1 className="text-2xl font-bold gradient-text">ADR Analysis</h1>
          <p className="text-sm text-gray-500 mt-1">Adverse Drug Reaction patterns across pediatric age groups</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={ageFilter}
            onChange={(e) => setAgeFilter(e.target.value)}
            className="select-field w-40"
            id="age-filter-select"
          >
            <option value="">All Age Groups</option>
            {AGE_GROUPS.map(ag => <option key={ag} value={ag}>{ag}</option>)}
          </select>
        </div>
      </div>

      {/* Top ADRs Bar Chart */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Top 20 Adverse Reactions (Preferred Terms)</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={topPT} layout="vertical" margin={{ left: 160 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
            <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <YAxis dataKey="pt_term" type="category" tick={{ fill: '#9ca3af', fontSize: 10 }} width={150}
              tickFormatter={(val) => val.length > 30 ? val.substring(0, 30) + '...' : val} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {topPT.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* SOC Heatmap */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">ADR × Age Group Heatmap</h3>
          <div className="overflow-auto max-h-96">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="table-header text-left sticky top-0 z-10 bg-surface-card">ADR</th>
                  {AGE_GROUPS.map(ag => (
                    <th key={ag} className="table-header text-center sticky top-0 z-10 bg-surface-card">{ag}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(heatmapGrid).slice(0, 25).map(([pt, counts]) => (
                  <tr key={pt} className="hover:bg-surface-hover/30">
                    <td className="px-3 py-2 text-gray-400 border-b border-surface-border/30 max-w-[180px] truncate" title={pt}>
                      {pt}
                    </td>
                    {AGE_GROUPS.map(ag => {
                      const val = counts[ag] || 0;
                      const intensity = val / maxCount;
                      return (
                        <td key={ag} className="px-3 py-2 text-center border-b border-surface-border/30">
                          {val > 0 && (
                            <span
                              className="inline-block px-2 py-0.5 rounded text-[10px] font-mono"
                              style={{
                                backgroundColor: `rgba(99, 102, 241, ${Math.max(intensity, 0.15)})`,
                                color: intensity > 0.5 ? '#fff' : '#a5b4fc',
                              }}
                            >
                              {val.toLocaleString()}
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Drug-ADR Pairs */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Top Drug–ADR Co-occurrences (PS Only)</h3>
          <div className="overflow-auto max-h-96">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="table-header text-left sticky top-0 z-10 bg-surface-card">Drug</th>
                  <th className="table-header text-left sticky top-0 z-10 bg-surface-card">ADR</th>
                  <th className="table-header text-center sticky top-0 z-10 bg-surface-card">Age</th>
                  <th className="table-header text-right sticky top-0 z-10 bg-surface-card">Count</th>
                </tr>
              </thead>
              <tbody>
                {drugAdrPairs.map((row, i) => (
                  <tr key={i} className="hover:bg-surface-hover/30">
                    <td className="table-cell text-neon-cyan max-w-[120px] truncate" title={row.drug}>{row.drug}</td>
                    <td className="table-cell text-gray-300 max-w-[120px] truncate" title={row.adr}>{row.adr}</td>
                    <td className="table-cell text-center">
                      <span className="stat-badge bg-pulse-500/20 text-pulse-300 border border-pulse-400/30 text-[10px]">
                        {row.age_group}
                      </span>
                    </td>
                    <td className="table-cell text-right font-mono text-neon-amber">{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
