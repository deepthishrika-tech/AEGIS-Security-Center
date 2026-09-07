import { useEffect, useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const savedToken = localStorage.getItem("aegis_token");

  const [page, setPage] = useState(
    window.location.pathname === "/dashboard" && savedToken
      ? "dashboard"
      : "login"
  );

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [token, setToken] = useState(savedToken);

  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("aegis_user") || "null")
  );

  const [dashboard, setDashboard] = useState(null);
  const [history, setHistory] = useState([]);

  /* =========================================================
     INTERACTION STATE
     ========================================================= */

  const [activeSection, setActiveSection] =
    useState("Command Center");

  const [showNotifications, setShowNotifications] =
    useState(false);

  const [showSearch, setShowSearch] =
    useState(false);

  const [showOperational, setShowOperational] =
    useState(false);

  const [selectedAlert, setSelectedAlert] =
    useState(null);

  const [selectedStatus, setSelectedStatus] =
    useState(null);

  const [searchText, setSearchText] =
    useState("");

  const [currentTime, setCurrentTime] =
    useState(new Date());

  /* =========================================================
     LIVE CLOCK
     ========================================================= */

  useEffect(() => {
    const clock = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(clock);
  }, []);

  /* =========================================================
     LOGIN
     ========================================================= */

  const handleLogin = async (e) => {
    e.preventDefault();

    setError("");

    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username.trim(),
            password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            "Invalid username or password."
        );
      }

      const receivedToken =
        data.access_token ||
        data.token ||
        data.accessToken;

      if (!receivedToken) {
        throw new Error(
          "Login succeeded but no authentication token was returned."
        );
      }

      const loggedInUser =
        data.user || {
          username: username.trim(),
          role: data.role || "SECURITY_ADMIN",
        };

      localStorage.setItem(
        "aegis_token",
        receivedToken
      );

      localStorage.setItem(
        "aegis_user",
        JSON.stringify(loggedInUser)
      );

      setToken(receivedToken);
      setUser(loggedInUser);
      setPage("dashboard");

      setActiveSection("Command Center");

      window.history.pushState(
        {},
        "",
        "/dashboard"
      );
    } catch (err) {
      console.error("Login error:", err);

      setError(
        err.message ||
          "Unable to connect to authentication server."
      );
    } finally {
      setLoading(false);
    }
  };

  /* =========================================================
     LOAD DASHBOARD
     ========================================================= */

  const loadDashboard = async () => {
    if (!token) {
      setPage("login");
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/dashboard`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        logout();
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to load dashboard."
        );
      }

      setDashboard(data);
    } catch (err) {
      console.error(
        "Dashboard error:",
        err
      );
    }
  };
  /* =========================================================
   LOAD DASHBOARD HISTORY
   ========================================================= */

const loadHistory = async () => {
  if (!token) {
    return;
  }

  try {
    const response = await fetch(
      `${API_URL}/api/history`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        "Unable to load dashboard history."
      );
    }

    const data = await response.json();

    setHistory(data.history || []);
  } catch (err) {
    console.error(
      "History error:",
      err
    );
  }
};

  /* =========================================================
     AUTO REFRESH
     ========================================================= */

  useEffect(() => {
  if (page === "dashboard" && token) {
    loadDashboard();
    loadHistory();

    const interval = setInterval(() => {
      loadDashboard();
      loadHistory();
    }, 2000);

    return () =>
      clearInterval(interval);
  }
}, [page, token]);
  /* =========================================================
     LOGOUT
     ========================================================= */

 const logout = async () => {
  const currentToken = token;

  try {
    if (currentToken) {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${currentToken}`,
        },
      });
    }
  } catch (err) {
    console.error("Logout logging error:", err);
  } finally {
    localStorage.removeItem("aegis_token");
    localStorage.removeItem("aegis_user");

    setToken(null);
    setUser(null);
    setDashboard(null);

    setShowNotifications(false);
    setShowSearch(false);
    setShowOperational(false);

    setPage("login");

    window.history.pushState({}, "", "/");
  }
};
  /* =========================================================
     NAVIGATION
     ========================================================= */

  const handleNavigation = (section) => {
    setActiveSection(section);

    setShowNotifications(false);
    setShowSearch(false);
    setShowOperational(false);
    setSelectedAlert(null);
    setSelectedStatus(null);
  };

  /* =========================================================
     SEARCH
     ========================================================= */

  const searchItems = [
    "Command Center",
    "Threat Intelligence",
    "Asset Matrix",
    "Executive Intelligence",
    "System Observatory",
    "AI Tool Fingerprint Detected",
    "Sequential Port Scanning",
    "Abnormal Request Burst",
    "Unusual Payload Structure",
    "Detection Engine",
    "FastAPI Backend",
    "Database",
    "Threat Simulator",
  ];

  const filteredSearchItems = searchItems.filter(
    (item) =>
      item
        .toLowerCase()
        .includes(searchText.toLowerCase())
  );

  const handleSearchSelect = (item) => {
    // Dashboard sections
    if (
      item === "Command Center" ||
      item === "Threat Intelligence" ||
      item === "Asset Matrix" ||
      item === "Executive Intelligence" ||
      item === "System Observatory"
    ) {
      handleNavigation(item);
    }

    // Security alerts
    else if (item === "AI Tool Fingerprint Detected") {
      setSelectedAlert({
        alert: "AI Tool Fingerprint Detected",
        description: "Adaptive request patterns",
        severity: "Critical",
        source: "192.168.1.42",
        time: "2m ago",
        status: "Investigating",
      });
    }

    else if (item === "Sequential Port Scanning") {
      setSelectedAlert({
        alert: "Sequential Port Scanning",
        description: "Multiple ports probed",
        severity: "High",
        source: "10.0.0.24",
        time: "5m ago",
        status: "Blocked",
      });
    }

    else if (item === "Abnormal Request Burst") {
      setSelectedAlert({
        alert: "Abnormal Request Burst",
        description: "High request frequency",
        severity: "Medium",
        source: "172.16.0.18",
        time: "9m ago",
        status: "Monitoring",
      });
    }

    else if (item === "Unusual Payload Structure") {
      setSelectedAlert({
        alert: "Unusual Payload Structure",
        description: "Encoded request detected",
        severity: "High",
        source: "192.168.1.87",
        time: "14m ago",
        status: "Blocked",
      });
    }

    // System components
    else if (item === "Detection Engine") {
      setSelectedStatus({
        name: "Detection Engine",
        value: "Healthy",
        description: "AI detection engine is operating normally.",
      });
    }

    else if (item === "FastAPI Backend") {
      setSelectedStatus({
        name: "FastAPI Backend",
        value: "Healthy",
        description: "Backend API is responding normally.",
      });
    }

    else if (item === "Database") {
      setSelectedStatus({
        name: "Database",
        value: "Healthy",
        description: "Database connection is currently available.",
      });
    }

    else if (item === "Threat Simulator") {
      setSelectedStatus({
        name: "Threat Simulator",
        value: "Warning",
        description: "Threat simulator requires attention.",
      });
    }

    // Reset search panel after selection
    setSearchText("");
    setShowSearch(false);
  };

  /* =========================================================
     LOGIN PAGE
     ========================================================= */

  if (page === "login") {
    return (
      <div className="aegis-page">

        <div className="login-card">

          <div className="brand">

            <div className="brand-icon">
              ◆
            </div>

            <div>

              <div className="brand-name">
                AEGIS
              </div>

              <div className="brand-subtitle">
                SECURITY CENTER
              </div>

            </div>

          </div>

          <div className="secure-badge">
            <span className="status-dot"></span>
            SECURE AUTHENTICATION GATEWAY
          </div>

          <div className="login-header">

            <div className="authorized">
              AUTHORIZED PERSONNEL ONLY
            </div>

            <h1>
              Security
              <br />
              Command Access
            </h1>

            <p>
              Authenticate to access the AEGIS
              AI Attack Detection and Response Center.
            </p>

          </div>

          <form
            onSubmit={handleLogin}
            className="login-form"
          >

            <label>USERNAME</label>

            <div className="input-wrapper">

              <span className="input-icon">
                ◉
              </span>

              <input
                type="text"
                placeholder="Enter authorized username"
                value={username}
                onChange={(e) =>
                  setUsername(e.target.value)
                }
                autoComplete="username"
              />

            </div>

            <label>PASSWORD</label>

            <div className="input-wrapper">

              <span className="input-icon">
                ◆
              </span>

              <input
                type="password"
                placeholder="Enter secure password"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                autoComplete="current-password"
              />

            </div>

            {error && (
              <div className="login-error">
                <span>⚠</span>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="login-button"
              disabled={loading}
            >
              {loading
                ? "AUTHENTICATING..."
                : "ACCESS SECURITY CENTER →"}
            </button>

          </form>

          <div className="security-features">

            <div className="security-box">

              <span>✓</span>

              <div>
                <strong>
                  Encrypted Session
                </strong>

                <small>
                  JWT authenticated access
                </small>
              </div>

            </div>

            <div className="security-box">

              <span>✓</span>

              <div>
                <strong>
                  Access Monitoring
                </strong>

                <small>
                  All activity is logged
                </small>
              </div>

            </div>

          </div>

          <div className="login-footer">
            AEGIS SECURITY CENTER
            <span>•</span>
            AUTHORIZED ACCESS ONLY
          </div>

        </div>

      </div>
    );
  }

  /* =========================================================
     DASHBOARD
     ========================================================= */

  return (
    <div className="dashboard-page">

      {/* =====================================================
          SIDEBAR
          ===================================================== */}

      <aside className="sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            ◆
          </div>

          <div>

            <div className="sidebar-title">
              AEGIS
            </div>

            <div className="sidebar-subtitle">
              COMMAND CENTER
            </div>

          </div>

        </div>

        <div className="sidebar-section">
          OPERATIONS
        </div>

        {/* COMMAND CENTER */}

        <button
          type="button"
          className={`sidebar-item ${
            activeSection === "Command Center"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigation("Command Center")
          }
        >

          <span>◈</span>

          <div>
            <strong>
              Command Center
            </strong>

            <small>
              Real-time security operations
            </small>
          </div>

        </button>

        {/* THREAT INTELLIGENCE */}

        <button
          type="button"
          className={`sidebar-item ${
            activeSection === "Threat Intelligence"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigation("Threat Intelligence")
          }
        >

          <span>△</span>

          <div>
            <strong>
              Threat Intelligence
            </strong>

            <small>
              Advanced threat analysis
            </small>
          </div>

        </button>

        {/* ASSET MATRIX */}

        <button
          type="button"
          className={`sidebar-item ${
            activeSection === "Asset Matrix"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigation("Asset Matrix")
          }
        >

          <span>▤</span>

          <div>
            <strong>
              Asset Matrix
            </strong>

            <small>
              Infrastructure management
            </small>
          </div>

        </button>

        {/* EXECUTIVE INTELLIGENCE */}

        <button
          type="button"
          className={`sidebar-item ${
            activeSection === "Executive Intelligence"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigation(
              "Executive Intelligence"
            )
          }
        >

          <span>▥</span>

          <div>
            <strong>
              Executive Intelligence
            </strong>

            <small>
              Strategic reporting
            </small>
          </div>

        </button>

        {/* SYSTEM OBSERVATORY */}

        <button
          type="button"
          className={`sidebar-item ${
            activeSection === "System Observatory"
              ? "active"
              : ""
          }`}
          onClick={() =>
            handleNavigation(
              "System Observatory"
            )
          }
        >

          <span>⌁</span>

          <div>
            <strong>
              System Observatory
            </strong>

            <small>
              Performance monitoring
            </small>
          </div>

        </button>

        <div className="sidebar-section">
          SYSTEM STATUS
        </div>

        {/* ALERT QUEUE */}

        <button
          type="button"
          style={clickableStyle}
          onClick={() =>
            setSelectedStatus({
              name: "Alert Queue",
              value:
                dashboard?.active_alerts ?? 47,
              description:
                "Current security alerts waiting for investigation.",
            })
          }
        >

          <div className="status-row">

            <span>
              Alert Queue
            </span>

            <span className="badge red">
              {dashboard?.active_alerts ?? 47}
            </span>

          </div>

        </button>

        {/* ACTIVE INCIDENTS */}

        <button
          type="button"
          style={clickableStyle}
          onClick={() =>
            setSelectedStatus({
              name: "Active Incidents",
              value:
                dashboard?.critical_risks ?? 12,
              description:
                "Currently active security incidents and risks.",
            })
          }
        >

          <div className="status-row">

            <span>
              Active Incidents
            </span>

            <span className="badge yellow">
              {dashboard?.critical_risks ?? 12}
            </span>

          </div>

        </button>

        {/* MONITORED ASSETS */}

        <button
          type="button"
          style={clickableStyle}
          onClick={() =>
            setSelectedStatus({
              name: "Monitored Assets",
              value:
                dashboard?.protected_assets ?? 2847,
              description:
                "Infrastructure assets currently monitored by AEGIS.",
            })
          }
        >

          <div className="status-row">

            <span>
              Monitored Assets
            </span>

            <span className="badge green">
              {dashboard?.protected_assets ?? 2847}
            </span>

          </div>

        </button>

        <div className="sidebar-bottom">

          <div className="logged-user">

            <div className="user-circle">

              {(user?.username || "AD")
                .substring(0, 2)
                .toUpperCase()}

            </div>

            <div>

              <strong>
                {user?.username || "Security Admin"}
              </strong>

              <small>
                {user?.role || "Administrator"}
              </small>

            </div>

            <button
              className="user-menu"
              onClick={logout}
              title="Sign out"
              type="button"
            >
              ⇥
            </button>

          </div>

        </div>

      </aside>

      {/* =====================================================
          MAIN CONTENT
          ===================================================== */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <div>

            <h1>
              {activeSection}
            </h1>

            <p>
              Real-time AI attack detection & security operations

              <span className="header-separator">
                •
              </span>

              {currentTime.toLocaleString()}
            </p>

          </div>

          <div className="header-actions">

            {/* OPERATIONAL */}

            <button
              type="button"
              className="operational"
              onClick={() =>
                setShowOperational(
                  !showOperational
                )
              }
            >

              <span></span>

              OPERATIONAL

            </button>

            {/* NOTIFICATIONS */}

            <button
              className="header-icon"
              type="button"
              onClick={() => {
                setShowNotifications(
                  !showNotifications
                );
                setShowSearch(false);
                setShowOperational(false);
              }}
            >

              ♟

              <b>
                3
              </b>

            </button>

            {/* SEARCH */}

            <button
              className="header-icon"
              type="button"
              onClick={() => {
                setShowSearch(
                  !showSearch
                );
                setShowNotifications(false);
                setShowOperational(false);
              }}
            >
              ⌕
            </button>

          </div>

        </header>

        {/* =====================================================
            COMMAND CENTER
            ===================================================== */}

        {activeSection === "Command Center" && (
          <>

            {/* STATISTICS */}

            <section className="stats-grid">

              <StatCard
                title="ACTIVE ALERTS"
                value={
                  dashboard?.active_alerts ?? 47
                }
                icon="▲"
                type="critical"
                change="↑ 12% from yesterday"
              />

              <StatCard
                title="PROTECTED ASSETS"
                value={
                  dashboard?.protected_assets ?? 2847
                }
                icon="⬟"
                type="success"
                change="↑ 3.2%"
              />

              <StatCard
                title="ATTACK SOURCES"
                value={
                  dashboard?.attack_sources ?? 23
                }
                icon="♟"
                type="info"
                change="↓ 2.1%"
                negative
              />

              <StatCard
                title="SYSTEM HEALTH"
                value={
                  dashboard
                    ? `${dashboard.system_health}%`
                    : "98.7%"
                }
                icon="⌁"
                type="success"
                change="↑ 0.3%"
              />

            </section>

            {/* ALERTS + HEALTH */}

            <section className="content-grid">

              {/* PRIORITY ALERTS */}

              <div className="panel alerts-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ⚠ &nbsp; Priority Alerts
                    </h2>

                    <span>
                      Latest detected security events
                    </span>

                  </div>

                  <span className="critical-count">
                    2 Critical
                  </span>

                </div>

                <div className="alerts-table">

                  <div className="table-header">
                    <span>ALERT</span>
                    <span>SEVERITY</span>
                    <span>SOURCE</span>
                    <span>TIME</span>
                    <span>STATUS</span>
                  </div>

                  <ClickableAlert
                    alert="AI Tool Fingerprint Detected"
                    description="Adaptive request patterns"
                    severity="Critical"
                    source="192.168.1.42"
                    time="2m ago"
                    status="Investigating"
                    onClick={setSelectedAlert}
                  />

                  <ClickableAlert
                    alert="Sequential Port Scanning"
                    description="Multiple ports probed"
                    severity="High"
                    source="10.0.0.24"
                    time="5m ago"
                    status="Blocked"
                    onClick={setSelectedAlert}
                  />

                  <ClickableAlert
                    alert="Abnormal Request Burst"
                    description="High request frequency"
                    severity="Medium"
                    source="172.16.0.18"
                    time="9m ago"
                    status="Monitoring"
                    onClick={setSelectedAlert}
                  />

                  <ClickableAlert
                    alert="Unusual Payload Structure"
                    description="Encoded request detected"
                    severity="High"
                    source="192.168.1.87"
                    time="14m ago"
                    status="Blocked"
                    onClick={setSelectedAlert}
                  />

                </div>

              </div>

              {/* SYSTEM HEALTH */}

              <div className="panel health-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ⌁ &nbsp; System Health
                    </h2>

                    <span>
                      Security services status
                    </span>

                  </div>

                </div>

                <div className="health-score">

                  <div className="health-ring">

                    <strong>
                      {dashboard?.system_health ?? 98.7}%
                    </strong>

                    <span>
                      Overall Health
                    </span>

                  </div>

                </div>

                <ServiceRow
                  name="Detection Engine"
                  status="Healthy"
                  onClick={() =>
                    setSelectedStatus({
                      name: "Detection Engine",
                      value: "Healthy",
                      description:
                        "AI detection engine is operating normally.",
                    })
                  }
                />

                <ServiceRow
                  name="FastAPI Backend"
                  status="Healthy"
                  onClick={() =>
                    setSelectedStatus({
                      name: "FastAPI Backend",
                      value: "Healthy",
                      description:
                        "Backend API is responding normally.",
                    })
                  }
                />

                <ServiceRow
                  name="Database"
                  status="Healthy"
                  onClick={() =>
                    setSelectedStatus({
                      name: "Database",
                      value: "Healthy",
                      description:
                        "Database connection is currently available.",
                    })
                  }
                />

                <ServiceRow
                  name="Threat Simulator"
                  status="Warning"
                  warning
                  onClick={() =>
                    setSelectedStatus({
                      name: "Threat Simulator",
                      value: "Warning",
                      description:
                        "Threat simulator requires attention.",
                    })
                  }
                />

              </div>

            </section>

            {/* THREAT DISTRIBUTION + RISK */}

            <section className="lower-grid">

              <div className="panel threat-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ▥ &nbsp; Threat Distribution
                    </h2>

                    <span>
                      Detected activity by category
                    </span>

                  </div>

                </div>

                <div className="threat-content">

                  <ThreatBar
                    label="AI Tools"
                    value={
                      dashboard?.threat_distribution?.ai_tools ?? 36
                    }
                    height="100%"
                    type="red"
                  />

                  <ThreatBar
                    label="Scanning"
                    value={
                      dashboard?.threat_distribution?.scanning ?? 28
                    }
                    height="78%"
                    type="orange"
                  />

                  <ThreatBar
                    label="Payloads"
                    value={
                      dashboard?.threat_distribution?.payloads ?? 16
                    }
                    height="52%"
                    type="yellow"
                  />

                  <ThreatBar
                    label="Auth"
                    value={
                      dashboard?.threat_distribution?.auth ?? 9
                    }
                    height="29%"
                    type="blue"
                  />

                  <ThreatBar
                    label="Other"
                    value={
                      dashboard?.threat_distribution?.other ?? 5
                    }
                    height="17%"
                    type="dark"
                  />

                </div>

              </div>

              {/* RISK */}

              <div className="panel risk-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ◈ &nbsp; Security Risk Score
                    </h2>

                    <span>
                      Current threat level
                    </span>

                  </div>

                </div>

                <div className="risk-score">

                  <div className="risk-ring">

                    <strong>
                      {dashboard?.risk_score ?? 92}
                    </strong>

                    <span>
                      / 100
                    </span>

                  </div>

                  <h3>
                    CRITICAL RISK
                  </h3>

                  <p>
                    Multiple high-confidence attack patterns detected.
                  </p>

                </div>

                <div className="risk-summary">

                  <div>

                    <span>
                      Critical Risks
                    </span>

                    <strong>
                      {dashboard?.critical_risks ?? 9}
                    </strong>

                  </div>

                  <div>

                    <span>
                      High Risks
                    </span>

                    <strong>
                      {dashboard?.high_risks ?? 17}
                    </strong>

                  </div>

                </div>

              </div>

            </section>

            {/* NETWORK + ANOMALIES */}

            <section className="activity-grid">

              <div className="panel network-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ⌁ &nbsp; Network Activity
                    </h2>

                    <span>
                      Real-time traffic behaviour
                    </span>

                  </div>

                  <span className="live-label">
                    ● LIVE
                  </span>

                </div>

                <div className="network-chart">

                  <div className="grid-lines"></div>

                  <svg
                    viewBox="0 0 1000 240"
                    preserveAspectRatio="none"
                  >

                    <polyline
                      points="
                        0,160
                        80,170
                        150,130
                        220,150
                        300,85
                        370,125
                        450,45
                        520,105
                        600,70
                        680,125
                        760,45
                        840,90
                        920,70
                        1000,35
                      "
                      fill="none"
                      stroke="#438cff"
                      strokeWidth="3"
                    />

                    <polyline
                      points="
                        0,205
                        80,180
                        150,195
                        220,205
                        300,130
                        370,160
                        450,185
                        520,85
                        600,145
                        680,55
                        760,115
                        840,70
                        920,105
                        1000,25
                      "
                      fill="none"
                      stroke="#ff4f5c"
                      strokeWidth="3"
                    />

                  </svg>

                </div>

              </div>

              {/* ANOMALIES */}

              <div className="panel anomaly-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ⚡ &nbsp; Recent Anomalies
                    </h2>

                    <span>
                      Behavioural detection engine
                    </span>

                  </div>

                </div>

                <AnomalyRow
                  icon="ϟ"
                  name="Adaptive Request Burst"
                  source="192.168.1.42"
                  score="92"
                  type="red"
                  onClick={() =>
                    setSelectedAlert({
                      alert: "Adaptive Request Burst",
                      description:
                        "Adaptive request behaviour detected.",
                      severity: "Critical",
                      source: "192.168.1.42",
                      time: "Recent",
                      status: "Investigating",
                    })
                  }
                />

                <AnomalyRow
                  icon="⌘"
                  name="Sequential Scan"
                  source="10.0.0.24"
                  score="87"
                  type="orange"
                  onClick={() =>
                    setSelectedAlert({
                      alert: "Sequential Scan",
                      description:
                        "Sequential network scanning behaviour detected.",
                      severity: "High",
                      source: "10.0.0.24",
                      time: "Recent",
                      status: "Blocked",
                    })
                  }
                />

                <AnomalyRow
                  icon="</>"
                  name="Payload Anomaly"
                  source="172.16.0.18"
                  score="71"
                  type="yellow"
                  onClick={() =>
                    setSelectedAlert({
                      alert: "Payload Anomaly",
                      description:
                        "Unusual payload structure detected.",
                      severity: "Medium",
                      source: "172.16.0.18",
                      time: "Recent",
                      status: "Monitoring",
                    })
                  }
                />

              </div>

            </section>

            {/* LIVE DASHBOARD HISTORY */}

            <section className="history-grid">

              <div className="panel history-panel">

                <div className="panel-header">

                  <div>

                    <h2>
                      ⏱ &nbsp; Live Dashboard History
                    </h2>

                    <span>
                      Real-time activity &amp; system events
                    </span>

                  </div>

                  <span className="live-label">
                    ● LIVE
                  </span>

                </div>

                <div className="history-list">

                  {history.length === 0 && (
                    <div className="history-empty">
                      No history events yet.
                    </div>
                  )}

                  {history.slice(0, 12).map((item) => (
                    <HistoryRow
                      key={item._id}
                      action={item.display_action}
                      username={item.display_username}
                      source={item.history_source}
                      timestamp={item.timestamp}
                    />
                  ))}

                </div>

              </div>

            </section>

          </>
        )}

        {/* =====================================================
            OTHER SECTIONS
            ===================================================== */}

        {activeSection !== "Command Center" && (
          <SectionView
            section={activeSection}
            dashboard={dashboard}
          />
        )}

        {/* FOOTER */}

        <div className="dashboard-footer">

          <span>
            AEGIS AI Attack Tool Detector v1.0.0
          </span>

          <span className="footer-live">
            ● Detection Engine Active
          </span>

        </div>

      </main>

      {/* =====================================================
          NOTIFICATION PANEL
          ===================================================== */}

      {showNotifications && (
        <FloatingPanel
          title="Notifications"
          onClose={() =>
            setShowNotifications(false)
          }
        >

          <NotificationItem
            title="Critical Alert"
            text="AI Tool Fingerprint Detected"
            time="2 minutes ago"
          />

          <NotificationItem
            title="High Severity"
            text="Sequential Port Scanning blocked"
            time="5 minutes ago"
          />

          <NotificationItem
            title="System"
            text="Detection Engine is Healthy"
            time="Just now"
          />

        </FloatingPanel>
      )}

      {/* =====================================================
          SEARCH PANEL
          ===================================================== */}

      {showSearch && (
        <FloatingPanel
          title="Search AEGIS"
          onClose={() =>
            setShowSearch(false)
          }
        >

          <input
            autoFocus
            value={searchText}
            onChange={(e) =>
              setSearchText(e.target.value)
            }
            placeholder="Search dashboard..."
            style={searchInputStyle}
          />

          <div style={{ marginTop: "12px" }}>

            {filteredSearchItems.map(
              (item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() =>
                    handleSearchSelect(item)
                  }
                  style={searchItemStyle}
                >
                  {item}
                </button>
              )
            )}

            {filteredSearchItems.length === 0 && (
              <div style={emptyStyle}>
                No matching result.
              </div>
            )}

          </div>

        </FloatingPanel>
      )}

      {/* =====================================================
          OPERATIONAL PANEL
          ===================================================== */}

      {showOperational && (
        <FloatingPanel
          title="System Operational Status"
          onClose={() =>
            setShowOperational(false)
          }
        >

          <div style={operationRowStyle}>
            <span>Detection Engine</span>
            <strong style={healthyText}>
              ● Healthy
            </strong>
          </div>

          <div style={operationRowStyle}>
            <span>FastAPI Backend</span>
            <strong style={healthyText}>
              ● Healthy
            </strong>
          </div>

          <div style={operationRowStyle}>
            <span>Database</span>
            <strong style={healthyText}>
              ● Connected
            </strong>
          </div>

          <div style={operationRowStyle}>
            <span>Threat Monitoring</span>
            <strong style={warningText}>
              ● Monitoring
            </strong>
          </div>

          <div style={operationRowStyle}>
            <span>Last Refresh</span>
            <strong>
              {currentTime.toLocaleTimeString()}
            </strong>
          </div>

        </FloatingPanel>
      )}

      {/* =====================================================
          ALERT DETAILS
          ===================================================== */}

      {selectedAlert && (
        <Modal
          title="Security Alert Details"
          onClose={() =>
            setSelectedAlert(null)
          }
        >

          <DetailRow
            label="Alert"
            value={selectedAlert.alert}
          />

          <DetailRow
            label="Description"
            value={selectedAlert.description}
          />

          <DetailRow
            label="Severity"
            value={selectedAlert.severity}
          />

          <DetailRow
            label="Source"
            value={selectedAlert.source}
          />

          <DetailRow
            label="Detected"
            value={selectedAlert.time}
          />

          <DetailRow
            label="Status"
            value={selectedAlert.status}
          />

          <div style={modalInfoStyle}>
            This event is currently displayed from
            the AEGIS security dashboard.
            In the next step, these events will
            also be recorded permanently in MongoDB.
          </div>

        </Modal>
      )}

      {/* =====================================================
          STATUS DETAILS
          ===================================================== */}

      {selectedStatus && (
        <Modal
          title="System Status"
          onClose={() =>
            setSelectedStatus(null)
          }
        >

          <DetailRow
            label="Component"
            value={selectedStatus.name}
          />

          <DetailRow
            label="Current Value"
            value={selectedStatus.value}
          />

          <DetailRow
            label="Description"
            value={selectedStatus.description}
          />

          <div style={modalInfoStyle}>
            Status information is currently
            retrieved from the active AEGIS
            dashboard state.
          </div>

        </Modal>
      )}

    </div>
  );
}


/* =========================================================
   STAT CARD
   ========================================================= */

function StatCard({
  title,
  value,
  icon,
  type,
  change,
  negative,
}) {
  return (
    <button
      type="button"
      className={`stat-card ${type}`}
      style={statButtonStyle}
    >

      <div>

        <span className="stat-title">
          {title}
        </span>

        <strong className="stat-value">
          {value}
        </strong>

        <span
          className={`stat-change ${
            negative ? "negative" : ""
          }`}
        >
          {change}
        </span>

      </div>

      <div className="stat-icon">
        {icon}
      </div>

    </button>
  );
}


/* =========================================================
   CLICKABLE ALERT
   ========================================================= */

function ClickableAlert({
  alert,
  description,
  severity,
  source,
  time,
  status,
  onClick,
}) {
  return (
    <button
      type="button"
      className="alert-row"
      style={alertButtonStyle}
      onClick={() =>
        onClick({
          alert,
          description,
          severity,
          source,
          time,
          status,
        })
      }
    >

      <div className="alert-name">

        <strong>
          {alert}
        </strong>

        <small>
          {description}
        </small>

      </div>

      <span
        className={`severity ${severity.toLowerCase()}`}
      >
        {severity}
      </span>

      <span className="alert-source">
        {source}
      </span>

      <span className="alert-time">
        {time}
      </span>

      <span
        className={`alert-status ${status.toLowerCase()}`}
      >
        {status}
      </span>

    </button>
  );
}


/* =========================================================
   SERVICE ROW
   ========================================================= */

function ServiceRow({
  name,
  status,
  warning = false,
  onClick,
}) {
  return (
    <button
      type="button"
      className="service-row"
      style={serviceButtonStyle}
      onClick={onClick}
    >

      <span
        className={
          warning
            ? "service-icon warning-icon"
            : "service-icon"
        }
      >
        {warning ? "!" : "✓"}
      </span>

      <strong>
        {name}
      </strong>

      <span
        className={`service-status ${
          warning ? "warning" : "healthy"
        }`}
      >
        {status}
      </span>

    </button>
  );
}


/* =========================================================
   THREAT BAR
   ========================================================= */

function ThreatBar({
  label,
  value,
  height,
  type,
}) {
  return (
    <div className="threat-bar">

      <div className="threat-number">
        {value}
      </div>

      <div className="bar-area">

        <div
          className={`bar-fill ${type}`}
          style={{
            height,
          }}
        ></div>

      </div>

      <span className="threat-label">
        {label}
      </span>

    </div>
  );
}


/* =========================================================
   ANOMALY ROW
   ========================================================= */

function AnomalyRow({
  icon,
  name,
  source,
  score,
  type,
  onClick,
}) {
  return (
    <button
      type="button"
      className="anomaly-row"
      style={anomalyButtonStyle}
      onClick={onClick}
    >

      <div
        className={`anomaly-icon ${type}`}
      >
        {icon}
      </div>

      <div className="anomaly-info">

        <strong>
          {name}
        </strong>

        <small>
          {source}
        </small>

      </div>

      <strong className="anomaly-score">
        {score}
      </strong>

    </button>
  );
}


/* =========================================================
   OTHER SECTION VIEW
   ========================================================= */

/* =========================================================
   DASHBOARD HISTORY ROW
   ========================================================= */

function HistoryRow({ action, username, source, timestamp }) {
  const tagClass = String(source || "system").toLowerCase();

  return (
    <div className="history-row">

      <div className="history-row-main">

        <span className={`history-source-tag ${tagClass}`}>
          {source || "SYSTEM"}
        </span>

        <span className="history-action">
          {action || "Event"}
        </span>

      </div>

      <div className="history-row-meta">

        <span>{username || "SYSTEM"}</span>

        <span>{formatRelativeTime(timestamp)}</span>

      </div>

    </div>
  );
}

function formatRelativeTime(timestamp) {
  if (!timestamp) {
    return "";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const diffSeconds = Math.max(
    0,
    Math.round((Date.now() - date.getTime()) / 1000)
  );

  if (diffSeconds < 5) {
    return "just now";
  }

  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  }

  const diffMinutes = Math.round(diffSeconds / 60);

  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);

  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.round(diffHours / 24);

  return `${diffDays}d ago`;
}

function SectionView({
  section,
  dashboard,
}) {
  const information = {
    "Threat Intelligence": {
      icon: "△",
      title: "Threat Intelligence",
      subtitle:
        "Advanced threat analysis and intelligence operations",
      items: [
        [
          "Active Threats",
          dashboard?.active_alerts ?? 47,
        ],
        [
          "Attack Sources",
          dashboard?.attack_sources ?? 23,
        ],
        [
          "Critical Risks",
          dashboard?.critical_risks ?? 9,
        ],
        [
          "High Risks",
          dashboard?.high_risks ?? 17,
        ],
      ],
    },

    "Asset Matrix": {
      icon: "▤",
      title: "Asset Matrix",
      subtitle:
        "Infrastructure and protected asset management",
      items: [
        [
          "Protected Assets",
          dashboard?.protected_assets ?? 2847,
        ],
        [
          "System Health",
          `${dashboard?.system_health ?? 98.7}%`,
        ],
        [
          "Monitored Systems",
          "Active",
        ],
        [
          "Infrastructure",
          "Operational",
        ],
      ],
    },

    "Executive Intelligence": {
      icon: "▥",
      title: "Executive Intelligence",
      subtitle:
        "Strategic security reporting and executive overview",
      items: [
        [
          "Risk Score",
          dashboard?.risk_score ?? 92,
        ],
        [
          "Critical Risks",
          dashboard?.critical_risks ?? 9,
        ],
        [
          "High Risks",
          dashboard?.high_risks ?? 17,
        ],
        [
          "Overall Health",
          `${dashboard?.system_health ?? 98.7}%`,
        ],
      ],
    },

    "System Observatory": {
      icon: "⌁",
      title: "System Observatory",
      subtitle:
        "Performance monitoring and service status",
      items: [
        [
          "Detection Engine",
          "Healthy",
        ],
        [
          "FastAPI Backend",
          "Healthy",
        ],
        [
          "Database",
          "Healthy",
        ],
        [
          "Threat Simulator",
          "Warning",
        ],
      ],
    },
  };

  const data =
    information[section] ||
    information["Threat Intelligence"];

  return (
    <section
      style={{
        marginTop: "28px",
      }}
    >

      <div
        className="panel"
        style={{
          padding: "28px",
          minHeight: "450px",
        }}
      >

        <div
          className="panel-header"
          style={{
            marginBottom: "30px",
          }}
        >

          <div>

            <h2>
              {data.icon} &nbsp; {data.title}
            </h2>

            <span>
              {data.subtitle}
            </span>

          </div>

          <span className="live-label">
            ● LIVE
          </span>

        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(2, minmax(220px, 1fr))",
            gap: "18px",
          }}
        >

          {data.items.map(
            ([label, value]) => (
              <div
                key={label}
                style={{
                  border:
                    "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "10px",
                  padding: "22px",
                  background:
                    "rgba(255,255,255,0.02)",
                }}
              >

                <div
                  style={{
                    fontSize: "12px",
                    letterSpacing: "1px",
                    color: "#7f94b2",
                    marginBottom: "12px",
                  }}
                >
                  {label}
                </div>

                <div
                  style={{
                    fontSize: "28px",
                    fontWeight: "700",
                    color: "#ffffff",
                  }}
                >
                  {value}
                </div>

                <div
                  style={{
                    marginTop: "10px",
                    fontSize: "12px",
                    color: "#19d88a",
                  }}
                >
                  ● Monitoring active
                </div>

              </div>
            )
          )}

        </div>

        <div
          style={{
            marginTop: "30px",
            padding: "18px",
            borderRadius: "8px",
            background:
              "rgba(67,140,255,0.06)",
            border:
              "1px solid rgba(67,140,255,0.15)",
            color: "#8fa8c7",
            fontSize: "13px",
            lineHeight: "1.7",
          }}
        >
          AEGIS is actively monitoring this
          operational area. The detailed backend
          event history will be connected to
          MongoDB in the next stage.
        </div>

      </div>

    </section>
  );
}


