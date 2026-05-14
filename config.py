"""
config.py — Central configuration for JARVIS.
Powered by Groq API (free, fast, works in India).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# === API Settings ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# === Model Settings ===
# llama-3.3-70b-versatile = very smart, completely free
MODEL_NAME = "llama-3.3-70b-versatile"

# === Assistant Personality ===
JARVIS_NAME = os.getenv("JARVIS_NAME", "JARVIS")

SYSTEM_PROMPT = f"""You are {JARVIS_NAME}, a highly intelligent personal AI assistant
inspired by Iron Man's JARVIS. You are:
- Concise and precise — no unnecessary filler words
- Proactively helpful — anticipate what the user needs
- Slightly witty but always professional
- Honest about your limitations

Keep responses under 3 sentences unless detail is specifically requested."""

# === Conversation Settings ===
MAX_HISTORY_TURNS = 10
# === Weather Settings ===
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Hyderabad")


def validate_startup_config() -> dict:
    """
    Validate critical runtime settings and return findings.
    Does not raise by default so caller can decide whether to exit.
    """
    errors = []
    warnings = []

    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is missing in environment/.env.")

    if not MODEL_NAME:
        errors.append("MODEL_NAME is empty.")

    if MAX_HISTORY_TURNS <= 0:
        errors.append("MAX_HISTORY_TURNS must be greater than 0.")

    if not DEFAULT_CITY:
        warnings.append("DEFAULT_CITY is empty; weather fallback may be poor.")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }