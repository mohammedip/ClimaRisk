import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import useAuthStore from "../store/authStore";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  .login-page {
    min-height: 100vh;
    background: #060a0f;
    display: flex;
    font-family: 'DM Sans', sans-serif;
    overflow: hidden;
    position: relative;
  }

  /* Animated background grid */
  .grid-bg {
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    animation: gridMove 20s linear infinite;
  }
  @keyframes gridMove {
    0% { transform: translateY(0); }
    100% { transform: translateY(60px); }
  }

  /* Glowing orbs */
  .orb {
    position: fixed; border-radius: 50%; filter: blur(80px); z-index: 0; pointer-events: none;
  }
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
  @keyframes orbFloat1 {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(40px, 30px); }
  }
  @keyframes orbFloat2 {
    0%,100% { transform: translate(0,0); }
    50% { transform: translate(-30px, -40px); }
  }

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
    border-radius: 100px;
    padding: 6px 16px;
    margin-bottom: 40px;
    width: fit-content;
  }
  .brand-dot { width: 7px; height: 7px; border-radius: 50%; background: #00c8ff; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.5; transform:scale(1.3); } }
  .brand-tag span { color: #00c8ff; font-size: 12px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; }

  .hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(52px, 6vw, 88px);
    font-weight: 800;
    line-height: 0.95;
    color: #fff;
    margin-bottom: 24px;
  }
  .hero-title .accent { color: transparent; -webkit-text-stroke: 1px rgba(0,200,255,0.6); }

  .hero-sub {
    color: #4a6280;
    font-size: 16px;
    line-height: 1.7;
    max-width: 400px;
    margin-bottom: 60px;
  }

  .stats {
    display: flex; gap: 40px;
  }
  .stat-item { display: flex; flex-direction: column; gap: 4px; }
  .stat-num { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 700; color: #fff; }
  .stat-label { font-size: 12px; color: #4a6280; text-transform: uppercase; letter-spacing: 1px; }

  /* Right panel */
  .right-panel {
    width: 480px;
    display: flex; align-items: center; justify-content: center;
    padding: 40px;
    position: relative; z-index: 1;
    border-left: 1px solid rgba(255,255,255,0.04);
    background: rgba(255,255,255,0.01);
  }

  .form-card {
    width: 100%;
    animation: slideUp 0.6s ease both;
  }
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .form-title {
    font-family: 'Syne', sans-serif;
    font-size: 32px; font-weight: 700;
    color: #fff;
    margin-bottom: 8px;
  }
  .form-sub { color: #4a6280; font-size: 14px; margin-bottom: 40px; }

  .field { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
  .field label { color: #8899aa; font-size: 12px; font-weight: 500; letter-spacing: 1px; text-transform: uppercase; }
  .field input {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 14px 18px;
    color: #fff;
    font-family: 'DM Sans', sans-serif;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s, background 0.2s;
  }
  .field input:focus {
    border-color: rgba(0,200,255,0.4);
    background: rgba(0,200,255,0.04);
  }
  .field input::placeholder { color: #2a3a4a; }

  .error-msg {
    background: rgba(255,60,60,0.08);
    border: 1px solid rgba(255,60,60,0.2);
    border-radius: 8px;
    padding: 10px 14px;
    color: #ff6b6b;
    font-size: 13px;
    margin-bottom: 16px;
  }

  .submit-btn {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    background: linear-gradient(135deg, #0066ff, #00c8ff);
    color: #fff;
    font-family: 'Syne', sans-serif;
    font-size: 15px; font-weight: 700;
    cursor: pointer;
    position: relative; overflow: hidden;
    transition: opacity 0.2s, transform 0.2s;
    margin-top: 8px;
  }
  .submit-btn:hover:not(:disabled) { opacity: 0.9; transform: translateY(-1px); }
  .submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .submit-btn::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
  }

  .switch-text {
    text-align: center;
    color: #4a6280;
    font-size: 13px;
    margin-top: 24px;
  }
  .switch-text a { color: #00c8ff; text-decoration: none; font-weight: 500; }
  .switch-text a:hover { text-decoration: underline; }

  @media (max-width: 900px) {
    .left-panel { display: none; }
    .right-panel { width: 100%; border: none; }
  }
`;

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  const login    = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const res = await api.post("/auth/login", { username, password });
      login({ id: res.data.user_id, username: res.data.username, role: res.data.role, team: res.data.team_name }, res.data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally { setLoading(false); }
  }

  return (
    <>
      <style>{CSS}</style>
      <div className="login-page">
        <div className="grid-bg" />
        <div className="orb orb-1" />
        <div className="orb orb-2" />

        {/* Left */}
        <div className="left-panel">
          <div className="brand-tag">
            <div className="brand-dot" />
            <span>Live Monitoring</span>
          </div>
          <h1 className="hero-title">
            Clima<br /><span className="accent">Risk</span>
          </h1>
          <p className="hero-sub">
            Real-time climate risk intelligence for flood and wildfire prediction across monitored zones.
          </p>
          <div className="stats">
            <div className="stat-item">
              <span className="stat-num">98%</span>
              <span className="stat-label">Accuracy</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">24/7</span>
              <span className="stat-label">Monitoring</span>
            </div>
            <div className="stat-item">
              <span className="stat-num">&lt;2s</span>
              <span className="stat-label">Response</span>
            </div>
          </div>
        </div>

        {/* Right */}
        <div className="right-panel">
          <div className="form-card">
            <h2 className="form-title">Welcome back</h2>
            <p className="form-sub">Sign in to access the dashboard</p>

            <form onSubmit={handleSubmit}>
              <div className="field">
                <label>Username</label>
                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="your_username" required />
              </div>
              <div className="field">
                <label>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" required />
              </div>
              {error && <div className="error-msg">{error}</div>}
              <button className="submit-btn" type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Sign in →"}
              </button>
            </form>

            <p className="switch-text">
              No account? <Link to="/register">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}