/* =========================================================
   NOTIFICATION ITEM
   ========================================================= */

function NotificationItem({
  title,
  text,
  time,
}) {
  return (
    <div
      style={{
        padding: "14px 0",
        borderBottom:
          "1px solid rgba(255,255,255,0.08)",
      }}
    >

      <strong
        style={{
          display: "block",
          color: "#ffffff",
          marginBottom: "5px",
        }}
      >
        {title}
      </strong>

      <span
        style={{
          display: "block",
          color: "#8fa8c7",
          fontSize: "13px",
        }}
      >
        {text}
      </span>

      <small
        style={{
          display: "block",
          marginTop: "5px",
          color: "#60758f",
        }}
      >
        {time}
      </small>

    </div>
  );
}


/* =========================================================
   FLOATING PANEL
   ========================================================= */

function FloatingPanel({
  title,
  children,
  onClose,
}) {
  return (
    <div style={floatingPanelStyle}>

      <div style={floatingHeaderStyle}>

        <strong>
          {title}
        </strong>

        <button
          type="button"
          onClick={onClose}
          style={closeButtonStyle}
        >
          ×
        </button>

      </div>

      <div>
        {children}
      </div>

    </div>
  );
}


/* =========================================================
   MODAL
   ========================================================= */

function Modal({
  title,
  children,
  onClose,
}) {
  return (
    <div style={modalOverlayStyle}>

      <div style={modalStyle}>

        <div style={modalHeaderStyle}>

          <strong>
            {title}
          </strong>

          <button
            type="button"
            onClick={onClose}
            style={closeButtonStyle}
          >
            ×
          </button>

        </div>

        <div>
          {children}
        </div>

      </div>

    </div>
  );
}


