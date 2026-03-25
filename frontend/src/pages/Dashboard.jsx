import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import api from "../api/client";
import useAuthStore from "../store/authStore";
import ChatPanel from "../components/Chatpanel";
import PredictionPanel from "../components/Predictionpanel";
import AlertPanel from "../components/Alertpanel";
import ManageZones from "../components/ManageZones";
import UsersPanel from "../components/UsersPanel";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const RISK_COLORS = {
  LOW:      "#22c55e",
  MEDIUM:   "#f59e0b",
  HIGH:     "#ef4444",
  CRITICAL: "#7c3aed",
};

function getRiskFromProb(prob) {
  if (prob >= 0.9) return "CRITICAL";
  if (prob >= 0.7) return "HIGH";
  if (prob >= 0.3) return "MEDIUM";
  return "LOW";
}

function riskIcon(level) {
  const color = RISK_COLORS[level] || "#22c55e";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
    <circle cx="16" cy="16" r="14" fill="${color}" opacity="0.15"/>
    <circle cx="16" cy="16" r="8"  fill="${color}" opacity="0.9"/>
    <circle cx="16" cy="16" r="4"  fill="white"    opacity="0.6"/>
  </svg>`;
  return L.divIcon({ html: svg, className: "", iconSize: [32,32], iconAnchor: [16,16] });
}

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }

  .dash { display: flex; height: 100vh; background: #060a0f; font-family: 'DM Sans', sans-serif; overflow: hidden; }

  .sidebar {
    width: 280px; flex-shrink: 0; background: #0b1120;
    border-right: 1px solid rgba(255,255,255,0.05);
    display: flex; flex-direction: column; padding: 0; overflow: hidden;
    position: relative; z-index: 10;
  }
  .sidebar-top { padding: 28px 24px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .sidebar-brand { display: flex; align-items: center; gap: 10px; margin-bottom: 24px; }
  .brand-icon { font-size: 18px; line-height: 1; }
  .brand-name { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 800; color: #fff; }
  .brand-name span { color: #00c8ff; }
  .live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,200,255,0.08); border: 1px solid rgba(0,200,255,0.15);
    border-radius: 100px; padding: 4px 10px; margin-bottom: 20px;
  }
  .live-dot { width: 6px; height: 6px; border-radius: 50%; background: #00c8ff; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.4)} }
  .live-badge span { color: #00c8ff; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; }
  .user-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 14px 16px; }
  .user-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .user-name { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: #f1f5f9; }
  .role-pill { font-size: 10px; font-weight: 700; letter-spacing: 1px; padding: 3px 9px; border-radius: 100px; }
  .role-PUBLIC  { background: rgba(0,200,255,0.15);  color: #00c8ff;  border: 1px solid rgba(0,200,255,0.25); }
  .role-RESCUE  { background: rgba(245,158,11,0.15); color: #f59e0b;  border: 1px solid rgba(245,158,11,0.25); }
  .role-ADMIN   { background: rgba(255,77,109,0.15); color: #ff4d6d;  border: 1px solid rgba(255,77,109,0.25); }
  .user-team { color: #4a6280; font-size: 12px; }
  .sidebar-nav { flex: 1; padding: 20px 16px; overflow-y: auto; }
  .nav-label { color: #2a3a4a; font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; padding: 0 8px; }
  .nav-item {
    display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 10px;
    color: #4a6280; font-size: 14px; cursor: pointer; transition: all 0.15s; margin-bottom: 2px; border: 1px solid transparent;
  }
  .nav-item:hover { background: rgba(255,255,255,0.04); color: #94a3b8; }
  .nav-item.active { background: rgba(0,200,255,0.08); color: #00c8ff; border-color: rgba(0,200,255,0.15); }
  .nav-icon { font-size: 16px; width: 20px; text-align: center; }
  .divider { height: 1px; background: rgba(255,255,255,0.05); margin: 12px 0; }
  .zone-list { padding: 0 8px; }
  .zone-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 4px; border-bottom: 1px solid rgba(255,255,255,0.04); cursor: pointer; transition: opacity 0.15s;
  }
  .zone-row:hover { opacity: 0.8; }
  .zone-row-left { display: flex; align-items: center; gap: 8px; }
  .zone-risk-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .zone-row-name { color: #94a3b8; font-size: 13px; }
  .zone-row-code { color: #2a3a4a; font-size: 11px; font-family: monospace; }
  .no-zones { color: #2a3a4a; font-size: 12px; font-style: italic; padding: 0 8px; }
  .sidebar-bottom { padding: 16px; border-top: 1px solid rgba(255,255,255,0.05); }
  .logout-btn {
    width: 100%; padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.07);
    background: transparent; color: #4a6280; font-family: 'DM Sans', sans-serif; font-size: 13px; cursor: pointer; transition: all 0.15s;
  }
  .logout-btn:hover { border-color: rgba(255,77,109,0.3); color: #ff4d6d; background: rgba(255,77,109,0.05); }

  .main { flex: 1; min-width: 0; display: flex; flex-direction: column; overflow: hidden; }
  .topbar {
    height: 60px; flex-shrink: 0; background: #0b1120;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
  }
  .topbar-title { font-family: 'Syne', sans-serif; font-size: 16px; font-weight: 700; color: #fff; }
  .topbar-right { display: flex; align-items: center; gap: 16px; }
  .stat-chip {
    display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 14px;
  }
  .stat-chip-dot { width: 7px; height: 7px; border-radius: 50%; }
  .stat-chip-label { color: #4a6280; font-size: 12px; }
  .stat-chip-val { color: #fff; font-size: 12px; font-weight: 600; }

  /* Panel content area */
  .content-area { flex: 1; min-height: 0; overflow-y: auto; position: relative; }
  .panel-scroll { padding: 24px; max-width: 1100px; }

  /* Map */
  .map-wrap { flex: 1; min-height: 0; position: relative; overflow: hidden; }
  .admin-fab { position: absolute; bottom: 24px; right: 24px; z-index: 1000; display: flex; flex-direction: column; gap: 10px; }
  .fab-btn { display: flex; align-items: center; gap: 10px; padding: 12px 20px; border-radius: 12px; border: none; font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
  .fab-primary { background: rgba(0,200,255,0.9); color: #060a0f; }
  .fab-primary:hover { background: #00c8ff; transform: translateY(-2px); }
  .risk-legend { position: absolute; bottom: 24px; left: 16px; z-index: 1000; background: rgba(11,17,32,0.9); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px 16px; display: flex; flex-direction: column; gap: 6px; }
  .legend-title { color: #4a6280; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }
  .legend-row { display: flex; align-items: center; gap: 8px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
  .legend-label { color: #94a3b8; font-size: 12px; }

  .leaflet-popup-content-wrapper { background: #0f1f35 !important; border: 1px solid rgba(0,200,255,0.2) !important; border-radius: 12px !important; color: #fff !important; box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important; }
  .leaflet-popup-tip { background: #0f1f35 !important; }
  .leaflet-popup-content { color: #fff !important; font-family: 'DM Sans', sans-serif !important; }
  .popup-name { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 8px; }
  .popup-row { display: flex; justify-content: space-between; font-size: 12px; color: #4a6280; margin-bottom: 4px; }
  .popup-val { color: #94a3b8; }
  .popup-risk { font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 100px; }
  .popup-risk-LOW      { background: rgba(34,197,94,0.15);  color: #22c55e; }
  .popup-risk-MEDIUM   { background: rgba(245,158,11,0.15); color: #f59e0b; }
  .popup-risk-HIGH     { background: rgba(239,68,68,0.15);  color: #ef4444; }
  .popup-risk-CRITICAL { background: rgba(124,58,237,0.15); color: #7c3aed; }
`;

// Nav definition — "view" key maps to which panel to show
const NAV = [
  { icon: "◉", label: "Live Map",     view: "map",         roles: ["PUBLIC","RESCUE","ADMIN"] },
  { icon: "⚡", label: "Predictions",  view: "predictions", roles: ["RESCUE","ADMIN"] },
  { icon: "🔔", label: "Alerts",       view: "alerts",      roles: ["PUBLIC","RESCUE","ADMIN"]          },
  { icon: "⬡",  label: "Manage Zones", view: "zones",       roles: ["ADMIN"]                   },
  { icon: "👥", label: "Users",        view: "users",       roles: ["ADMIN"]                   },
];

const VIEW_TITLES = {
  map:         "Live Risk Map",
  predictions: "Risk Predictions",
  alerts:      "Active Alerts",
  zones:       "Manage Zones",
  users:       "User Management",
};

export default function Dashboard() {
  const [zones,       setZones]       = useState([]);
  const [predictions, setPredictions] = useState({});
  const [loading,     setLoading]     = useState(true);
  const [activeView,  setActiveView]  = useState("map");
  const wrapRef  = useRef(null);
  const [mapHeight, setMapHeight] = useState(0);
  const user   = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  useEffect(() => {
    if (!wrapRef.current) return;
    const ro = new ResizeObserver(([entry]) => setMapHeight(entry.contentRect.height));
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    api.get("/zones/")
      .then((res) => setZones(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));

    const loadPredictions = () =>
      api.get("/predictions/latest")
        .then((res) => {
          const map = {};
          res.data.forEach((p) => { map[p.zone_id] = p; });
          setPredictions(map);
        })
        .catch(console.error);

    loadPredictions();
    const interval = setInterval(loadPredictions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  function handleLogout() { logout(); navigate("/login"); }

  const role = user?.role || "PUBLIC";

  const riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  Object.values(predictions).forEach((p) => {
    if (riskCounts[p.overall_risk] !== undefined) riskCounts[p.overall_risk]++;
  });

  // Render the right panel based on activeView
  function renderContent() {
    switch (activeView) {
      case "map":
        return (
          <div className="map-wrap" ref={wrapRef}>
            {mapHeight > 0 && (
              <MapContainer
                center={[46.2276, 2.2137]} zoom={6} minZoom={4}
                style={{ width: "100%", height: `${mapHeight}px` }}
                scrollWheelZoom maxBounds={[[-90,-180],[90,180]]} maxBoundsViscosity={1.0}
              >
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  attribution="Tiles &copy; Esri" maxZoom={19}
                />
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
                  attribution="" maxZoom={19}
                />
                {zones.map((zone) => {
                  const pred = predictions[zone.id];
                  const risk = pred ? getRiskFromProb(pred.flood_prob) : "LOW";
                  return (
                    <Marker key={zone.id} position={[zone.latitude, zone.longitude]} icon={riskIcon(risk)}>
                      <Popup>
                        <div className="popup-name">{zone.name}</div>
                        <div className="popup-row"><span>Overall Risk</span><span className={`popup-risk popup-risk-${risk}`}>{risk}</span></div>
                        <div className="popup-row"><span>Flood</span><span className="popup-val">{pred ? `${pred.flood_risk} (${Math.round(pred.flood_prob * 100)}%)` : "—"}</span></div>
                        <div className="popup-row"><span>Fire</span><span className="popup-val">{pred ? `${pred.fire_risk} (${Math.round(pred.fire_prob * 100)}%)` : "—"}</span></div>
                        <div className="popup-row"><span>Code</span><span className="popup-val">{zone.code}</span></div>
                        <div className="popup-row"><span>Region</span><span className="popup-val">{zone.region || "—"}</span></div>
                        <div className="popup-row"><span>Population</span><span className="popup-val">{zone.population?.toLocaleString() || "—"}</span></div>
                        {pred?.last_updated && <div className="popup-row"><span>Updated</span><span className="popup-val">{new Date(pred.last_updated).toLocaleTimeString()}</span></div>}
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            )}
            <div className="risk-legend">
              <div className="legend-title">Risk Level</div>
              {Object.entries(RISK_COLORS).map(([level, color]) => (
                <div className="legend-row" key={level}>
                  <div className="legend-dot" style={{ background: color }} />
                  <span className="legend-label">{level}</span>
                </div>
              ))}
            </div>
            {(role === "RESCUE" || role === "ADMIN") && <ChatPanel zoneContext="" />}
            
          </div>
        );

      case "predictions":
        return (
          <div className="content-area">
            <div className="panel-scroll">
              <PredictionPanel zones={zones} />
            </div>
          </div>
        );

      case "alerts":
        return (
          <div className="content-area">
            <div className="panel-scroll">
              <AlertPanel autoRefresh={true} refreshInterval={15000} />
            </div>
          </div>
        );

      case "chat":
        // ChatPanel is already a floating widget on the map — show it standalone here too
        return (
          <div className="content-area">
            <div className="panel-scroll" style={{ color: "#4a6280", fontFamily: "'DM Sans',sans-serif", fontSize: 13 }}>
              <p>AI Chat is available as a floating panel on the <strong style={{ color: "#94a3b8" }}>Live Map</strong> view (bottom-right corner) for RESCUE and ADMIN roles.</p>
            </div>
          </div>
        );

      default:
        return (
          <div className="content-area">
            <div className="panel-scroll" style={{ color: "#2a3a4a", fontFamily: "'Syne',sans-serif", fontSize: 13, letterSpacing: 2 }}>
              {activeView === 'zones' ? <ManageZones predictions={predictions} /> : activeView === 'users' ? <UsersPanel /> : VIEW_TITLES[activeView]?.toUpperCase() + ' — COMING SOON'}
            </div>
          </div>
        );
    }
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="dash">

        {/* Sidebar */}
        <div className="sidebar">
          <div className="sidebar-top">
            <div className="sidebar-brand">
              <span className="brand-icon">🌊🔥</span>
              <span className="brand-name">Clima<span>Risk</span></span>
            </div>
            <div className="live-badge">
              <div className="live-dot" />
              <span>Live Monitoring</span>
            </div>
            <div className="user-card">
              <div className="user-row">
                <span className="user-name">{user?.username}</span>
                <span className={`role-pill role-${role}`}>{role}</span>
              </div>
              {user?.team && <div className="user-team">{user.team}</div>}
            </div>
          </div>

          <div className="sidebar-nav">
            <div className="nav-label">Navigation</div>
            {NAV.filter((item) => item.roles.includes(role)).map((item) => (
              <div
                key={item.view}
                className={`nav-item ${activeView === item.view ? "active" : ""}`}
                onClick={() => setActiveView(item.view)}
              >
                <span className="nav-icon">{item.icon}</span>
                {item.label}
              </div>
            ))}
            <div className="divider" />
            <div className="nav-label">Monitored Zones</div>
            <div className="zone-list">
              {loading && <p className="no-zones">Loading...</p>}
              {!loading && zones.length === 0 && <p className="no-zones">No zones yet</p>}
              {zones.map((z) => {
                const pred = predictions[z.id];
                const risk = pred?.overall_risk || "LOW";
                return (
                  <div
                    className="zone-row"
                    key={z.id}
                    onClick={() => setActiveView("map")}
                  >
                    <div className="zone-row-left">
                      <div className="zone-risk-dot" style={{ background: RISK_COLORS[risk] }} />
                      <span className="zone-row-name">{z.name}</span>
                    </div>
                    <span className="zone-row-code">{z.code}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="sidebar-bottom">
            <button className="logout-btn" onClick={handleLogout}>Sign out</button>
          </div>
        </div>

        {/* Main */}
        <div className="main">
          <div className="topbar">
            <span className="topbar-title">{VIEW_TITLES[activeView] || "Dashboard"}</span>
            <div className="topbar-right">
              <div className="stat-chip">
                <div className="stat-chip-dot" style={{ background: "#22c55e" }} />
                <span className="stat-chip-label">Zones</span>
                <span className="stat-chip-val">{zones.length}</span>
              </div>
              {riskCounts.HIGH + riskCounts.CRITICAL > 0 && (
                <div
                  className="stat-chip"
                  style={{ cursor: "pointer" }}
                  onClick={() => setActiveView("alerts")}
                >
                  <div className="stat-chip-dot" style={{ background: "#ef4444", animation: "pulse 2s infinite" }} />
                  <span className="stat-chip-label">Alerts</span>
                  <span className="stat-chip-val">{riskCounts.HIGH + riskCounts.CRITICAL}</span>
                </div>
              )}
              <div className="stat-chip">
                <div className="stat-chip-dot" style={{ background: "#00c8ff" }} />
                <span className="stat-chip-label">Status</span>
                <span className="stat-chip-val">Online</span>
              </div>
            </div>
          </div>

          {renderContent()}
        </div>
      </div>
    </>
  );
}