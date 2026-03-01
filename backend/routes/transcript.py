from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yt_dlp
import openai
import os
import re
import json
import tempfile

router = APIRouter()

class TranscriptRequest(BaseModel):
    url: str

class TranscriptResponse(BaseModel):
    transcript: list[dict]
    video_id: str
    title: str
    channel: str
    duration: int
    source: str

def extract_video_id(url: str) -> str:
    match = re.search(r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

def get_cookies_path(tmpdir: str) -> str | None:
    """Read cookies from Render secret file and copy to writable temp path."""
    secret_path = "/etc/secrets/cookies.txt"
    if os.path.exists(secret_path):
        cookies_path = os.path.join(tmpdir, "cookies.txt")
        with open(secret_path, "r") as src, open(cookies_path, "w") as dst:
            dst.write(src.read())
        return cookies_path

    # Fallback for local dev
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        cookies_path = os.path.join(tmpdir, "cookies.txt")
        with open(cookies_path, "w") as f:
            f.write(cookies_content)
        return cookies_path

    return None

def base_ydl_opts(cookies_path: str | None) -> dict:
    opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    if cookies_path:
        opts['cookiefile'] = cookies_path
    return opts

@router.post("/", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    try:
        video_id = extract_video_id(request.url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    with tempfile.TemporaryDirectory() as tmpdir:
        cookies_path = get_cookies_path(tmpdir)

        # ── 1. Get video metadata ─────────────────────────────────────────
        metadata = {"title": "Unknown Title", "channel": "Unknown Channel", "duration": 0}
        try:
            with yt_dlp.YoutubeDL(base_ydl_opts(cookies_path)) as ydl:
                info = ydl.extract_info(request.url, download=False)
                metadata = {
                    "title": info.get("title", "Unknown Title"),
                    "channel": info.get("uploader", "Unknown Channel"),
                    "duration": info.get("duration", 0),
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch video info: {str(e)}")

        # ── 2. Try downloading subtitles via yt-dlp ───────────────────────
        try:
            subtitle_path = os.path.join(tmpdir, "subs")
            ydl_opts = {
                **base_ydl_opts(cookies_path),
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'en-US', 'en-GB'],
                'subtitlesformat': 'json3',
                'outtmpl': subtitle_path,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([request.url])

            # Find the downloaded subtitle file
            sub_file = None
            for f in os.listdir(tmpdir):
                if f.startswith("subs") and f.endswith(".json3"):
                    sub_file = os.path.join(tmpdir, f)
                    break

            if sub_file:
                with open(sub_file, "r") as f:
                    sub_data = json.load(f)

                transcript = []
                for event in sub_data.get("events", []):
                    if "segs" not in event:
                        continue
                    text = "".join(s.get("utf8", "") for s in event["segs"]).strip()
                    if not text or text == "\n":
                        continue
                    start = event.get("tStartMs", 0) / 1000
                    duration = event.get("dDurationMs", 2000) / 1000
                    transcript.append({"text": text, "start": start, "duration": duration})

                if transcript:
                    return TranscriptResponse(
                        transcript=transcript,
                        video_id=video_id,
                        title=metadata["title"],
                        channel=metadata["channel"],
                        duration=metadata["duration"],
                        source="youtube_captions"
                    )
        except Exception:
            pass

        # ── 3. Fallback: Whisper via OpenAI ──────────────────────────────
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(
                status_code=422,
                detail="No captions found and no OpenAI API key set for Whisper fallback."
            )

        try:
            client = openai.OpenAI(api_key=openai_key)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True,
            }
            if cookies_path:
                ydl_opts['cookiefile'] = cookies_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([request.url])

            audio_path = None
            for f in os.listdir(tmpdir):
                if f.endswith('.mp3'):
                    audio_path = os.path.join(tmpdir, f)
                    break

            if not audio_path:
                raise Exception("Audio download failed")

            with open(audio_path, 'rb') as audio_file:
                whisper_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            segments = []
            for seg in whisper_response.segments:
                segments.append({
                    "text": seg["text"],
                    "start": seg["start"],
                    "duration": seg["end"] - seg["start"]
                })

            return TranscriptResponse(
                transcript=segments,
                video_id=video_id,
                title=metadata["title"],
                channel=metadata["channel"],
                duration=metadata["duration"],
                source="whisper"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
