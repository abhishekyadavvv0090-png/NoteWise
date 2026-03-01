# NoteWise 📝
### AI-Powered YouTube Video Note-Taking Web App

NoteWise lets you paste any YouTube URL, watch the video inside the app, and automatically generates intelligent timestamped notes using Claude AI — in real time.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite |
| YouTube Player | react-youtube |
| Backend | FastAPI (Python) |
| AI Notes | Anthropic Claude Sonnet |
| Transcription | YouTube Captions → Whisper (fallback) |
| PDF Export | ReportLab |
| Database | MongoDB (optional for MVP) |

---

## Project Structure

```
notewise/
├── frontend/               # React app
│   ├── src/
│   │   ├── App.jsx         # Main app logic
│   │   ├── index.css       # Global styles
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── URLInput.jsx    # Landing page + URL entry
│   │       ├── VideoPlayer.jsx # YouTube embed
│   │       ├── NotesPanel.jsx  # Live notes display
│   │       ├── CustomInput.jsx # User instruction input
│   │       └── StatusBar.jsx   # Session controls + export
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── backend/                # FastAPI server
    ├── main.py             # App entry point
    ├── requirements.txt
    ├── .env.example        # ← Copy this to .env
    └── routes/
        ├── transcript.py   # YouTube captions + Whisper
        ├── notes.py        # Claude AI note generation
        └── pdf_export.py   # Professional PDF export
```

---

## Setup Instructions

### Step 1 — Get API Keys

You'll need:

1. **Anthropic API Key** (required for Claude AI notes)
   - Go to https://console.anthropic.com
   - Create an account → API Keys → Create Key

2. **OpenAI API Key** (optional — only needed if YouTube videos have no captions)
   - Go to https://platform.openai.com/api-keys
   - Create an account → API keys → Create new secret key

3. **MongoDB Connection String**
   - Log into your MongoDB Atlas account at https://cloud.mongodb.com
   - Create a new project → Build a Database → Free tier (M0)
   - Click "Connect" → "Drivers" → Copy the connection string
   - Replace `<password>` with your actual database password

---

### Step 2 — Backend Setup

```bash
# Navigate to backend
cd notewise/backend

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
```

Now open `.env` and fill in your keys:

```env
ANTHROPIC_API_KEY=sk-ant-...         # Your Anthropic key
OPENAI_API_KEY=sk-...                # Your OpenAI key (optional)
MONGODB_URI=mongodb+srv://...        # Your MongoDB connection string
MONGODB_DB_NAME=notewise
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

You should see: `Uvicorn running on http://127.0.0.1:8000`

Test it: Open http://localhost:8000 → should show `{"message": "NoteWise API is running"}`

---

### Step 3 — Frontend Setup

```bash
# Navigate to frontend (new terminal)
cd notewise/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

You should see: `Local: http://localhost:5173`

Open http://localhost:5173 in your browser — NoteWise is running! 🎉

---

## How to Use

1. **Open NoteWise** at http://localhost:5173
2. **Paste a YouTube URL** (any public video with captions works best)
3. **Click "Activate Action Mode"** — the video loads and transcript is fetched
4. **Click Play** on the video — AI notes start generating automatically
5. During playback, **type custom instructions** in the box (e.g. "Add more detail about X")
6. When done, **click "Stop & Finish"**
7. **Click "Download PDF"** to export your professional notes

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/transcript/` | Fetch YouTube transcript (captions or Whisper) |
| POST | `/api/notes/generate` | Generate notes from a transcript chunk |
| POST | `/api/notes/process-full-transcript` | Generate notes for remaining transcript |
| POST | `/api/notes/custom-instruction` | Process user custom instruction |
| POST | `/api/pdf/export` | Export notes as professional PDF |
| GET | `/health` | Health check |

---

## Troubleshooting

**"No captions available"**
→ Set your `OPENAI_API_KEY` in `.env` for Whisper fallback.
→ Or try a video that has captions enabled (most popular videos do).

**"ANTHROPIC_API_KEY not set"**
→ Make sure your `.env` file exists in the `backend/` folder with the correct key.

**Frontend can't reach backend**
→ Make sure backend is running on port 8000.
→ The Vite proxy config in `vite.config.js` forwards `/api` requests automatically.

**PDF export is empty**
→ You need to have at least 1 note generated before exporting.

---

## Next Steps (Post-MVP)

- [ ] User authentication (Clerk or Supabase Auth)
- [ ] Save sessions to MongoDB
- [ ] Edit/delete individual notes
- [ ] Multiple language support
- [ ] Share notes via link
- [ ] Chrome extension version

---

Built with ❤️ using React, FastAPI, and Claude AI.
