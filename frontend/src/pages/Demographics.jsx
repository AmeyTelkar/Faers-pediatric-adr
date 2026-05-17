import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Users, Baby, Heart, Globe } from 'lucide-react';
import api from '../api/client';
import useUploadStore from '../store/uploadStore';

const AGE_COLORS = {
  NEONATE: '#f43f5e',
  INFANT: '#f59e0b',
  CHILD: '#6366f1',
  ADOLESCENT: '#10b981',
};

const SEX_COLORS = { M: '#6366f1', F: '#ec4899', UNK: '#6b7280', NS: '#6b7280' };

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="glass-card-hover p-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${color || 'text-gray-100'}`}>{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-lg bg-surface-dark`}>
          <Icon className={`w-5 h-5 ${color || 'text-pulse-400'}`} />
        </div>
      </div>
    </div>
  );
}

export default function Demographics() {
  const [summary, setSummary] = useState(null);
  const [pyramid, setPyramid] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const { selectedYear, selectedQuarter, getActiveQuarterFilter } = useUploadStore();

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const qFilter = getActiveQuarterFilter();
        const qp = qFilter !== 'ALL' ? `?quarter=${qFilter}` : '';
        const [sumRes, pyrRes, ctrRes] = await Promise.all([
          api.get(`/demographics/summary${qp}`),
          api.get(`/demographics/age-pyramid${qp}`),
          api.get(`/demographics/country-dist?limit=15${qFilter !== 'ALL' ? `&quarter=${qFilter}` : ''}`),
        ]);
        setSummary(sumRes.data);
        setPyramid(pyrRes.data);
        setCountries(ctrRes.data);
      } catch (err) {
        console.error('Failed to load demographics:', err);
      }
      setLoading(false);
    }
    load();
  }, [selectedYear, selectedQuarter]);

  // Build pyramid chart data
  const pyramidData = {};
  pyramid.forEach(({ age_group, sex, count }) => {
    if (!pyramidData[age_group]) pyramidData[age_group] = { age_group, Male: 0, Female: 0, Other: 0 };
    if (sex === 'M') pyramidData[age_group].Male = count;
    else if (sex === 'F') pyramidData[age_group].Female = count;
    else pyramidData[age_group].Other += count;
  });
  const pyramidChartData = Object.values(pyramidData);

  // Build sex pie data
  const sexData = summary?.sex_distribution
    ? Object.entries(summary.sex_distribution).map(([sex, count]) => ({
        name: sex === 'M' ? 'Male' : sex === 'F' ? 'Female' : 'Unknown',
        value: count,
        color: SEX_COLORS[sex] || SEX_COLORS.UNK,
      }))
    : [];

  // Age group pie data
  const ageData = summary?.age_group_distribution
    ? Object.entries(summary.age_group_distribution).map(([group, count]) => ({
        name: group,
        value: count,
        color: AGE_COLORS[group] || '#6b7280',
      }))
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pulse-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
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
        <h1 className="text-2xl font-bold gradient-text">Demographics Analysis</h1>
        <p className="text-sm text-gray-500 mt-1">Pediatric population breakdown by ICH E11 age bands</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Users}
          label="Total Patients"
          value={summary?.total_patients?.toLocaleString() || '0'}
          color="text-pulse-400"
        />
        <StatCard
          icon={Baby}
          label="Avg Age (years)"
          value={summary?.age_stats?.mean || '—'}
          sub={`Median: ${summary?.age_stats?.median || '—'}`}
          color="text-neon-cyan"
        />
        <StatCard
          icon={Heart}
          label="Quarters Loaded"
          value={summary?.quarters_available?.length || 0}
          sub={summary?.quarters_available?.join(', ')}
          color="text-neon-pink"
        />
        <StatCard
          icon={Globe}
          label="Countries"
          value={countries.length}
          sub="Reporter countries"
          color="text-neon-green"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Age Pyramid */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Age-Sex Distribution Pyramid</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pyramidChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
              <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis dataKey="age_group" type="category" tick={{ fill: '#9ca3af', fontSize: 11 }} width={100} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }}
                itemStyle={{ color: '#e5e7eb' }}
              />
              <Legend />
              <Bar dataKey="Male" fill="#6366f1" radius={[0, 4, 4, 0]} />
              <Bar dataKey="Female" fill="#ec4899" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sex Distribution Donut */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Sex Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={sexData} cx="50%" cy="50%" innerRadius={70} outerRadius={110}
                   dataKey="value" nameKey="name" paddingAngle={3} stroke="none">
                {sexData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }} itemStyle={{ color: '#e5e7eb' }} />
              <Legend formatter={(value) => <span className="text-gray-300 text-sm">{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Age Group + Country */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Age Group Donut */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">ICH E11 Age Groups</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={ageData} cx="50%" cy="50%" innerRadius={70} outerRadius={110}
                   dataKey="value" nameKey="name" paddingAngle={3} stroke="none">
                {ageData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }} itemStyle={{ color: '#e5e7eb' }} />
              <Legend formatter={(value) => <span className="text-gray-300 text-sm">{value}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Countries */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Top Reporter Countries</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={countries.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2d2d4a" />
              <XAxis dataKey="country" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2d2d4a', borderRadius: 8, color: '#e5e7eb' }} itemStyle={{ color: '#e5e7eb' }} />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]}>
                {countries.slice(0, 10).map((_, i) => (
                  <Cell key={i} fill={`hsl(${240 + i * 12}, 70%, 60%)`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
