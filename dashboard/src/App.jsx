import React, { useState, useEffect } from 'react';
import { Shield, Users, Activity, AlertTriangle, ShieldCheck, UserX } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

function App() {
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  
  useEffect(() => {
    // Polling function for status and logs
    const fetchData = async () => {
      try {
        const statusRes = await fetch(`${API_BASE}/api/status`);
        if (statusRes.ok) {
          setStatus(await statusRes.json());
        }
        
        const logsRes = await fetch(`${API_BASE}/api/logs`);
        if (logsRes.ok) {
          setLogs(await logsRes.json());
        }
      } catch (e) {
        console.error("API Connection Error", e);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const getThreatColor = (level) => {
    if (level === 'High') return 'threat-high';
    if (level === 'Medium') return 'threat-medium';
    return 'threat-low';
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <div className="header">
        <h1>Intelligent Security Command Center</h1>
        <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
           <div className={`spinner`} style={{width: 15, height: 15, borderWidth: 2, display: status ? 'block' : 'none'}}></div>
           <span style={{color: status ? '#10b981' : '#ef4444'}}>
             {status ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}
           </span>
        </div>
      </div>

      {/* Main Video Panel */}
      <div className="glass-panel">
        <h2 style={{marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px'}}>
          <Activity size={20} color="var(--accent-cyan)"/> Live Camera Feed
        </h2>
        <div className="video-container">
          <img 
            src={`${API_BASE}/video_feed`} 
            alt="Live Video Stream" 
            className="video-feed"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.parentElement.innerHTML = '<div style="color: #64748b; display: flex; flex-direction: column; align-items: center; gap: 10px"><AlertTriangle size={40}/> Camera Feed Unavailable. Ensure backend is running.</div>';
            }}
          />
        </div>
        
        {/* System Stats Row */}
        <div className="stats-grid" style={{marginTop: '24px', gridTemplateColumns: 'repeat(4, 1fr)'}}>
          <div className="stat-card">
            <div className="stat-value">{status?.registered_users || 0}</div>
            <div className="stat-label">Registered Faces</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{status?.database?.threat_records || 0}</div>
            <div className="stat-label">Total Threats Logged</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{color: 'var(--threat-low)'}}>{status?.recent_responses?.low_threat_responses || 0}</div>
            <div className="stat-label">Low Threat Events</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{color: 'var(--threat-high)'}}>{status?.recent_responses?.high_threat_responses || 0}</div>
            <div className="stat-label">High Threat Events</div>
          </div>
        </div>
      </div>

      {/* Side Panel */}
      <div className="side-panel">
        
        {/* Quick Access Control Status */}
        <div className="glass-panel" style={{padding: '16px'}}>
          <h3 style={{marginBottom: '12px', fontSize: '1.1rem'}}>Access Roles Configured</h3>
          <div style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
            {status?.roles?.map(r => (
              <span key={r} className="badge badge-blue" style={{background: 'var(--glass-bg)', border: '1px solid var(--accent-blue)'}}>{r}</span>
            ))}
          </div>
        </div>

        {/* Real-time Event Feed */}
        <div className="glass-panel" style={{flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
          <h2 style={{marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <Shield size={20} color="var(--accent-blue)"/> Event Log
          </h2>
          
          <div className="logs-container">
            {logs.length === 0 && <p style={{color: '#64748b', textAlign: 'center'}}>Waiting for events...</p>}
            
            {logs.map((log, i) => (
              <div key={i} className={`log-item ${getThreatColor(log.data.threat_level)}`}>
                <div className="log-header">
                  <span className="log-name">
                    {log.data.is_authorized ? <ShieldCheck size={14} color="#10b981" style={{display: 'inline', verticalAlign: 'text-bottom'}}/> : <UserX size={14} color="#ef4444" style={{display: 'inline', verticalAlign: 'text-bottom'}}/>}
                    {' '} {log.data.user_id === 'unknown' ? 'Unknown Person' : log.data.user_id}
                  </span>
                  <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                </div>
                <div className="log-details">
                  <span className={`badge ${log.data.is_authorized ? 'badge-green' : 'badge-red'}`}>
                    {log.data.is_authorized ? 'Access Granted' : 'Access Denied'}
                  </span>
                  <span className={`badge ${log.data.threat_level === 'High' ? 'badge-red' : log.data.threat_level === 'Medium' ? 'badge-yellow' : 'badge-green'}`}>
                    Threat: {log.data.threat_level}
                  </span>
                  <span className="badge" style={{background: 'rgba(255,255,255,0.1)'}}>
                    Score: {(log.data.threat_score).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

export default App;
