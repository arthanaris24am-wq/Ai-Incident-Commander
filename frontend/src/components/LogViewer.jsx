import { useState, useRef, useEffect } from "react";
import { FaSearch, FaArrowDown, FaSyncAlt } from "react-icons/fa";

function LogViewer({ logs, onRefresh, containerName }) {
  const [filter, setFilter] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const logEndRef = useRef(null);

  // Split logs into lines
  const rawLines = typeof logs === 'string' ? logs.split('\n') : [];
  
  // Filter logs
  const filteredLines = rawLines.filter(line => 
    line.toLowerCase().includes(filter.toLowerCase())
  );

  const scrollToBottom = () => {
    if (autoScroll && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [filteredLines, autoScroll]);

  return (
    <div className="log-viewer-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 15 }}>
        <h3>📜 Live Logs: {containerName || "Container"}</h3>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div className="search-box" style={{ position: 'relative' }}>
            <FaSearch style={{ position: 'absolute', left: 10, top: 10, color: '#94a3b8' }} />
            <input 
              type="text" 
              placeholder="Filter logs..." 
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ padding: '8px 10px 8px 30px', borderRadius: 4, border: '1px solid #334155', background: '#0f172a', color: '#f8fafc' }}
            />
          </div>
          
          <button 
            className={`button ${autoScroll ? 'button-primary' : ''}`}
            style={{ padding: '8px 12px', background: autoScroll ? '#0284c7' : '#334155', color: '#f8fafc', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            onClick={() => setAutoScroll(!autoScroll)}
            title="Toggle Auto-Scroll"
          >
            <FaArrowDown />
          </button>
          
          <button 
            className="button"
            style={{ padding: '8px 12px', background: '#334155', color: '#f8fafc', border: 'none', borderRadius: 4, cursor: 'pointer' }}
            onClick={onRefresh}
            title="Refresh Logs"
          >
            <FaSyncAlt />
          </button>
        </div>
      </div>

      <div className="log-box" style={{ 
        flex: 1, 
        background: '#0f172a', 
        color: '#e2e8f0', 
        padding: 15, 
        borderRadius: 8, 
        overflowY: 'auto',
        fontFamily: 'monospace',
        minHeight: '400px',
        maxHeight: '600px'
      }}>
        {filteredLines.length > 0 ? (
          filteredLines.map((line, idx) => (
            <div key={idx} style={{ 
              borderBottom: '1px solid #1e293b', 
              padding: '4px 0',
              wordBreak: 'break-all'
            }}>
              {line}
            </div>
          ))
        ) : (
          <div style={{ color: '#64748b', textAlign: 'center', marginTop: 20 }}>
            {logs ? "No logs match your filter." : "No logs available."}
          </div>
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}

export default LogViewer;