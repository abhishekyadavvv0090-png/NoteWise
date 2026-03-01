import { useState, useRef, useCallback, useEffect } from "react";
import axios from "axios";
import Header from "./components/Header.jsx";
import VideoPlayer from "./components/VideoPlayer.jsx";
import NotesPanel from "./components/NotesPanel.jsx";
import URLInput from "./components/URLInput.jsx";
import CustomInput from "./components/CustomInput.jsx";
import StatusBar from "./components/StatusBar.jsx";

const API_BASE = "/api";

export default function App() {
  const [url, setUrl] = useState("");
  const [videoId, setVideoId] = useState(null);
  const [videoMeta, setVideoMeta] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [notes, setNotes] = useState([]);
  const [actionMode, setActionMode] = useState(false); // "Activate Action Mode" toggled
  const [isPlaying, setIsPlaying] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);
  const [sessionEnded, setSessionEnded] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | active | processing | done
  const [customInstruction, setCustomInstruction] = useState("");
  const [isSendingInstruction, setIsSendingInstruction] = useState(false);

  const noteProcessingRef = useRef(false);
  const processedUpToRef = useRef(0);
  const playerRef = useRef(null);
  const noteIntervalRef = useRef(null);

  // Extract video ID from URL
  const extractVideoId = (url) => {
    const match = url.match(/(?:v=|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})/);
    return match ? match[1] : null;
  };

  // Activate action mode: load video + transcript
  const handleActivateActionMode = async () => {
    if (!url.trim()) {
      setError("Please enter a YouTube URL first.");
      return;
    }
    const vid = extractVideoId(url.trim());
    if (!vid) {
      setError("Invalid YouTube URL. Please check and try again.");
      return;
    }

    setError("");
    setStatus("loading");
    setIsLoadingTranscript(true);
    setNotes([]);
    setTranscript([]);
    setSessionEnded(false);
    processedUpToRef.current = 0;

    try {
      setVideoId(vid);
      setActionMode(true);

      // Fetch transcript + metadata
      const res = await axios.post(`${API_BASE}/transcript/`, { url: url.trim() });
      setTranscript(res.data.transcript);
      setVideoMeta({
        title: res.data.title,
        channel: res.data.channel,
        duration: res.data.duration,
        url: url.trim(),
        source: res.data.source,
      });
      setStatus("ready");
      setIsLoadingTranscript(false);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load video transcript.");
      setStatus("idle");
      setIsLoadingTranscript(false);
      setActionMode(false);
    }
  };

  // When video starts playing → begin AI note generation
  const handleVideoPlay = useCallback(async () => {
    setIsPlaying(true);
    if (!actionMode || transcript.length === 0 || sessionEnded) return;

    setStatus("active");

    // Generate notes progressively every 15 seconds of transcript
    if (noteIntervalRef.current) clearInterval(noteIntervalRef.current);

    // Initial batch: first 60 seconds
    generateNotesForRange(0, 60);

    noteIntervalRef.current = setInterval(() => {
      const currentTime = playerRef.current?.getCurrentTime?.() || 0;
      const lookAheadEnd = currentTime + 90;

      if (processedUpToRef.current < lookAheadEnd) {
        generateNotesForRange(processedUpToRef.current, lookAheadEnd);
      }
    }, 15000);
  }, [actionMode, transcript, sessionEnded]);

  const handleVideoPause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const generateNotesForRange = async (startSec, endSec) => {
    if (noteProcessingRef.current || transcript.length === 0) return;
    if (processedUpToRef.current >= endSec) return;

    const chunk = transcript.filter(
      (e) => e.start >= processedUpToRef.current && e.start < endSec
    );

    if (chunk.length === 0) {
      processedUpToRef.current = endSec;
      return;
    }

    noteProcessingRef.current = true;
    setIsProcessing(true);

    try {
      const res = await axios.post(`${API_BASE}/notes/generate`, {
        transcript_chunk: chunk,
        video_title: videoMeta?.title || "Video",
        existing_notes: notes,
      });

      if (res.data.notes?.length > 0) {
        setNotes((prev) => {
          const existingTs = new Set(prev.map((n) => n.timestamp));
          const newNotes = res.data.notes.filter((n) => !existingTs.has(n.timestamp));
          return [...prev, ...newNotes].sort((a, b) => a.timestamp - b.timestamp);
        });
      }
      processedUpToRef.current = endSec;
    } catch (err) {
      console.error("Note generation error:", err);
    } finally {
      noteProcessingRef.current = false;
      setIsProcessing(false);
    }
  };

  // Stop session → generate PDF
  const handleStopSession = async () => {
    if (noteIntervalRef.current) clearInterval(noteIntervalRef.current);
    setIsPlaying(false);
    setSessionEnded(true);
    setStatus("done");

    // Process any remaining unprocessed transcript
    const remainingChunk = transcript.filter(
      (e) => e.start >= processedUpToRef.current
    );
    if (remainingChunk.length > 0 && !noteProcessingRef.current) {
      setIsProcessing(true);
      try {
        const res = await axios.post(`${API_BASE}/notes/process-full-transcript`, {
          transcript_chunk: remainingChunk,
          video_title: videoMeta?.title || "Video",
        });
        if (res.data.notes?.length > 0) {
          setNotes((prev) => {
            const existingTs = new Set(prev.map((n) => n.timestamp));
            const newNotes = res.data.notes.filter((n) => !existingTs.has(n.timestamp));
            return [...prev, ...newNotes].sort((a, b) => a.timestamp - b.timestamp);
          });
        }
      } catch (err) {
        console.error("Final processing error:", err);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  // Send custom instruction
  const handleSendInstruction = async () => {
    if (!customInstruction.trim() || !videoMeta) return;
    setIsSendingInstruction(true);

    try {
      const res = await axios.post(`${API_BASE}/notes/custom-instruction`, {
        instruction: customInstruction.trim(),
        current_notes: notes,
        video_title: videoMeta.title,
        context_transcript: transcript.slice(0, 50),
      });

      if (res.data.notes?.length > 0) {
        setNotes((prev) =>
          [...prev, ...res.data.notes].sort((a, b) => a.timestamp - b.timestamp)
        );
      }
      setCustomInstruction("");
    } catch (err) {
      setError("Failed to process instruction: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsSendingInstruction(false);
    }
  };

  // Export PDF
  const handleExportPDF = async () => {
    if (!videoMeta || notes.length === 0) return;
    setStatus("exporting");

    try {
      const res = await axios.post(
        `${API_BASE}/pdf/export`,
        {
          video_title: videoMeta.title,
          channel: videoMeta.channel,
          url: videoMeta.url,
          duration: videoMeta.duration,
          notes: notes,
        },
        { responseType: "blob" }
      );

      const blob = new Blob([res.data], { type: "application/pdf" });
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `NoteWise_${videoMeta.title.slice(0, 40)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError("PDF export failed. Please try again.");
    } finally {
      setStatus("done");
    }
  };

  // Reset everything
  const handleReset = () => {
    if (noteIntervalRef.current) clearInterval(noteIntervalRef.current);
    setUrl("");
    setVideoId(null);
    setVideoMeta(null);
    setTranscript([]);
    setNotes([]);
    setActionMode(false);
    setIsPlaying(false);
    setIsProcessing(false);
    setSessionEnded(false);
    setError("");
    setStatus("idle");
    setCustomInstruction("");
    processedUpToRef.current = 0;
    noteProcessingRef.current = false;
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (noteIntervalRef.current) clearInterval(noteIntervalRef.current);
    };
  }, []);

  return (
    <div style={styles.app}>
      {/* Background effect */}
      <div style={styles.bgGlow} />

      <Header onReset={handleReset} hasSession={actionMode} />

      <main style={styles.main}>
        {/* URL Input Phase */}
        {!actionMode && (
          <URLInput
            url={url}
            onUrlChange={setUrl}
            onActivate={handleActivateActionMode}
            isLoading={isLoadingTranscript}
            error={error}
          />
        )}

        {/* Active Session Phase */}
        {actionMode && (
          <div style={styles.sessionLayout}>
            {/* Status Bar */}
            <StatusBar
              status={status}
              isProcessing={isProcessing}
              videoMeta={videoMeta}
              notesCount={notes.length}
              onStop={handleStopSession}
              onExport={handleExportPDF}
              onReset={handleReset}
              sessionEnded={sessionEnded}
            />

            {error && (
              <div style={styles.errorBanner}>
                ⚠️ {error}
                <button onClick={() => setError("")} style={styles.errorClose}>×</button>
              </div>
            )}

            {/* Main Content: Player + Notes */}
            <div style={styles.contentGrid}>
              {/* Left: Video Player */}
              <div style={styles.playerSection}>
                <div style={styles.playerCard}>
                  <VideoPlayer
                    videoId={videoId}
                    onPlay={handleVideoPlay}
                    onPause={handleVideoPause}
                    playerRef={playerRef}
                    isActionMode={actionMode}
                  />
                </div>

                {/* Custom Instruction Input */}
                {actionMode && !sessionEnded && (
                  <CustomInput
                    value={customInstruction}
                    onChange={setCustomInstruction}
                    onSend={handleSendInstruction}
                    isLoading={isSendingInstruction}
                  />
                )}
              </div>

              {/* Right: Notes Panel */}
              <div style={styles.notesSection}>
                <NotesPanel
                  notes={notes}
                  isProcessing={isProcessing}
                  isPlaying={isPlaying}
                  sessionEnded={sessionEnded}
                  onSeek={(timestamp) => {
                    playerRef.current?.seekTo?.(timestamp);
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

const styles = {
  app: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "var(--bg-primary)",
    position: "relative",
    overflow: "hidden",
  },
  bgGlow: {
    position: "fixed",
    top: "-20%",
    right: "-10%",
    width: "600px",
    height: "600px",
    background: "radial-gradient(circle, rgba(245,166,35,0.04) 0%, transparent 70%)",
    pointerEvents: "none",
    zIndex: 0,
  },
  main: {
    flex: 1,
    position: "relative",
    zIndex: 1,
    padding: "0 24px 40px",
    maxWidth: "1400px",
    margin: "0 auto",
    width: "100%",
  },
  sessionLayout: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  contentGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 420px",
    gap: "20px",
    alignItems: "start",
  },
  playerSection: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  playerCard: {
    borderRadius: "var(--radius)",
    overflow: "hidden",
    background: "#000",
    boxShadow: "var(--shadow-lg)",
    border: "1px solid var(--border)",
  },
  notesSection: {
    position: "sticky",
    top: "20px",
    maxHeight: "calc(100vh - 100px)",
    display: "flex",
    flexDirection: "column",
  },
  errorBanner: {
    background: "rgba(248, 113, 113, 0.1)",
    border: "1px solid rgba(248, 113, 113, 0.3)",
    borderRadius: "var(--radius-sm)",
    padding: "12px 16px",
    color: "#F87171",
    fontSize: "14px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
  },
  errorClose: {
    background: "none",
    color: "#F87171",
    fontSize: "18px",
    lineHeight: 1,
    padding: "0 4px",
    flexShrink: 0,
  },
};
