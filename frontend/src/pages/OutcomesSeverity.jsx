import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const SEVERITY_COLORS = {
  DE: '#ef4444', LT: '#f97316', HO: '#f59e0b',
  DS: '#eab308', CA: '#a855f7', RI: '#6366f1', OT: '#6b7280',
};
const SEVERITY_LABELS = {
  DE: 'Death', LT: 'Life-Threatening', HO: 'Hospitalization',
  DS: 'Disability', CA: 'Congenital Anomaly', RI: 'Required Intervention', OT: 'Other',
};
const AGE_GROUPS = ['NEONATE', 'INFANT', 'CHILD', 'ADOLESCENT'];

export default function OutcomesSeverity() {
  const [distribution, setDistribution] = useState([]);
  const [trend, setTrend] = useState([]);
  const [byDrug, setByDrug] = useState([]);
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
        const [distRes, trendRes, drugRes] = await Promise.all([
          api.get(`/outcomes/distribution${qs}`),
          api.get(`/outcomes/severity-trend${qs}`),
          api.get(`/outcomes/by-drug${qs}${qs ? '&' : '?'}limit=15`),
        ]);
        setDistribution(distRes.data);
        setTrend(trendRes.data);
        setByDrug(drugRes.data);
      } catch (err) { console.error(err); }
      setLoading(false);
    }
    load();
  }, [ageFilter, selectedYear, selectedQuarter]);

  const pieData = distribution.map(d => ({
    name: SEVERITY_LABELS[d.outc_cod] || d.outc_cod,
    value: d.count,
    color: SEVERITY_COLORS[d.outc_cod] || '#6b7280',
  }));

  // Group trend by quarter
  const trendByQuarter = {};
  trend.forEach(({ quarter, outc_cod, count }) => {
    if (!trendByQuarter[quarter]) trendByQuarter[quarter] = { quarter };
    trendByQuarter[quarter][outc_cod] = (trendByQuarter[quarter][outc_cod] || 0) + count;
  });
  const trendData = Object.values(trendByQuarter);

  const sevBadge = (score) => {
    if (score >= 6) return 'severity-badge-de';
    if (score >= 5) return 'severity-badge-lt';
    if (score >= 4) return 'severity-badge-ho';
    return 'severity-badge-default';
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
          <h1 className="text-2xl font-bold gradient-text">Outcomes & Severity</h1>
          <p className="text-sm text-gray-500 mt-1">Outcome severity analysis across pediatric populations</p>
        </div>
        <select value={ageFilter} onChange={e => setAgeFilter(e.target.value)} className="select-field w-40" id="outcome-age-filter">
          <option value="">All Age Groups</option>
          {AGE_GROUPS.map(ag => <option key={ag} value={ag}>{ag}</option>)}
        </select>
      </div>

      {/* Severity Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {distribution.map(d => (
          <div key={d.outc_cod} className="glass-card-hover p-4 text-center">
            <div className="w-8 h-8 rounded-full mx-auto mb-2 flex items-center justify-center"
              style={{ backgroundColor: `${SEVERITY_COLORS[d.outc_cod]}20` }}>
              <span className="text-xs font-bold" style={{ color: SEVERITY_COLORS[d.outc_cod] }}>
                {d.severity_score}
              </span>
            </div>
            <p className="text-[10px] text-gray-500 uppercase">{d.outc_cod}</p>
            <p className="text-lg font-bold text-gray-200">{d.count?.toLocaleString()}</p>
            <p className="text-[10px] text-gray-500">{SEVERITY_LABELS[d.outc_cod]}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outcome Distribution Pie */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Outcome Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={110}
                dataKey="value" nameKey="name" paddingAngle={2} stroke="none">
                {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }} itemStyle={{ color: '#e5e7eb' }} />
              <Legend formatter={v => <span className="text-gray-300 text-xs">{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Trend by Quarter */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Severity Trend by Quarter</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
              <XAxis dataKey="quarter" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }} itemStyle={{ color: '#e5e7eb' }} />
              <Legend formatter={v => <span className="text-gray-300 text-xs">{SEVERITY_LABELS[v] || v}</span>} />
              {Object.keys(SEVERITY_COLORS).map(code => (
                <Bar key={code} dataKey={code} stackId="a" fill={SEVERITY_COLORS[code]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Severity by Drug */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-4">Highest Severity by Drug (Primary Suspect)</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="table-header text-left">Drug</th>
                <th className="table-header text-center">Max Severity</th>
                <th className="table-header text-center">Outcome Codes</th>
                <th className="table-header text-right">Reports</th>
              </tr>
            </thead>
            <tbody>
              {byDrug.map((row, i) => (
                <tr key={i} className="hover:bg-surface-hover/30">
                  <td className="table-cell text-neon-cyan font-medium">{row.drug}</td>
                  <td className="table-cell text-center">
                    <span className={`stat-badge ${sevBadge(row.max_severity)}`}>
                      {row.max_severity}/7
                    </span>
                  </td>
                  <td className="table-cell text-center">
                    <div className="flex gap-1 justify-center flex-wrap">
                      {(row.outcome_codes || []).map((c, j) => (
                        <span key={j} className="text-[10px] px-1.5 py-0.5 rounded"
                          style={{ backgroundColor: `${SEVERITY_COLORS[c]}20`, color: SEVERITY_COLORS[c] }}>
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="table-cell text-right font-mono">{row.report_count}</td>
                </tr>
              ))}
              {byDrug.length === 0 && (
                <tr><td colSpan={4} className="table-cell text-center py-8 text-gray-500">No outcome data available</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
