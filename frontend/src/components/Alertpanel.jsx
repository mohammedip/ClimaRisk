import { useState, useEffect, useCallback } from "react";
import api from "../api/client";
import useAuthStore from "../store/authStore";

const RISK_CONFIG = {
  LOW:      { color: "#22c55e", bg: "rgba(34,197,94,0.07)",   border: "rgba(34,197,94,0.2)",   rank: 0 },
  MEDIUM:   { color: "#f59e0b", bg: "rgba(245,158,11,0.07)",  border: "rgba(245,158,11,0.2)",  rank: 1 },
  HIGH:     { color: "#ef4444", bg: "rgba(239,68,68,0.07)",   border: "rgba(239,68,68,0.2)",   rank: 2 },
  CRITICAL: { color: "#7c3aed", bg: "rgba(124,58,237,0.07)",  border: "rgba(124,58,237,0.2)",  rank: 3 },
};

const HAZARD_META = {
  FLOOD: { label: "FLOOD", icon: "💧", accent: "#38bdf8" },
  FIRE:  { label: "FIRE",  icon: "🔥", accent: "#fb923c" },
};

const CSS = `
  @keyframes ap-blink  { 0%,100%{opacity:1}50%{opacity:0.25} }
  @keyframes ap-pulse  { 0%,100%{opacity:1}50%{opacity:0.35} }
  @keyframes ap-in     { from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)} }

  .ap-wrap        { background:#060a0f; border-radius:8px; padding:20px; font-family:'DM Sans',sans-serif; }
  .ap-hd          { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
  .ap-title-row   { display:flex; align-items:center; gap:8px; }
  .ap-title       { font-family:'Syne',sans-serif; font-size:12px; font-weight:700; letter-spacing:3px; color:#f1f5f9; text-transform:uppercase; }
  .ap-count-badge { border-radius:50%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:700; color:#fff; }
  .ap-sub         { font-size:10px; color:#4a6280; margin-top:3px; letter-spacing:1px; }
  .ap-sync-btn    { background:transparent; border:1px solid rgba(255,255,255,0.08); border-radius:8px; color:#00c8ff; cursor:pointer; padding:6px 14px; font-size:10px; letter-spacing:1px; font-family:'DM Sans',sans-serif; transition:all 0.2s; }
  .ap-sync-btn:hover    { background:rgba(0,200,255,0.06); border-color:rgba(0,200,255,0.3); }
  .ap-sync-btn:disabled { opacity:0.4; cursor:not-allowed; }
  .ap-stats       { display:flex; gap:8px; margin-bottom:16px; }
  .ap-stat        { flex:1; padding:10px 8px; background:#0b1120; border-radius:6px; text-align:center; border:1px solid #1a2740; transition:border-color 0.3s; }
  .ap-stat-num    { font-family:'Syne',sans-serif; font-size:22px; font-weight:800; }
  .ap-stat-lbl    { font-size:9px; color:#4a6280; letter-spacing:1px; margin-top:2px; }
  .ap-tabs        { display:flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }
  .ap-tab         { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 12px; font-size:9px; letter-spacing:1px; font-family:'DM Sans',sans-serif; transition:all 0.15s; }
  .ap-tab.active  { border-color:rgba(0,200,255,0.4); color:#00c8ff; background:rgba(0,200,255,0.06); }
  .ap-list        { max-height:440px; overflow-y:auto; padding-right:2px; }
  .ap-row         { display:flex; border-radius:6px; overflow:hidden; margin-bottom:8px; transition:opacity 0.3s; border:1px solid; animation:ap-in 0.3s ease-out; }
  .ap-stripe      { width:3px; flex-shrink:0; }
  .ap-body        { flex:1; padding:12px 14px; }
  .ap-row-hd      { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px; }
  .ap-tags        { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
  .ap-tag         { font-size:9px; letter-spacing:1.5px; padding:2px 8px; border-radius:4px; font-family:'Syne',sans-serif; font-weight:700; }
  .ap-active-pill { font-size:9px; padding:1px 6px; border-radius:4px; border:1px solid rgba(239,68,68,0.4); color:#ef4444; animation:ap-blink 1.3s step-end infinite; }
  .ap-time        { font-size:10px; color:#2a3a4a; white-space:nowrap; margin-left:8px; }
  .ap-zone-row    { display:flex; align-items:center; gap:6px; margin-bottom:5px; }
  .ap-zone-txt    { font-size:11px; color:#94a3b8; letter-spacing:.5px; }
  .ap-zone-code   { font-size:10px; color:#4a6280; font-family:monospace; }
  .ap-msg         { font-size:12px; color:#64748b; line-height:1.55; margin:0; }
  .ap-actions     { display:flex; flex-direction:column; justify-content:center; gap:6px; padding:12px 10px; border-left:1px solid rgba(255,255,255,0.05); flex-shrink:0; }
  .ap-act-btn     { background:transparent; border:1px solid; border-radius:5px; cursor:pointer; padding:5px 10px; font-size:9px; letter-spacing:1px; font-family:'DM Sans',sans-serif; transition:all 0.2s; white-space:nowrap; }
  .ap-empty       { padding:36px 0; text-align:center; }
  .ap-empty-icon  { font-size:26px; margin-bottom:10px; }
  .ap-empty-txt   { font-size:11px; color:#2a3a4a; letter-spacing:2px; }
  .ap-skel        { height:72px; background:#0b1120; border-radius:6px; margin-bottom:8px; border:1px solid #1a2740; animation:ap-pulse 1.4s ease-in-out infinite; }
  .ap-err         { padding:20px; text-align:center; color:#ef4444; font-size:12px; }
  .ap-resolved    { font-size:9px; color:#2a3a4a; letter-spacing:1px; padding:4px 0; }
`;

