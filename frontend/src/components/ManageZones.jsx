import { useState, useEffect, useCallback } from "react";
import api from "../api/client";

const CSS = `
  @keyframes mz-in  { from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)} }
  @keyframes mz-pulse{ 0%,100%{opacity:1}50%{opacity:.4} }

  .mz-wrap       { background:#060a0f; border-radius:8px; padding:20px; font-family:'DM Sans',sans-serif; animation:mz-in .3s ease-out; }
  .mz-hd         { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
  .mz-title      { font-family:'Syne',sans-serif; font-size:12px; font-weight:700; letter-spacing:3px; color:#f1f5f9; text-transform:uppercase; }
  .mz-sub        { font-size:10px; color:#4a6280; margin-top:3px; letter-spacing:1px; }
  .mz-add-btn    { background:rgba(0,200,255,0.9); border:none; border-radius:8px; color:#060a0f; cursor:pointer; padding:8px 18px; font-family:'Syne',sans-serif; font-size:11px; font-weight:700; letter-spacing:1px; transition:all .2s; }
  .mz-add-btn:hover { background:#00c8ff; }

  .mz-table-wrap { border:1px solid #1a2740; border-radius:8px; overflow:hidden; }
  .mz-table      { width:100%; border-collapse:collapse; }
  .mz-table th   { background:#0b1120; padding:10px 14px; text-align:left; font-size:9px; letter-spacing:2px; color:#4a6280; font-family:'Syne',sans-serif; font-weight:700; border-bottom:1px solid #1a2740; }
  .mz-table td   { padding:12px 14px; font-size:12px; color:#94a3b8; border-bottom:1px solid rgba(255,255,255,0.03); vertical-align:middle; }
  .mz-table tr:last-child td { border-bottom:none; }
  .mz-table tr:hover td { background:rgba(255,255,255,0.02); }
  .mz-code       { font-family:monospace; font-size:11px; color:#4a6280; }
  .mz-risk       { font-size:9px; font-weight:700; padding:2px 8px; border-radius:4px; letter-spacing:1px; font-family:'Syne',sans-serif; }
  .mz-risk-LOW      { background:rgba(34,197,94,0.12);  color:#22c55e; }
  .mz-risk-MEDIUM   { background:rgba(245,158,11,0.12); color:#f59e0b; }
  .mz-risk-HIGH     { background:rgba(239,68,68,0.12);  color:#ef4444; }
  .mz-risk-CRITICAL { background:rgba(124,58,237,0.12); color:#7c3aed; }
  .mz-risk-NONE     { background:rgba(255,255,255,0.05); color:#4a6280; }
  .mz-act-row    { display:flex; gap:6px; }
  .mz-act-btn    { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 10px; font-size:10px; font-family:'DM Sans',sans-serif; transition:all .2s; }
  .mz-act-btn:hover { border-color:rgba(0,200,255,0.3); color:#00c8ff; }
  .mz-del-btn    { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 10px; font-size:10px; font-family:'DM Sans',sans-serif; transition:all .2s; }
  .mz-del-btn:hover { border-color:rgba(239,68,68,0.4); color:#ef4444; }

  .mz-skel       { height:48px; background:#0b1120; border-radius:4px; margin-bottom:4px; animation:mz-pulse 1.4s ease-in-out infinite; }
  .mz-empty      { padding:40px; text-align:center; color:#2a3a4a; font-size:12px; letter-spacing:2px; }
  .mz-err        { padding:16px; color:#ef4444; font-size:12px; text-align:center; }

  /* Modal */
  .mz-modal-bg   { position:fixed; inset:0; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:center; z-index:9999; }
  .mz-modal      { background:#0b1120; border:1px solid #1a2740; border-radius:12px; padding:28px; width:100%; max-width:480px; animation:mz-in .25s ease-out; }
  .mz-modal-title{ font-family:'Syne',sans-serif; font-size:14px; font-weight:700; color:#f1f5f9; margin-bottom:20px; letter-spacing:1px; }
  .mz-form-grid  { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }
  .mz-field      { display:flex; flex-direction:column; gap:4px; }
  .mz-field.full { grid-column:1/-1; }
  .mz-lbl        { font-size:9px; color:#4a6280; letter-spacing:1.5px; font-family:'Syne',sans-serif; }
  .mz-input      { background:#060a0f; border:1px solid rgba(255,255,255,0.07); border-radius:8px; color:#94a3b8; padding:8px 12px; font-size:12px; font-family:'DM Sans',sans-serif; transition:border-color .2s; }
  .mz-input:focus{ outline:none; border-color:rgba(0,200,255,0.35); color:#f1f5f9; }
  .mz-modal-foot { display:flex; justify-content:flex-end; gap:8px; margin-top:20px; }
  .mz-cancel-btn { background:transparent; border:1px solid rgba(255,255,255,0.08); border-radius:8px; color:#4a6280; cursor:pointer; padding:8px 18px; font-size:12px; font-family:'DM Sans',sans-serif; transition:all .2s; }
  .mz-cancel-btn:hover { color:#94a3b8; border-color:rgba(255,255,255,0.2); }
  .mz-save-btn   { background:rgba(0,200,255,0.9); border:none; border-radius:8px; color:#060a0f; cursor:pointer; padding:8px 22px; font-family:'Syne',sans-serif; font-size:11px; font-weight:700; letter-spacing:1px; transition:all .2s; }
  .mz-save-btn:hover    { background:#00c8ff; }
  .mz-save-btn:disabled { opacity:.4; cursor:not-allowed; }
  .mz-modal-err  { font-size:11px; color:#ef4444; margin-top:8px; text-align:center; }

  .mz-confirm-bg   { position:fixed; inset:0; background:rgba(0,0,0,0.75); display:flex; align-items:center; justify-content:center; z-index:9999; }
  .mz-confirm      { background:#0b1120; border:1px solid rgba(239,68,68,0.3); border-radius:12px; padding:28px; width:100%; max-width:380px; animation:mz-in .2s ease-out; }
  .mz-confirm-title{ font-family:'Syne',sans-serif; font-size:14px; font-weight:700; color:#f1f5f9; margin-bottom:8px; }
  .mz-confirm-msg  { font-size:12px; color:#64748b; margin-bottom:20px; line-height:1.6; }
  .mz-confirm-foot { display:flex; justify-content:flex-end; gap:8px; }
  .mz-confirm-del  { background:rgba(239,68,68,0.9); border:none; border-radius:8px; color:#fff; cursor:pointer; padding:8px 20px; font-family:'Syne',sans-serif; font-size:11px; font-weight:700; transition:all .2s; }
  .mz-confirm-del:hover { background:#ef4444; }
`;

