"""
memory/permanent.py - JARVIS Permanent Memory.
Saves user information to a JSON file so JARVIS
remembers you across sessions even after restart.
"""
import json
import os
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MEMORY_FILE = os.path.join(BASE_DIR, "memory", "jarvis_memory.json")


class PermanentMemory:
    """
    Handles permanent memory storage for JARVIS.
    Data is saved to a JSON file and loaded on startup.
    Survives restarts — JARVIS never forgets!
    """

    def __init__(self):
        self.data = self._load()
        logger.info(f"Permanent memory loaded. "
                    f"{len(self.data)} items in memory.")

    def _load(self) -> dict:
        """Load memory from JSON file."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Memory load error: {e}")
                return {}
        return {}

    def _save(self):
        """Save memory to JSON file."""
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.data, f, indent=4)
            logger.debug("Memory saved.")
        except Exception as e:
            logger.error(f"Memory save error: {e}")

    def remember(self, key: str, value: str):
        """
        Store a key-value pair in permanent memory.

        Args:
            key: What to remember (e.g. 'name', 'city')
            value: The value (e.g. 'Rajesh', 'Hyderabad')
        """
        self.data[key] = value
        self._save()
        logger.info(f"Remembered: {key} = {value}")

    def recall(self, key: str) -> str | None:
        """
        Retrieve a value from permanent memory.

        Args:
            key: What to recall

        Returns:
            The stored value or None if not found
        """
        return self.data.get(key, None)

    def forget(self, key: str):
        """Remove a specific memory."""
        if key in self.data:
            del self.data[key]
            self._save()
            logger.info(f"Forgot: {key}")

    def forget_all(self):
        """Wipe all permanent memory."""
        self.data = {}
        self._save()
        logger.info("All permanent memory cleared.")

    def get_all(self) -> dict:
        """Returns all stored memories."""
        return self.data

    def summary(self) -> str:
        """Returns a human readable summary of memory."""
        if not self.data:
            return "I have no permanent memories stored yet sir."
        items = [f"{k}: {v}" for k, v in self.data.items()]
        return "I remember: " + ", ".join(items) + " sir."