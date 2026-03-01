
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp
import openai
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
    source: str  # "youtube_captions" or "whisper"

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Invalid YouTube URL")

def write_cookies_file(tmpdir: str) -> str | None:
    # First try secret file (Render production)
    secret_path = "/etc/secrets/cookies.txt"
    if os.path.exists(secret_path):
        return secret_path

    # Fallback: env variable (local dev)
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if not cookies_content:
        return None
    cookies_path = os.path.join(tmpdir, "cookies.txt")
    with open(cookies_path, "w") as f:
        f.write(cookies_content)
    return cookies_path

def get_video_metadata(url: str, cookies_path: str | None) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path

    try:
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

    with tempfile.TemporaryDirectory() as tmpdir:
        cookies_path = write_cookies_file(tmpdir)
        metadata = get_video_metadata(request.url, cookies_path)

        # ── 1. Try YouTube captions ──────────────────────────────────────────
        try:
            if cookies_path:
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['en', 'en-US', 'en-GB'],
                    cookies=cookies_path,
                )
            else:
                transcript_list = YouTubeTranscriptApi.get_transcript(
                    video_id,
                    languages=['en', 'en-US', 'en-GB'],
                )

            return TranscriptResponse(
                transcript=transcript_list,
                video_id=video_id,
                title=metadata["title"],
                channel=metadata["channel"],
                duration=metadata["duration"],
                source="youtube_captions"
            )
        except (TranscriptsDisabled, NoTranscriptFound):
            pass
        except Exception:
            pass

        # ── 2. Fallback: Whisper via OpenAI ──────────────────────────────────
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(
                status_code=422,
                detail="No YouTube captions available and no OpenAI API key set for Whisper fallback."
            )

        try:
            client = openai.OpenAI(api_key=openai_key)
            audio_path = os.path.join(tmpdir, "audio.mp3")

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

            for f in os.listdir(tmpdir):
                if f.endswith('.mp3'):
                    audio_path = os.path.join(tmpdir, f)
                    break

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
