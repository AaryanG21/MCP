import { useState, useEffect, useRef } from 'react';
import './index.css';

// Components
const SearchBar = ({ onSearch, disabled }) => {
  const [prompt, setPrompt] = useState('Find the ownership details of Tata Sons, save those details in a local file, and display them on the dashboard.');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (prompt.trim() && !disabled) {
      onSearch(prompt);
    }
  };

  return (
    <form className="search-container card" onSubmit={handleSubmit}>
      <input
        type="text"
        className="search-input"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter agent instruction..."
        disabled={disabled}
      />
      <button type="submit" className="search-button" disabled={disabled}>
        {disabled ? 'Running...' : 'Run Agent'}
      </button>
    </form>
  );
};

const ResultsCard = ({ data }) => {
  return (
    <div className="card">
      <h2>📊 Company Data</h2>
      {data ? (
        <ul className="data-list">
          <li>
            <span className="data-label">Company Name</span>
            <span className="data-value">{data.company_name || 'N/A'}</span>
          </li>
          <li>
            <span className="data-label">Founders</span>
            <span className="data-value">{data.founders || 'N/A'}</span>
          </li>
          <li>
            <span className="data-label">Ownership</span>
            <span className="data-value">{data.ownership || 'N/A'}</span>
          </li>
          <li>
            <span className="data-label">Headquarters</span>
            <span className="data-value">{data.headquarters || 'N/A'}</span>
          </li>
          <li>
            <span className="data-label">Industry</span>
            <span className="data-value">{data.industry || 'N/A'}</span>
          </li>
        </ul>
      ) : (
        <p style={{ color: 'var(--text-secondary)' }}>No data fetched yet. Run the agent to see results.</p>
      )}
    </div>
  );
};

const FileStatusCard = ({ status }) => {
  return (
    <div className="card">
      <h2>💾 File Save Status</h2>
      <div className="file-status-content">
        {status ? (
          <>
            <div className="status-icon">
              {status.status === 'success' ? '✅' : '❌'}
            </div>
            <p className="data-value">{status.message}</p>
          </>
        ) : (
          <p style={{ color: 'var(--text-secondary)' }}>Waiting for agent to save file...</p>
        )}
      </div>
    </div>
  );
};

const LogPanel = ({ logs }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="card log-panel">
      <h2>⚡ Execution Logs</h2>
      <div className="log-container">
        {logs.length === 0 ? (
          <div style={{ color: 'var(--text-secondary)' }}>Waiting for agent execution...</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className={`log-entry log-type-${log.type}`}>
              <span className="log-time">[{log.time}]</span>
              {log.type === 'step' && <strong>Step {log.step}: </strong>}
              <span>{log.type === 'data' ? JSON.stringify(log.data, null, 2) : log.message || JSON.stringify(log)}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

function App() {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const [companyData, setCompanyData] = useState(null);
  const [fileStatus, setFileStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    // Connect to MCP Server via WebSocket
    const ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
      setConnected(true);
      console.log('Connected to MCP WebSocket Server');
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const logEntry = { ...payload, time: new Date().toLocaleTimeString() };
        
        setLogs((prev) => [...prev, logEntry]);

        if (payload.type === 'data') {
          setCompanyData(payload.data);
        } else if (payload.type === 'file_status') {
          setFileStatus(payload.status);
        } else if (payload.type === 'log' && payload.message === 'Agent workflow finished successfully.') {
          setIsRunning(false);
        }
      } catch (err) {
        console.error('Error parsing WS message:', err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('Disconnected from MCP WebSocket Server');
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  const handleSearch = (prompt) => {
    if (socket && connected) {
      setIsRunning(true);
      // Reset state for new run
      setLogs([]);
      setCompanyData(null);
      setFileStatus(null);
      
      socket.send(JSON.stringify({ prompt }));
    } else {
      alert("WebSocket is not connected. Make sure the backend server is running.");
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>MCP Agent Dashboard</h1>
        <p>Local Autonomous Agent Execution System</p>
        
        <div style={{ marginTop: '1rem' }}>
          <span className={`connection-badge ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {connected ? 'Connected to Backend Server' : 'Disconnected from Backend Server'}
          </span>
        </div>
      </div>

      <SearchBar onSearch={handleSearch} disabled={isRunning || !connected} />

      <div className="dashboard-grid">
        <ResultsCard data={companyData} />
        <FileStatusCard status={fileStatus} />
        <LogPanel logs={logs} />
      </div>
    </div>
  );
}

export default App;
