import { useEffect, useRef } from "react";
import { Bot, User, Clock } from "lucide-react";

export default function NotesPanel({ notes, isProcessing, isPlaying, sessionEnded, onSeek }) {
  const bottomRef = useRef(null);
  const panelRef = useRef(null);

  // Auto-scroll to latest note
  useEffect(() => {
    if (isPlaying && notes.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [notes.length, isPlaying]);

  return (
    <div style={styles.panel}>
      {/* Panel Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.title}>Notes</span>
          {notes.length > 0 && (
            <span style={styles.count}>{notes.length}</span>
          )}
        </div>
        {isProcessing && (
          <div style={styles.processingBadge}>
            <span style={styles.processingDot} />
            Generating...
          </div>
        )}
      </div>

      {/* Notes List */}
      <div style={styles.notesList} ref={panelRef}>
        {notes.length === 0 && !isProcessing && (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>📝</div>
            <div style={styles.emptyTitle}>
              {isPlaying ? "Generating notes..." : "Notes will appear here"}
            </div>
            <div style={styles.emptyDesc}>
              {sessionEnded
                ? "Session ended. Export your notes as PDF."
                : "Press play on the video to start AI note-taking"}
            </div>
          </div>
        )}

        {notes.map((note, i) => (
          <NoteItem
            key={`${note.timestamp}-${i}`}
            note={note}
            onSeek={onSeek}
            index={i}
          />
        ))}

        {isProcessing && notes.length > 0 && (
          <div style={styles.processingItem}>
            <span style={styles.thinkingDots}>
              <span />
              <span />
              <span />
            </span>
            <span style={styles.processingText}>AI is thinking...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Footer */}
      {notes.length > 0 && (
        <div style={styles.footer}>
          <span style={styles.footerStat}>
            {notes.filter(n => n.type === "user").length} custom · {notes.filter(n => n.type !== "user").length} AI
          </span>
        </div>
      )}
    </div>
  );
}

function NoteItem({ note, onSeek, index }) {
  const isUser = note.type === "user";

  return (
    <div
      style={{
        ...styles.noteItem,
        ...(isUser ? styles.noteItemUser : {}),
        animationDelay: `${Math.min(index * 0.05, 0.3)}s`,
      }}
      className="animate-slideIn"
    >
      <div style={styles.noteHeader}>
        <button
          onClick={() => onSeek(note.timestamp)}
          style={styles.timestampBtn}
          title="Jump to this moment"
        >
          <Clock size={10} />
          {note.timestamp_label || "00:00"}
        </button>

        <div style={{
          ...styles.typeTag,
          ...(isUser ? styles.typeTagUser : styles.typeTagAI)
        }}>
          {isUser ? <User size={9} /> : <Bot size={9} />}
          {isUser ? "Custom" : "AI"}
        </div>
      </div>

      <p style={styles.noteContent}>{note.content}</p>
    </div>
  );
}

const styles = {
  panel: {
    background: "var(--bg-card)",
    border: "1px solid var(--border-strong)",
    borderRadius: "var(--radius)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    maxHeight: "calc(100vh - 100px)",
    height: "calc(100vh - 100px)",
    boxShadow: "var(--shadow)",
  },
  header: {
    padding: "16px 18px",
    borderBottom: "1px solid var(--border)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexShrink: 0,
  },
  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  title: {
    fontFamily: "var(--font-display)",
    fontSize: "15px",
    fontWeight: 700,
    color: "var(--text-primary)",
  },
  count: {
    background: "var(--accent-dim)",
    color: "var(--accent)",
    fontSize: "11px",
    fontWeight: 700,
    padding: "2px 8px",
    borderRadius: "100px",
    border: "1px solid rgba(245,166,35,0.2)",
  },
  processingBadge: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "11px",
    color: "var(--blue)",
    fontWeight: 500,
  },
  processingDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "var(--blue)",
    animation: "blink 1.2s ease-in-out infinite",
    display: "inline-block",
  },
  notesList: {
    flex: 1,
    overflowY: "auto",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "60px 20px",
    gap: "12px",
    textAlign: "center",
  },
  emptyIcon: {
    fontSize: "32px",
    opacity: 0.4,
  },
  emptyTitle: {
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text-secondary)",
  },
  emptyDesc: {
    fontSize: "12px",
    color: "var(--text-muted)",
    lineHeight: 1.6,
  },
  noteItem: {
    background: "var(--bg-secondary)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-sm)",
    padding: "12px 14px",
    borderLeft: "3px solid var(--blue)",
    cursor: "default",
    transition: "border-color 0.2s, background 0.2s",
  },
  noteItemUser: {
    borderLeft: "3px solid var(--accent)",
    background: "rgba(245, 166, 35, 0.04)",
  },
  noteHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "8px",
  },
  timestampBtn: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "3px 8px",
    background: "var(--blue-dim)",
    color: "var(--blue)",
    borderRadius: "100px",
    fontSize: "10px",
    fontWeight: 700,
    fontFamily: "var(--font-display)",
    cursor: "pointer",
    border: "none",
    letterSpacing: "0.05em",
    transition: "all 0.15s",
  },
  typeTag: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "10px",
    fontWeight: 600,
    padding: "2px 7px",
    borderRadius: "100px",
    letterSpacing: "0.03em",
  },
  typeTagAI: {
    background: "var(--blue-dim)",
    color: "var(--blue)",
    border: "1px solid rgba(91,141,239,0.2)",
  },
  typeTagUser: {
    background: "var(--accent-dim)",
    color: "var(--accent)",
    border: "1px solid rgba(245,166,35,0.2)",
  },
  noteContent: {
    fontSize: "13px",
    color: "var(--text-primary)",
    lineHeight: 1.65,
    fontWeight: 400,
  },
  processingItem: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "10px 14px",
    background: "var(--blue-dim)",
    borderRadius: "var(--radius-sm)",
    border: "1px dashed rgba(91,141,239,0.3)",
  },
  thinkingDots: {
    display: "flex",
    gap: "4px",
    "& span": {
      width: "6px",
      height: "6px",
      borderRadius: "50%",
      background: "var(--blue)",
      animation: "blink 1.2s ease-in-out infinite",
    }
  },
  processingText: {
    fontSize: "12px",
    color: "var(--blue)",
    fontWeight: 500,
  },
  footer: {
    padding: "10px 18px",
    borderTop: "1px solid var(--border)",
    flexShrink: 0,
  },
  footerStat: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
};
