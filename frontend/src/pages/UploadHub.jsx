import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, CheckCircle, XCircle, AlertCircle, Loader2, ChevronRight, Database, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import useUploadStore from '../store/uploadStore';
import api from '../api/client';

const FILE_TYPES = [
  { key: 'DEMO', label: 'Demographics', hint: 'primaryid, caseid, age, sex...', required: true },
  { key: 'DRUG', label: 'Drugs', hint: 'primaryid, drugname, role_cod...', required: true },
  { key: 'REAC', label: 'Reactions', hint: 'primaryid, pt, drug_rec_act', required: true },
  { key: 'OUTC', label: 'Outcomes', hint: 'primaryid, outc_cod', required: true },
  { key: 'RPSR', label: 'Report Sources', hint: 'primaryid, rpsr_cod', required: false },
  { key: 'THER', label: 'Therapy', hint: 'primaryid, start_dt, end_dt...', required: false },
  { key: 'INDI', label: 'Indications', hint: 'primaryid, indi_pt', required: false },
];

const PIPELINE_STEPS = [
  'Parsing files', 'Validating headers', 'Deduplicating DEMO',
  'Normalizing age', 'Pediatric filter', 'Handling dates',
  'Filtering related tables', 'Normalizing drugs', 'Scoring outcomes',
  'Building preview',
];

function FileCard({ type, file, onDrop, onRemove }) {
  const statusIcon = file
    ? <CheckCircle className="w-5 h-5 text-neon-green" />
    : <div className="w-5 h-5 rounded-full border-2 border-dashed border-gray-600" />;

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => onDrop(type.key, files[0]),
    accept: { 'text/plain': ['.txt'] },
    maxFiles: 1,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`glass-card-hover p-4 cursor-pointer transition-all duration-300 ${
        isDragActive ? 'border-neon-cyan shadow-lg shadow-neon-cyan/20' : ''
      } ${file ? 'border-neon-green/30' : ''}`}
      id={`file-card-${type.key}`}
    >
      <input {...getInputProps()} />
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {statusIcon}
          <div>
            <span className="text-sm font-semibold text-gray-200">{type.label}</span>
            {type.required && <span className="ml-1 text-[10px] text-neon-amber">*</span>}
          </div>
        </div>
        {file && (
          <button
            onClick={(e) => { e.stopPropagation(); onRemove(type.key); }}
            className="p-1 rounded hover:bg-surface-hover transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5 text-gray-500 hover:text-neon-red" />
          </button>
        )}
      </div>
      <p className="text-[11px] text-gray-500 font-mono truncate">{type.hint}</p>
      {file && (
        <div className="mt-2 flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-neon-cyan" />
          <span className="text-xs text-neon-cyan truncate">{file.name}</span>
          <span className="text-[10px] text-gray-500">({(file.size / 1024 / 1024).toFixed(1)} MB)</span>
        </div>
      )}
      {!file && (
        <p className="mt-2 text-xs text-gray-600">Drop .txt file or click</p>
      )}
    </div>
  );
}

