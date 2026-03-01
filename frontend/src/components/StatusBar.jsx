import { Square, Download, Tv2, Loader2 } from "lucide-react";

function formatDuration(secs) {
  if (!secs) return "";
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

const STATUS_CONFIG = {
  loading:   { label: "Loading...", color: "var(--text-muted)", dot: "var(--text-muted)" },
  ready:     { label: "Ready · Press Play to Start", color: "var(--text-secondary)", dot: "var(--text-secondary)" },
  active:    { label: "Live Note-Taking", color: "var(--success)", dot: "var(--success)" },
  processing:{ label: "Processing...", color: "var(--blue)", dot: "var(--blue)" },
  done:      { label: "Session Complete", color: "var(--accent)", dot: "var(--accent)" },
  exporting: { label: "Exporting PDF...", color: "var(--blue)", dot: "var(--blue)" },
  idle:      { label: "Idle", color: "var(--text-muted)", dot: "var(--text-muted)" },
};

export default function StatusBar({
  status, isProcessing, videoMeta, notesCount,
  onStop, onExport, onReset, sessionEnded
}) {
  const cfg = STATUS_CONFIG[isProcessing ? "processing" : status] || STATUS_CONFIG.idle;
  const displayStatus = isProcessing ? "processing" : status;

  return (
    <div style={styles.bar}>
      {/* Left: Status + Video Info */}
      <div style={styles.left}>
        <div style={styles.statusPill}>
          <span style={{ ...styles.statusDot, background: cfg.dot }} />
          <span style={{ color: cfg.color, fontSize: "12px", fontWeight: 600 }}>
            {cfg.label}
          </span>
        </div>

        {videoMeta && (
          <>
            <div style={styles.divider} />
            <div style={styles.videoInfo}>
              <Tv2 size={13} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
              <span style={styles.videoTitle} title={videoMeta.title}>
                {videoMeta.title}
              </span>
              {videoMeta.duration > 0 && (
                <span style={styles.duration}>{formatDuration(videoMeta.duration)}</span>
              )}
            </div>
          </>
        )}
      </div>

      {/* Right: Action Buttons */}
      <div style={styles.right}>
        {notesCount > 0 && (
          <span style={styles.notesCount}>{notesCount} notes</span>
        )}

        {!sessionEnded && (
          <button onClick={onStop} style={styles.stopBtn}>
            <Square size={13} fill="currentColor" />
            Stop & Finish
          </button>
        )}

        {sessionEnded && notesCount > 0 && (
          <button
            onClick={onExport}
            style={styles.exportBtn}
            disabled={status === "exporting"}
          >
            {status === "exporting" ? (
              <Loader2 size={13} style={{ animation: "spin 0.8s linear infinite" }} />
            ) : (
              <Download size={13} />
            )}
            {status === "exporting" ? "Exporting..." : "Download PDF"}
          </button>
        )}
      </div>
    </div>
  );
}

const styles = {
  bar: {
    background: "var(--bg-card)",
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius)",
    padding: "12px 18px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "16px",
    boxShadow: "var(--shadow)",
  },
  left: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    flex: 1,
    minWidth: 0,
  },
  statusPill: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexShrink: 0,
  },
  statusDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    display: "inline-block",
    animation: "blink 1.5s ease-in-out infinite",
  },
  divider: {
    width: "1px",
    height: "16px",
    background: "var(--border-strong)",
    flexShrink: 0,
  },
  videoInfo: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    minWidth: 0,
    flex: 1,
  },
  videoTitle: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    fontWeight: 500,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    flex: 1,
  },
  duration: {
    fontSize: "11px",
    color: "var(--text-muted)",
    flexShrink: 0,
    padding: "2px 8px",
    background: "var(--bg-hover)",
    borderRadius: "100px",
    fontFamily: "var(--font-display)",
    fontWeight: 600,
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexShrink: 0,
  },
  notesCount: {
    fontSize: "12px",
    color: "var(--text-muted)",
    padding: "4px 10px",
    background: "var(--bg-hover)",
    borderRadius: "100px",
    border: "1px solid var(--border)",
  },
  stopBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "8px 16px",
    background: "rgba(248, 113, 113, 0.1)",
    border: "1px solid rgba(248, 113, 113, 0.3)",
    borderRadius: "var(--radius-sm)",
    color: "#F87171",
    fontSize: "13px",
    fontWeight: 600,
    fontFamily: "var(--font-body)",
  },
  exportBtn: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    padding: "8px 18px",
    background: "var(--accent)",
    border: "none",
    borderRadius: "var(--radius-sm)",
    color: "#000",
    fontSize: "13px",
    fontWeight: 700,
    fontFamily: "var(--font-display)",
    boxShadow: "0 4px 14px rgba(245,166,35,0.3)",
    cursor: "pointer",
  },
};
