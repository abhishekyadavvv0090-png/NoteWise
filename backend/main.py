from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import transcript, notes, pdf_export
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="NoteWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://notewise-kohl.vercel.app",  # ✅ Production frontend
        "http://localhost:5173",              # ✅ Local dev (Vite)
        "http://localhost:3000",              # ✅ Local dev (CRA)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcript.router, prefix="/api/transcript", tags=["transcript"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(pdf_export.router, prefix="/api/pdf", tags=["pdf"])

@app.get("/")
async def root():
    return {"message": "NoteWise API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}
