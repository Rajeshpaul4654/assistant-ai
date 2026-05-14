"""
brain/llm.py - The intelligence core of JARVIS.
Phase 5 update - adds permanent memory.
Powered by Groq API.
"""
from groq import Groq
from config import (
    GROQ_API_KEY, MODEL_NAME,
    SYSTEM_PROMPT, MAX_HISTORY_TURNS, JARVIS_NAME
)
from memory.permanent import PermanentMemory
from utils.logger import get_logger

logger = get_logger(__name__)


class JarvisBrain:
    """
    Manages AI conversations with memory using Groq.
    Phase 5 - now includes permanent memory across sessions.
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.history = []
        self.permanent = PermanentMemory()
        self.turn_count = 0
        self.system_prompt = self._build_system_prompt()
        logger.info(
            f"{JARVIS_NAME} brain initialized with Groq {MODEL_NAME}."
        )

    def _build_system_prompt(self) -> str:
        """Build personalized system prompt using permanent memory."""
        prompt = SYSTEM_PROMPT
        name = self.permanent.recall("name")
        city = self.permanent.recall("city")

        if name or city:
            prompt += "\n\nWhat you know about the user:"
            if name:
                prompt += f"\n- Name: {name} (always address them as {name})"
            if city:
                prompt += f"\n- City: {city}"

        return prompt

    def think(self, user_input: str) -> str:
        """
        Takes user input and returns JARVIS's response.

        Args:
            user_input: What the user typed or said

        Returns:
            JARVIS's response as a string
        """
        lower_input = user_input.lower()

        # Learn user's name
        if "my name is" in lower_input:
            name = lower_input.split("my name is", 1)[1].strip()
            name = name.replace(".", "").replace(",", "").strip()
            name = name.title()
            self.permanent.remember("name", name)
            self.system_prompt = self._build_system_prompt()
            logger.info(f"Learned user name: {name}")

        # Learn user's city
        if "i live in" in lower_input or "i am from" in lower_input:
            for phrase in ["i live in", "i am from"]:
                if phrase in lower_input:
                    city = lower_input.split(phrase, 1)[1].strip()
                    city = city.replace(".", "").replace(",", "").strip()
                    city = city.title()
                    self.permanent.remember("city", city)
                    self.system_prompt = self._build_system_prompt()
                    logger.info(f"Learned user city: {city}")

        # Learn user's profession
        if "i am a " in lower_input or "i work as" in lower_input:
            for phrase in ["i am a ", "i work as "]:
                if phrase in lower_input:
                    job = lower_input.split(phrase, 1)[1].strip()
                    job = job.replace(".", "").replace(",", "").strip()
                    self.permanent.remember("profession", job)
                    self.system_prompt = self._build_system_prompt()
                    logger.info(f"Learned user profession: {job}")

        # Add to session history
        self.history.append({
            "role": "user",
            "content": user_input
        })

        try:
            logger.debug(f"Sending to Groq: {user_input[:50]}...")

            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.system_prompt}
                ] + self.history,
                temperature=0.7,
                max_tokens=1024
            )

            reply = response.choices[0].message.content

            self.history.append({
                "role": "assistant",
                "content": reply
            })

            self.turn_count += 1

            if len(self.history) > MAX_HISTORY_TURNS * 2:
                self.history = self.history[-(MAX_HISTORY_TURNS * 2):]
                logger.debug("History trimmed.")

            logger.info(f"JARVIS responded ({len(reply)} chars)")
            return reply

        except Exception as e:
            self.history.pop()
            error_msg = f"I encountered an error: {str(e)}"
            logger.error(f"Groq error: {e}", exc_info=True)
            return error_msg

    def classify_intent(self, user_input: str) -> dict:
        """
        Classify what the user wants to do.
        Returns intent type and extracted details.
        """
        text = user_input.lower().strip()

        # Spotify — check FIRST before open/website
        if "play song" in text or "play the song" in text:
            for phrase in ["play the song ", "play song "]:
                if phrase in text:
                    song = text.split(phrase, 1)[1].strip()
                    return {"intent": "spotify_play_song", "song": song}

        if any(phrase in text for phrase in [
            "play music", "resume music", "play spotify"
        ]):
            return {"intent": "spotify_play", "target": None}

        if any(phrase in text for phrase in [
            "pause music", "stop music", "pause spotify"
        ]):
            return {"intent": "spotify_pause", "target": None}

        if any(phrase in text for phrase in [
            "next song", "skip song", "next track"
        ]):
            return {"intent": "spotify_next", "target": None}

        if any(phrase in text for phrase in [
            "previous song", "last song", "previous track"
        ]):
            return {"intent": "spotify_previous", "target": None}

        if any(phrase in text for phrase in [
            "what song", "current song", "what's playing", "what is playing"
        ]):
            return {"intent": "spotify_current", "target": None}

        if "open spotify" in text:
            return {"intent": "spotify_open", "target": None}

        # WhatsApp send-message intent (do not catch "open whatsapp")
        if any(phrase in text for phrase in [
            "send whatsapp", "send message to"
        ]) or (
            text.startswith("whatsapp ") and
            not text.startswith("whatsapp web")
        ):
            return {"intent": "whatsapp", "command": text}

        # Open application or website
        if any(phrase in text for phrase in ["open ", "launch ", "start "]):
            for phrase in ["open ", "launch ", "start "]:
                if phrase in text:
                    rest = text.split(phrase, 1)[1].strip()
                    # Keep multi-word names (e.g. "task manager", "visual studio code")
                    # and trim common filler words.
                    target = rest
                    for filler in ["the ", "app ", "application ", "website ", "site "]:
                        if target.startswith(filler):
                            target = target[len(filler):].strip()

                    website_keywords = [
                        "youtube", "google", "github", "gmail",
                        "whatsapp", "instagram", "twitter",
                        "facebook", "linkedin", "netflix",
                        "amazon", "flipkart", "stackoverflow",
                        "chatgpt"
                    ]
                    if any(site in target for site in website_keywords) or "." in target:
                        return {"intent": "open_website", "target": target}
                    return {"intent": "open_app", "target": target}

        # Web search
        if any(phrase in text for phrase in [
            "search for ", "search ", "google "
        ]):
            for phrase in ["search for ", "search ", "google "]:
                if phrase in text:
                    query = text.split(phrase, 1)[1].strip()
                    return {"intent": "search", "query": query}

        # Time
        if any(phrase in text for phrase in [
            "what time", "current time", "time now"
        ]):
            return {"intent": "time", "target": None}

        # Date
        if any(phrase in text for phrase in [
            "what date", "today's date", "what day", "current date"
        ]):
            return {"intent": "date", "target": None}

        # Screenshot
        if any(phrase in text for phrase in [
            "screenshot", "take a screenshot", "capture screen"
        ]):
            return {"intent": "screenshot", "target": None}

        # Battery
        if any(phrase in text for phrase in [
            "battery", "battery status", "battery level"
        ]):
            return {"intent": "battery", "target": None}

        # System info
        if any(phrase in text for phrase in [
            "system info", "cpu", "ram", "memory usage"
        ]):
            return {"intent": "system_info", "target": None}

        # Weather
        if any(phrase in text for phrase in [
            "weather", "temperature", "forecast"
        ]):
            city = None
            for phrase in ["weather in ", "temperature in ", "forecast for "]:
                if phrase in text:
                    city = text.split(phrase, 1)[1].strip()
                    break
            return {"intent": "weather", "city": city}

        # Reminder
        if any(phrase in text for phrase in [
            "remind me", "set reminder", "set a reminder"
        ]):
            return {"intent": "reminder", "command": text}

        # Clipboard
        if any(phrase in text for phrase in [
            "clipboard", "read clipboard"
        ]):
            return {"intent": "clipboard", "target": None}

        # Joke
        if any(phrase in text for phrase in [
            "joke", "tell me a joke", "make me laugh"
        ]):
            return {"intent": "joke", "target": None}

        # What do you remember
        if any(phrase in text for phrase in [
            "what do you remember", "what you know about me", "my info"
        ]):
            return {"intent": "recall_all", "target": None}

        # Default — normal AI chat
        return {"intent": "chat", "target": None}

    def reset_memory(self):
        """Clear session memory only."""
        self.history.clear()
        self.turn_count = 0
        logger.info("Session memory cleared.")

    def reset_permanent_memory(self):
        """Clear ALL memory including permanent."""
        self.history.clear()
        self.turn_count = 0
        self.permanent.forget_all()
        logger.info("All memory cleared including permanent.")

    def get_history_summary(self) -> str:
        """Returns memory status."""
        session = self.turn_count
        permanent = len(self.permanent.get_all())
        return (
            f"{session} session turns in memory. "
            f"{permanent} permanent memories stored."
        )