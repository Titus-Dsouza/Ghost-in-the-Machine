# Ghost in the Machine

**Tagline:** *Some code never truly dies.*

A spooky, cartoon‑style Halloween website where visitors chat with the ghost of
a forgotten programming language, generate spooky stories, and consult a
forgotten oracle — powered exclusively by the **Google Gemini API** through a
Flask backend. Built for the Hacktoberfest Open‑Source AI Challenge.

Frontend (HTML/CSS/JavaScript/images) is cleanly separated under `frontend/`;
the AI API key stays exclusively on the backend and is never exposed to the
browser.

---

## Table of Contents
- [Demo](#demo)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Run Locally (macOS)](#setup--run-locally-macos)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Routes](#api-routes)
- [Running the Tests](#running-the-tests)
- [Design & Visuals](#design--visuals)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Demo
Start the Flask server and open `http://127.0.0.1:5000/` (or the port you
configure). The hero section shows a black Halloween world with a floating CSS
ghost mascot, SVG ghost stickers, a glowing pumpkin, small bats, spiderwebs, and
a haunted terminal chatbot.

---

## Features
- **Hero screen** with animated glitch title, label, tagline, and "ENTER IF YOU DARE" / "SUMMON THE GHOST" buttons.
- **Haunted terminal chatbot** that talks to Google Gemini via the Flask backend. Supports free‑form chat and built‑in commands:
  - `/help` – list commands
  - `/story` – generate a spooky story
  - `/oracle` – ask a technical/fictional question
  - `/clear` – clear the conversation
- **Real AI responses** from Gemini (no hardcoded fake replies), with a typing indicator, duplicate‑submission prevention, and safe plain‑text rendering.
- **Conversation context** is maintained during the session (recent turns are sent with each message).
- **Story panel** with clickable story ideas that call `POST /api/story`.
- **Oracle section** with example questions about old tech.
- **About section and footer** explaining the Gemini‑only architecture.
- **Responsive, accessible** layout. Keyboard‑friendly and works on mobile.
- **Backend‑only API key:** `GEMINI_API_KEY` is read on the server; the frontend contains no secrets.

---

## Tech Stack
- **Frontend:** HTML5, CSS3 (custom properties, animations), vanilla JavaScript (`fetch()`), inline SVG artwork.
- **Backend:** Python 3, Flask, `python-dotenv`.
- **AI:** Google Gemini API via the official `google-genai` Python SDK (a Flash model).

---

## Project Structure
```text
Halloween/
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
│       ├── ghost.svg
│       ├── ghost-happy.svg
│       ├── pumpkin.svg
│       └── bat.svg
│
└── tests/
    └── test_app.py
```

---

## Setup & Run Locally (macOS)

### 1. Create and activate a Python virtual environment
```bash
cd /Users/titusdsouza/Halloween
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Obtain a Gemini API key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account and click **Create API key**.
3. Copy the key (it looks like `AIzaSy...`).

### 4. Add the key to `.env`
```bash
cp .env.example .env
```

Then edit `.env` and paste your key:
```
GEMINI_API_KEY=AIzaSyYourActualKeyFromAIStudio
GEMINI_MODEL=gemini-1.5-flash
```

The `.env` file is gitignored and must never be committed. The key is read
exclusively by the backend (`app.py`); it is never sent to the browser.

### 5. Configure `GEMINI_MODEL`
`GEMINI_MODEL` selects the Gemini model (default: `gemini-1.5-flash`, a
currently supported Flash model). Change it in `.env` if you want a different
supported model.

### 6. Run the Flask application
```bash
# Default port 5000
python app.py

# Or with a custom port
PORT=5002 python app.py
```

### 7. Open the website and test the chatbot
Open `http://127.0.0.1:5000/` (or `http://127.0.0.1:5002/` if you used that
port). Click **ENTER IF YOU DARE**, type a message in the terminal, and hit
**Send** or **Enter**. The ghost will answer using a real Gemini generation.

Note: if no valid `GEMINI_API_KEY` is in `.env`, the chatbot will clearly
report that setup is required instead of faking a response.

---

## Configuration
| Variable | Example | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google Gemini API key (required for AI responses). |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use (default `gemini-1.5-flash`). |
| `PORT` | `5002` | Port for the Flask development server (default `5000`). |

All values belong in `.env` (see `.env.example` for placeholders).

---

## Usage
1. **Enter the haunted terminal** – click *ENTER IF YOU DARE* or *SUMMON THE GHOST*.
2. **Chat** – type a message and press *Enter* or click *Send*.
3. **Commands** – use the shortcut buttons or type `/help`, `/story`, `/oracle`, `/clear`.
4. **Stories** – click any story idea in *TALES FROM THE CURSED CIRCUIT*, or *Generate Another Story*.
5. **Oracle** – click an example question or type your own and press *Enter*.

The status indicator below the terminal shows:
- `GHOST ONLINE — GEMINI CONNECTED` – API key configured and the backend is ready.
- `SETUP REQUIRED — GEMINI API KEY MISSING` – no key found; add one to `.env` and restart.

---

## API Routes
- `GET /` – serves `frontend/index.html`.
- `GET /api/health` – application status and whether Gemini is configured (no secrets revealed).
- `POST /api/chat` – body `{ "message": "...", "conversation": [...] }`; returns `{ "response": "..." }`. Errors return `400` for invalid input, `503` when Gemini is not configured, and `502`/`504`/`429` style statuses for API, network, timeout, or empty-response failures.
- `POST /api/story` – generates a spooky story through Gemini; returns `{ "story": "..." }`.

---

## Running the Tests
```bash
source venv/bin/activate
pytest
```
Tests use the Flask test client and a faked Gemini client, so no API key or
network access is required.

---

## Design & Visuals
- **Colors:** Black/midnight-purple backgrounds (`#080609`, `#151019`), pumpkin orange (`#FF7518`), haunted purple (`#7138A8`), ghost white, toxic green.
- **Animations:** Floating ghost mascot, glitch title effect, floating SVG ghost stickers, pulsing glowing pumpkin, flapping bats, subtle CSS/SVG spiderwebs.
- **Assets:** Ghost, happy ghost, pumpkin, and bat artwork are local SVGs under `frontend/images/`; no external image URLs.
- **Typography:** *Outfit* for headings, *Inter* for body, monospace for the terminal.

---

## Troubleshooting
| Issue | Likely Cause | Fix |
|-------|---------------|-----|
| `SETUP REQUIRED — GEMINI API KEY MISSING` | No `GEMINI_API_KEY` in `.env` | Add a valid key from Google AI Studio to `.env` and restart the app. |
| `401` / `503` errors from `/api/chat` | Invalid or missing API key | Verify the key in `.env` matches AI Studio and restart the app. |
| `429` errors | Gemini rate limit / quota exceeded | Wait, then retry; check your quota in Google AI Studio. |
| Empty or failed AI response | API error, network failure, timeout | Backend returns a clear error message instead of faking a response; check your connection and key. |
| Port conflict (`Address already in use`) | Another process on port 5000 | Run with a different port: `PORT=5002 python app.py`. |
| Assets returning 404 | `frontend/` files missing | Ensure `frontend/css/style.css`, `frontend/js/script.js`, and `frontend/images/*.svg` exist and were not moved out of `frontend/`. |
| `google.genai` import error | Dependencies not installed | Run `pip install -r requirements.txt` inside the activated virtual environment. |

No Ollama, `ollama serve`, `ollama pull`, Gemma, or port `11434` are used anywhere in this project.

---

## License
This project is released under the MIT License.

---

*Happy haunting!*
- **Tests:** pytest with the Flask test client (no network, faked Gemini client).