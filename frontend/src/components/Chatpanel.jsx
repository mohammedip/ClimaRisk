import { useState, useRef, useEffect } from "react";
import useAuthStore from "../store/authStore";
import ReactMarkdown from "react-markdown";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

  .chat-fab {
    position: fixed; bottom: 28px; right: 28px; z-index: 2000;
    display: flex; align-items: center; gap: 10px;
    padding: 14px 22px; border-radius: 16px; border: none;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    color: #fff; font-family: 'Syne', sans-serif;
    font-size: 14px; font-weight: 700; cursor: pointer;
    box-shadow: 0 8px 32px rgba(245,158,11,0.35);
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .chat-fab:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(245,158,11,0.45); }

  .chat-panel {
    position: fixed; bottom: 100px; right: 28px; z-index: 2000;
    width: 420px; height: 580px;
    background: #0b1120;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    display: flex; flex-direction: column;
    box-shadow: 0 24px 80px rgba(0,0,0,0.6);
    animation: panelIn 0.25s ease both;
    overflow: hidden;
  }
  @keyframes panelIn {
    from { opacity: 0; transform: translateY(16px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  .chat-header {
    padding: 18px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,0.02);
  }
  .chat-header-left { display: flex; align-items: center; gap: 12px; }
  .chat-avatar {
    width: 36px; height: 36px; border-radius: 10px;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  .chat-title { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: #fff; }
  .chat-sub   { font-size: 11px; color: #4a6280; }
  .online-dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(1.4)} }

  .close-btn {
    background: rgba(255,255,255,0.05); border: none;
    color: #4a6280; width: 30px; height: 30px; border-radius: 8px;
    cursor: pointer; font-size: 16px; transition: all 0.15s;
    display: flex; align-items: center; justify-content: center;
  }
  .close-btn:hover { background: rgba(255,77,109,0.15); color: #ff4d6d; }

  .chat-messages {
    flex: 1; overflow-y: auto; padding: 16px;
    display: flex; flex-direction: column; gap: 12px;
    scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent;
  }

  .msg { display: flex; flex-direction: column; gap: 4px; max-width: 85%; }
  .msg.user { align-self: flex-end; align-items: flex-end; }
  .msg.ai   { align-self: flex-start; align-items: flex-start; }

  .msg-bubble {
    padding: 10px 14px; border-radius: 14px;
    font-size: 13px; line-height: 1.6; white-space: pre-wrap;
  }
  .msg.user .msg-bubble {
    background: linear-gradient(135deg, #0066ff, #0099ff);
    color: #fff; border-bottom-right-radius: 4px;
  }
  .  .msg.ai .msg-bubble {
    padding: 14px 16px; border-radius: 3px 14px 14px 14px;
    font-size: 13px; line-height: 1.7;
    background: #0d1829;
    border: 1px solid rgba(255,255,255,0.07);
    color: #94a3b8;
    box-shadow: 0 2px 16px rgba(0,0,0,0.3);
    white-space: normal;
  }

  /* paragraphs */
  .msg.ai .msg-bubble p {
    margin: 0 0 10px 0; color: #94a3b8;
  }
  .msg.ai .msg-bubble p:last-child { margin-bottom: 0; }

  /* headings */
  .msg.ai .msg-bubble h1,
  .msg.ai .msg-bubble h2 {
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700;
    color: #f1f5f9; letter-spacing: 0.5px;
    margin: 14px 0 6px 0; padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .msg.ai .msg-bubble h3 {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 700;
    color: #f59e0b; letter-spacing: 0.5px;
    margin: 12px 0 5px 0;
  }
  .msg.ai .msg-bubble h4 {
    font-size: 12px; font-weight: 600;
    color: #cbd5e1; margin: 10px 0 4px 0;
  }

  /* lists */
  .msg.ai .msg-bubble ul {
    margin: 6px 0 10px 0; padding: 0;
    list-style: none;
  }
  .msg.ai .msg-bubble ul li {
    position: relative; padding-left: 16px; margin-bottom: 6px;
    color: #94a3b8;
  }
  .msg.ai .msg-bubble ul li::before {
    content: '▸';
    position: absolute; left: 0;
    color: #f59e0b; font-size: 10px; top: 2px;
  }
  .msg.ai .msg-bubble ol {
    margin: 6px 0 10px 0; padding-left: 20px;
  }
  .msg.ai .msg-bubble ol li {
    margin-bottom: 6px; color: #94a3b8;
    padding-left: 4px;
  }
  .msg.ai .msg-bubble ol li::marker {
    color: #f59e0b; font-weight: 700; font-size: 11px;
  }

  /* nested lists */
  .msg.ai .msg-bubble ul ul,
  .msg.ai .msg-bubble ol ol,
  .msg.ai .msg-bubble ul ol,
  .msg.ai .msg-bubble ol ul {
    margin: 4px 0 4px 8px;
  }
  .msg.ai .msg-bubble ul ul li::before { color: #64748b; }

  /* inline emphasis */
  .msg.ai .msg-bubble strong {
    color: #e2e8f0; font-weight: 600;
  }
  .msg.ai .msg-bubble em {
    color: #64748b; font-style: italic;
  }

  /* inline code */
  .msg.ai .msg-bubble code {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.15);
    border-radius: 4px; padding: 1px 6px;
    font-size: 11px; color: #f59e0b;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    letter-spacing: 0;
  }

  /* code blocks */
  .msg.ai .msg-bubble pre {
    background: #060d18;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid rgba(245,158,11,0.4);
    border-radius: 8px; padding: 12px 14px;
    overflow-x: auto; margin: 10px 0;
  }
  .msg.ai .msg-bubble pre code {
    background: none; border: none; padding: 0;
    color: #64748b; font-size: 11px; line-height: 1.7;
  }

  /* blockquote — used for warnings / notes */
  .msg.ai .msg-bubble blockquote {
    margin: 10px 0; padding: 10px 14px;
    background: rgba(245,158,11,0.05);
    border-left: 3px solid #f59e0b;
    border-radius: 0 6px 6px 0;
    color: #78716c;
  }
  .msg.ai .msg-bubble blockquote p { color: #78716c; margin: 0; }

  /* horizontal rule — section divider */
  .msg.ai .msg-bubble hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 12px 0;
  }

  /* tables */
  .msg.ai .msg-bubble table {
    width: 100%; border-collapse: collapse;
    margin: 10px 0; font-size: 11px;
  }
  .msg.ai .msg-bubble th {
    background: rgba(245,158,11,0.08);
    color: #f59e0b; font-weight: 600;
    padding: 6px 10px; text-align: left;
    border-bottom: 1px solid rgba(245,158,11,0.2);
    letter-spacing: 0.5px;
  }
  .msg.ai .msg-bubble td {
    padding: 6px 10px; color: #64748b;
    border-bottom: 1px solid rgba(255,255,255,0.04);
  }
  .msg.ai .msg-bubble tr:last-child td { border-bottom: none; }

  /* links */
  .msg.ai .msg-bubble a {
    color: #38bdf8; text-decoration: none;
    border-bottom: 1px solid rgba(56,189,248,0.3);
    transition: border-color 0.15s;
  }
  .msg.ai .msg-bubble a:hover { border-color: #38bdf8; }
  .msg-time { font-size: 10px; color: #2a3a4a; }

  .typing { display: flex; gap: 4px; align-items: center; padding: 4px 0; }
  .typing span {
    width: 6px; height: 6px; border-radius: 50%;
    background: #4a6280; animation: bounce 1.2s infinite;
  }
  .typing span:nth-child(2) { animation-delay: 0.2s; }
  .typing span:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce { 0%,80%,100%{transform:translateY(0)} 40%{transform:translateY(-6px)} }

  .chat-input-area {
    padding: 14px 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
    display: flex; gap: 10px; align-items: flex-end;
  }
  .chat-input {
    flex: 1; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 10px 14px;
    color: #fff; font-family: 'DM Sans', sans-serif; font-size: 13px;
    resize: none; outline: none; min-height: 40px; max-height: 100px;
    transition: border-color 0.2s;
  }
  .chat-input:focus { border-color: rgba(245,158,11,0.4); }
  .chat-input::placeholder { color: #2a3a4a; }

  .send-btn {
    width: 40px; height: 40px; border-radius: 10px; border: none;
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    color: #fff; font-size: 16px; cursor: pointer;
    transition: opacity 0.2s, transform 0.2s; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
  }
  .send-btn:hover:not(:disabled) { opacity: 0.85; transform: scale(1.05); }
  .send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .empty-state {
    flex: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 12px;
    color: #2a3a4a; text-align: center; padding: 24px;
  }
  .empty-icon { font-size: 40px; opacity: 0.5; }
  .empty-title { font-family: 'Syne', sans-serif; font-size: 15px; color: #4a6280; }
  .empty-sub   { font-size: 12px; line-height: 1.6; }

  .suggestions { display: flex; flex-direction: column; gap: 6px; width: 100%; margin-top: 8px; }
  .suggestion {
    padding: 8px 12px; border-radius: 8px;
    border: 1px solid rgba(245,158,11,0.2);
    background: rgba(245,158,11,0.05);
    color: #f59e0b; font-size: 12px; cursor: pointer;
    text-align: left; transition: background 0.15s;
  }
  .suggestion:hover { background: rgba(245,158,11,0.1); }
`;

const SUGGESTIONS = [
  "What is the evacuation protocol for flood zones?",
  "What are the wildfire risk indicators?",
  "How should I respond to a CRITICAL alert?",
];

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ChatPanel({ zoneContext = "" }) {
  const [open,     setOpen]     = useState(false);
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem("chat_messages");
      return saved ? JSON.parse(saved).map(m => ({ ...m, time: new Date(m.time) })) : [];
    } catch { return []; }
  });
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const bottomRef = useRef(null);

  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    localStorage.setItem("chat_messages", JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function clearChat() {
    setMessages([]);
    localStorage.removeItem("chat_messages");
  }

  async function sendMessage(text) {
    const question = text || input.trim();
    if (!question || loading) return;
    setInput("");

    const userMsg = { role: "user", content: question, time: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const aiMsg = { role: "ai", content: "", time: new Date() };
    setMessages((prev) => [...prev, aiMsg]);

    try {
      const response = await fetch("/api/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ question, zone_context: zoneContext }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const reader  = response.body.getReader();
      const decoder = new TextDecoder();
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        full += decoder.decode(value);
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { ...aiMsg, content: full };
          return updated;
        });
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...aiMsg,
          content: `⚠️ ${err.message}`,
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <>
      <style>{CSS}</style>

      {!open && (
        <button className="chat-fab" onClick={() => setOpen(true)}>
          🤖 AI Emergency Chat
        </button>
      )}

      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-header-left">
              <div className="chat-avatar">🤖</div>
              <div>
                <div className="chat-title">ClimaRisk AI</div>
                <div className="chat-sub">Powered by Mistral · RAG enabled</div>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div className="online-dot" />
              <button className="close-btn" title="Clear chat" onClick={clearChat}>🗑</button>
              <button className="close-btn" onClick={() => setOpen(false)}>✕</button>
            </div>
          </div>

          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🌊🔥</div>
              <div className="empty-title">Ask me anything</div>
              <div className="empty-sub">I can answer questions about emergency protocols, risk zones, and climate predictions.</div>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestion" onClick={() => sendMessage(s)}>{s}</button>
                ))}
              </div>
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`msg ${msg.role}`}>
                  <div className="msg-bubble">
                    {msg.role === "ai" ? (
                      msg.content
                        ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                        : loading && i === messages.length - 1
                          ? <div className="typing"><span/><span/><span/></div>
                          : null
                    ) : (
                      msg.content
                    )}
                  </div>
                  <div className="msg-time">{formatTime(msg.time)}</div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}

          <div className="chat-input-area">
            <textarea
              className="chat-input"
              placeholder="Ask about protocols, zones, predictions..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button className="send-btn" onClick={() => sendMessage()} disabled={!input.trim() || loading}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}