const EMPTY_FORM = { name:"", code:"", latitude:"", longitude:"", region:"", population:"", area_km2:"" };

function ZoneModal({ zone, onSave, onClose }) {
  const isEdit = !!zone?.id;
  const [form, setForm]     = useState(zone ? {
    name:       zone.name       || "",
    code:       zone.code       || "",
    latitude:   zone.latitude   ?? "",
    longitude:  zone.longitude  ?? "",
    region:     zone.region     || "",
    population: zone.population ?? "",
    area_km2:   zone.area_km2   ?? "",
  } : EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error,  setError]  = useState(null);

  function set(k, v) { setForm(f => ({ ...f, [k]: v })); }

  async function submit() {
    if (!form.name || !form.code || !form.latitude || !form.longitude) {
      setError("Name, code, latitude and longitude are required."); return;
    }
    setSaving(true); setError(null);
    try {
      const payload = {
        name:       form.name,
        code:       form.code.toUpperCase(),
        latitude:   parseFloat(form.latitude),
        longitude:  parseFloat(form.longitude),
        region:     form.region     || null,
        population: form.population ? parseInt(form.population) : null,
        area_km2:   form.area_km2   ? parseFloat(form.area_km2) : null,
      };
      if (isEdit) {
        const res = await api.put(`/zones/${zone.id}`, payload);
        onSave(res.data);
      } else {
        const res = await api.post("/zones/", payload);
        onSave(res.data);
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setSaving(false); }
  }

  return (
    <div className="mz-modal-bg" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="mz-modal">
        <div className="mz-modal-title">{isEdit ? "✏️ Edit Zone" : "⬡ Add New Zone"}</div>
        <div className="mz-form-grid">
          <div className="mz-field">
            <div className="mz-lbl">ZONE NAME *</div>
            <input className="mz-input" value={form.name} onChange={e => set("name", e.target.value)} placeholder="Soummam Valley" />
          </div>
          <div className="mz-field">
            <div className="mz-lbl">CODE *</div>
            <input className="mz-input" value={form.code} onChange={e => set("code", e.target.value)} placeholder="SOM-01" maxLength={20} />
          </div>
          <div className="mz-field">
            <div className="mz-lbl">LATITUDE *</div>
            <input className="mz-input" type="number" step="0.0001" value={form.latitude} onChange={e => set("latitude", e.target.value)} placeholder="36.7525" />
          </div>
          <div className="mz-field">
            <div className="mz-lbl">LONGITUDE *</div>
            <input className="mz-input" type="number" step="0.0001" value={form.longitude} onChange={e => set("longitude", e.target.value)} placeholder="3.0420" />
          </div>
          <div className="mz-field">
            <div className="mz-lbl">REGION</div>
            <input className="mz-input" value={form.region} onChange={e => set("region", e.target.value)} placeholder="Béjaïa" />
          </div>
          <div className="mz-field">
            <div className="mz-lbl">POPULATION</div>
            <input className="mz-input" type="number" value={form.population} onChange={e => set("population", e.target.value)} placeholder="120000" />
          </div>
          <div className="mz-field full">
            <div className="mz-lbl">AREA (km²)</div>
            <input className="mz-input" type="number" step="0.1" value={form.area_km2} onChange={e => set("area_km2", e.target.value)} placeholder="450.5" />
          </div>
        </div>
        {error && <div className="mz-modal-err">⚠ {error}</div>}
        <div className="mz-modal-foot">
          <button className="mz-cancel-btn" onClick={onClose}>Cancel</button>
          <button className="mz-save-btn" onClick={submit} disabled={saving}>
            {saving ? "SAVING..." : isEdit ? "SAVE CHANGES" : "CREATE ZONE"}
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfirmDelete({ zone, onConfirm, onClose }) {
  const [deleting, setDeleting] = useState(false);
  async function confirm() {
    setDeleting(true);
    await onConfirm(zone.id);
    setDeleting(false);
  }
  return (
    <div className="mz-confirm-bg" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="mz-confirm">
        <div className="mz-confirm-title">Delete Zone</div>
        <div className="mz-confirm-msg">
          Are you sure you want to delete <strong style={{ color: "#f1f5f9" }}>{zone.name}</strong> ({zone.code})?
          This will also delete all predictions and alerts for this zone. This cannot be undone.
        </div>
        <div className="mz-confirm-foot">
          <button className="mz-cancel-btn" onClick={onClose}>Cancel</button>
          <button className="mz-confirm-del" onClick={confirm} disabled={deleting}>
            {deleting ? "DELETING..." : "DELETE"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ManageZones({ predictions = {} }) {
  const [zones,     setZones]     = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editZone,  setEditZone]  = useState(null);
  const [delZone,   setDelZone]   = useState(null);

  const fetchZones = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await api.get("/zones/");
      setZones(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchZones(); }, [fetchZones]);

  function handleSaved(zone) {
    setZones(prev => {
      const exists = prev.find(z => z.id === zone.id);
      return exists ? prev.map(z => z.id === zone.id ? zone : z) : [zone, ...prev];
    });
    setShowModal(false);
    setEditZone(null);
  }

  async function handleDelete(id) {
    try {
      await api.delete(`/zones/${id}`);
      setZones(prev => prev.filter(z => z.id !== id));
      setDelZone(null);
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    }
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="mz-wrap">
        {/* Header */}
        <div className="mz-hd">
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <div style={{ width:2, height:18, background:"#00c8ff", borderRadius:1 }} />
              <span className="mz-title">Manage Zones</span>
            </div>
            <div className="mz-sub">GET · POST · PUT · DELETE /api/zones/</div>
          </div>
          <button className="mz-add-btn" onClick={() => { setEditZone(null); setShowModal(true); }}>
            + Add Zone
          </button>
        </div>

        {/* Table */}
        {loading ? (
          [1,2,3].map(i => <div key={i} className="mz-skel" />)
        ) : error ? (
          <div className="mz-err">⚠ {error}</div>
        ) : zones.length === 0 ? (
          <div className="mz-empty">NO ZONES YET — ADD YOUR FIRST ZONE</div>
        ) : (
          <div className="mz-table-wrap">
            <table className="mz-table">
              <thead>
                <tr>
                  <th>NAME</th>
                  <th>CODE</th>
                  <th>COORDINATES</th>
                  <th>REGION</th>
                  <th>POPULATION</th>
                  <th>RISK</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {zones.map(z => {
                  const pred = predictions[z.id];
                  const risk = pred?.overall_risk || "NONE";
                  return (
                    <tr key={z.id}>
                      <td style={{ color:"#f1f5f9", fontWeight:500 }}>{z.name}</td>
                      <td><span className="mz-code">{z.code}</span></td>
                      <td style={{ fontFamily:"monospace", fontSize:11 }}>
                        {z.latitude?.toFixed(4)}, {z.longitude?.toFixed(4)}
                      </td>
                      <td>{z.region || "—"}</td>
                      <td>{z.population?.toLocaleString() || "—"}</td>
                      <td><span className={`mz-risk mz-risk-${risk}`}>{risk}</span></td>
                      <td>
                        <div className="mz-act-row">
                          <button className="mz-act-btn" onClick={() => { setEditZone(z); setShowModal(true); }}>
                            ✏ Edit
                          </button>
                          <button className="mz-del-btn" onClick={() => setDelZone(z)}>
                            ✕ Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <ZoneModal
          zone={editZone}
          onSave={handleSaved}
          onClose={() => { setShowModal(false); setEditZone(null); }}
        />
      )}
      {delZone && (
        <ConfirmDelete
          zone={delZone}
          onConfirm={handleDelete}
          onClose={() => setDelZone(null)}
        />
      )}
    </>
  );
}