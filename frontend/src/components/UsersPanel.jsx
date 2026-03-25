import { useState, useEffect, useCallback } from "react";
import api from "../api/client";
import useAuthStore from "../store/authStore";

const ROLES = ["PUBLIC", "RESCUE", "ADMIN"];

const ROLE_CFG = {
  PUBLIC:  { color:"#00c8ff", bg:"rgba(0,200,255,0.1)",   border:"rgba(0,200,255,0.25)"   },
  RESCUE:  { color:"#f59e0b", bg:"rgba(245,158,11,0.1)",  border:"rgba(245,158,11,0.25)"  },
  ADMIN:   { color:"#ff4d6d", bg:"rgba(255,77,109,0.1)",  border:"rgba(255,77,109,0.25)"  },
};

const CSS = `
  @keyframes up-in    { from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)} }
  @keyframes up-pulse { 0%,100%{opacity:1}50%{opacity:.4} }

  .up-wrap       { background:#060a0f; border-radius:8px; padding:20px; font-family:'DM Sans',sans-serif; animation:up-in .3s ease-out; }
  .up-hd         { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }
  .up-title      { font-family:'Syne',sans-serif; font-size:12px; font-weight:700; letter-spacing:3px; color:#f1f5f9; text-transform:uppercase; }
  .up-sub        { font-size:10px; color:#4a6280; margin-top:3px; letter-spacing:1px; }
  .up-sync-btn   { background:transparent; border:1px solid rgba(255,255,255,0.08); border-radius:8px; color:#00c8ff; cursor:pointer; padding:6px 14px; font-size:10px; letter-spacing:1px; font-family:'DM Sans',sans-serif; transition:all .2s; }
  .up-sync-btn:hover { background:rgba(0,200,255,0.06); border-color:rgba(0,200,255,0.3); }

  .up-stats      { display:flex; gap:8px; margin-bottom:16px; }
  .up-stat       { flex:1; padding:10px 8px; background:#0b1120; border-radius:6px; text-align:center; border:1px solid #1a2740; }
  .up-stat-num   { font-family:'Syne',sans-serif; font-size:22px; font-weight:800; }
  .up-stat-lbl   { font-size:9px; color:#4a6280; letter-spacing:1px; margin-top:2px; }

  .up-filters    { display:flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }
  .up-filter     { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 14px; font-size:9px; letter-spacing:1px; font-family:'DM Sans',sans-serif; transition:all .15s; }
  .up-filter.active { border-color:rgba(0,200,255,0.4); color:#00c8ff; background:rgba(0,200,255,0.06); }

  .up-search     { width:100%; background:#0b1120; border:1px solid rgba(255,255,255,0.07); border-radius:8px; color:#94a3b8; padding:8px 14px; font-size:12px; font-family:'DM Sans',sans-serif; margin-bottom:14px; transition:border-color .2s; }
  .up-search:focus { outline:none; border-color:rgba(0,200,255,0.3); color:#f1f5f9; }

  .up-table-wrap { border:1px solid #1a2740; border-radius:8px; overflow:hidden; }
  .up-table      { width:100%; border-collapse:collapse; }
  .up-table th   { background:#0b1120; padding:10px 14px; text-align:left; font-size:9px; letter-spacing:2px; color:#4a6280; font-family:'Syne',sans-serif; font-weight:700; border-bottom:1px solid #1a2740; }
  .up-table td   { padding:12px 14px; font-size:12px; color:#94a3b8; border-bottom:1px solid rgba(255,255,255,0.03); vertical-align:middle; }
  .up-table tr:last-child td { border-bottom:none; }
  .up-table tr:hover td { background:rgba(255,255,255,0.02); }

  .up-avatar     { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-family:'Syne',sans-serif; font-size:12px; font-weight:700; flex-shrink:0; }
  .up-user-cell  { display:flex; align-items:center; gap:10px; }
  .up-username   { font-size:13px; color:#f1f5f9; font-weight:500; }
  .up-email      { font-size:10px; color:#4a6280; }
  .up-team       { font-size:11px; color:#4a6280; font-style:italic; }
  .up-inactive   { font-size:9px; padding:2px 8px; border-radius:4px; background:rgba(239,68,68,0.1); color:#ef4444; border:1px solid rgba(239,68,68,0.25); letter-spacing:1px; }
  .up-you        { font-size:9px; padding:2px 8px; border-radius:4px; background:rgba(0,200,255,0.08); color:#00c8ff; border:1px solid rgba(0,200,255,0.2); letter-spacing:1px; }

  .up-role-select{ background:#060a0f; border:1px solid rgba(255,255,255,0.08); border-radius:6px; color:#94a3b8; padding:4px 8px; font-size:11px; font-family:'DM Sans',sans-serif; cursor:pointer; transition:border-color .2s; }
  .up-role-select:focus { outline:none; border-color:rgba(0,200,255,0.3); }
  .up-role-select:disabled { opacity:.4; cursor:not-allowed; }

  .up-act-row    { display:flex; gap:6px; align-items:center; }
  .up-act-btn    { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 10px; font-size:10px; font-family:'DM Sans',sans-serif; transition:all .2s; white-space:nowrap; }
  .up-act-btn:hover { border-color:rgba(0,200,255,0.3); color:#00c8ff; }
  .up-deact-btn  { background:transparent; border:1px solid rgba(255,255,255,0.07); border-radius:6px; color:#4a6280; cursor:pointer; padding:4px 10px; font-size:10px; font-family:'DM Sans',sans-serif; transition:all .2s; }
  .up-deact-btn:hover { border-color:rgba(239,68,68,0.4); color:#ef4444; }
  .up-act-btn:disabled, .up-deact-btn:disabled { opacity:.3; cursor:not-allowed; }

  .up-skel       { height:56px; background:#0b1120; border-radius:4px; margin-bottom:4px; animation:up-pulse 1.4s ease-in-out infinite; }
  .up-empty      { padding:40px; text-align:center; color:#2a3a4a; font-size:12px; letter-spacing:2px; }
  .up-err        { padding:16px; color:#ef4444; font-size:12px; text-align:center; }
`;

