import { useState } from "react";
import { Zap, Youtube } from "lucide-react";

export default function URLInput({ url, onUrlChange, onActivate, isLoading, error }) {
  const [focused, setFocused] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") onActivate();
  };

  return (
    <div style={styles.wrapper}>
      {/* Hero section */}
      <div style={styles.hero}>
        <div style={styles.badge}>
          <Zap size={12} style={{ color: "var(--accent)" }} />
          <span>AI-Powered Note Generation</span>
        </div>

        <h1 style={styles.headline}>
          Turn any YouTube video
          <br />
          <span style={styles.headlineAccent}>into smart notes</span>
        </h1>

        <p style={styles.subtext}>
          Paste a YouTube URL, watch the video, and let NoteWise generate
          <br />
          intelligent timestamped notes in real-time — automatically.
        </p>
      </div>

      {/* URL Input Card */}
      <div style={styles.card}>
        <div style={styles.inputGroup}>
          <div style={{
            ...styles.inputWrapper,
            ...(focused ? styles.inputWrapperFocused : {}),
            ...(error ? styles.inputWrapperError : {}),
          }}>
            <Youtube size={18} style={styles.inputIcon} />
            <input
              type="text"
              value={url}
              onChange={(e) => onUrlChange(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              onKeyDown={handleKeyDown}
              placeholder="https://www.youtube.com/watch?v=..."
              style={styles.input}
              disabled={isLoading}
            />
          </div>

          <button
            onClick={onActivate}
            disabled={isLoading || !url.trim()}
            style={{
              ...styles.activateBtn,
              ...(isLoading ? styles.activateBtnLoading : {}),
              ...((!url.trim() && !isLoading) ? styles.activateBtnDisabled : {}),
            }}
          >
            {isLoading ? (
              <>
                <span style={styles.spinner} />
                Loading...
              </>
            ) : (
              <>
                <Zap size={16} />
                Activate Action Mode
              </>
            )}
          </button>
        </div>

        {error && (
          <div style={styles.errorMsg}>⚠️ {error}</div>
        )}

        <div style={styles.hint}>
          Works with any public YouTube video that has captions · Auto-falls back to Whisper AI
        </div>
      </div>

      {/* Feature highlights */}
      <div style={styles.features}>
        {[
          { icon: "⚡", title: "Real-time Notes", desc: "Notes appear live as the video plays" },
          { icon: "🤖", title: "Claude AI", desc: "Powered by Anthropic's Claude for intelligent summaries" },
          { icon: "📄", title: "PDF Export", desc: "Download a clean, professional PDF instantly" },
          { icon: "✏️", title: "Custom Instructions", desc: "Add your own notes or guide the AI mid-session" },
        ].map((f, i) => (
          <div key={i} style={styles.featureCard}>
            <div style={styles.featureIcon}>{f.icon}</div>
            <div>
              <div style={styles.featureTitle}>{f.title}</div>
              <div style={styles.featureDesc}>{f.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "calc(100vh - 80px)",
    padding: "60px 0",
    gap: "40px",
  },
  hero: {
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "16px",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 14px",
    background: "var(--accent-dim)",
    border: "1px solid rgba(245, 166, 35, 0.2)",
    borderRadius: "100px",
    fontSize: "12px",
    color: "var(--accent)",
    fontWeight: 500,
    letterSpacing: "0.03em",
    textTransform: "uppercase",
  },
  headline: {
    fontFamily: "var(--font-display)",
    fontSize: "clamp(36px, 5vw, 56px)",
    fontWeight: 800,
    lineHeight: 1.1,
    letterSpacing: "-1px",
    color: "var(--text-primary)",
  },
  headlineAccent: {
    background: "linear-gradient(135deg, var(--accent) 0%, #FF8C00 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  subtext: {
    fontSize: "16px",
    color: "var(--text-secondary)",
    lineHeight: 1.7,
    maxWidth: "500px",
  },
  card: {
    width: "100%",
    maxWidth: "680px",
    background: "var(--bg-card)",
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius)",
    padding: "28px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    boxShadow: "var(--shadow)",
  },
  inputGroup: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
  },
  inputWrapper: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    gap: "10px",
    background: "var(--bg-secondary)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-sm)",
    padding: "0 16px",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  inputWrapperFocused: {
    borderColor: "rgba(245, 166, 35, 0.4)",
    boxShadow: "0 0 0 3px rgba(245, 166, 35, 0.08)",
  },
  inputWrapperError: {
    borderColor: "rgba(248, 113, 113, 0.4)",
  },
  inputIcon: {
    color: "var(--text-muted)",
    flexShrink: 0,
  },
  input: {
    flex: 1,
    background: "none",
    border: "none",
    color: "var(--text-primary)",
    fontSize: "14px",
    padding: "14px 0",
    caretColor: "var(--accent)",
    width: "100%",
  },
  activateBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "14px 22px",
    background: "var(--accent)",
    color: "#000",
    borderRadius: "var(--radius-sm)",
    fontSize: "14px",
    fontWeight: 700,
    fontFamily: "var(--font-display)",
    whiteSpace: "nowrap",
    flexShrink: 0,
    transition: "all 0.2s",
    boxShadow: "0 4px 16px rgba(245, 166, 35, 0.3)",
  },
  activateBtnLoading: {
    opacity: 0.7,
    cursor: "wait",
  },
  activateBtnDisabled: {
    opacity: 0.4,
    cursor: "not-allowed",
    boxShadow: "none",
  },
  spinner: {
    display: "inline-block",
    width: "14px",
    height: "14px",
    border: "2px solid rgba(0,0,0,0.2)",
    borderTopColor: "#000",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
  errorMsg: {
    color: "#F87171",
    fontSize: "13px",
    padding: "8px 12px",
    background: "rgba(248, 113, 113, 0.08)",
    borderRadius: "var(--radius-sm)",
    border: "1px solid rgba(248, 113, 113, 0.2)",
  },
  hint: {
    fontSize: "12px",
    color: "var(--text-muted)",
    textAlign: "center",
  },
  features: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "12px",
    maxWidth: "680px",
    width: "100%",
  },
  featureCard: {
    display: "flex",
    alignItems: "flex-start",
    gap: "14px",
    padding: "16px",
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-sm)",
  },
  featureIcon: {
    fontSize: "20px",
    lineHeight: 1,
    flexShrink: 0,
  },
  featureTitle: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--text-primary)",
    marginBottom: "2px",
  },
  featureDesc: {
    fontSize: "12px",
    color: "var(--text-muted)",
    lineHeight: 1.5,
  },
};
