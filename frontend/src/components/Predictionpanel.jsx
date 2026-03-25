import { useState, useCallback } from "react";
import api from "../api/client";

const RISK_CONFIG = {
  LOW:      { color: "#22c55e", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)"   },
  MEDIUM:   { color: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.25)"  },
  HIGH:     { color: "#ef4444", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.25)"   },
  CRITICAL: { color: "#7c3aed", bg: "rgba(124,58,237,0.08)",  border: "rgba(124,58,237,0.25)"  },
};

// Thresholds match backend schemas/prediction.py exactly:
// >= 50% = CRITICAL, >= 30% = HIGH, >= 10% = MEDIUM, < 10% = LOW
const ZONE_THRESHOLDS = [
  { label: "LOW",      color: "#22c55e", from: 0,  to: 30  },
  { label: "MEDIUM",   color: "#f59e0b", from: 30, to: 70  },
  { label: "HIGH",     color: "#ef4444", from: 70, to: 90  },
  { label: "CRITICAL", color: "#7c3aed", from: 90, to: 100 },
];

const RISK_ORDER = { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3 };

const CSS = `
  @keyframes pp-ping  { 75%,100% { transform:scale(2.2); opacity:0; } }
  @keyframes pp-pulse { 0%,100% { opacity:1; } 50% { opacity:0.35; } }

  .pp-wrap        { background:#060a0f; border-radius:8px; padding:20px; font-family:'DM Sans',sans-serif; }
  .pp-hd          { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px; }
  .pp-title       { font-family:'Syne',sans-serif; font-size:12px; font-weight:700; letter-spacing:3px; color:#f1f5f9; text-transform:uppercase; }
  .pp-sub         { font-size:10px; color:#4a6280; margin-top:3px; letter-spacing:1px; }
  .pp-badge       { padding:5px 14px; border-radius:8px; font-size:10px; letter-spacing:2px; border:1px solid; font-family:'Syne',sans-serif; font-weight:700; transition:all 0.4s; }
  .pp-cards       { display:flex; gap:12px; flex-wrap:wrap; }
  .pp-card        { background:#0b1120; border-radius:8px; padding:18px 20px; flex:1; min-width:260px; position:relative; overflow:hidden; transition:border-color 0.4s; border:1px solid #1a2740; }
  .pp-stripe      { position:absolute; top:0; left:0; width:3px; height:100%; transition:background 0.4s; }
  .pp-type-row    { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
  .pp-type-icon   { font-size:15px; }
  .pp-type-lbl    { font-size:10px; letter-spacing:2px; color:#4a6280; font-family:'Syne',sans-serif; }
  .pp-level-row   { display:flex; align-items:center; gap:6px; margin-bottom:12px; }
  .pp-dot-wrap    { position:relative; display:inline-block; width:9px; height:9px; }
  .pp-dot-ring    { position:absolute; inset:0; border-radius:50%; animation:pp-ping 1.6s cubic-bezier(0,0,.2,1) infinite; opacity:.5; }
  .pp-dot-core    { position:absolute; inset:0; border-radius:50%; }
  .pp-level-txt   { font-size:10px; letter-spacing:2px; font-family:'Syne',sans-serif; }
  .pp-select      { width:100%; background:#060a0f; border:1px solid rgba(255,255,255,0.07); border-radius:8px; color:#94a3b8; padding:7px 10px; font-size:12px; font-family:'DM Sans',sans-serif; cursor:pointer; margin-bottom:10px; }
  .pp-select:focus { outline:none; border-color:rgba(0,200,255,0.35); }
  .pp-grid        { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }
  .pp-field-lbl   { font-size:9px; color:#4a6280; letter-spacing:1px; margin-bottom:3px; }
  .pp-input       { width:100%; background:#060a0f; border:1px solid rgba(255,255,255,0.06); border-radius:6px; color:#94a3b8; padding:6px 10px; font-size:11px; font-family:'DM Sans',sans-serif; transition:border-color 0.2s; }
  .pp-input:focus { outline:none; border-color:rgba(0,200,255,0.3); color:#f1f5f9; }
  .pp-run-btn     { width:100%; padding:9px; border-radius:8px; border:none; background:rgba(0,200,255,0.9); color:#060a0f; font-family:'Syne',sans-serif; font-size:11px; font-weight:700; letter-spacing:2px; cursor:pointer; margin-top:4px; transition:all 0.2s; }
  .pp-run-btn:hover    { background:#00c8ff; }
  .pp-run-btn:disabled { opacity:0.4; cursor:not-allowed; }
  .pp-result      { margin-top:16px; padding-top:14px; border-top:1px solid rgba(255,255,255,0.05); }
  .pp-score-row   { display:flex; align-items:baseline; gap:5px; margin-bottom:10px; }
  .pp-score-big   { font-family:'Syne',sans-serif; font-size:50px; font-weight:800; line-height:1; letter-spacing:-2px; transition:color 0.4s; }
  .pp-score-sym   { font-family:'Syne',sans-serif; font-size:20px; font-weight:700; opacity:.6; }
  .pp-bar-track   { height:4px; background:#1a2740; border-radius:2px; overflow:hidden; }
  .pp-bar-fill    { height:100%; border-radius:2px; transition:width 1.1s cubic-bezier(0.4,0,.2,1), background 0.4s; }
  .pp-ticks       { display:flex; justify-content:space-between; margin-top:3px; }
  .pp-tick        { font-size:9px; color:#2a3a4a; }
  .pp-zones       { display:flex; gap:5px; margin-top:12px; }
  .pp-zseg        { flex:1; text-align:center; padding:3px 2px; border-radius:3px; border:1px solid; transition:all 0.3s; }
  .pp-zbar        { width:100%; height:2px; border-radius:1px; margin-bottom:3px; }
  .pp-zlbl        { font-size:8px; color:#4a6280; }
  .pp-ts          { margin-top:10px; font-size:9px; color:#2a3a4a; letter-spacing:1px; }
  .pp-skel        { height:52px; background:#0b1120; border-radius:6px; animation:pp-pulse 1.4s ease-in-out infinite; margin-top:14px; }
  .pp-empty       { font-size:11px; color:#2a3a4a; margin-top:12px; }
  .pp-err         { font-size:11px; color:#ef4444; margin-top:10px; }
`;

