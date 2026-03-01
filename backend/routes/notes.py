from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from groq import Groq
import os
import json

router = APIRouter()

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    return Groq(api_key=api_key)

class GenerateNotesRequest(BaseModel):
    transcript_chunk: list[dict]
    video_title: str
    existing_notes: list[dict] = []

class CustomInstructionRequest(BaseModel):
    instruction: str
    current_notes: list[dict]
    video_title: str
    context_transcript: list[dict] = []

def format_timestamp(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

@router.post("/generate")
async def generate_notes(request: GenerateNotesRequest):
    client = get_groq_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    start_time = request.transcript_chunk[0]["start"] if request.transcript_chunk else 0
    timestamp_label = format_timestamp(start_time)

    system_prompt = """You are NoteWise, an expert AI note-taking assistant.
Generate intelligent, concise notes from video transcripts.
Rules:
- Be concise but comprehensive
- Highlight key concepts, facts, definitions, and insights
- Return ONLY a valid JSON array, no markdown fences, no explanation
- Each note: {"timestamp": <float seconds>, "timestamp_label": "<MM:SS>", "content": "<note text>", "type": "ai"}
- Generate 1-3 notes per chunk"""

    user_prompt = f"""Video: {request.video_title}

Transcript:
{transcript_text}

Return ONLY a valid JSON array."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        notes = json.loads(response_text)
        return {"notes": notes, "success": True}
    except json.JSONDecodeError:
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
    client = get_groq_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    system_prompt = """You are NoteWise, an expert AI note-taking assistant.
Generate comprehensive notes from a full video transcript.
Rules:
- Create well-organized timestamped notes
- Highlight key concepts, definitions, examples, takeaways
- Return ONLY a valid JSON array, no markdown fences, no explanation
- Each note: {"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "ai"}
- One note per meaningful topic/section"""

    user_prompt = f"""Video: {request.video_title}

Transcript:
{transcript_text}

Return ONLY a valid JSON array."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.3,
        )
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        notes = json.loads(response_text)
        return {"notes": notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-instruction")
async def process_custom_instruction(request: CustomInstructionRequest):
    client = get_groq_client()

    existing_notes_text = "\n".join([
        f"[{n.get('timestamp_label', '00:00')}] {n.get('content', '')}"
        for n in request.current_notes
    ])

    system_prompt = """You are NoteWise, an AI note-taking assistant.
Generate new notes based on the user's custom instruction.
Rules:
- Return ONLY a valid JSON array of NEW notes to add, no markdown fences
- Each note: {"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "user"}
- Do NOT repeat existing notes"""

    user_prompt = f"""Video: {request.video_title}

Existing notes:
{existing_notes_text}

User instruction: {request.instruction}

Return ONLY a valid JSON array."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        new_notes = json.loads(response_text)
        return {"notes": new_notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
