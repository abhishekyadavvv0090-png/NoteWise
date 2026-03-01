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
    transcript: list[dict]  # [{text, start, duration}]
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

def get_video_metadata(url: str) -> dict:
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }
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

    metadata = get_video_metadata(request.url)

    # Try YouTube captions first
    try:
        transcript_list = YouTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
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

    # Fallback: Whisper via OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(
            status_code=422,
            detail="No YouTube captions available and no OpenAI API key set for Whisper fallback."
        )

    try:
        client = openai.OpenAI(api_key=openai_key)
        # Download audio
        with tempfile.TemporaryDirectory() as tmpdir:
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([request.url])

            # Find downloaded file
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
