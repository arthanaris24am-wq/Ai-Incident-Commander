import { useEffect, useState } from "react";
import { 
  getIncidentDetails, 
  investigateIncident, 
  approveAction, 
  executeAction, 
  resolveIncident 
} from "../services/api";
import { FaExclamationTriangle, FaRobot, FaCheckCircle, FaSpinner } from "react-icons/fa";
import io from "socket.io-client";
import Timeline from "./Timeline";
import SolutionsPanel from "./SolutionsPanel";
import VerificationPanel from "./VerificationPanel";

export default function IncidentDetails({ incidentId, currentMetrics = {}, onBack }) {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [error, setError] = useState("");

  async function loadDetails() {
    try {
      const data = await getIncidentDetails(incidentId);
      setIncident(data);
    } catch (e) {
      setError("Failed to load incident details");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDetails();
    
    const socket = io(import.meta.env.VITE_API_URL || "http://localhost:5000");
    socket.on("incident_update", (data) => {
      if (data.incident_id === parseInt(incidentId)) {
        loadDetails();
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [incidentId]);

  async function handleInvestigate() {
    setInvestigating(true);
    setError("");
    try {
      await investigateIncident(incidentId);
      await loadDetails();
    } catch (e) {
      setError("Investigation failed: " + e.message);
    } finally {
      setInvestigating(false);
    }
  }

  async function handleApprove(actionId) {
    setActionLoading(true);
    setError("");
    try {
      await approveAction(incidentId, actionId);
      await loadDetails();
    } catch (e) {
      setError("Approval failed: " + e.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleExecute(actionId) {
    setActionLoading(true);
    setError("");
    try {
      await executeAction(incidentId, actionId);
      await loadDetails();
    } catch (e) {
      setError("Execution failed: " + e.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function handleResolve() {
    setActionLoading(true);
    setError("");
    try {
      await resolveIncident(incidentId);
      await loadDetails();
    } catch (e) {
      // API error handling
      setError(e.response?.data?.error || e.message || "Resolution failed");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading && !incident) return <div>Loading...</div>;
  if (!incident) return <div>Incident not found.</div>;

  const statusStr = String(incident.status).toUpperCase();
  const isResolved = statusStr === "RESOLVED";
  const badgeClass = isResolved
    ? "status-badge"
    : ["OPEN", "FAILED"].includes(statusStr)
    ? "status-badge critical"
    : "status-badge warning";

  const liveCpu = Number(currentMetrics?.cpu || 0);
  const liveMem = Number(currentMetrics?.memory_percent || 0);
  const liveDisk = Number(currentMetrics?.disk_percent || 0);
  const isMetricsNormalized = liveCpu < 80 && liveMem < 85;

  return (
    <div className="incident-details">
      <div className="panel-header">
        <button className="text-button" onClick={onBack}>&larr; Back to Incidents</button>
        <h2 style={{ color: '#f8fafc' }}>{incident.title || "Incident Details"}</h2>
        <span className={badgeClass}>{incident.status}</span>
      </div>
      
      {error && <div className="error-banner">{error}</div>}

      <div className="dashboard-grid">
        <div className="panel" style={{ color: '#e2e8f0' }}>
          <h3>Overview</h3>
          <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Recorded Peak Message:</strong> {incident.message}</p>
          <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Level:</strong> {incident.level}</p>
          <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Source:</strong> {incident.source}</p>
          <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>First Detected:</strong> {incident.first_seen || incident.timestamp}</p>
          {incident.resolved_at && (
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Resolved At:</strong> {incident.resolved_at}</p>
          )}

          {/* Live vs Recorded Status */}
          {currentMetrics && (currentMetrics.cpu !== undefined || currentMetrics.memory_percent !== undefined) && (
            <div style={{ marginTop: 16, padding: 14, background: '#0f172a', borderRadius: 8, border: '1px solid #334155' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>Live System Status vs Triggered Incident</span>
                <span style={{ 
                  fontSize: '0.75rem', 
                  padding: '3px 9px', 
                  borderRadius: '12px', 
                  fontWeight: 700,
                  background: isMetricsNormalized ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: isMetricsNormalized ? '#4ade80' : '#f87171'
                }}>
                  {isMetricsNormalized ? '✓ Live Metrics Normalized' : '⚠️ Metrics Elevated'}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: '#1e293b', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#64748b', fontSize: '0.75rem' }}>Live CPU</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1.1rem' }}>{liveCpu.toFixed(1)}%</div>
                </div>
                <div style={{ background: '#1e293b', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#64748b', fontSize: '0.75rem' }}>Live Memory</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1.1rem' }}>{liveMem.toFixed(1)}%</div>
                </div>
                <div style={{ background: '#1e293b', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ color: '#64748b', fontSize: '0.75rem' }}>Live Disk</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '1.1rem' }}>{liveDisk.toFixed(1)}%</div>
                </div>
              </div>
              {!isResolved && isMetricsNormalized && (
                <div style={{ marginTop: 10, fontSize: '0.8rem', color: '#38bdf8' }}>
                  ℹ️ System monitoring reports normal operating bounds. The incident peak has passed and can be safely verified and resolved.
                </div>
              )}
            </div>
          )}
          
          <div style={{ marginTop: 20, padding: 15, background: '#1e293b', borderRadius: 8 }}>
            <h4 style={{ color: '#38bdf8', marginBottom: 10 }}>AI Investigation Results</h4>
            <div style={{ marginBottom: 15 }}>
              <strong style={{ color: '#94a3b8' }}>Root Cause:</strong>
              <pre style={{ 
                color: '#f8fafc', 
                background: '#0f1728', 
                padding: 10, 
                borderRadius: 5, 
                marginTop: 5,
                whiteSpace: 'pre-wrap',
                fontFamily: 'inherit'
              }}>
                {incident.root_cause || "Not analyzed yet"}
              </pre>
            </div>
            
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>AI Confidence:</strong> {incident.confidence ? incident.confidence * 100 + "%" : "N/A"}</p>
            
            <div style={{ marginTop: 15 }}>
              <strong style={{ color: '#94a3b8' }}>Recommendation:</strong>
              <div style={{ color: '#f8fafc', marginTop: 5, whiteSpace: 'pre-wrap' }}>
                {incident.recommendation || "N/A"}
              </div>
            </div>
          </div>
          
          <div style={{ marginTop: 20 }}>
            <button className="button button-primary" onClick={handleInvestigate} disabled={investigating || actionLoading || incident.status === 'VERIFYING' || incident.status === 'RESOLVED'}>
              {investigating ? <><FaSpinner className="spin" /> Investigating...</> : <><FaRobot /> Ask AI to Investigate</>}
            </button>
            {' '}
            <button className="button button-success" onClick={handleResolve} disabled={investigating || actionLoading || incident.status === 'RESOLVED' || incident.status === 'VERIFYING'}>
              {actionLoading || incident.status === 'VERIFYING' ? <><FaSpinner className="spin" /> Verifying...</> : <><FaCheckCircle /> Resolve Incident</>}
            </button>
          </div>
        </div>

        <SolutionsPanel 
          actions={incident.actions} 
          actionLoading={actionLoading} 
          onApprove={handleApprove} 
          onExecute={handleExecute} 
        />
      </div>
      
      <Timeline events={incident.events} />
      
      <VerificationPanel verifications={incident.verifications} />

      <div className="panel" style={{marginTop: 20, color: '#e2e8f0'}}>
        <h3>Evidence</h3>
        {incident.evidence && incident.evidence.length > 0 ? (
          <ul>
            {incident.evidence.map(e => (
              <li key={e.id} style={{ marginBottom: 10 }}>
                <strong style={{ color: '#94a3b8' }}>{e.evidence_type}:</strong> 
                <pre style={{
                  background: '#1e293b', 
                  color: '#f8fafc',
                  padding: 10, 
                  borderRadius: 5, 
                  overflowX: 'auto',
                  marginTop: 5
                }}>{
                  typeof e.data === 'string' ? e.data : JSON.stringify(e.data, null, 2)
                }</pre>
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ color: '#64748b' }}>No evidence gathered yet.</p>
        )}
      </div>
    </div>
  );
}
