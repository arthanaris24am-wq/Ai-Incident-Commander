import React from 'react';

export default function Timeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="panel" style={{marginTop: 20, color: '#e2e8f0'}}>
        <h3>Incident Timeline</h3>
        <p style={{ color: '#64748b' }}>No timeline events recorded.</p>
      </div>
    );
  }

  return (
    <div className="panel" style={{marginTop: 20, color: '#e2e8f0'}}>
      <h3>Incident Timeline</h3>
      <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
        {[...events].reverse().map((event, index) => (
          <li key={event.id || index} style={{ marginBottom: 15, position: 'relative', paddingLeft: 20, borderLeft: '2px solid #38bdf8' }}>
            <span style={{ position: 'absolute', left: -6, top: 4, width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }}></span>
            <strong style={{ color: '#94a3b8', display: 'block', fontSize: '0.9em' }}>{event.timestamp}</strong>
            <span style={{ color: '#f8fafc', fontWeight: 'bold', marginRight: 10 }}>[{event.source}]</span>
            <span style={{ color: '#f8fafc' }}>{event.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
