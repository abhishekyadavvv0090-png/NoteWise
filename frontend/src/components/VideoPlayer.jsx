import YouTube from "react-youtube";

export default function VideoPlayer({ videoId, onPlay, onPause, playerRef, isActionMode }) {
  const opts = {
    width: "100%",
    height: "100%",
    playerVars: {
      autoplay: 0,
      modestbranding: 1,
      rel: 0,
      fs: 1,
    },
  };

  const handleReady = (event) => {
    playerRef.current = event.target;
  };

  return (
    <div style={styles.wrapper}>
      {/* Action mode indicator */}
      {isActionMode && (
        <div style={styles.modeBadge}>
          <span style={styles.modeDot} />
          ACTION MODE
        </div>
      )}

      <div style={styles.playerContainer}>
        <YouTube
          videoId={videoId}
          opts={opts}
          onReady={handleReady}
          onPlay={onPlay}
          onPause={onPause}
          style={styles.ytPlayer}
          iframeClassName="yt-iframe"
        />
      </div>

      <style>{`
        .yt-iframe {
          width: 100% !important;
          height: 100% !important;
          display: block;
        }
      `}</style>
    </div>
  );
}

const styles = {
  wrapper: {
    position: "relative",
    background: "#000",
  },
  modeBadge: {
    position: "absolute",
    top: "12px",
    left: "12px",
    zIndex: 10,
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "5px 10px",
    background: "rgba(0,0,0,0.85)",
    border: "1px solid rgba(245, 166, 35, 0.4)",
    borderRadius: "100px",
    fontSize: "10px",
    fontWeight: 700,
    color: "var(--accent)",
    letterSpacing: "0.08em",
    fontFamily: "var(--font-display)",
    backdropFilter: "blur(8px)",
  },
  modeDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "var(--accent)",
    display: "inline-block",
    animation: "blink 1.5s ease-in-out infinite",
  },
  playerContainer: {
    position: "relative",
    paddingBottom: "56.25%", // 16:9
    height: 0,
    overflow: "hidden",
  },
  ytPlayer: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
  },
};
