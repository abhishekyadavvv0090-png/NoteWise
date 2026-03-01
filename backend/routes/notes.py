from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import json

router = APIRouter()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

class GenerateNotesRequest(BaseModel):
    transcript_chunk: list[dict]
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
    type: str = "ai"

def format_timestamp(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

@router.post("/generate")
async def generate_notes(request: GenerateNotesRequest):
    model = get_gemini_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    start_time = request.transcript_chunk[0]["start"] if request.transcript_chunk else 0
    timestamp_label = format_timestamp(start_time)

    prompt = f"""You are NoteWise, an expert AI note-taking assistant.
Your job is to create intelligent, concise, educational notes from video transcripts.

Rules:
- Be concise but comprehensive
- Highlight key concepts, facts, definitions, and insights
- Use clear language a student would understand
- Return ONLY a JSON array of note objects, no markdown fences
- Each note object: {{"timestamp": <float seconds>, "timestamp_label": "<MM:SS>", "content": "<note text>", "type": "ai"}}
- Generate 1-3 notes per chunk depending on content density

Video: {request.video_title}

Transcript chunk:
{transcript_text}

Return ONLY valid JSON array, nothing else."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
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
    model = get_gemini_client()

    transcript_text = "\n".join([
        f"[{format_timestamp(e['start'])}] {e['text']}"
        for e in request.transcript_chunk
    ])

    prompt = f"""You are NoteWise, an expert AI note-taking assistant.
Generate comprehensive, intelligent notes from a video transcript.

Rules:
- Create well-organized, timestamped notes
- Group related content logically
- Highlight key concepts, definitions, examples, and takeaways
- Return ONLY a JSON array of note objects, no markdown fences
- Each note: {{"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "ai"}}
- Aim for one note per meaningful topic/section

Video: {request.video_title}

Full transcript:
{transcript_text}

Return ONLY valid JSON array, nothing else."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        notes = json.loads(response_text)
        return {"notes": notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-instruction")
async def process_custom_instruction(request: CustomInstructionRequest):
    model = get_gemini_client()

    existing_notes_text = "\n".join([
        f"[{n.get('timestamp_label', '00:00')}] {n.get('content', '')}"
        for n in request.current_notes
    ])

    prompt = f"""You are NoteWise, an AI note-taking assistant.
The user has given a custom instruction to enhance their notes.

Rules:
- Understand the user's instruction and generate new notes that satisfy it
- Return ONLY a JSON array of NEW note objects to add, no markdown fences
- Each note: {{"timestamp": <float>, "timestamp_label": "<MM:SS>", "content": "<note>", "type": "user"}}
- Do NOT repeat existing notes

Video: {request.video_title}

Existing notes:
{existing_notes_text}

User instruction: {request.instruction}

Return ONLY valid JSON array, nothing else."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        new_notes = json.loads(response_text)
        return {"notes": new_notes, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