/* =========================================================
   DETAIL ROW
   ========================================================= */

function DetailRow({
  label,
  value,
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: "20px",
        padding: "13px 0",
        borderBottom:
          "1px solid rgba(255,255,255,0.07)",
      }}
    >

      <span
        style={{
          color: "#7188a5",
          fontSize: "13px",
        }}
      >
        {label}
      </span>

      <strong
        style={{
          color: "#ffffff",
          fontSize: "13px",
          textAlign: "right",
        }}
      >
        {value}
      </strong>

    </div>
  );
}


/* =========================================================
   INLINE STYLES
   These styles only make existing dashboard elements
   clickable without changing the dashboard design.
   ========================================================= */

const clickableStyle = {
  width: "100%",
  border: "none",
  background: "transparent",
  padding: 0,
  margin: 0,
  cursor: "pointer",
  color: "inherit",
  textAlign: "left",
};

const statButtonStyle = {
  border: "none",
  textAlign: "left",
  cursor: "pointer",
  width: "100%",
  font: "inherit",
};

const alertButtonStyle = {
  width: "100%",
  border: "none",
  cursor: "pointer",
  textAlign: "left",
  color: "inherit",
  font: "inherit",
};

const serviceButtonStyle = {
  width: "100%",
  border: "none",
  cursor: "pointer",
  color: "inherit",
  font: "inherit",
  textAlign: "left",
};

