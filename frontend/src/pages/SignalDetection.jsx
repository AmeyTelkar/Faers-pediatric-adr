import { useState, useEffect, useMemo } from 'react';
import { BarChart3, Filter, Download, ArrowUpDown, Search, AlertTriangle, CheckCircle } from 'lucide-react';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const AGE_GROUPS = ['NEONATE', 'INFANT', 'CHILD', 'ADOLESCENT'];

function SignalBadge({ isSignal }) {
  return isSignal ? (
    <span className="stat-badge signal-positive"><AlertTriangle className="w-3 h-3" /> Signal</span>
  ) : (
    <span className="stat-badge signal-negative"><CheckCircle className="w-3 h-3" /> No signal</span>
  );
}

export default function SignalDetection() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    ageGroups: new Set(AGE_GROUPS),
    minN: 3,
    signalOnly: false,
    searchDrug: '',
    searchAdr: '',
    method: 'any',
  });
  const [sortConfig, setSortConfig] = useState({ key: 'n11', direction: 'desc' });
  const { selectedYear, selectedQuarter, getActiveQuarterFilter } = useUploadStore();

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const qFilter = getActiveQuarterFilter();
        const res = await api.get('/signals/compute', {
          params: {
            min_n: filters.minN,
            signal_only: filters.signalOnly,
            drug: filters.searchDrug || undefined,
            adr: filters.searchAdr || undefined,
            age_group: Array.from(filters.ageGroups).join(',') || undefined,
            quarter: qFilter,
            limit: 1000,
          },
        });
        setSignals(res.data);
      } catch (err) {
        console.error('Failed to load signals:', err);
      }
      setLoading(false);
    }
    load();
  }, [filters.ageGroups, filters.minN, filters.signalOnly, filters.searchDrug, filters.searchAdr, selectedYear, selectedQuarter]);

  const isRowSignal = (row) => {
    const prr_ok = (row.prr || 0) >= 2 && (row.prr_chi2 || 0) >= 4;
    const ror_ok = (row.ror || 0) >= 2 && (row.ror_ci_lower || 0) > 1;
    const ic_ok = row.ic025 != null && row.ic025 > 0;
    const eb_ok = row.eb05 != null && row.eb05 > 2;

    if (filters.method === 'prr') return prr_ok;
    if (filters.method === 'ror') return ror_ok;
    if (filters.method === 'ic') return ic_ok;
    if (filters.method === 'ebgm') return eb_ok;
    return prr_ok || ror_ok || ic_ok || eb_ok;
  };

  const filteredSignals = useMemo(() => {
    return signals
      .filter(s => filters.ageGroups.has(s.age_group))
      .map(s => ({ ...s, is_signal: isRowSignal(s) }));
  }, [signals, filters.ageGroups, filters.method]);

  const sortedSignals = useMemo(() => {
    const sorted = [...filteredSignals];
    sorted.sort((a, b) => {
      const aVal = a[sortConfig.key] ?? -Infinity;
      const bVal = b[sortConfig.key] ?? -Infinity;
      return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
    });
    return sorted;
  }, [filteredSignals, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc',
    }));
  };

  const toggleAgeGroup = (ag) => {
    setFilters(prev => {
      const next = new Set(prev.ageGroups);
      next.has(ag) ? next.delete(ag) : next.add(ag);
      return { ...prev, ageGroups: next };
    });
  };

  const exportCSV = () => {
    const headers = ['Drug', 'ADR', 'Age Group', 'N', 'PRR', 'ROR', 'IC', 'IC025', 'EBGM', 'EB05', 'Signal'];
    const rows = sortedSignals.map(s => [
      s.drugname_normalized, s.pt_term, s.age_group, s.n11,
      s.prr, s.ror, s.ic, s.ic025, s.ebgm, s.eb05, s.is_signal,
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'signal_detection_results.csv';
    a.click();
  };

  const SortHeader = ({ label, field }) => (
    <th
      className="table-header cursor-pointer hover:text-pulse-300 select-none"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {label}
        <ArrowUpDown className="w-3 h-3" />
      </div>
    </th>
  );

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
          <h1 className="text-2xl font-bold gradient-text">Signal Detection</h1>
          <p className="text-sm text-gray-500 mt-1">PRR · ROR · IC · EBGM disproportionality analysis</p>
        </div>
        <button onClick={exportCSV} className="btn-secondary flex items-center gap-2" id="export-csv-btn">
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Age Groups */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Age Groups:</span>
            {AGE_GROUPS.map(ag => (
              <button
                key={ag}
                onClick={() => toggleAgeGroup(ag)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-all ${
                  filters.ageGroups.has(ag)
                    ? 'bg-pulse-500/20 text-pulse-300 border-pulse-500/40'
                    : 'bg-surface-dark text-gray-600 border-surface-border'
                }`}
              >
                {ag}
              </button>
            ))}
          </div>

          {/* Min N */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Min N:</span>
            <input
              type="number"
              value={filters.minN}
              onChange={(e) => setFilters(prev => ({ ...prev, minN: parseInt(e.target.value) || 3 }))}
              className="input-field w-16 text-center text-xs"
              min={1}
              id="min-n-input"
            />
          </div>

          {/* Method */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Method:</span>
            <select
              value={filters.method}
              onChange={(e) => setFilters(prev => ({ ...prev, method: e.target.value }))}
              className="select-field w-28 text-xs"
              id="method-select"
            >
              <option value="any">Any Signal</option>
              <option value="prr">PRR Only</option>
              <option value="ror">ROR Only</option>
              <option value="ic">IC Only</option>
              <option value="ebgm">EBGM Only</option>
            </select>
          </div>

          {/* Signal Only */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.signalOnly}
              onChange={(e) => setFilters(prev => ({ ...prev, signalOnly: e.target.checked }))}
              className="rounded border-surface-border bg-surface-dark text-pulse-500"
              id="signal-only-checkbox"
            />
            <span className="text-xs text-gray-400">Signals only</span>
          </label>

          {/* Search */}
          <div className="relative ml-auto">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
            <input
              placeholder="Search drug..."
              value={filters.searchDrug}
              onChange={(e) => setFilters(prev => ({ ...prev, searchDrug: e.target.value }))}
              className="input-field pl-8 w-40 text-xs"
              id="search-drug-input"
            />
          </div>
        </div>
      </div>

      {/* Signal Count */}
      <div className="flex items-center gap-4 text-sm text-gray-400">
        <span>{sortedSignals.length} results</span>
        <span>|</span>
        <span className="text-neon-red">{sortedSignals.filter(s => s.is_signal).length} signals detected</span>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
          <table className="w-full">
            <thead className="sticky top-0 z-10">
              <tr>
                <SortHeader label="Drug" field="drugname_normalized" />
                <SortHeader label="ADR (PT)" field="pt_term" />
                <SortHeader label="Age" field="age_group" />
                <SortHeader label="N" field="n11" />
                <SortHeader label="PRR" field="prr" />
                <SortHeader label="ROR" field="ror" />
                <SortHeader label="IC" field="ic" />
                <SortHeader label="IC025" field="ic025" />
                <SortHeader label="EBGM" field="ebgm" />
                <SortHeader label="EB05" field="eb05" />
                <th className="table-header">Signal</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={11} className="table-cell text-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pulse-500 mx-auto" />
                </td></tr>
              ) : sortedSignals.length === 0 ? (
                <tr><td colSpan={11} className="table-cell text-center py-12 text-gray-500">
                  No signals found. Upload data and compute signals first.
                </td></tr>
              ) : sortedSignals.map((s, i) => (
                <tr key={i} className={`hover:bg-surface-hover/30 transition-colors ${
                  s.is_signal ? 'bg-neon-red/5' : ''
                }`}>
                  <td className="table-cell text-neon-cyan font-medium max-w-[150px] truncate" title={s.drugname_normalized}>
                    {s.drugname_normalized}
                  </td>
                  <td className="table-cell max-w-[150px] truncate" title={s.pt_term}>{s.pt_term}</td>
                  <td className="table-cell">
                    <span className="stat-badge bg-pulse-500/15 text-pulse-300 border border-pulse-400/20 text-[10px]">
                      {s.age_group}
                    </span>
                  </td>
                  <td className="table-cell font-mono text-right">{s.n11}</td>
                  <td className={`table-cell font-mono text-right ${s.prr >= 2 ? 'text-neon-amber' : ''}`}>
                    {s.prr != null ? Number(s.prr).toFixed(2) : '—'}
                  </td>
                  <td className={`table-cell font-mono text-right ${s.ror >= 2 ? 'text-neon-amber' : ''}`}>
                    {s.ror != null ? Number(s.ror).toFixed(2) : '—'}
                  </td>
                  <td className="table-cell font-mono text-right">
                    {s.ic != null ? Number(s.ic).toFixed(2) : '—'}
                  </td>
                  <td className={`table-cell font-mono text-right ${s.ic025 > 0 ? 'text-neon-amber' : ''}`}>
                    {s.ic025 != null ? Number(s.ic025).toFixed(2) : '—'}
                  </td>
                  <td className="table-cell font-mono text-right">
                    {s.ebgm != null ? Number(s.ebgm).toFixed(2) : '—'}
                  </td>
                  <td className={`table-cell font-mono text-right ${s.eb05 > 2 ? 'text-neon-amber' : ''}`}>
                    {s.eb05 != null ? Number(s.eb05).toFixed(2) : '—'}
                  </td>
                  <td className="table-cell"><SignalBadge isSignal={s.is_signal} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
