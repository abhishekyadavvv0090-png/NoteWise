from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yt_dlp
import openai
import httpx
import os
import re
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

def get_video_metadata(url: str) -> dict:
    """Get video metadata using yt-dlp (no auth needed for metadata on most videos)."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown Title"),
                "channel": info.get("uploader", "Unknown Channel"),
                "duration": info.get("duration", 0),
            }
    except Exception:
        return {"title": "Unknown Title", "channel": "Unknown Channel", "duration": 0}

@router.post("/", response_model=TranscriptResponse)
async def get_transcript(request: TranscriptRequest):
    try:
        video_id = extract_video_id(request.url)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    metadata = get_video_metadata(request.url)

    # ── 1. Supadata API (primary) ─────────────────────────────────────────
    supadata_key = os.getenv("SUPADATA_API_KEY")
    if supadata_key:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.get(
                    "https://api.supadata.ai/v1/youtube/transcript",
                    params={"url": request.url, "lang": "en", "text": "false"},
                    headers={"x-api-key": supadata_key}
                )
            if res.status_code == 200:
                data = res.json()
                # Supadata returns list of {text, offset, duration}
                transcript = []
                for item in data.get("content", []):
                    transcript.append({
                        "text": item.get("text", ""),
                        "start": item.get("offset", 0) / 1000,  # ms to seconds
                        "duration": item.get("duration", 2000) / 1000,
                    })
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
            pass  # Fall through to Whisper

    # ── 2. Fallback: Whisper via OpenAI ──────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(
            status_code=422,
            detail="No transcript available. Set SUPADATA_API_KEY or OPENAI_API_KEY."
        )

    try:
        client = openai.OpenAI(api_key=openai_key)
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, 'audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': True,
            }
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
