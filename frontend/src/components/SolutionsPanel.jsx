import React from 'react';

export default function SolutionsPanel({ actions, actionLoading, onApprove, onExecute }) {
  return (
    <div className="panel" style={{ color: '#e2e8f0' }}>
      <h3>Recommended Actions</h3>
      {actions && actions.length > 0 ? (
        actions.map(action => (
          <div key={action.id} className="action-card" style={{border: '1px solid #334155', padding: 15, marginBottom: 10, borderRadius: 8}}>
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Action:</strong> {action.action_type}</p>
            {action.target && <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Target:</strong> {action.target}</p>}
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Description:</strong> {action.description}</p>
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Risk Level:</strong> {action.risk_level}</p>
            {action.confidence != null && <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Confidence:</strong> {Math.round(action.confidence * 100)}%</p>}
            <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Status:</strong> {action.status}</p>
            {action.result && <p style={{ color: '#cbd5e1' }}><strong style={{ color: '#94a3b8' }}>Result:</strong> {action.result}</p>}
            
            <div style={{marginTop: 10}}>
              {action.status === 'PENDING' && (
                <button className="button button-warning" onClick={() => onApprove(action.id)} disabled={actionLoading}>Approve</button>
              )}
              {(action.status === 'APPROVED' || (action.status === 'PENDING' && action.risk_level !== 'HIGH')) && (
                <button className="button button-primary" onClick={() => onExecute(action.id)} disabled={actionLoading} style={{marginLeft: 10}}>Execute</button>
              )}
            </div>
          </div>
        ))
      ) : (
        <p>No actions recommended yet.</p>
      )}
    </div>
  );
}