const anomalyButtonStyle = {
  width: "100%",
  border: "none",
  cursor: "pointer",
  color: "inherit",
  font: "inherit",
  textAlign: "left",
};

const floatingPanelStyle = {
  position: "fixed",
  top: "82px",
  right: "28px",
  width: "360px",
  maxHeight: "520px",
  overflowY: "auto",
  zIndex: 1000,
  background: "#0d1117",
  border:
    "1px solid rgba(255,255,255,0.12)",
  borderRadius: "12px",
  padding: "18px",
  boxShadow:
    "0 20px 60px rgba(0,0,0,0.55)",
};

const floatingHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  paddingBottom: "15px",
  marginBottom: "8px",
  borderBottom:
    "1px solid rgba(255,255,255,0.08)",
  color: "#ffffff",
};

const closeButtonStyle = {
  border: "none",
  background: "transparent",
  color: "#8fa8c7",
  fontSize: "25px",
  cursor: "pointer",
  lineHeight: 1,
};

const searchInputStyle = {
  width: "100%",
  padding: "12px 14px",
  borderRadius: "7px",
  border:
    "1px solid rgba(255,255,255,0.12)",
  background: "#080b10",
  color: "#ffffff",
  outline: "none",
  fontSize: "14px",
};

const searchItemStyle = {
  width: "100%",
  display: "block",
  padding: "11px 12px",
  border: "none",
  borderRadius: "6px",
  background: "transparent",
  color: "#c8d5e5",
  textAlign: "left",
  cursor: "pointer",
  fontSize: "13px",
};

