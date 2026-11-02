import {
  FaTachometerAlt,
  FaExclamationTriangle,
  FaDocker,
  FaFileAlt,
  FaRobot,
  FaCog,
} from "react-icons/fa";

function Sidebar({ activePage, setActivePage }) {
  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <FaTachometerAlt />,
    },
    {
      id: "incidents",
      label: "Incidents",
      icon: <FaExclamationTriangle />,
    },
    {
      id: "docker",
      label: "Docker",
      icon: <FaDocker />,
    },
    {
      id: "logs",
      label: "Logs",
      icon: <FaFileAlt />,
    },
    {
      id: "ai",
      label: "AI Analysis",
      icon: <FaRobot />,
    },
    {
      id: "settings",
      label: "Settings",
      icon: <FaCog />,
    },
  ];

  return (
    <aside className="sidebar">

      <div className="sidebar-logo">
        <div className="logo-icon">
          AI
        </div>

        <div>
          <h2>Incident</h2>
          <span>Commander</span>
        </div>
      </div>

      <div className="sidebar-section-title">
        OPERATIONS
      </div>

      <nav className="sidebar-menu">

        {menuItems.map((item) => (

          <button
            key={item.id}
            className={
              activePage === item.id
                ? "sidebar-item active"
                : "sidebar-item"
            }
            onClick={() => setActivePage(item.id)}
          >

            <span className="sidebar-icon">
              {item.icon}
            </span>

            <span>
              {item.label}
            </span>

          </button>

        ))}

      </nav>

      <div className="sidebar-footer">

        <div className="system-status">

          <span className="status-dot"></span>

          <div>
            <strong>System Online</strong>
            <small>Monitoring active</small>
          </div>

        </div>

        <div className="sidebar-version">
          AI Commander v1.0
        </div>

      </div>

    </aside>
  );
}

export default Sidebar;