function relTime(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (diff < 60)   return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function AlertRow({ alert, onResolve, onDismiss, canAct }) {
  const sev  = RISK_CONFIG[alert.risk_level]   || RISK_CONFIG.LOW;
  const haz  = HAZARD_META[alert.hazard_type]  || HAZARD_META.FLOOD;
  const resolved = !alert.is_active;

  return (
    <div
      className="ap-row"
      style={{
        background:   resolved ? "#0b1120"  : sev.bg,
        borderColor:  resolved ? "#1a2740"  : sev.border,
        opacity:      resolved ? 0.55       : 1,
      }}
    >
      <div className="ap-stripe" style={{ background: resolved ? "#1a2740" : sev.color }} />

      <div className="ap-body">
        {/* Top row */}
        <div className="ap-row-hd">
          <div className="ap-tags">
            <span className="ap-tag" style={{ background: haz.accent + "18", color: haz.accent }}>
              {haz.icon} {haz.label}
            </span>
            <span className="ap-tag" style={{ background: sev.color + "18", color: sev.color }}>
              {alert.risk_level}
            </span>
            {!resolved && <span className="ap-active-pill">ACTIVE</span>}
          </div>
          <span className="ap-time">{relTime(alert.created_at)}</span>
        </div>

        {/* Zone */}
        <div className="ap-zone-row">
          <span style={{ fontSize: 11, color: "#4a6280" }}>📍</span>
          <span className="ap-zone-txt">{alert.zone?.name || `Zone #${alert.zone_id}`}</span>
          {alert.zone?.code && <span className="ap-zone-code">· {alert.zone.code}</span>}
        </div>

        {/* Title + message */}
        <p className="ap-msg" style={{ color: resolved ? "#4a6280" : "#94a3b8" }}>
          <strong style={{ color: resolved ? "#4a6280" : "#c7d0e0", fontSize: 12 }}>{alert.title}</strong>
          {" — "}
          {alert.message}
        </p>

        {/* Resolved info */}
        {resolved && alert.resolved_at && (
          <div className="ap-resolved">
            RESOLVED · {new Date(alert.resolved_at).toLocaleString("fr-FR")}
          </div>
        )}
      </div>

      {/* Actions — only active alerts, only RESCUE/ADMIN */}
      {!resolved && canAct && (
        <div className="ap-actions">
          <button
            className="ap-act-btn"
            style={{ borderColor: sev.color + "66", color: sev.color }}
            onClick={() => onResolve(alert.id)}
            onMouseEnter={(e) => { e.target.style.background = sev.color + "18"; }}
            onMouseLeave={(e) => { e.target.style.background = "transparent"; }}
          >
            ✓ RESOLVE
          </button>
          <button
            className="ap-act-btn"
            style={{ borderColor: "rgba(255,255,255,0.08)", color: "#4a6280" }}
            onClick={() => onDismiss(alert.id)}
            onMouseEnter={(e) => { e.target.style.color = "#94a3b8"; }}
            onMouseLeave={(e) => { e.target.style.color = "#4a6280"; }}
          >
            ✕ HIDE
          </button>
        </div>
      )}
    </div>
  );
}

const FILTERS = ["ALL", "FLOOD", "FIRE", "CRITICAL", "HIGH", "MEDIUM", "LOW"];

export default function AlertPanel({ autoRefresh = true, refreshInterval = 15000 }) {
  const [alerts,   setAlerts]   = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [filter,   setFilter]   = useState("ALL");
  const [showResolved, setShowResolved] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  // Track locally dismissed (hidden, not resolved via API)
  const [dismissed, setDismissed] = useState(new Set());

  const user   = useAuthStore((s) => s.user);
  const role   = user?.role || "PUBLIC";
  const canAct = role === "RESCUE" || role === "ADMIN";

  const fetchAlerts = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await api.get("/alerts/");
      setAlerts(res.data);
      setLastSync(new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);

  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchAlerts, refreshInterval);
    return () => clearInterval(id);
  }, [autoRefresh, refreshInterval, fetchAlerts]);

  // PATCH /alerts/{id}/resolve
  const resolveAlert = useCallback(async (id) => {
    // Optimistic update
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, is_active: false, resolved_at: new Date().toISOString() } : a));
    try {
      await api.patch(`/alerts/${id}/resolve`);
    } catch (e) {
      // Roll back on failure
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, is_active: true, resolved_at: null } : a));
    }
  }, []);

  // Local dismiss (hide from UI without API call)
  const dismissAlert = useCallback((id) => {
    setDismissed((prev) => new Set([...prev, id]));
  }, []);

  // Stats
  const active   = alerts.filter((a) => a.is_active && !dismissed.has(a.id));
  const critical = active.filter((a) => a.risk_level === "CRITICAL");
  const high     = active.filter((a) => a.risk_level === "HIGH");
  const resolved = alerts.filter((a) => !a.is_active);

  // Filtered + sorted list
  const displayed = alerts
    .filter((a) => !dismissed.has(a.id))
    .filter((a) => showResolved ? true : a.is_active)
    .filter((a) => {
      if (filter === "ALL")   return true;
      if (filter === "FLOOD") return a.hazard_type === "FLOOD";
      if (filter === "FIRE")  return a.hazard_type === "FIRE";
      return a.risk_level === filter;
    })
    .sort((a, b) => {
      // Active first, then by severity desc, then by date desc
      if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
      const rd = (RISK_CONFIG[b.risk_level]?.rank || 0) - (RISK_CONFIG[a.risk_level]?.rank || 0);
      if (rd !== 0) return rd;
      return new Date(b.created_at) - new Date(a.created_at);
    });

  return (
    <>
      <style>{CSS}</style>
      <div className="ap-wrap">

        {/* Header */}
        <div className="ap-hd">
          <div>
            <div className="ap-title-row">
              <div style={{ width: 2, height: 18, background: critical.length ? "#7c3aed" : "#ef4444", borderRadius: 1 }} />
              <span className="ap-title">Active Alerts</span>
              {active.length > 0 && (
                <div className="ap-count-badge" style={{ background: critical.length ? "#7c3aed" : "#ef4444" }}>
                  {active.length}
                </div>
              )}
            </div>
            <div className="ap-sub">
              GET /alerts/ · {autoRefresh ? `auto ${refreshInterval / 1000}s` : "manual"}
              {lastSync && ` · synced ${lastSync}`}
            </div>
          </div>
          <button className="ap-sync-btn" onClick={fetchAlerts} disabled={loading}>
            {loading ? "SYNCING..." : "↻ SYNC"}
          </button>
        </div>

        {/* Stats */}
        <div className="ap-stats">
          {[
            { label: "CRITICAL", value: critical.length, color: "#7c3aed" },
            { label: "HIGH",     value: high.length,     color: "#ef4444" },
            { label: "ACTIVE",   value: active.length,   color: "#94a3b8" },
            { label: "RESOLVED", value: resolved.length, color: "#4a6280" },
          ].map((s) => (
            <div
              key={s.label}
              className="ap-stat"
              style={{ borderColor: s.value > 0 && s.label !== "RESOLVED" ? s.color + "44" : "#1a2740" }}
            >
              <div className="ap-stat-num" style={{ color: s.color }}>{s.value}</div>
              <div className="ap-stat-lbl">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="ap-tabs">
          {FILTERS.map((f) => (
            <button key={f} className={`ap-tab ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
              {f}
            </button>
          ))}
          <button
            className={`ap-tab ${showResolved ? "active" : ""}`}
            style={{ marginLeft: "auto" }}
            onClick={() => setShowResolved((v) => !v)}
          >
            {showResolved ? "▼ HIDE RESOLVED" : "▶ SHOW RESOLVED"}
          </button>
        </div>

        {/* List */}
        <div className="ap-list">
          {error ? (
            <div className="ap-err">⚠ Failed to load alerts: {error}</div>
          ) : loading && !alerts.length ? (
            [1, 2, 3].map((i) => <div key={i} className="ap-skel" />)
          ) : displayed.length === 0 ? (
            <div className="ap-empty">
              <div className="ap-empty-icon">✅</div>
              <div className="ap-empty-txt">NO ACTIVE ALERTS</div>
            </div>
          ) : (
            displayed.map((alert) => (
              <AlertRow
                key={alert.id}
                alert={alert}
                onResolve={resolveAlert}
                onDismiss={dismissAlert}
                canAct={canAct}
              />
            ))
          )}
        </div>
      </div>
    </>
  );
}