function roleBadge(role) {
  const cfg = ROLE_CFG[role] || ROLE_CFG.PUBLIC;
  return (
    <span style={{
      fontSize:9, fontWeight:700, padding:"2px 8px", borderRadius:4,
      background:cfg.bg, color:cfg.color, border:`1px solid ${cfg.border}`,
      letterSpacing:1, fontFamily:"'Syne',sans-serif"
    }}>{role}</span>
  );
}

function avatarColors(role) {
  const map = { PUBLIC:"rgba(0,200,255,0.15)", RESCUE:"rgba(245,158,11,0.15)", ADMIN:"rgba(255,77,109,0.15)" };
  const txt = { PUBLIC:"#00c8ff", RESCUE:"#f59e0b", ADMIN:"#ff4d6d" };
  return { bg: map[role] || map.PUBLIC, color: txt[role] || txt.PUBLIC };
}

export default function UsersPanel() {
  const [users,    setUsers]    = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);
  const [filter,   setFilter]   = useState("ALL");
  const [search,   setSearch]   = useState("");
  const [updating, setUpdating] = useState(new Set());

  const currentUser = useAuthStore(s => s.user);

  const fetchUsers = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const res = await api.get("/users/");
      setUsers(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  async function changeRole(userId, newRole) {
    setUpdating(s => new Set([...s, `role-${userId}`]));
    try {
      const res = await api.patch(`/users/${userId}/role`, { role: newRole });
      setUsers(prev => prev.map(u => u.id === userId ? res.data : u));
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setUpdating(s => { const n = new Set(s); n.delete(`role-${userId}`); return n; });
    }
  }

  async function toggleActive(user) {
    const key = `active-${user.id}`;
    setUpdating(s => new Set([...s, key]));
    try {
      const endpoint = user.is_active ? `/users/${user.id}/deactivate` : `/users/${user.id}/activate`;
      const res = await api.patch(endpoint);
      setUsers(prev => prev.map(u => u.id === user.id ? res.data : u));
    } catch (e) {
      alert(e.response?.data?.detail || e.message);
    } finally {
      setUpdating(s => { const n = new Set(s); n.delete(key); return n; });
    }
  }

  // Stats
  const total   = users.length;
  const admins  = users.filter(u => u.role === "ADMIN").length;
  const rescue  = users.filter(u => u.role === "RESCUE").length;
  const inactive= users.filter(u => !u.is_active).length;

  // Filter + search
  const displayed = users
    .filter(u => filter === "ALL" || u.role === filter)
    .filter(u => {
      if (!search) return true;
      const q = search.toLowerCase();
      return u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q) || (u.team_name || "").toLowerCase().includes(q);
    });

  return (
    <>
      <style>{CSS}</style>
      <div className="up-wrap">

        {/* Header */}
        <div className="up-hd">
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
              <div style={{ width:2, height:18, background:"#ff4d6d", borderRadius:1 }} />
              <span className="up-title">User Management</span>
            </div>
            <div className="up-sub">GET /api/users/ · ADMIN only</div>
          </div>
          <button className="up-sync-btn" onClick={fetchUsers} disabled={loading}>
            {loading ? "LOADING..." : "↻ REFRESH"}
          </button>
        </div>

        {/* Stats */}
        <div className="up-stats">
          {[
            { label:"TOTAL",    value:total,    color:"#94a3b8" },
            { label:"ADMINS",   value:admins,   color:"#ff4d6d" },
            { label:"RESCUE",   value:rescue,   color:"#f59e0b" },
            { label:"INACTIVE", value:inactive, color:"#4a6280" },
          ].map(s => (
            <div key={s.label} className="up-stat">
              <div className="up-stat-num" style={{ color:s.color }}>{s.value}</div>
              <div className="up-stat-lbl">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="up-filters">
          {["ALL", ...ROLES].map(f => (
            <button key={f} className={`up-filter ${filter===f?"active":""}`} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>

        {/* Search */}
        <input
          className="up-search"
          placeholder="Search by username, email or team..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        {/* Table */}
        {loading ? (
          [1,2,3,4].map(i => <div key={i} className="up-skel" />)
        ) : error ? (
          <div className="up-err">⚠ {error}</div>
        ) : displayed.length === 0 ? (
          <div className="up-empty">NO USERS FOUND</div>
        ) : (
          <div className="up-table-wrap">
            <table className="up-table">
              <thead>
                <tr>
                  <th>USER</th>
                  <th>TEAM</th>
                  <th>ROLE</th>
                  <th>JOINED</th>
                  <th>STATUS</th>
                  <th>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {displayed.map(u => {
                  const isMe    = u.id === currentUser?.id;
                  const av      = avatarColors(u.role);
                  const initials= u.username.slice(0,2).toUpperCase();
                  const joined  = u.created_at ? new Date(u.created_at).toLocaleDateString("fr-FR") : "—";
                  const roleKey = `role-${u.id}`;
                  const actKey  = `active-${u.id}`;

                  return (
                    <tr key={u.id} style={{ opacity: u.is_active ? 1 : 0.55 }}>
                      {/* User cell */}
                      <td>
                        <div className="up-user-cell">
                          <div className="up-avatar" style={{ background:av.bg, color:av.color }}>{initials}</div>
                          <div>
                            <div className="up-username">
                              {u.username}
                              {isMe && <span className="up-you" style={{ marginLeft:6 }}>YOU</span>}
                            </div>
                            <div className="up-email">{u.email}</div>
                          </div>
                        </div>
                      </td>

                      {/* Team */}
                      <td><span className="up-team">{u.team_name || "—"}</span></td>

                      {/* Role selector */}
                      <td>
                        {isMe ? roleBadge(u.role) : (
                          <select
                            className="up-role-select"
                            value={u.role}
                            disabled={updating.has(roleKey)}
                            onChange={e => changeRole(u.id, e.target.value)}
                          >
                            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                          </select>
                        )}
                      </td>

                      {/* Joined */}
                      <td style={{ fontFamily:"monospace", fontSize:11 }}>{joined}</td>

                      {/* Status */}
                      <td>
                        {u.is_active
                          ? <span style={{ fontSize:10, color:"#22c55e", letterSpacing:1 }}>● ACTIVE</span>
                          : <span className="up-inactive">INACTIVE</span>
                        }
                      </td>

                      {/* Actions */}
                      <td>
                        <div className="up-act-row">
                          {!isMe && (
                            <button
                              className={u.is_active ? "up-deact-btn" : "up-act-btn"}
                              disabled={updating.has(actKey)}
                              onClick={() => toggleActive(u)}
                              onMouseEnter={e => { if (u.is_active) { e.target.style.borderColor="rgba(239,68,68,0.4)"; e.target.style.color="#ef4444"; } }}
                              onMouseLeave={e => { e.target.style.borderColor="rgba(255,255,255,0.07)"; e.target.style.color="#4a6280"; }}
                            >
                              {updating.has(actKey) ? "..." : u.is_active ? "Deactivate" : "Activate"}
                            </button>
                          )}
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
    </>
  );
}