"""
web_app.py - Simple local web dashboard for JARVIS.

Run:
    python web_app.py
Then open:
    http://127.0.0.1:5000
"""
from flask import Flask, jsonify, render_template, request

from actions.executor import Executor
from brain.llm import JarvisBrain
from config import JARVIS_NAME, validate_startup_config
from utils.logger import get_logger

logger = get_logger(__name__)
app = Flask(__name__)
brain = JarvisBrain()
executor = Executor()


def handle_intent(intent: dict, original_message: str) -> str:
    """Route recognized intents to system action handlers."""
    intent_name = intent.get("intent")
    handlers = {
        "open_app": lambda i: executor.open_application(i.get("target", "")),
        "open_website": lambda i: executor.open_website(i.get("target", "")),
        "search": lambda i: executor.web_search(i.get("query", "")),
        "time": lambda i: executor.get_time(),
        "date": lambda i: executor.get_date(),
        "screenshot": lambda i: executor.take_screenshot(),
        "battery": lambda i: executor.get_battery(),
        "system_info": lambda i: executor.get_system_info(),
        "weather": lambda i: executor.get_weather(i.get("city")),
        "reminder": lambda i: executor.parse_reminder(i.get("command", "")),
        "clipboard": lambda i: executor.read_clipboard(),
        "joke": lambda i: executor.tell_joke(),
        "recall_all": lambda i: brain.permanent.summary(),
        "spotify_open": lambda i: executor.spotify.open_spotify(),
        "spotify_play": lambda i: executor.spotify.play(),
        "spotify_pause": lambda i: executor.spotify.pause(),
        "spotify_next": lambda i: executor.spotify.next_track(),
        "spotify_previous": lambda i: executor.spotify.previous_track(),
        "spotify_current": lambda i: executor.spotify.get_current_song(),
        "spotify_play_song": lambda i: executor.spotify.play_song(i.get("song", "")),
        "whatsapp": lambda i: executor.whatsapp.parse_command(i.get("command", "")),
    }

    handler = handlers.get(intent_name)
    if handler:
        return handler(intent)

    return brain.think(original_message)


@app.get("/")
def index():
    """Render dashboard page."""
    return render_template("index.html", jarvis_name=JARVIS_NAME)


@app.get("/api/health")
def health():
    """Basic server/config health endpoint."""
    validation = validate_startup_config()
    return jsonify(
        {
            "ok": validation["ok"],
            "warnings": validation["warnings"],
            "errors": validation["errors"],
        }
    )


@app.post("/api/chat")
def chat():
    """Chat endpoint for browser UI with intent execution."""
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Message is required."}), 400

    try:
        intent = brain.classify_intent(message)
        logger.info(f"Web intent detected: {intent}")
        reply = handle_intent(intent, message)
        return jsonify(
            {"ok": True, "reply": reply, "intent": intent.get("intent", "chat")}
        )
    except Exception as e:
        logger.error(f"Web chat error: {e}", exc_info=True)
        return jsonify({"ok": False, "error": "Failed to process request."}), 500


if __name__ == "__main__":
    validation = validate_startup_config()
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"Startup warning: {warning}")
    if not validation["ok"]:
        for error in validation["errors"]:
            logger.error(f"Startup config error: {error}")
        raise SystemExit("Startup configuration is invalid. Check logs/.env.")

    logger.info("Starting JARVIS web dashboard on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