const emptyStyle = {
  color: "#7188a5",
  padding: "15px 0",
  fontSize: "13px",
};

const operationRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "13px 0",
  borderBottom:
    "1px solid rgba(255,255,255,0.07)",
  color: "#c8d5e5",
  fontSize: "13px",
};

const healthyText = {
  color: "#19d88a",
};

const warningText = {
  color: "#ffc857",
};

const modalOverlayStyle = {
  position: "fixed",
  inset: 0,
  zIndex: 2000,
  background:
    "rgba(0,0,0,0.72)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  padding: "20px",
};

const modalStyle = {
  width: "520px",
  maxWidth: "100%",
  background: "#0d1117",
  border:
    "1px solid rgba(255,255,255,0.13)",
  borderRadius: "12px",
  padding: "22px",
  boxShadow:
    "0 30px 90px rgba(0,0,0,0.65)",
};

const modalHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: "18px",
  paddingBottom: "15px",
  borderBottom:
    "1px solid rgba(255,255,255,0.08)",
  color: "#ffffff",
  fontSize: "17px",
};

const modalInfoStyle = {
  marginTop: "18px",
  padding: "13px",
  borderRadius: "7px",
  background:
    "rgba(67,140,255,0.06)",
  border:
    "1px solid rgba(67,140,255,0.12)",
  color: "#7f94b2",
  fontSize: "12px",
  lineHeight: "1.6",
};


/* =========================================================
   EXPORT
   ========================================================= */

export default App;