import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";

const ROLES = [
  { value: "PUBLIC", label: "Public",       sub: "View risk data only",   color: "#00c8ff", icon: "◎" },
  { value: "RESCUE", label: "Rescue Agent", sub: "Full access + AI chat", color: "#f59e0b", icon: "⬡" },
];

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }

  .reg-page {
    min-height: 100vh;
    background: #060a0f;
    display: flex;
    font-family: 'DM Sans', sans-serif;
    overflow: hidden;
    position: relative;
  }

  .grid-bg {
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    animation: gridMove 20s linear infinite;
  }
  @keyframes gridMove { 0% { transform: translateY(0); } 100% { transform: translateY(60px); } }

  .orb { position: fixed; border-radius: 50%; filter: blur(80px); z-index: 0; pointer-events: none; }
  .orb-1 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(0,150,255,0.12), transparent 70%);
    top: -100px; left: -100px;
    animation: orbFloat1 12s ease-in-out infinite;
  }
  .orb-2 {
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0,255,180,0.08), transparent 70%);
    bottom: -80px; right: -80px;
    animation: orbFloat2 15s ease-in-out infinite;
  }
  @keyframes orbFloat1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(40px,30px); } }
  @keyframes orbFloat2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-30px,-40px); } }

  /* Left panel */
  .left-panel {
    flex: 1;
    display: flex; flex-direction: column; justify-content: center;
    padding: 80px;
    position: relative; z-index: 1;
  }

  .brand-tag {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,200,255,0.08);
    border: 1px solid rgba(0,200,255,0.2);
    border-radius: 100px; padding: 6px 16px;
    margin-bottom: 40px; width: fit-content;
  }
  .brand-dot { width: 7px; height: 7px; border-radius: 50%; background: #00c8ff; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.5; transform:scale(1.3); } }
  .brand-tag span { color: #00c8ff; font-size: 12px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; }

  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(48px, 5vw, 80px);
    font-weight: 800; line-height: 0.95;
    color: #fff; margin-bottom: 24px;
  }
  .hero-title .accent { color: transparent; -webkit-text-stroke: 1px rgba(0,200,255,0.6); }

  .hero-sub {
    color: #4a6280; font-size: 15px; line-height: 1.7;
    max-width: 380px; margin-bottom: 48px;
  }

  /* Role preview cards on left */
  .role-preview { display: flex; flex-direction: column; gap: 10px; }
  .role-card {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 18px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.05);
    background: rgba(255,255,255,0.02);
    max-width: 340px;
  }
  .role-card-icon { font-size: 20px; width: 36px; text-align: center; }
  .role-card-text { display: flex; flex-direction: column; gap: 2px; }
  .role-card-name { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; }
  .role-card-desc { font-size: 12px; color: #4a6280; }

  /* Right panel */
  .right-panel {
    width: 500px;
    display: flex; align-items: center; justify-content: center;
    padding: 40px 48px;
    position: relative; z-index: 1;
    border-left: 1px solid rgba(255,255,255,0.04);
    background: rgba(255,255,255,0.01);
    overflow-y: auto;
  }

  .form-card {
    width: 100%;
    animation: slideUp 0.6s ease both;
  }
  @keyframes slideUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }

  .form-title { font-family: 'Syne', sans-serif; font-size: 32px; font-weight: 700; color: #fff; margin-bottom: 8px; }
  .form-sub { color: #4a6280; font-size: 14px; margin-bottom: 36px; }

  .field { margin-bottom: 16px; }
  .field label { display: block; color: #8899aa; font-size: 11px; font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px; }
  .field input {
    width: 100%;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 13px 18px;
    color: #fff; font-family: 'DM Sans', sans-serif; font-size: 15px;
    outline: none; transition: border-color 0.2s, background 0.2s;
  }
  .field input:focus { border-color: rgba(0,200,255,0.35); background: rgba(0,200,255,0.03); }
  .field input::placeholder { color: #2a3a4a; }

  .role-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
  .role-option {
    padding: 12px 10px; border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.02);
    cursor: pointer; transition: all 0.2s; text-align: left;
  }
  .role-option:hover { background: rgba(255,255,255,0.04); }
  .role-opt-icon { font-size: 16px; margin-bottom: 6px; display: block; }
  .role-opt-name { font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; margin-bottom: 2px; }
  .role-opt-desc { font-size: 10px; color: #4a6280; line-height: 1.3; }

  .error-msg {
    background: rgba(255,60,60,0.08); border: 1px solid rgba(255,60,60,0.2);
    border-radius: 8px; padding: 10px 14px; color: #ff6b6b; font-size: 13px; margin-bottom: 14px;
  }

  .submit-btn {
    width: 100%; padding: 15px; border-radius: 10px; border: none;
    background: linear-gradient(135deg, #0066ff, #00c8ff);
    color: #fff; font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700;
    cursor: pointer; position: relative; overflow: hidden;
    transition: opacity 0.2s, transform 0.2s; margin-top: 6px;
  }
  .submit-btn::after { content:''; position:absolute; inset:0; background:linear-gradient(135deg,rgba(255,255,255,0.12),transparent); }
  .submit-btn:hover:not(:disabled) { opacity:0.9; transform:translateY(-1px); }
  .submit-btn:disabled { opacity:0.5; cursor:not-allowed; }

  .switch-text { text-align:center; color:#4a6280; font-size:13px; margin-top:20px; }
  .switch-text a { color:#00c8ff; text-decoration:none; font-weight:500; }

  @media (max-width: 900px) {
    .left-panel { display: none; }
    .right-panel { width: 100%; border: none; }
  }
`;

export default function Register() {
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "PUBLIC", team_name: "" });
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function handleChange(e) { setForm({ ...form, [e.target.name]: e.target.value }); }

  async function handleSubmit(e) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await api.post("/auth/register", form);
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally { setLoading(false); }
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="reg-page">
        <div className="grid-bg" />
        <div className="orb orb-1" />
        <div className="orb orb-2" />

        {/* Left */}
        <div className="left-panel">
          <div className="brand-tag">
            <div className="brand-dot" />
            <span>New Account</span>
          </div>
          <h1 className="hero-title">
            Join the<br /><span className="accent">Network</span>
          </h1>
          <p className="hero-sub">
            Get access to real-time flood and wildfire risk predictions, zone monitoring, and AI-powered emergency response tools.
          </p>

          <div className="role-preview">
            {ROLES.map((r) => (
              <div className="role-card" key={r.value} style={{ borderColor: `${r.color}22` }}>
                <span className="role-card-icon" style={{ color: r.color }}>{r.icon}</span>
                <div className="role-card-text">
                  <span className="role-card-name" style={{ color: r.color }}>{r.label}</span>
                  <span className="role-card-desc">{r.sub}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right */}
        <div className="right-panel">
          <div className="form-card">
            <h2 className="form-title">Create account</h2>
            <p className="form-sub">Fill in your details to get started</p>

            <form onSubmit={handleSubmit}>
              <div className="field">
                <label>Username</label>
                <input name="username" placeholder="your_username" value={form.username} onChange={handleChange} required />
              </div>
              <div className="field">
                <label>Email</label>
                <input name="email" type="email" placeholder="you@example.com" value={form.email} onChange={handleChange} required />
              </div>
              <div className="field">
                <label>Password</label>
                <input name="password" type="password" placeholder="••••••••" value={form.password} onChange={handleChange} required />
              </div>

              <div className="field">
                <label>Role</label>
                <div className="role-grid">
                  {ROLES.map((r) => (
                    <div
                      key={r.value}
                      className="role-option"
                      style={{ borderColor: form.role === r.value ? r.color : undefined, background: form.role === r.value ? `${r.color}11` : undefined }}
                      onClick={() => setForm({ ...form, role: r.value })}
                    >
                      <span className="role-opt-icon" style={{ color: r.color }}>{r.icon}</span>
                      <div className="role-opt-name" style={{ color: form.role === r.value ? r.color : "#cbd5e1" }}>{r.label}</div>
                      <div className="role-opt-desc">{r.sub}</div>
                    </div>
                  ))}
                </div>
              </div>

              {form.role === "RESCUE" && (
                <div className="field">
                  <label>Team Name</label>
                  <input name="team_name" placeholder="e.g. SDIS 13 — Alpha" value={form.team_name} onChange={handleChange} />
                </div>
              )}

              {error && <div className="error-msg">{error}</div>}

              <button className="submit-btn" type="submit" disabled={loading}>
                {loading ? "Creating account..." : "Create account →"}
              </button>
            </form>

            <p className="switch-text">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}