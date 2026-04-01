import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; background: #F8FAFC; color: #0F172A; }
  :root {
    --primary: #1A56DB;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --surface: #F8FAFC;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #64748B;
    --hint: #94A3B8;
  }
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 220px; background: #0F172A; padding: 24px 0;
    display: flex; flex-direction: column; flex-shrink: 0;
  }
  .sidebar-logo {
    padding: 0 20px 24px; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;
  }
  .sidebar-logo span { color: #fff; font-size: 18px; font-weight: 800; }
  .nav-item {
    padding: 10px 20px; display: flex; align-items: center; gap: 10px;
    color: rgba(255,255,255,0.5); font-size: 14px; font-weight: 500;
    cursor: pointer; border-radius: 0; transition: all 0.15s;
    text-decoration: none;
  }
  .nav-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
  .nav-item.active { color: #fff; background: rgba(26,86,219,0.3); border-right: 2px solid var(--primary); }
  .main { flex: 1; overflow: auto; }
  .topbar {
    background: #fff; padding: 16px 28px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 10;
  }
  .topbar h1 { font-size: 18px; font-weight: 700; }
  .badge-live {
    background: #ECFDF5; color: var(--success); font-size: 11px; font-weight: 700;
    padding: 4px 10px; border-radius: 20px; display: flex; align-items: center; gap: 4px;
  }
  .badge-live::before { content: ''; width: 6px; height: 6px; background: var(--success); border-radius: 50%; }
  .content { padding: 24px 28px; }
  .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .metric-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 20px; display: flex; flex-direction: column; gap: 8px;
  }
  .metric-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
  .metric-val { font-size: 26px; font-weight: 800; }
  .metric-label { font-size: 12px; color: var(--muted); }
  .metric-change { font-size: 12px; font-weight: 600; }
  .up { color: var(--success); }
  .down { color: var(--danger); }
  .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 24px; }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 20px;
  }
  .card-title { font-size: 14px; font-weight: 700; margin-bottom: 16px; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
  td { padding: 12px 12px; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }
  .status-pill {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
  }
  .pill-paid { background: #ECFDF5; color: var(--success); }
  .pill-approved { background: #EFF6FF; color: var(--primary); }
  .pill-rejected { background: #FEF2F2; color: var(--danger); }
  .pill-pending { background: #FFFBEB; color: var(--warning); }
  .disruption-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
  .disruption-row:last-child { border-bottom: none; }
  .sev-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .sev-extreme { background: #991B1B; }
  .sev-severe { background: var(--danger); }
  .sev-moderate { background: var(--warning); }
  .dss-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
  .dss-fill { height: 100%; border-radius: 3px; background: var(--primary); }
`

// ── Mock data ─────────────────────────────────────────────────────────────────

const weeklyClaimsData = [
  { day: 'Mon', claims: 12, payouts: 8400 },
  { day: 'Tue', claims: 8, payouts: 5600 },
  { day: 'Wed', claims: 24, payouts: 18200 },
  { day: 'Thu', claims: 31, payouts: 24800 },
  { day: 'Fri', claims: 19, payouts: 14300 },
  { day: 'Sat', claims: 42, payouts: 31500 },
  { day: 'Sun', claims: 15, payouts: 11200 },
]

const tierDistribution = [
  { name: 'Basic', value: 22, color: '#10B981' },
  { name: 'Smart', value: 53, color: '#1A56DB' },
  { name: 'Pro', value: 25, color: '#F59E0B' },
]

const mockClaims = [
  { id: 'CLM001', worker: 'Ravi K.', city: 'Bangalore', event: '🌧️ Heavy Rain', amount: '₹390', status: 'paid', fraud: 5 },
  { id: 'CLM002', worker: 'Arjun M.', city: 'Delhi', event: '🌡️ Extreme Heat', amount: '₹195', status: 'paid', fraud: 0 },
  { id: 'CLM003', worker: 'Meena S.', city: 'Mumbai', event: '🌧️ Heavy Rain', amount: '₹550', status: 'approved', fraud: 12 },
  { id: 'CLM004', worker: 'Suresh P.', city: 'Chennai', event: '🏭 AQI Spike', amount: '₹325', status: 'pending', fraud: 8 },
  { id: 'CLM005', worker: 'Vijay T.', city: 'Bangalore', event: '🌧️ Heavy Rain', amount: '₹0', status: 'rejected', fraud: 78 },
]

const mockDisruptions = [
  { city: 'Mumbai', type: '🌧️ Heavy Rain', severity: 'extreme', dss: 1.0, active: true },
  { city: 'Delhi', type: '🌡️ Heat', severity: 'severe', dss: 0.6, active: true },
  { city: 'Bangalore', type: '🌧️ Rain', severity: 'moderate', dss: 0.3, active: true },
  { city: 'Chennai', type: '🏭 AQI', severity: 'severe', dss: 0.5, active: false },
]

// ── Components ────────────────────────────────────────────────────────────────

function Sidebar({ active, setActive }) {
  const items = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'claims', label: 'Claims', icon: '📋' },
    { id: 'disruptions', label: 'Disruptions', icon: '⚠️' },
    { id: 'workers', label: 'Workers', icon: '👥' },
  ]
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <span>🛡️</span>
        <span>GigShield</span>
      </div>
      {items.map(item => (
        <div
          key={item.id}
          className={`nav-item ${active === item.id ? 'active' : ''}`}
          onClick={() => setActive(item.id)}
        >
          <span>{item.icon}</span>
          <span>{item.label}</span>
        </div>
      ))}
      <div style={{ marginTop: 'auto', padding: '0 20px' }}>
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, marginBottom: 4 }}>Environment</div>
        <div style={{ color: '#F59E0B', fontSize: 12, fontWeight: 600 }}>🧪 Development</div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, change, up, color }) {
  return (
    <div className="metric-card">
      <div className="metric-icon" style={{ background: color + '18' }}>
        <span>{icon}</span>
      </div>
      <div className="metric-val">{value}</div>
      <div className="metric-label">{label}</div>
      {change && <div className={`metric-change ${up ? 'up' : 'down'}`}>{up ? '↑' : '↓'} {change}</div>}
    </div>
  )
}

function OverviewPage() {
  return (
    <>
      <div className="metrics-grid">
        <MetricCard icon="👷" label="Active Workers" value="1,247" change="12% this week" up color="#1A56DB" />
        <MetricCard icon="🛡️" label="Active Policies" value="892" change="8% this week" up color="#10B981" />
        <MetricCard icon="📋" label="Claims This Week" value="151" change="24% vs last week" up color="#F59E0B" />
        <MetricCard icon="💰" label="Payouts This Week" value="₹1.14L" change="18% vs last week" up color="#8B5CF6" />
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-title">Claims & Payouts (This Week)</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weeklyClaimsData} barSize={20}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="claims" fill="#1A56DB" radius={[4,4,0,0]} name="Claims" />
              <Bar dataKey="payouts" fill="#10B981" radius={[4,4,0,0]} name="Payout (₹)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Policy Tier Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={tierDistribution} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="value">
                {tierDistribution.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-title">Active Disruptions</div>
          {mockDisruptions.map((d, i) => (
            <div key={i} className="disruption-row">
              <div className={`sev-dot sev-${d.severity}`} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{d.city} — {d.type}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>{d.severity.toUpperCase()} • DSS {(d.dss * 100).toFixed(0)}%</div>
              </div>
              <div className="dss-bar">
                <div className="dss-fill" style={{ width: `${d.dss * 100}%` }} />
              </div>
              <span style={{ fontSize: 11, color: d.active ? 'var(--success)' : 'var(--hint)', fontWeight: 600 }}>
                {d.active ? 'LIVE' : 'ENDED'}
              </span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-title">Fraud Summary</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Auto-approved (score < 30)', val: '138', color: 'var(--success)' },
              { label: 'Under review (30–70)', val: '9', color: 'var(--warning)' },
              { label: 'Auto-rejected (score > 70)', val: '4', color: 'var(--danger)' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: 'var(--muted)' }}>{item.label}</span>
                <span style={{ fontWeight: 700, color: item.color, fontSize: 16 }}>{item.val}</span>
              </div>
            ))}
            <div style={{ marginTop: 8, padding: 12, background: 'var(--surface)', borderRadius: 10, fontSize: 12, color: 'var(--muted)' }}>
              📌 Loss ratio this week: <strong style={{ color: 'var(--text)' }}>41.3%</strong> — within target (≤55%)
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

function ClaimsPage() {
  return (
    <div className="card">
      <div className="card-title">All Claims</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Worker</th>
              <th>City</th>
              <th>Event</th>
              <th>Amount</th>
              <th>Fraud Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {mockClaims.map(c => (
              <tr key={c.id}>
                <td style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{c.id}</td>
                <td style={{ fontWeight: 600 }}>{c.worker}</td>
                <td>{c.city}</td>
                <td>{c.event}</td>
                <td style={{ fontWeight: 700 }}>{c.amount}</td>
                <td>
                  <span style={{ color: c.fraud > 70 ? 'var(--danger)' : c.fraud > 30 ? 'var(--warning)' : 'var(--success)', fontWeight: 700 }}>
                    {c.fraud}/100
                  </span>
                </td>
                <td><span className={`status-pill pill-${c.status}`}>{c.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function DisruptionsPage() {
  return (
    <div className="card">
      <div className="card-title">Disruption Events Monitor</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>City</th><th>Type</th><th>Severity</th><th>DSS Multiplier</th><th>Status</th></tr>
          </thead>
          <tbody>
            {mockDisruptions.map((d, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600 }}>{d.city}</td>
                <td>{d.type}</td>
                <td>
                  <span className={`status-pill ${d.severity === 'extreme' ? 'pill-rejected' : d.severity === 'severe' ? 'pill-pending' : 'pill-approved'}`}>
                    {d.severity}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="dss-bar" style={{ width: 80 }}>
                      <div className="dss-fill" style={{ width: `${d.dss * 100}%` }} />
                    </div>
                    <span style={{ fontWeight: 600 }}>{(d.dss * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td><span className={`status-pill ${d.active ? 'pill-paid' : 'pill-rejected'}`}>{d.active ? 'ACTIVE' : 'ENDED'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [active, setActive] = useState('overview')

  const pages = {
    overview: { title: 'Overview', component: <OverviewPage /> },
    claims: { title: 'Claims Management', component: <ClaimsPage /> },
    disruptions: { title: 'Disruption Monitor', component: <DisruptionsPage /> },
    workers: { title: 'Workers', component: <div className="card"><p style={{color:'var(--muted)'}}>Workers management — Phase 2</p></div> },
  }
  const page = pages[active]

  return (
    <>
      <style>{styles}</style>
      <div className="layout">
        <Sidebar active={active} setActive={setActive} />
        <div className="main">
          <div className="topbar">
            <h1>{page.title}</h1>
            <div className="badge-live">Live Data</div>
          </div>
          <div className="content">{page.component}</div>
        </div>
      </div>
    </>
  )
}
