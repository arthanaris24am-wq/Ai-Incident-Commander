import React from 'react';
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

export default function VerificationPanel({ verifications }) {
  if (!verifications || verifications.length === 0) {
    return null;
  }

  return (
    <div className="panel" style={{marginTop: 20, color: '#e2e8f0'}}>
      <h3>Verification Results</h3>
      {verifications.map((v, index) => (
        <div key={v.id || index} style={{
          padding: 15, 
          marginBottom: 10, 
          borderRadius: 8,
          background: v.result === 'PASSED' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${v.result === 'PASSED' ? '#22c55e' : '#ef4444'}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 5 }}>
            {v.result === 'PASSED' ? (
              <FaCheckCircle style={{ color: '#22c55e', marginRight: 10 }} />
            ) : (
              <FaTimesCircle style={{ color: '#ef4444', marginRight: 10 }} />
            )}
            <strong style={{ color: v.result === 'PASSED' ? '#22c55e' : '#ef4444' }}>
              {v.result}
            </strong>
          </div>
          <p style={{ margin: '5px 0 0 26px', color: '#cbd5e1' }}>{v.message}</p>
          <span style={{ display: 'block', margin: '5px 0 0 26px', fontSize: '0.85em', color: '#94a3b8' }}>
            {v.timestamp}
          </span>
        </div>
      ))}
    </div>
  );
}
