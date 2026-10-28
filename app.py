"""
Ghost in the Machine — Flask backend.

Frontend (HTML/CSS/JS/images) lives in frontend/ and is served by this app.
AI power comes exclusively from the Google Gemini API via the official
google-genai Python SDK. No Ollama, no Gemma, no local models.
"""

import os
import logging
from flask import Flask, request, jsonify, send_from_directory

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (backend only — the API key never leaves this process)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Conversation window kept for context (most recent turns).
MAX_CONVERSATION_TURNS = 6

# ---------------------------------------------------------------------------
# Gemini client (lazily created so the app boots even without an API key)
# ---------------------------------------------------------------------------
_gemini_client = None


def get_gemini_client():
    """Return the Gemini client, or None if no API key is configured."""
    global _gemini_client
    if _gemini_client is not None or not GEMINI_API_KEY:
        return _gemini_client
    try:
        from google import genai

        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as exc:  # pragma: no cover - SDK import issues
        logging.warning("Failed to initialise Google Gemini client: %s", exc)
        _gemini_client = False  # mark as unavailable
    return _gemini_client or None




# ---------------------------------------------------------------------------
# System prompts — mischievous cartoon ghost personality
# ---------------------------------------------------------------------------
GHOST_SYSTEM_PROMPT = (
    "You are a mischievous, cartoonish ghost who haunts an abandoned computer. "
    "Speak in a witty, slightly sarcastic, spooky tone. Keep answers concise "
    "(a couple of sentences unless asked to elaborate). When relevant, give "
    "accurate technical facts about computing, and clearly mark fictional or "
    "spooky elements as make-believe. Never claim to be a real person. "
    "Stay in character as a friendly Halloween ghost."
)

STORY_SYSTEM_PROMPT = (
    "You are a ghost storyteller haunting an old computer. Generate a short, "
    "original, playful spooky story about programming, technology, or forgotten "
    "code. Keep it atmospheric, cartoonish rather than gory, and suitable for a "
    "broad audience. End with a light mischievous ghost signature."
)

# ---------------------------------------------------------------------------
# Flask app — static files are served from frontend/
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="frontend", static_url_path="/frontend")


@app.route("/")
def index():
    """Serve the haunted homepage."""
    return send_from_directory("frontend", "index.html")


@app.route("/api/health")
def health():
    """Report application status without revealing any secrets."""
    return jsonify(
        {
            "status": "ok",
            "gemini_configured": bool(GEMINI_API_KEY),
            "model": GEMINI_MODEL if GEMINI_API_KEY else None,
        }
    )


# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------
def _gemini_error_status(error):
    """Map a Gemini/SDK error to a sensible HTTP status code."""
    code = getattr(error, "code", None)
    if code:
        return code
    message = str(error).lower()
    if "rate limit" in message or "429" in message or "quota" in message:
        return 429
    if "unauthenticated" in message or "401" in message or "api key" in message:
        return 401
    if "permission" in message or "403" in message:
        return 403
    if "not found" in message or "404" in message:
        return 404
    if "deadline" in message or "timeout" in message or "504" in message:
        return 504
    if "500" in message or "502" in message or "503" in message:
        return int(next(part for part in ("500", "502", "503") if part in message))
    return 502


def _gemini_error_message(error, status):
    """Return a user-friendly explanation of a Gemini API failure."""
    message = str(error)
    if status == 400 and ("API key not valid" in message or "API_KEY_INVALID" in message):
        return "The Gemini API key is not valid. Check GEMINI_API_KEY in .env and restart the app."
    if status == 401:
        return "Gemini API authentication failed. Check GEMINI_API_KEY in .env."
    if status == 403:
        return "Gemini API access forbidden. Check your API key's permissions."
    if status == 404:
        return f"The Gemini model '{GEMINI_MODEL}' was not found. Check GEMINI_MODEL in .env."
    if status == 429:
        return "Gemini API rate limit or quota exceeded. Please try again later."
    if status in (500, 502, 503, 504):
        return "The Gemini API is temporarily unavailable or the request timed out. Please try again later."
    return f"Gemini API request failed (HTTP {status})."


class _GeminiError(RuntimeError):
    """Raised when the Gemini API cannot produce a usable answer."""

    def __init__(self, message, http_status=502):
        super().__init__(message)
        self.http_status = http_status


def _generate_with_gemini(system_prompt, user_text, conversation=None, temperature=0.7):
    """Call the Gemini API and return the generated text.

    Raises _GeminiError (with an http_status attribute) on failure so callers
    can turn it into a proper HTTP error response instead of faking success.
    """
    client = get_gemini_client()
    if client is None:
        raise _GeminiError(
            "Gemini API key is not configured on the server. "
            "Add GEMINI_API_KEY to .env and restart the app.",
            503,
        )

    from google.genai import types

    # Build contents: previous turns first, then the current user message.
    contents = []
    if conversation:
        for turn in conversation[-MAX_CONVERSATION_TURNS:]:
            role = turn.get("role", "user")
            if role not in ("user", "model"):
                role = "user"
            parts = [{"text": str(turn.get("content", ""))}]
            contents.append({"role": role, "parts": parts})
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
            ),
        )
    except Exception as exc:  # network, auth, rate limit, timeout, etc.
        status = _gemini_error_status(exc)
        raise _GeminiError(_gemini_error_message(exc, status), status)

    text = getattr(response, "text", None) or ""
    text = text.strip()
    if not text:
        raise _GeminiError("Gemini returned an empty response.", 502)
    return text



# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def _handle_command(message):
    """Handle built-in terminal commands without calling Gemini."""
    command = message.strip().split()[0]
    if command == "/help":
        return (
            "Available commands:\n"
            "/help       – Show this help message.\n"
            "/story      – Generate a spooky programming story.\n"
            "/oracle     – Ask the ghost a question about old tech.\n"
            "/clear      – Clear the haunted terminal."
        ), False
    if command == "/story":
        story = generate_story()
        return story, False
    if command == "/oracle":
        return "What would you like to ask the forgotten oracle?", False
    if command == "/clear":
        return "__CLEAR__", False
    return f"Unknown command '{command}'. Type /help for available commands.", False


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    user_message = data.get("message", "")
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Message is required and must not be empty."}), 400

    conversation = data.get("conversation")
    if not isinstance(conversation, list):
        conversation = []

    # Built-in commands work even without a Gemini key.
    if user_message.strip().startswith("/"):
        reply, _ = _handle_command(user_message)
        if reply == "__CLEAR__":
            return jsonify({"response": "__CLEAR__", "cleared": True})
        return jsonify({"response": reply})

    try:
        answer = _generate_with_gemini(GHOST_SYSTEM_PROMPT, user_message, conversation)
    except _GeminiError as exc:
        return jsonify({"error": str(exc)}), exc.http_status

    return jsonify({"response": answer})


def generate_story():
    """Generate one spooky story through Gemini (raises on failure)."""
    return _generate_with_gemini(
        STORY_SYSTEM_PROMPT,
        "Tell me a short, original spooky story about programming or forgotten code.",
        temperature=0.8,
    )


@app.route("/api/story", methods=["POST"])
def story_endpoint():
    try:
        story = generate_story()
    except _GeminiError as exc:
        return jsonify({"error": str(exc)}), exc.http_status
    return jsonify({"story": story})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
