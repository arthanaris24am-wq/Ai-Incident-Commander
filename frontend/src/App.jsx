import { useEffect, useState } from "react";

import {
  getMetrics,
  getIncidents,
  getContainers,
  getAIReport,
  getContainerLogs,
  getApplicationLogs,
  injectTestLog,
  clearApplicationLogs,
  startContainer,
  stopContainer,
  restartContainer,
  resolveAllIncidents,
} from "./services/api";

import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import DockerCard from "./components/DockerCard";
import LogViewer from "./components/LogViewer";
import LiveChart from "./components/LiveChart";
import IncidentDetails from "./components/IncidentDetails";

import {
  FaMicrochip,
  FaMemory,
  FaHdd,
  FaExclamationTriangle,
  FaRobot,
  FaDocker,
  FaHeartbeat,
  FaCheckCircle,
} from "react-icons/fa";

import "./App.css";


function App() {

  // ============================================
  // STATE
  // ============================================

  const [activePage, setActivePage] = useState("dashboard");
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedContainerId, setSelectedContainerId] = useState(null);

  const [metrics, setMetrics] = useState({});
  const [incidents, setIncidents] = useState([]);
  const [containers, setContainers] = useState([]);
  const [report, setReport] = useState({});
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState("");
  const [appLogs, setAppLogs] = useState("");
  const [logTab, setLogTab] = useState("app");
  const [injectStatus, setInjectStatus] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resolvingAll, setResolvingAll] = useState(false);

  async function handleResolveAll() {
    setResolvingAll(true);
    try {
      await resolveAllIncidents();
      const incs = await getIncidents();
      setIncidents(incs || []);
    } catch (err) {
      console.error("Resolve all failed:", err);
    } finally {
      setResolvingAll(false);
    }
  }


  // ============================================
  // LOAD DASHBOARD DATA
  // ============================================

  async function loadDashboard() {

    setLoading(true);
    setError("");

    try {

      const results = await Promise.allSettled([
        getMetrics(),
        getIncidents(),
        getContainers(),
        getAIReport(),
      ]);


      const [
        metricsResult,
        incidentsResult,
        containersResult,
        reportResult,
      ] = results;


      // ========================================
      // METRICS
      // ========================================

      if (metricsResult.status === "fulfilled") {

        const metricsData = metricsResult.value || {};

        setMetrics(metricsData);


        setHistory((previous) => {

          const newPoint = {
            time: new Date().toLocaleTimeString(),

            cpu: Number(
              metricsData?.cpu || 0
            ),

            memory: Number(
              metricsData?.memory_percent || 0
            ),

            disk: Number(
              metricsData?.disk_percent || 0
            ),
          };


          return [
            ...previous,
            newPoint,
          ].slice(-20);

        });

      } else {

        console.error(
          "Metrics API failed:",
          metricsResult.reason
        );

      }


      // ========================================
      // INCIDENTS
      // ========================================

      if (incidentsResult.status === "fulfilled") {

        setIncidents(
          incidentsResult.value || []
        );

      } else {

        console.error(
          "Incidents API failed:",
          incidentsResult.reason
        );

      }


      // ========================================
      // DOCKER
      // ========================================

      if (containersResult.status === "fulfilled") {

        setContainers(
          containersResult.value || []
        );

      } else {

        console.error(
          "Docker API failed:",
          containersResult.reason
        );

      }


      // ========================================
      // AI REPORT
      // ========================================

      if (reportResult.status === "fulfilled") {

        setReport(
          reportResult.value || {}
        );

      } else {

        console.error(
          "AI Report API failed:",
          reportResult.reason
        );

      }


      // ========================================
      // CHECK FAILED APIs
      // ========================================

      const failedAPIs = [];


      if (
        metricsResult.status === "rejected"
      ) {
        failedAPIs.push("Metrics");
      }


      if (
        incidentsResult.status === "rejected"
      ) {
        failedAPIs.push("Incidents");
      }


      if (
        containersResult.status === "rejected"
      ) {
        failedAPIs.push("Docker");
      }


      if (
        reportResult.status === "rejected"
      ) {
        failedAPIs.push("AI Report");
      }


      if (failedAPIs.length > 0) {

        setError(
          `Failed APIs: ${failedAPIs.join(", ")}`
        );

      } else {

        setError("");

      }

    } catch (err) {

      console.error(
        "Dashboard unexpected error:",
        err
      );

      setError(
        err?.message ||
        "Unexpected frontend error."
      );

    } finally {

      setLoading(false);

    }

  }


  // ============================================
  // AUTO REFRESH & SOCKET.IO
  // ============================================

  useEffect(() => {

    loadDashboard();

    // Set up Socket.IO
    import("socket.io-client").then(({ io }) => {
      const socket = io("http://127.0.0.1:5000");

      socket.on("connect", () => {
        console.log("Socket.IO Connected");
      });

      socket.on("new_incident", (data) => {
        console.log("New incident received:", data);
        loadDashboard();
      });

      socket.on("incident_update", (data) => {
        console.log("Incident update received:", data);
        loadDashboard();
      });

      socket.on("metrics_update", (data) => {
        // Option to just update metrics without full reload
        loadDashboard();
      });

      return () => {
        socket.disconnect();
      };
    });

    const interval = setInterval(() => {
      loadDashboard();
    }, 5000);

    return () => {
      clearInterval(interval);
    };

  }, []);


  // ============================================
  // DOCKER START
  // ============================================

  async function handleStart(id) {

    try {

      await startContainer(id);

      await loadDashboard();

    } catch (err) {

      console.error(
        "Start container error:",
        err
      );

      setError(
        err?.message ||
        "Unable to start container."
      );

    }

  }


  // ============================================
  // DOCKER STOP
  // ============================================

  async function handleStop(id) {

    try {

      await stopContainer(id);

      await loadDashboard();

    } catch (err) {

      console.error(
        "Stop container error:",
        err
      );

      setError(
        err?.message ||
        "Unable to stop container."
      );

    }

  }


  // ============================================
  // DOCKER RESTART
  // ============================================

  async function handleRestart(id) {

    try {

      await restartContainer(id);

      await loadDashboard();

    } catch (err) {

      console.error(
        "Restart container error:",
        err
      );

      setError(
        err?.message ||
        "Unable to restart container."
      );

    }

  }


  // ============================================
  // CONTAINER LOGS
  // ============================================

  async function handleLogs(id) {

    try {
      setSelectedContainerId(id);

      const data =
        await getContainerLogs(id);


      setLogs(
        data?.logs ||
        "No logs available."
      );


      setActivePage("logs");

    } catch (err) {

      console.error(
        "Container logs error:",
        err
      );

      setLogs(
        "Unable to load container logs."
      );

      setLogTab("docker");
      setActivePage("logs");

    }

  }

  async function loadAppLogs() {
    try {
      const data = await getApplicationLogs();
      setAppLogs(data?.logs || "No application logs recorded yet.");
    } catch (err) {
      console.error("Application logs error:", err);
      setAppLogs("Unable to load application logs.");
    }
  }

  async function handleInjectLog(level, message, component = "application") {
    try {
      setInjectStatus(`Injecting [${level}]...`);
      await injectTestLog(level, message, component);
      await loadAppLogs();
      setInjectStatus(`Injected [${level}] log!`);
      setTimeout(() => setInjectStatus(""), 3000);
    } catch (err) {
      setInjectStatus(`Failed to inject: ${err.message}`);
    }
  }

  async function handleClearAppLogs() {
    try {
      await clearApplicationLogs();
      await loadAppLogs();
      setInjectStatus("Application log file cleared.");
      setTimeout(() => setInjectStatus(""), 2500);
    } catch (err) {
      setInjectStatus(`Error clearing logs: ${err.message}`);
    }
  }


  // ============================================
  // METRIC CARD
  // ============================================

  function renderMetricCard(
    icon,
    title,
    value,
    unit = "%"
  ) {

    return (

      <div className="metric-card">

        <div className="metric-icon">

          {icon}

        </div>


        <div className="metric-content">

          <span>
            {title}
          </span>


          <strong>

            {value}

            {unit}

          </strong>

        </div>

      </div>

    );

  }


  // ============================================
  // DASHBOARD PAGE
  // ============================================

  function DashboardPage() {

    const openIncidents =
      incidents.filter(
        (item) =>
          String(item.status).toUpperCase() !==
          "RESOLVED"
      ).length;


    const runningContainers =
      containers.filter(
        (container) =>
          String(container.status).toLowerCase() ===
          "running"
      ).length;


    const stoppedContainers =
      containers.filter(
        (container) =>
          String(container.status).toLowerCase() !==
          "running"
      ).length;


    return (

      <>

        {/* PAGE HEADER */}

        <div className="page-heading">

          <div>

            <h2>
              System Overview
            </h2>

            <p>
              Monitor infrastructure health and active services.
            </p>

          </div>


          <div className="live-indicator">

            <span></span>

            LIVE MONITORING

          </div>

        </div>


        {/* METRICS */}

        <div className="metric-grid">

          {renderMetricCard(
            <FaMicrochip />,
            "CPU Usage",
            Number(metrics.cpu || 0).toFixed(1)
          )}


          {renderMetricCard(
            <FaMemory />,
            "Memory Usage",
            Number(
              metrics.memory_percent || 0
            ).toFixed(1)
          )}


          {renderMetricCard(
            <FaHdd />,
            "Disk Usage",
            Number(
              metrics.disk_percent || 0
            ).toFixed(1)
          )}


          {renderMetricCard(
            <FaExclamationTriangle />,
            "Open Incidents",
            openIncidents,
            ""
          )}

        </div>


        {/* CHARTS */}

        <div className="chart-grid">

          <LiveChart
            title="CPU Usage"
            data={history}
            dataKey="cpu"
            color="#38bdf8"
          />


          <LiveChart
            title="Memory Usage"
            data={history}
            dataKey="memory"
            color="#22c55e"
          />


          <LiveChart
            title="Disk Usage"
            data={history}
            dataKey="disk"
            color="#f59e0b"
          />

        </div>


        {/* LOWER DASHBOARD */}

        <div className="dashboard-grid">


          {/* DOCKER */}

          <div className="panel">

            <div className="panel-header">

              <h3>

                <FaDocker />

                Docker Overview

              </h3>


              <button
                className="text-button"
                onClick={() =>
                  setActivePage("docker")
                }
              >
                View All
              </button>

            </div>


            <div className="docker-summary">

              <div>

                <strong>
                  {containers.length}
                </strong>

                <span>
                  Total
                </span>

              </div>


              <div>

                <strong className="text-green">

                  {runningContainers}

                </strong>

                <span>
                  Running
                </span>

              </div>


              <div>

                <strong className="text-red">

                  {stoppedContainers}

                </strong>

                <span>
                  Stopped
                </span>

              </div>

            </div>

          </div>


          {/* AI HEALTH */}

          <div className="panel">

            <div className="panel-header">

              <h3>

                <FaRobot />

                AI Health

              </h3>


              <button
                className="text-button"
                onClick={() =>
                  setActivePage("ai")
                }
              >
                Details
              </button>

            </div>


            <div className="ai-health">

              <div
                className={
                  report.overall_health ===
                  "CRITICAL"
                    ? "health-circle critical"
                    : "health-circle"
                }
              >

                <FaHeartbeat />


                <strong>

                  {
                    report.overall_health ||
                    "UNKNOWN"
                  }

                </strong>

              </div>


              <div>

                <span>
                  Confidence
                </span>


                <strong>

                  {
                    report.confidence || 0
                  }%

                </strong>

              </div>

            </div>

          </div>

        </div>


      </>

    );

  }


  // ============================================
  // DOCKER PAGE
  // ============================================

  function DockerPage() {

    return (

      <>

        <div className="page-heading">

          <div>

            <h2>
              Docker Management
            </h2>

            <p>
              Monitor and control Docker containers.
            </p>

          </div>

        </div>


        <div className="docker-grid">

          {containers.length === 0 ? (

            <div className="empty-state">

              <FaDocker size={50} />

              <h3>
                No Containers Found
              </h3>

              <p>
                Docker containers will appear here when available.
              </p>

            </div>

          ) : (

            containers.map(
              (container) => (

                <DockerCard
                  key={container.id}
                  container={container}
                  onStart={handleStart}
                  onStop={handleStop}
                  onRestart={handleRestart}
                  onLogs={handleLogs}
                />

              )
            )

          )}

        </div>

      </>

    );

  }


  // ============================================
  // INCIDENTS PAGE
  // ============================================

  function IncidentsPage() {

    return (

      <>

        <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>

          <div>

            <h2>
              Incident Management
            </h2>

            <p>
              Review and monitor detected system incidents.
            </p>

          </div>

          {incidents && incidents.some(i => i.status !== "RESOLVED") && (
            <button
              className="button button-success"
              style={{ padding: '9px 18px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', cursor: 'pointer' }}
              onClick={handleResolveAll}
              disabled={resolvingAll}
            >
              <FaCheckCircle /> {resolvingAll ? "Resolving All..." : "Resolve All Issues"}
            </button>
          )}

        </div>


        <div className="panel">

          {incidents.length === 0 ? (

            <div className="empty-state">

              <FaHeartbeat size={45} />

              <h3>
                No Incidents
              </h3>

              <p>
                Your infrastructure currently has no recorded incidents.
              </p>

            </div>

          ) : (

            incidents.map(
              (incident) => {
                const statusStr = String(incident.status).toUpperCase();
                const isResolved = statusStr === "RESOLVED";
                const badgeClass = isResolved
                  ? "status-badge"
                  : ["OPEN", "FAILED"].includes(statusStr)
                  ? "status-badge critical"
                  : "status-badge warning";

                const isCpuIncident = incident.type === "CPU_HIGH" || (incident.message && incident.message.toLowerCase().includes("cpu"));
                const isMemIncident = incident.type === "MEMORY_HIGH" || (incident.message && incident.message.toLowerCase().includes("memory"));

                return (
                  <div
                    className="incident-row"
                    key={incident.id}
                  >
                    <div className="incident-icon">
                      <FaExclamationTriangle />
                    </div>

                    <div className="incident-info">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <strong>{incident.level}</strong>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>#{incident.id}</span>
                        {incident.type && (
                          <span style={{ fontSize: '10px', background: '#334155', color: '#cbd5e1', padding: '1px 6px', borderRadius: '4px' }}>
                            {incident.type}
                          </span>
                        )}
                      </div>

                      <p style={{ margin: '4px 0', color: '#f1f5f9' }}>
                        {incident.message}
                      </p>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginTop: '4px' }}>
                        <small>{incident.timestamp}</small>
                        {!isResolved && isCpuIncident && (
                          <span style={{ 
                            fontSize: '11px', 
                            padding: '1px 7px', 
                            borderRadius: '4px',
                            background: Number(metrics.cpu || 0) < 80 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: Number(metrics.cpu || 0) < 80 ? '#4ade80' : '#f87171',
                            fontWeight: 600
                          }}>
                            Live CPU: {Number(metrics.cpu || 0).toFixed(1)}% {Number(metrics.cpu || 0) < 80 ? '(Stabilized)' : '(Elevated)'}
                          </span>
                        )}
                        {!isResolved && isMemIncident && (
                          <span style={{ 
                            fontSize: '11px', 
                            padding: '1px 7px', 
                            borderRadius: '4px',
                            background: Number(metrics.memory_percent || 0) < 85 ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                            color: Number(metrics.memory_percent || 0) < 85 ? '#4ade80' : '#f87171',
                            fontWeight: 600
                          }}>
                            Live RAM: {Number(metrics.memory_percent || 0).toFixed(1)}% {Number(metrics.memory_percent || 0) < 85 ? '(Stabilized)' : '(Elevated)'}
                          </span>
                        )}
                        {isResolved && (
                          <span style={{ fontSize: '11px', color: '#4ade80' }}>
                            ✓ Stabilized & Resolved
                          </span>
                        )}
                      </div>
                    </div>

                    <span className={badgeClass}>
                      {incident.status}
                    </span>
                    
                    <button className="button button-primary" style={{marginLeft: 15}} onClick={() => {
                      setSelectedIncidentId(incident.id);
                      setActivePage("incident_details");
                    }}>
                      View Details
                    </button>
                  </div>
                );
              }
            )

          )}

        </div>

      </>

    );

  }


  // ============================================
  // LOGS PAGE
  // ============================================

  function LogsPage() {

    const selectedContainer = containers.find(c => c.id === selectedContainerId);
    const containerName = selectedContainer ? selectedContainer.name : "Container";

    useEffect(() => {
      if (logTab === "app") {
        loadAppLogs();
      }
    }, [logTab]);

    return (

      <>

        <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>

          <div>

            <h2>
              System &amp; Application Logs
            </h2>

            <p>
              Real-time telemetry, error tracking, and container diagnostics.
            </p>

          </div>

          <div style={{ display: 'flex', gap: 8, background: '#1e293b', padding: 4, borderRadius: 8 }}>
            <button
              onClick={() => setLogTab("app")}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                background: logTab === "app" ? '#0284c7' : 'transparent',
                color: logTab === "app" ? '#ffffff' : '#94a3b8',
                transition: 'all 0.2s'
              }}
            >
              📄 Application Logs ({appLogs ? appLogs.split('\n').filter(Boolean).length : 0})
            </button>
            <button
              onClick={() => setLogTab("docker")}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                background: logTab === "docker" ? '#0284c7' : 'transparent',
                color: logTab === "docker" ? '#ffffff' : '#94a3b8',
                transition: 'all 0.2s'
              }}
            >
              🐳 Docker Logs ({containers.length})
            </button>
          </div>

        </div>

        {logTab === "app" && (
          <div style={{
            background: '#1e293b',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12
          }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Quick Test Simulation:</span>
              <button
                className="button"
                style={{ padding: '6px 12px', fontSize: '0.8rem', background: '#334155', color: '#f8fafc', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                onClick={() => handleInjectLog("INFO", "Routine healthcheck passed successfully.", "application")}
              >
                + Inject INFO
              </button>
              <button
                className="button"
                style={{ padding: '6px 12px', fontSize: '0.8rem', background: '#b45309', color: '#fef3c7', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                onClick={() => handleInjectLog("WARNING", "High memory buffer threshold reached (82%).", "memory")}
              >
                + Inject WARNING
              </button>
              <button
                className="button"
                style={{ padding: '6px 12px', fontSize: '0.8rem', background: '#dc2626', color: '#fee2e2', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                onClick={() => handleInjectLog("ERROR", "Connection refused to database pool MySQL on port 3306", "database")}
              >
                🚨 Inject ERROR (Triggers Incident)
              </button>
              <button
                className="button"
                style={{ padding: '6px 12px', fontSize: '0.8rem', background: '#475569', color: '#e2e8f0', border: 'none', borderRadius: 4, cursor: 'pointer' }}
                onClick={handleClearAppLogs}
              >
                Clear Log File
              </button>
            </div>
            {injectStatus && (
              <span style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 500 }}>
                {injectStatus}
              </span>
            )}
          </div>
        )}

        {logTab === "docker" && containers.length > 0 && (
          <div style={{
            background: '#1e293b',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 12
          }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Select Container:</span>
            <select
              value={selectedContainerId || ""}
              onChange={(e) => handleLogs(e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: 4,
                border: '1px solid #475569',
                background: '#0f172a',
                color: '#f8fafc',
                cursor: 'pointer'
              }}
            >
              <option value="" disabled>Choose a container...</option>
              {containers.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.status})
                </option>
              ))}
            </select>
          </div>
        )}

        {logTab === "docker" && containers.length === 0 && (
          <div style={{
            background: '#1e293b',
            padding: '16px 20px',
            borderRadius: 8,
            marginBottom: 16,
            color: '#cbd5e1',
            borderLeft: '4px solid #f59e0b'
          }}>
            <strong>Docker is currently unavailable or has no active containers.</strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
              Docker Desktop is not running on this machine. You can view all real-time system logs under the <strong>Application Logs</strong> tab above.
            </p>
          </div>
        )}

        <LogViewer
          logs={logTab === "app" ? appLogs : logs}
          containerName={logTab === "app" ? "application.log" : containerName}
          onRefresh={logTab === "app" ? loadAppLogs : () => selectedContainerId && handleLogs(selectedContainerId)}
        />

      </>

    );

  }


  // ============================================
  // AI PAGE
  // ============================================

  function AIPage() {

    const isCritical =
      report.overall_health ===
      "CRITICAL";


    return (

      <>

        <div className="page-heading">

          <div>

            <h2>
              AI Incident Analysis
            </h2>

            <p>
              AI-generated infrastructure health assessment.
            </p>

          </div>

        </div>


        <div className="ai-dashboard">


          {/* AI MAIN CARD */}

          <div
            className={
              isCritical
                ? "ai-main-card critical"
                : "ai-main-card"
            }
          >

            <FaRobot size={45} />


            <h2>

              {
                report.overall_health ||
                "UNKNOWN"
              }

            </h2>


            <p>

              Analysis confidence:

              {" "}

              <strong>

                {
                  report.confidence || 0
                }%

              </strong>

            </p>

          </div>


          {/* DETECTED PROBLEMS */}

          <div className="panel">

            <h3>
              Detected Problems
            </h3>


            {
              report.detected_problems?.length
                ? (

                  <ul>

                    {
                      report.detected_problems.map(
                        (problem, index) => (

                          <li
                            key={index}
                          >
                            {problem}
                          </li>

                        )
                      )
                    }

                  </ul>

                )
                : (

                  <p>
                    No problems detected.
                  </p>

                )
            }

          </div>


          {/* RECOMMENDATIONS */}

          <div className="panel">

            <h3>
              Recommended Actions
            </h3>


            {
              report.recommended_actions?.length
                ? (

                  <ul>

                    {
                      report.recommended_actions.map(
                        (action, index) => (

                          <li
                            key={index}
                          >
                            {action}
                          </li>

                        )
                      )
                    }

                  </ul>

                )
                : (

                  <p>
                    No recommendations available.
                  </p>

                )
            }

          </div>

        </div>

      </>

    );

  }


  // ============================================
  // SETTINGS PAGE
  // ============================================

  function SettingsPage() {

    return (

      <>

        <div className="page-heading">

          <div>

            <h2>
              Settings
            </h2>

            <p>
              AI Incident Commander configuration.
            </p>

          </div>

        </div>


        <div className="panel">

          <h3>
            System Configuration
          </h3>


          <div className="setting-row">

            <span>
              Auto Refresh
            </span>

            <strong>
              5 seconds
            </strong>

          </div>


          <div className="setting-row">

            <span>
              Backend
            </span>

            <strong>
              127.0.0.1:5000
            </strong>

          </div>


          <div className="setting-row">

            <span>
              Monitoring
            </span>

            <strong className="text-green">
              Enabled
            </strong>

          </div>

        </div>

      </>

    );

  }


  // ============================================
  // PAGE ROUTER
  // ============================================

  function renderPage() {

    switch (activePage) {

      case "incidents":
        return <IncidentsPage />;

      case "docker":
        return <DockerPage />;

      case "logs":
        return <LogsPage />;

      case "ai":
        return <AIPage />;

      case "settings":
        return <SettingsPage />;

      case "incident_details":
        return <IncidentDetails incidentId={selectedIncidentId} currentMetrics={metrics} onBack={() => setActivePage("incidents")} />;

      default:
        return <DashboardPage />;

    }

  }


  // ============================================
  // MAIN UI
  // ============================================

  return (

    <div className="app-layout">


      {/* SIDEBAR */}

      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />


      {/* MAIN */}

      <main className="main-content">


        {/* TOP BAR */}

        <TopBar
          metrics={metrics}
          incidents={incidents}
          onRefresh={loadDashboard}
          loading={loading}
        />


        {/* CONTENT */}

        <div className="content-area">


          {/* ERROR */}

          {error && (

            <div className="error-banner">

              ⚠️ {error}

            </div>

          )}


          {/* PAGE */}

          {renderPage()}


        </div>

      </main>

    </div>

  );

}


export default App;