function PipelineProgress({ currentStep, totalSteps, pipelineDone }) {
  return (
    <div className="glass-card p-4 mt-4 animate-fade-in">
      <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
        {pipelineDone ? (
          <CheckCircle className="w-4 h-4 text-neon-green" />
        ) : (
          <Loader2 className="w-4 h-4 animate-spin text-neon-cyan" />
        )}
        {pipelineDone ? 'Pipeline Complete - Loading Preview...' : 'Pipeline Running...'}
      </h4>
      <div className="space-y-2">
        {PIPELINE_STEPS.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
              i < currentStep ? 'bg-neon-green/20 text-neon-green' :
              i === currentStep ? 'bg-neon-cyan/20 text-neon-cyan animate-pulse' :
              'bg-surface-dark text-gray-600'
            }`}>
              {i < currentStep ? '\u2713' : i + 1}
            </div>
            <span className={`text-xs ${
              i < currentStep ? 'text-neon-green' :
              i === currentStep ? 'text-neon-cyan font-medium' :
              'text-gray-600'
            }`}>{step}</span>
          </div>
        ))}
      </div>
      <div className="mt-3 h-1.5 bg-surface-dark rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-pulse-500 to-neon-cyan rounded-full transition-all duration-500"
          style={{ width: `${(currentStep / totalSteps) * 100}%` }}
        />
      </div>
      {pipelineDone && (
        <div className="mt-3 flex items-center gap-2 text-xs text-neon-cyan">
          <Loader2 className="w-3 h-3 animate-spin" />
          Finalizing results and building preview data...
        </div>
      )}
    </div>
  );
}

function PreviewTable({ stats }) {
  if (!stats) return null;

  return (
    <div className="glass-card p-6 mt-4 animate-fade-in space-y-6">
      <h3 className="text-lg font-semibold gradient-text">Pipeline Preview</h3>

      {/* Row counts */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Raw DEMO Rows', value: stats.demo_raw_rows?.toLocaleString(), color: 'text-gray-300' },
          { label: 'After Dedup', value: stats.demo_after_dedup?.toLocaleString(), color: 'text-neon-cyan' },
          { label: 'Pediatric Only', value: stats.demo_after_pediatric_filter?.toLocaleString(), color: 'text-neon-green' },
          { label: 'Pediatric %', value: `${stats.pediatric_pct}%`, color: 'text-neon-amber' },
        ].map((item, i) => (
          <div key={i} className="bg-surface-dark/50 rounded-lg p-3 border border-surface-border">
            <p className="text-[11px] text-gray-500 uppercase tracking-wider">{item.label}</p>
            <p className={`text-xl font-bold mt-1 ${item.color}`}>{item.value}</p>
          </div>
        ))}
      </div>

      {/* Age Group Distribution */}
      {stats.age_group_distribution && (
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Age Group Distribution (ICH E11)</h4>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(stats.age_group_distribution).map(([group, count]) => (
              <div key={group} className="stat-badge bg-pulse-500/20 text-pulse-300 border border-pulse-500/30">
                {group}: {count.toLocaleString()}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sex Distribution */}
      {stats.sex_distribution && (
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Sex Distribution</h4>
          <div className="flex gap-2">
            {Object.entries(stats.sex_distribution).map(([sex, count]) => (
              <div key={sex} className="stat-badge bg-neon-purple/20 text-neon-purple border border-neon-purple/30">
                {sex === 'M' ? 'Male' : sex === 'F' ? 'Female' : sex}: {count.toLocaleString()}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top ADRs */}
      {stats.top_adr && Object.keys(stats.top_adr).length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Top 10 Adverse Reactions</h4>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="table-header text-left">PT Term</th>
                  <th className="table-header text-right">Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stats.top_adr).map(([term, count]) => (
                  <tr key={term} className="hover:bg-surface-hover/50">
                    <td className="table-cell text-gray-300">{term}</td>
                    <td className="table-cell text-right font-mono text-neon-cyan">{count.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Null Rates */}
      {stats.null_rates && (
        <div>
          <h4 className="text-sm font-medium text-gray-400 mb-2">Data Completeness (Null Rates)</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {Object.entries(stats.null_rates).map(([col, pct]) => (
              <div key={col} className="bg-surface-dark/50 rounded-lg p-2 border border-surface-border">
                <p className="text-[10px] text-gray-500 uppercase">{col}</p>
                <p className={`text-sm font-bold ${pct > 50 ? 'text-neon-red' : pct > 20 ? 'text-neon-amber' : 'text-neon-green'}`}>
                  {pct}% null
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function QuarterHistoryPanel() {
  const { loadedYears, loadedQuarters, setSelectedYear, setSelectedQuarter } = useUploadStore();

  return (
    <div className="mt-8 bg-surface-dark rounded-xl border border-surface-border p-6 shadow-xl animate-fade-in">
      <h3 className="text-gray-200 font-semibold mb-4">
        Loaded Quarters — {loadedQuarters.length} of 20 slots used
        <span className="text-xs text-gray-500 font-normal ml-2">
          (5 years × 4 quarters = 20 total)
        </span>
      </h3>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-[10px] font-mono text-gray-500 mb-1">
          <span>2021 Q1</span>
          <span>2023 Q2</span>
          <span>2025 Q4</span>
          <span>20 slots</span>
        </div>
        <div className="w-full bg-surface-card rounded-full h-2">
          <div className="bg-gradient-to-r from-pulse-500 to-neon-purple h-2 rounded-full"
               style={{width: `${Math.min((loadedQuarters.length / Math.max(loadedQuarters.length, 4)) * 100, 100)}%`}} />
        </div>
        <div className="text-[10px] text-gray-500 mt-1 font-mono">
          {loadedQuarters.length} quarters loaded ({loadedYears.length} year{loadedYears.length !== 1 ? 's' : ''})
        </div>
      </div>

      {/* Grouped by year */}
      {loadedYears.map(yearGroup => (
        <div key={yearGroup.year} className="mb-6">

          {/* Year header */}
          <div className="flex items-center gap-3 mb-3">
            <span className="text-pulse-400 font-bold text-lg">{yearGroup.year}</span>
            <span className="text-gray-400 text-xs">
              {yearGroup.quarter_count} quarter{yearGroup.quarter_count > 1 ? 's' : ''} loaded
              · {yearGroup.total_patients?.toLocaleString()} patients
              · {yearGroup.total_signals?.toLocaleString()} signals
            </span>
            <button
              onClick={() => { setSelectedYear(yearGroup.year); setSelectedQuarter('ALL'); }}
              className="text-[10px] px-2 py-0.5 rounded bg-pulse-900 border border-pulse-500/50 text-pulse-300 
                         hover:bg-pulse-800 transition-colors"
            >
              Analyze {yearGroup.year}
            </button>
          </div>

          {/* Quarter cards for this year */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {loadedQuarters
              .filter(q => q.value.startsWith(String(yearGroup.year)))
              .map(q => (
                <button key={q.value}
                     onClick={() => { setSelectedYear(yearGroup.year); setSelectedQuarter(q.value); }}
                     className="bg-surface-card rounded-lg p-3 border border-surface-border text-left
                                hover:border-pulse-500 transition-colors cursor-pointer group">
                  <div className="text-pulse-400 font-mono text-sm font-bold group-hover:text-pulse-300">{q.value}</div>
                  <div className="text-gray-400 text-xs mt-1">{q.label}</div>
                  <div className="text-gray-300 text-xs mt-2 font-mono">{q.patients?.toLocaleString()} <span className="text-gray-500 font-sans">pts</span></div>
                  <div className="text-gray-500 text-xs">{q.signals?.toLocaleString() || 0} signals</div>
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono
                      ${q.gnn_trained ? 'bg-neon-green/15 text-neon-green border border-neon-green/30' : 'bg-surface-dark text-gray-500 border border-surface-border'}`}>
                      GNN {q.gnn_trained ? 'TRAINED' : 'pending'}
                    </span>
                    {q.superseded > 0 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-neon-amber/15 text-neon-amber border border-neon-amber/30 font-mono">
                        {q.superseded} dedup
                      </span>
                    )}
                  </div>
                </button>
              ))}

            {/* Empty slots for remaining quarters in this year */}
            {Array.from({length: 4 - (loadedYears.find(y => y.year === yearGroup.year)?.quarter_count || 0)})
              .map((_, i) => (
                <div key={`empty-${yearGroup.year}-${i}`}
                     className="bg-surface-card/30 rounded-lg p-3 border border-dashed border-surface-border opacity-40">
                  <div className="text-gray-500 text-xs font-mono">Q{(loadedYears.find(y=>y.year===yearGroup.year)?.quarter_count||0)+i+1} {yearGroup.year}</div>
                  <div className="text-gray-600 text-[10px] mt-1">Not yet uploaded</div>
                </div>
              ))
            }
          </div>
        </div>
      ))}

      {/* Future years skeleton — dynamically show next year if not loaded */}
      {(() => {
        const loadedYearNums = loadedYears.map(ly => ly.year);
        const maxLoadedYear = loadedYearNums.length > 0 ? Math.max(...loadedYearNums) : new Date().getFullYear();
        const nextYear = maxLoadedYear + 1;
        const futureYears = [nextYear].filter(y => !loadedYearNums.includes(y));
        return futureYears.map(y => (
          <div key={y} className="mb-4 opacity-30">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-gray-500 font-bold text-lg">{y}</span>
              <span className="text-gray-600 text-xs">Upload files to start this year</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[1,2,3,4].map(q => (
                <div key={q} className="bg-surface-card/20 rounded-lg p-3 border border-dashed border-surface-border">
                  <div className="text-gray-600 font-mono text-xs">Q{q} {y}</div>
                </div>
              ))}
            </div>
          </div>
        ));
      })()}
    </div>
  );
}

