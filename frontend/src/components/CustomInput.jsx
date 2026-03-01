import { useState } from "react";
import { SendHorizonal, Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "Add more detail about this topic",
  "Include key formulas or equations",
  "Summarize the main argument",
  "Add a glossary of terms used",
];

export default function CustomInput({ value, onChange, onSend, isLoading }) {
  const [focused, setFocused] = useState(false);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim()) onSend();
    }
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <Sparkles size={13} style={{ color: "var(--accent)" }} />
        <span style={styles.title}>Custom Instruction</span>
        <span style={styles.hint}>press Enter to send</span>
      </div>

      <div style={{
        ...styles.inputRow,
        ...(focused ? styles.inputRowFocused : {}),
      }}>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder='e.g. "Add more detail about photosynthesis" or "Include this formula: E=mc²"'
          style={styles.textarea}
          rows={2}
          disabled={isLoading}
        />
        <button
          onClick={onSend}
          disabled={isLoading || !value.trim()}
          style={{
            ...styles.sendBtn,
            ...((!value.trim() || isLoading) ? styles.sendBtnDisabled : {}),
          }}
        >
          {isLoading ? (
            <span style={styles.spinner} />
          ) : (
            <SendHorizonal size={16} />
          )}
        </button>
      </div>

      {/* Quick suggestions */}
      <div style={styles.suggestions}>
        {SUGGESTIONS.map((s, i) => (
          <button
            key={i}
            onClick={() => { onChange(s); }}
            style={styles.suggestion}
            disabled={isLoading}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    background: "var(--bg-card)",
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius)",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    boxShadow: "var(--shadow)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  title: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--text-primary)",
    flex: 1,
  },
  hint: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  inputRow: {
    display: "flex",
    gap: "10px",
    alignItems: "flex-end",
    background: "var(--bg-secondary)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-sm)",
    padding: "10px 12px",
    transition: "border-color 0.2s, box-shadow 0.2s",
  },
  inputRowFocused: {
    borderColor: "rgba(245, 166, 35, 0.3)",
    boxShadow: "0 0 0 3px rgba(245, 166, 35, 0.06)",
  },
  textarea: {
    flex: 1,
    background: "none",
    border: "none",
    color: "var(--text-primary)",
    fontSize: "13px",
    lineHeight: 1.6,
    resize: "none",
    caretColor: "var(--accent)",
    "::placeholder": { color: "var(--text-muted)" },
  },
  sendBtn: {
    width: "34px",
    height: "34px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "var(--accent)",
    color: "#000",
    borderRadius: "8px",
    flexShrink: 0,
    fontWeight: 700,
    transition: "all 0.15s",
    border: "none",
  },
  sendBtnDisabled: {
    opacity: 0.35,
    cursor: "not-allowed",
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
  suggestions: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  suggestion: {
    padding: "4px 10px",
    background: "var(--bg-hover)",
    border: "1px solid var(--border)",
    borderRadius: "100px",
    fontSize: "11px",
    color: "var(--text-secondary)",
    cursor: "pointer",
    transition: "all 0.15s",
    fontFamily: "var(--font-body)",
  },
};