function ZoneSegments({ pct }) {
  return (
    <div className="pp-zones">
      {ZONE_THRESHOLDS.map((z) => {
        const active = pct >= z.from && pct < (z.to === 100 ? 101 : z.to);
        return (
          <div key={z.label} className="pp-zseg" style={{ background: active ? z.color + "18" : "transparent", borderColor: active ? z.color : "#1a2740" }}>
            <div className="pp-zbar" style={{ background: z.color }} />
            <span className="pp-zlbl">{z.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function RiskCard({ type, icon, result, loading, error, onRun, zones }) {
  const isFlood = type === "flood";

  // Shared
  const [zoneId, setZoneId] = useState("");
  // Flood inputs
  const [rainfall,  setRainfall]  = useState("25");
  const [river,     setRiver]     = useState("1.5");
  const [soil,      setSoil]      = useState("15");
  // elevation auto-fetched from zone coordinates via Open-Meteo
  // Fire inputs
  const [temp,     setTemp]     = useState("35");
  const [humidity, setHumidity] = useState("20");
  const [wind,     setWind]     = useState("40");
  const [ndvi,     setNdvi]     = useState("0.4");
  const [fwi,      setFwi]      = useState("18");

  const cfg = result ? (RISK_CONFIG[result.risk_level] || RISK_CONFIG.LOW) : null;
  const pct = result ? Math.round(result.probability * 100) : 0;
  const ts  = result?.created_at
    ? new Date(result.created_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  function submit() {
    if (!zoneId) return;
    if (isFlood) {
      onRun({ zone_id: +zoneId, rainfall_mm: +rainfall, river_level_m: +river, soil_moisture_pct: +soil * 100, });
    } else {
      onRun({ zone_id: +zoneId, temperature_c: +temp, humidity_pct: +humidity, wind_speed_kmh: +wind, fwi: +fwi });
    }
  }

  return (
    <div className="pp-card" style={{ borderColor: cfg ? cfg.border : "#1a2740" }}>
      <div className="pp-stripe" style={{ background: cfg ? cfg.color : "#1a2740" }} />

      {/* Type label + live level */}
      <div className="pp-type-row">
        <span className="pp-type-icon">{icon}</span>
        <span className="pp-type-lbl">RISK {type.toUpperCase()}</span>
      </div>
      {cfg && !loading && (
        <div className="pp-level-row">
          <span className="pp-dot-wrap">
            <span className="pp-dot-ring" style={{ background: cfg.color }} />
            <span className="pp-dot-core" style={{ background: cfg.color }} />
          </span>
          <span className="pp-level-txt" style={{ color: cfg.color }}>{cfg.label}</span>
        </div>
      )}

      {/* Zone selector */}
      <select className="pp-select" value={zoneId} onChange={(e) => setZoneId(e.target.value)}>
        <option value="">— Select zone —</option>
        {zones.map((z) => (
          <option key={z.id} value={z.id}>{z.name} ({z.code})</option>
        ))}
      </select>

      {/* Inputs */}
      {isFlood ? (
        <>
          <div className="pp-grid">
            <div><div className="pp-field-lbl">RAINFALL (mm)</div><input className="pp-input" type="number" value={rainfall} onChange={(e) => setRainfall(e.target.value)} /></div>
            <div><div className="pp-field-lbl">RIVER LEVEL (m)</div><input className="pp-input" type="number" value={river} onChange={(e) => setRiver(e.target.value)} /></div>
          </div>
          <div className="pp-grid">
            <div><div className="pp-field-lbl">SOIL MOISTURE (%)</div><input className="pp-input" type="number" step="0.1" value={soil} onChange={(e) => setSoil(e.target.value)} /></div>

          </div>
          <div className="pp-info-note">📍 Elevation auto-detected from zone coordinates</div>
        </>
      ) : (
        <>
          <div className="pp-grid">
            <div><div className="pp-field-lbl">TEMPERATURE (°C)</div><input className="pp-input" type="number" value={temp} onChange={(e) => setTemp(e.target.value)} /></div>
            <div><div className="pp-field-lbl">HUMIDITY (%)</div><input className="pp-input" type="number" value={humidity} onChange={(e) => setHumidity(e.target.value)} /></div>
            <div><div className="pp-field-lbl">WIND (km/h)</div><input className="pp-input" type="number" value={wind} onChange={(e) => setWind(e.target.value)} /></div>
            <div><div className="pp-field-lbl">FWI INDEX</div><input className="pp-input" type="number" value={fwi} onChange={(e) => setFwi(e.target.value)} /></div>
          </div>
        </>
      )}

      <button className="pp-run-btn" onClick={submit} disabled={loading || !zoneId}>
        {loading ? "RUNNING..." : "▶ RUN PREDICTION"}
      </button>

      {/* Result area */}
      {loading && <div className="pp-skel" />}
      {!loading && error && <div className="pp-err">⚠ {error}</div>}
      {!loading && !error && result && (
        <div className="pp-result">
          <div className="pp-score-row">
            <span className="pp-score-big" style={{ color: cfg.color }}>{pct}</span>
            <span className="pp-score-sym" style={{ color: cfg.color }}>%</span>
          </div>
          <div className="pp-bar-track">
            <div className="pp-bar-fill" style={{ width: `${pct}%`, background: cfg.color, boxShadow: `0 0 6px ${cfg.color}55` }} />
          </div>
          <div className="pp-ticks">
            {[0, 30, 50, 80, 100].map((v) => <span key={v} className="pp-tick">{v}</span>)}
          </div>
          <ZoneSegments pct={pct} />
          {ts && <div className="pp-ts">UPDATED · {ts} · model: {result.model_version}</div>}
        </div>
      )}
      {!loading && !error && !result && (
        <div className="pp-empty">Select a zone and press RUN to predict</div>
      )}
    </div>
  );
}

export default function PredictionPanel({ zones = [] }) {
  const [floodResult,  setFloodResult]  = useState(null);
  const [fireResult,   setFireResult]   = useState(null);
  const [floodLoading, setFloodLoading] = useState(false);
  const [fireLoading,  setFireLoading]  = useState(false);
  const [floodError,   setFloodError]   = useState(null);
  const [fireError,    setFireError]    = useState(null);

  const runFlood = useCallback(async (body) => {
    setFloodLoading(true); setFloodError(null);
    try {
      const res = await api.post("/predictions/flood?dry_run=true", body);
      setFloodResult(res.data);
    } catch (e) {
      setFloodError(e.response?.data?.detail || e.message);
    } finally { setFloodLoading(false); }
  }, []);

  const runFire = useCallback(async (body) => {
    setFireLoading(true); setFireError(null);
    try {
      const res = await api.post("/predictions/fire?dry_run=true", body);
      setFireResult(res.data);
    } catch (e) {
      setFireError(e.response?.data?.detail || e.message);
    } finally { setFireLoading(false); }
  }, []);

  const worstRisk = (() => {
    if (!floodResult && !fireResult) return null;
    const fl = floodResult?.risk_level || "LOW";
    const fi = fireResult?.risk_level  || "LOW";
    return RISK_CONFIG[(RISK_ORDER[fl] || 0) >= (RISK_ORDER[fi] || 0) ? fl : fi];
  })();

  return (
    <>
      <style>{CSS}</style>
      <div className="pp-wrap">
        <div className="pp-hd">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 2, height: 18, background: "#00c8ff", borderRadius: 1 }} />
              <span className="pp-title">Risk Predictions</span>
            </div>
            <div className="pp-sub">ML · XGBoost v8.0 · POST /predictions/flood|fire</div>
          </div>
          {worstRisk && (
            <div className="pp-badge" style={{ color: worstRisk.color, borderColor: worstRisk.border, background: worstRisk.bg }}>
              OVERALL · {(floodResult?.risk_level && fireResult?.risk_level) ?
                (RISK_ORDER[floodResult.risk_level] >= RISK_ORDER[fireResult.risk_level] ? floodResult.risk_level : fireResult.risk_level)
                : (floodResult?.risk_level || fireResult?.risk_level)}
            </div>
          )}
        </div>
        <div className="pp-cards">
          <RiskCard type="flood" icon="💧" result={floodResult} loading={floodLoading} error={floodError} onRun={runFlood} zones={zones} />
          <RiskCard type="fire"  icon="🔥" result={fireResult}  loading={fireLoading}  error={fireError}  onRun={runFire}  zones={zones} />
        </div>
      </div>
    </>
  );
}