export default function UploadHub() {
  const {
    files, quarter, year, taskId, previewStats, status,
    setFile, removeFile, setQuarter, setYear, setTaskId, setPreviewStats, setStatus, setError, reset,
    loadedQuarters, fetchLoadedQuarters, setSelectedQuarter,
  } = useUploadStore();

  const [pipelineStep, setPipelineStep] = useState(0);

  useEffect(() => {
    fetchLoadedQuarters();
  }, []);

  const handleFileDrop = useCallback((fileType, file) => {
    if (file) {
      setFile(fileType, file);
      toast.success(`${fileType} file loaded`);
    }
  }, [setFile]);

  const handleRunPipeline = async () => {
    const fileCount = Object.keys(files).length;
    if (fileCount === 0) {
      toast.error('Upload at least one file');
      return;
    }

    // Check required files
    const required = ['DEMO', 'DRUG', 'REAC', 'OUTC'];
    const missing = required.filter(r => !files[r]);
    if (missing.length > 0) {
      toast.error(`Missing required files: ${missing.join(', ')}`);
      return;
    }

    setStatus('processing');
    setPipelineStep(0);

    const formData = new FormData();
    Object.entries(files).forEach(([, file]) => {
      formData.append('files', file);
    });
    formData.append('quarter', `${year}${quarter}`);
    formData.append('year', year.toString());

    try {
      const res = await api.post('/upload/ingest', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      });

      setTaskId(res.data.task_id);

      // Animate pipeline progress (slower for large files)
      const progressInterval = setInterval(() => {
        setPipelineStep(prev => {
          if (prev >= 9) {
            clearInterval(progressInterval);
            return 10;
          }
          return prev + 1;
        });
      }, 3000);

      // Poll for results
      const pollInterval = setInterval(async () => {
        try {
          const taskRes = await api.get(`/upload/task/${res.data.task_id}`);
          if (taskRes.data.status === 'ready') {
            clearInterval(pollInterval);
            clearInterval(progressInterval);
            setPipelineStep(10);
            setPreviewStats(taskRes.data.preview);
            setStatus('preview');
            toast.success('Pipeline complete! Review results below.');
          } else if (taskRes.data.status === 'failed') {
            clearInterval(pollInterval);
            clearInterval(progressInterval);
            setStatus('error');
            setError(taskRes.data.error);
            toast.error(`Pipeline failed: ${taskRes.data.error}`);
          }
        } catch (err) {
          console.error('Poll error:', err);
        }
      }, 2000);

    } catch (err) {
      setStatus('error');
      toast.error(`Upload failed: ${err.message}`);
    }
  };

  const handleApprove = async () => {
    if (!taskId) return;
    setStatus('approving');
    toast('Pushing data to PostgreSQL... This may take a few minutes for large datasets.', { icon: '\u23F3', duration: 10000 });
    try {
      const res = await api.post(`/upload/approve/${taskId}`, {}, {
        timeout: 3600000, // 60 min timeout for massive multi-million row inserts
      });
      setStatus('approved');
      toast.success(`Data committed to database! Session: ${res.data.session_id?.slice(0, 8)}...`, { duration: 8000 });
      // Refresh loaded quarters
      fetchLoadedQuarters();
    } catch (err) {
      setStatus('preview'); // go back to preview so they can retry
      const msg = err.response?.data?.detail || err.message;
      if (err.code === 'ECONNABORTED') {
        toast.error('Request timed out. The data may still be inserting. Check the backend logs.', { duration: 10000 });
      } else {
        toast.error(`Approval failed: ${msg}`, { duration: 10000 });
      }
    }
  };

  const handleReject = async () => {
    if (!taskId) return;
    try {
      await api.post(`/upload/reject/${taskId}`);
      setPreviewStats(null);
      setStatus('idle');
      toast('Data discarded', { icon: '🗑️' });
    } catch (err) {
      toast.error('Reject failed');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">FAERS Data Upload</h1>
          <p className="text-sm text-gray-500 mt-1">Upload quarterly FAERS files for pediatric ADR analysis</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400">Year</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="input-field w-24 text-center"
              min={2004}
              max={new Date().getFullYear() + 2}
              id="year-input"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400">Quarter</label>
            <select
              value={quarter}
              onChange={(e) => setQuarter(e.target.value)}
              className="select-field w-20"
              id="quarter-select"
            >
              <option value="Q1">Q1</option>
              <option value="Q2">Q2</option>
              <option value="Q3">Q3</option>
              <option value="Q4">Q4</option>
            </select>
          </div>
        </div>
      </div>

      {/* File Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {FILE_TYPES.map((type) => (
          <FileCard
            key={type.key}
            type={type}
            file={files[type.key]}
            onDrop={handleFileDrop}
            onRemove={removeFile}
          />
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleRunPipeline}
          disabled={status === 'processing' || Object.keys(files).length === 0}
          className="btn-primary flex items-center gap-2"
          id="run-pipeline-btn"
        >
          {status === 'processing' ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Processing...</>
          ) : (
            <><Upload className="w-4 h-4" /> Run Pipeline</>
          )}
        </button>

        <button onClick={reset} className="btn-secondary" id="reset-btn">
          Reset
        </button>

        <div className="ml-auto text-sm text-gray-500">
          {Object.keys(files).length} / 7 files loaded
        </div>
      </div>

      {/* Pipeline Progress */}
      {status === 'processing' && (
        <PipelineProgress currentStep={pipelineStep} totalSteps={10} pipelineDone={pipelineStep >= 10} />
      )}

      {/* Preview */}
      {(status === 'preview' || status === 'approving') && previewStats && (
        <>
          <PreviewTable stats={previewStats} />
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={handleApprove}
              disabled={status === 'approving'}
              className="btn-primary flex items-center gap-2"
              id="approve-btn"
            >
              {status === 'approving' ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Pushing to Database...</>
              ) : (
                <><Database className="w-4 h-4" /> Approve & Push to DB</>
              )}
            </button>
            <button
              onClick={handleReject}
              disabled={status === 'approving'}
              className="btn-danger flex items-center gap-2"
              id="reject-btn"
            >
              <XCircle className="w-4 h-4" /> Reject
            </button>
            {status === 'approving' && (
              <span className="text-xs text-neon-cyan animate-pulse">Inserting rows into PostgreSQL... Please wait</span>
            )}
          </div>
        </>
      )}

      {/* Success */}
      {status === 'approved' && (
        <div className="glass-card p-6 border-neon-green/30 animate-fade-in">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-neon-green" />
            <div>
              <h3 className="text-lg font-semibold text-neon-green">Data Successfully Committed</h3>
              <p className="text-sm text-gray-400">Navigate to other pages to explore the data.</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Quarter History ──────────────────────────────────── */}
      {loadedQuarters.length > 0 && <QuarterHistoryPanel />}
    </div>
  );
}

