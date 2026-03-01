from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import os
import json

router = APIRouter()

def get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)

class GenerateNotesRequest(BaseModel):
    transcript_chunk: list[dict]  # [{text, start, duration}]
    video_title: str
    existing_notes: list[dict] = []

class CustomInstructionRequest(BaseModel):
    instruction: str
    current_notes: list[dict]
    video_title: str
    context_transcript: list[dict] = []

class NoteItem(BaseModel):
    timestamp: float
    timestamp_label: str
    content: str
    type: str = "ai"  # "ai" or "user"

def format_timestamp(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def chunk_transcript(transcript: list[dict], chunk_size: int = 30) -> list[list[dict]]:
    """Group transcript entries into ~30-second chunks"""
    chunks = []
    current_chunk = []
    chunk_start = transcript[0]["start"] if transcript else 0

    for entry in transcript:
        current_chunk.append(entry)
        elapsed = entry["start"] - chunk_start
        if elapsed >= chunk_size:
            chunks.append(current_chunk)
            current_chunk = []
            chunk_start = entry["start"] + entry.get("duration", 0)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

@router.post("/generate")
async def generate_notes(request: GenerateNotesRequest):
    """Generate AI notes from a transcript chunk"""
    client = get_claude_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    start_time = request.transcript_chunk[0]["start"] if request.transcript_chunk else 0
    timestamp_label = format_timestamp(start_time)

    system_prompt = """You are NoteWise, an expert AI note-taking assistant. 
Your job is to create intelligent, concise, educational notes from video transcripts.

Rules:
- Be concise but comprehensive
- Highlight key concepts, facts, definitions, and insights
- Use clear language a student would understand
- Format: Return ONLY a JSON array of note objects
- Each note object: {"timestamp": <float seconds>, "timestamp_label": "<MM:SS>", "content": "<note text>", "type": "ai"}
- Generate 1-3 notes per chunk depending on content density
- Focus on what's most valuable to remember"""

    user_prompt = f"""Video: {request.video_title}

Transcript chunk:
{transcript_text}

Generate smart notes for this section. Return ONLY valid JSON array."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text.strip()
        # Clean markdown fences if present
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        notes = json.loads(response_text)

        return {"notes": notes, "success": True}
    except json.JSONDecodeError:
        # Fallback: return a single note
        return {
            "notes": [{
                "timestamp": start_time,
                "timestamp_label": timestamp_label,
                "content": f"Content covered at {timestamp_label}",
                "type": "ai"
            }],
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-full-transcript")
async def process_full_transcript(request: GenerateNotesRequest):
    """Process entire transcript and generate comprehensive notes"""
    client = get_claude_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    system_prompt = """You are NoteWise, an expert AI note-taking assistant.
Generate comprehensive, intelligent notes from a video transcript.

Rules:
- Create well-organized, timestamped notes
- Group related content logically
- Highlight key concepts, definitions, examples, and takeaways
- Return ONLY a JSON array of note objects
- Each note: {"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "ai"}
- Aim for one note per meaningful topic/section"""

    user_prompt = f"""Video: {request.video_title}

Full transcript:
{transcript_text}

Generate comprehensive notes. Return ONLY valid JSON array."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        notes = json.loads(response_text)
        return {"notes": notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-instruction")
async def process_custom_instruction(request: CustomInstructionRequest):
    """Process a custom user instruction and merge into notes"""
    client = get_claude_client()

    existing_notes_text = "\n".join([
        f"[{n.get('timestamp_label', '00:00')}] {n.get('content', '')}"
        for n in request.current_notes
    ])

    system_prompt = """You are NoteWise, an AI note-taking assistant.
The user has given you a custom instruction to enhance their notes.
You should:
1. Understand the user's instruction
2. Generate new note(s) that satisfy the request
3. Return ONLY a JSON array of new note objects to ADD to existing notes
4. Each note: {"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "user"}
5. Do NOT repeat existing notes - only return NEW notes to add"""

    user_prompt = f"""Video: {request.video_title}

Existing notes:
{existing_notes_text}

User instruction: {request.instruction}

Generate new note(s) based on this instruction. Return ONLY valid JSON array."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        new_notes = json.loads(response_text)
        return {"notes": new_notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
