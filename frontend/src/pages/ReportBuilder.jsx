import { useState, useEffect, useRef } from 'react';
import { FileText, Download, Loader2, CheckSquare, Square } from 'lucide-react';
import { jsPDF } from 'jspdf';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const AGE_GROUPS = ['NEONATE', 'INFANT', 'CHILD', 'ADOLESCENT'];
const SECTIONS = [
  { key: 'summary', label: 'Executive Summary' },
  { key: 'demographics', label: 'Demographics Overview' },
  { key: 'top_drugs', label: 'Top Suspect Drugs' },
  { key: 'top_adrs', label: 'Top Adverse Reactions' },
  { key: 'outcomes', label: 'Outcome Distribution' },
  { key: 'signals', label: 'Signal Detection Results' },
];

const OUTCOME_LABELS = {
  DE: 'Death', LT: 'Life-Threatening', HO: 'Hospitalization',
  DS: 'Disability', CA: 'Congenital Anomaly',
  RI: 'Required Intervention', OT: 'Other Serious',
};

export default function ReportBuilder() {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const { selectedYear, selectedQuarter, getActiveQuarterFilter, loadedQuarters } = useUploadStore();
  const [quarter, setQuarter] = useState('ALL');
  const [ageGroup, setAgeGroup] = useState('');
  const [selectedSections, setSelectedSections] = useState(new Set(SECTIONS.map(s => s.key)));
  const reportRef = useRef(null);

  // Default to the most recent quarter for fast loading
  useEffect(() => {
    if (loadedQuarters.length > 0 && quarter === 'ALL') {
      setQuarter(loadedQuarters[0]?.value || 'ALL');
    }
  }, [loadedQuarters]);

  const loadReport = async (signalLimit = 50) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (quarter && quarter !== 'ALL') {
        params.append('quarter', quarter);
      }
      if (ageGroup) params.append('age_group', ageGroup);
      params.append('signal_limit', String(signalLimit));
      const res = await api.get(`/reports/summary?${params}`);
      setReportData(res.data);
    } catch (err) {
      console.error('Report load error:', err);
      alert('Failed to load report data. Please try a specific quarter instead of All Quarters.');
    }
    setLoading(false);
  };

  useEffect(() => { loadReport(50); }, [quarter, ageGroup]);

  const toggleSection = (key) => {
    setSelectedSections(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const exportPDF = async () => {
    setGenerating(true);
    try {
      const params = new URLSearchParams();
      if (quarter && quarter !== 'ALL') {
        params.append('quarter', quarter);
      }
      if (ageGroup && ageGroup !== 'all') {
        params.append('age_group', ageGroup);
      }

      // Check if we already have the token from the store, if not assume api handles it,
      // but api might not have the raw token, we should probably just use the configured api client,
      // but fetch is easier for blob downloading. Let's just use the api client to get the blob.
      const response = await api.get(`/reports/export-pdf?${params.toString()}`, {
        responseType: 'blob'
      });

      const blob = response.data;
      const url  = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const q    = quarter || 'ALL';
      const ag   = ageGroup || 'all';
      link.href     = url;
      link.download = `FAERS_Pediatric_Report_${q}_${ag}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch (err) {
      console.error('PDF export error:', err);
      alert('PDF export failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const d = reportData;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold gradient-text">Report Builder</h1>
          <p className="text-sm text-gray-500 mt-1">Generate exportable PDF reports from analysis findings</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={quarter} onChange={e => setQuarter(e.target.value)} className="select-field min-w-[220px]" id="report-quarter">
            <option value="ALL">All Quarters (5 Years)</option>
            {loadedQuarters.map(q => <option key={q.value} value={q.value}>{q.label || q.value}</option>)}
          </select>
          <select value={ageGroup} onChange={e => setAgeGroup(e.target.value)} className="select-field min-w-[180px]" id="report-age">
            <option value="">All Age Groups</option>
            {AGE_GROUPS.map(ag => <option key={ag} value={ag}>{ag}</option>)}
          </select>
          <button onClick={exportPDF} disabled={generating || !d} className="btn-primary flex items-center gap-2" id="export-pdf-btn">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Export PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Section Selector */}
        <div className="glass-card p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Include Sections</h3>
          <div className="space-y-2">
            {SECTIONS.map(s => (
              <button key={s.key} onClick={() => toggleSection(s.key)}
                className="flex items-center gap-2 w-full text-left px-2 py-1.5 rounded hover:bg-surface-hover transition-colors">
                {selectedSections.has(s.key) ?
                  <CheckSquare className="w-4 h-4 text-pulse-400" /> :
                  <Square className="w-4 h-4 text-gray-600" />}
                <span className={`text-sm ${selectedSections.has(s.key) ? 'text-gray-200' : 'text-gray-500'}`}>{s.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Report Preview */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="glass-card p-12 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-pulse-500" />
            </div>
          ) : !d ? (
            <div className="glass-card p-12 text-center text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No data available. Upload FAERS data first.</p>
            </div>
          ) : (
            <div ref={reportRef} className="glass-card p-8 space-y-8">
              {/* Header */}
              <div className="text-center border-b border-surface-border pb-6">
                <h2 className="text-xl font-bold gradient-text">FAERS Pediatric ADR Analysis Report</h2>
                <p className="text-sm text-gray-400 mt-1">Generated by PulseTech Dashboard</p>
                <p className="text-xs text-gray-500 mt-1">
                  {d.filters?.quarter ? `Quarter: ${d.filters.quarter}` : 'All Quarters'}
                  {' | '}
                  {d.filters?.age_group ? `Age Group: ${d.filters.age_group}` : 'All Age Groups'}
                </p>
              </div>

              {/* Summary */}
              {selectedSections.has('summary') && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-pulse-500 rounded-full" /> Executive Summary
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="bg-surface-dark/50 rounded-lg p-4 border border-surface-border">
                      <p className="text-xs text-gray-500">Total Patients</p>
                      <p className="text-2xl font-bold text-pulse-400">{d.summary?.total_patients?.toLocaleString() || 0}</p>
                    </div>
                    <div className="bg-surface-dark/50 rounded-lg p-4 border border-surface-border">
                      <p className="text-xs text-gray-500">Confirmed Signals</p>
                      <p className="text-2xl font-bold text-neon-red">{(d.summary?.total_signals || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-surface-dark/50 rounded-lg p-4 border border-surface-border">
                      <p className="text-xs text-gray-500">Suspect Drugs</p>
                      <p className="text-2xl font-bold text-neon-cyan">{(d.summary?.total_suspect_drugs || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-surface-dark/50 rounded-lg p-4 border border-surface-border">
                      <p className="text-xs text-gray-500">Unique ADRs</p>
                      <p className="text-2xl font-bold text-neon-amber">{(d.summary?.total_adverse_reactions || 0).toLocaleString()}</p>
                    </div>
                    <div className="bg-surface-dark/50 rounded-lg p-4 border border-surface-border">
                      <p className="text-xs text-gray-500">Age Groups</p>
                      <p className="text-2xl font-bold text-neon-pink">{Object.keys(d.summary?.age_distribution || {}).length}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Demographics */}
              {selectedSections.has('demographics') && d.summary && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-neon-cyan rounded-full" /> Demographics
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-xs text-gray-500 mb-2">Age Groups</h4>
                      {Object.entries(d.summary.age_distribution || {}).map(([g, c]) => (
                        <div key={g} className="flex justify-between text-sm py-1 border-b border-surface-border/30">
                          <span className="text-gray-300">{g}</span>
                          <span className="font-mono text-pulse-300">{c.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="text-xs text-gray-500 mb-2">Sex Distribution</h4>
                      {Object.entries(d.summary.sex_distribution || {}).map(([s, c]) => (
                        <div key={s} className="flex justify-between text-sm py-1 border-b border-surface-border/30">
                          <span className="text-gray-300">{s === 'M' ? 'Male' : s === 'F' ? 'Female' : s}</span>
                          <span className="font-mono text-neon-pink">{c.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Top Drugs */}
              {selectedSections.has('top_drugs') && d.top_suspect_drugs?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-neon-amber rounded-full" /> Top Suspect Drugs
                  </h3>
                  <table className="w-full text-sm">
                    <thead><tr><th className="table-header text-left">#</th><th className="table-header text-left">Drug</th><th className="table-header text-right">Reports</th></tr></thead>
                    <tbody>
                      {d.top_suspect_drugs.map((dr, i) => (
                        <tr key={i}><td className="table-cell text-gray-500">{i+1}</td><td className="table-cell text-neon-cyan">{dr.drug}</td><td className="table-cell text-right font-mono">{dr.count}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Top ADRs */}
              {selectedSections.has('top_adrs') && d.top_adverse_reactions?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-neon-pink rounded-full" /> Top Adverse Reactions
                  </h3>
                  <table className="w-full text-sm">
                    <thead><tr><th className="table-header text-left">#</th><th className="table-header text-left">ADR (PT)</th><th className="table-header text-right">Reports</th></tr></thead>
                    <tbody>
                      {d.top_adverse_reactions.map((a, i) => (
                        <tr key={i}><td className="table-cell text-gray-500">{i+1}</td><td className="table-cell text-gray-300">{a.adr}</td><td className="table-cell text-right font-mono">{a.count}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Outcomes */}
              {selectedSections.has('outcomes') && d.outcome_distribution && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-neon-red rounded-full" /> Outcomes
                  </h3>
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(d.outcome_distribution).map(([code, count]) => (
                      <div key={code} className="stat-badge bg-surface-dark border border-surface-border">
                        <span className="font-semibold text-neon-red">{code}</span>
                        <span className="text-gray-400 ml-1">({OUTCOME_LABELS[code] || code})</span>:
                        <span className="font-mono ml-1">{count.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedSections.has('signals') && d.top_signals?.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-3 flex items-center gap-2">
                    <div className="w-1 h-5 bg-neon-purple rounded-full" /> 
                    Signal Detection Results
                    <span className="text-xs text-gray-500 font-normal ml-2">
                      Showing {d.top_signals.length.toLocaleString()} of {(d.summary?.total_computed_pairs || d.top_signals.length).toLocaleString()} computed pairs
                    </span>
                  </h3>
                  <div className="overflow-x-auto max-h-[600px] overflow-y-auto border border-surface-border rounded-lg">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-surface-card z-10 shadow-sm">
                        <tr>
                          <th className="table-header text-left">Drug</th>
                          <th className="table-header text-left">ADR</th>
                          <th className="table-header">Age</th>
                          <th className="table-header text-center">Confirmed</th>
                          <th className="table-header text-right">N</th>
                          <th className="table-header text-right">PRR</th>
                          <th className="table-header text-right">ROR</th>
                          <th className="table-header text-right">IC025</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d.top_signals.map((s, i) => (
                          <tr key={i} className={s.is_signal ? 'bg-neon-red/5' : ''}>
                            <td className="table-cell text-neon-cyan">{s.drugname_normalized || ''}</td>
                            <td className="table-cell text-gray-300">{s.pt_term || ''}</td>
                            <td className="table-cell text-center text-gray-500">{s.age_group}</td>
                            <td className="table-cell text-center">
                              {s.is_signal ? <span className="text-neon-red font-bold">Yes</span> : <span className="text-gray-600">No</span>}
                            </td>
                            <td className="table-cell text-right font-mono">{s.n11}</td>
                            <td className="table-cell text-right font-mono text-gray-300">{s.prr ? Number(s.prr).toFixed(1) : '-'}</td>
                            <td className="table-cell text-right font-mono text-gray-300">{s.ror ? Number(s.ror).toFixed(1) : '-'}</td>
                            <td className="table-cell text-right font-mono text-gray-300">{s.ic025 ? Number(s.ic025).toFixed(2) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="text-center pt-4 border-t border-surface-border">
                <p className="text-[10px] text-gray-600">
                  PulseTech FAERS Pediatric ADR Dashboard • Powered by PRR/ROR/IC/EBGM Signal Detection & GNN
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
