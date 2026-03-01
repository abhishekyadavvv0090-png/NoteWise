import { RotateCcw } from "lucide-react";

export default function Header({ onReset, hasSession }) {
  return (
    <header style={styles.header}>
      <div style={styles.inner}>
        <div style={styles.logo}>
          <div style={styles.logoIcon}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5z" fill="var(--accent)" opacity="0.9"/>
              <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <span style={styles.logoText}>NoteWise</span>
            <span style={styles.logoTagline}>AI YouTube Notes</span>
          </div>
        </div>

        <div style={styles.nav}>
          {hasSession && (
            <button onClick={onReset} style={styles.resetBtn}>
              <RotateCcw size={14} />
              New Session
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

const styles = {
  header: {
    borderBottom: "1px solid var(--border)",
    backdropFilter: "blur(20px)",
    background: "rgba(10, 10, 15, 0.85)",
    position: "sticky",
    top: 0,
    zIndex: 100,
  },
  inner: {
    maxWidth: "1400px",
    margin: "0 auto",
    padding: "14px 24px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  logo: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  logoIcon: {
    width: "40px",
    height: "40px",
    background: "var(--accent-dim)",
    border: "1px solid rgba(245, 166, 35, 0.2)",
    borderRadius: "10px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  logoText: {
    fontFamily: "var(--font-display)",
    fontSize: "20px",
    fontWeight: 700,
    color: "var(--text-primary)",
    display: "block",
    lineHeight: 1.2,
    letterSpacing: "-0.3px",
  },
  logoTagline: {
    fontSize: "10px",
    color: "var(--text-muted)",
    display: "block",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  resetBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 14px",
    background: "var(--bg-hover)",
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius-sm)",
    color: "var(--text-secondary)",
    fontSize: "13px",
    fontWeight: 500,
  },
};
