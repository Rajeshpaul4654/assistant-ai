"""
actions/executor.py - JARVIS System Command Executor.
Complete version with WhatsApp, Spotify, Weather.
"""
import os
import subprocess
import webbrowser
import pyautogui
import psutil
import requests
import pyperclip
import threading
import time
from datetime import datetime
from actions.whatsapp import WhatsAppManager
from actions.spotify import SpotifyManager
from utils.logger import get_logger
from config import DEFAULT_CITY

logger = get_logger(__name__)

# ── App mappings ─────────────────────────────────────────────
APPS = {
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":      r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":         r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "notepad":      "notepad.exe",
    "calculator":   "calc.exe",
    "paint":        "mspaint.exe",
    "wordpad":      "wordpad.exe",
    "cmd":          "cmd.exe",
    "explorer":     "explorer.exe",
    "task manager": "taskmgr.exe",
    "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":   r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "vlc":          r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "spotify":      r"C:\Users\DELL\AppData\Local\Microsoft\WindowsApps\Spotify.exe",
    "vscode":       r"C:\Users\DELL\AppData\Local\Programs\Microsoft VS Code\Code.exe",
}

# ── Website mappings ─────────────────────────────────────────
WEBSITES = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "github":        "https://www.github.com",
    "gmail":         "https://mail.google.com",
    "whatsapp":      "https://web.whatsapp.com",
    "instagram":     "https://www.instagram.com",
    "twitter":       "https://www.twitter.com",
    "facebook":      "https://www.facebook.com",
    "linkedin":      "https://www.linkedin.com",
    "netflix":       "https://www.netflix.com",
    "amazon":        "https://www.amazon.in",
    "flipkart":      "https://www.flipkart.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt":       "https://chat.openai.com",
}


class Executor:
    """
    Executes all system commands for JARVIS.
    Complete version with all features.
    """

    def __init__(self):
        self.reminders = []
        self.whatsapp = WhatsAppManager()
        self.spotify = SpotifyManager()
        logger.info("Executor initialized.")

    def _request_json_with_retries(
        self, url: str, timeout: int = 5, attempts: int = 3, backoff: float = 0.6
    ):
        """Request JSON endpoint with simple exponential backoff retries."""
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_error = e
                if attempt < attempts:
                    sleep_for = backoff * (2 ** (attempt - 1))
                    logger.warning(
                        f"Request failed (attempt {attempt}/{attempts}) for {url}: {e}"
                    )
                    time.sleep(sleep_for)
        raise last_error

    # ── App & Web ─────────────────────────────────────────────

    def open_application(self, app_name: str) -> str:
        """Open an application by name."""
        app_name = app_name.lower().strip()
        if app_name in APPS:
            path = APPS[app_name]
            try:
                subprocess.Popen(path)
                logger.info(f"Opened app: {app_name}")
                return f"Opening {app_name} sir."
            except FileNotFoundError:
                return f"Could not find {app_name} on your system sir."
            except Exception as e:
                return f"Failed to open {app_name} sir."
        try:
            subprocess.Popen(app_name)
            return f"Opening {app_name} sir."
        except Exception:
            return f"I don't know how to open {app_name} sir."

    def open_website(self, site_name: str) -> str:
        """Open a website by name or URL."""
        site_name = site_name.lower().strip()
        if site_name in WEBSITES:
            webbrowser.open(WEBSITES[site_name])
            return f"Opening {site_name} sir."
        if "." in site_name:
            webbrowser.open(f"https://{site_name}")
            return f"Opening {site_name} sir."
        return f"I don't know the website {site_name} sir."

    def web_search(self, query: str) -> str:
        """Search Google for a query."""
        if not query:
            return "What would you like me to search for sir?"
        search_url = (
            f"https://www.google.com/search?q={query.replace(' ', '+')}"
        )
        webbrowser.open(search_url)
        return f"Searching Google for {query} sir."

    # ── System Info ───────────────────────────────────────────

    def get_time(self) -> str:
        """Returns current time."""
        time_str = datetime.now().strftime("%I:%M %p")
        return f"The current time is {time_str} sir."

    def get_date(self) -> str:
        """Returns today's date."""
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {date_str} sir."

    def take_screenshot(self) -> str:
        """Takes a screenshot and saves to desktop."""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jarvis_screenshot_{timestamp}.png"
            filepath = os.path.join(desktop, filename)
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            return f"Screenshot saved to desktop as {filename} sir."
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return "Could not take screenshot sir."

    def get_battery(self) -> str:
        """Returns battery status."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "not plugged in"
                return f"Battery is at {percent} percent and {plugged} sir."
            return "Could not read battery status sir."
        except Exception:
            return "Could not read battery status sir."

    def get_system_info(self) -> str:
        """Returns CPU and RAM usage."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            return (
                f"CPU usage is {cpu} percent and "
                f"RAM usage is {ram} percent sir."
            )
        except Exception:
            return "Could not retrieve system information sir."

    # ── Weather ───────────────────────────────────────────────

    def get_weather(self, city: str = None) -> str:
        """Gets current weather using wttr.in — no API key needed."""
        city = city or DEFAULT_CITY

        try:
            url = f"https://wttr.in/{city}?format=j1"
            data = self._request_json_with_retries(url, timeout=5, attempts=3)
            current = data["current_condition"][0]
            temp = current["temp_C"]
            feels_like = current["FeelsLikeC"]
            humidity = current["humidity"]
            description = current["weatherDesc"][0]["value"]
            wind_speed = current["windspeedKmph"]

            return (
                f"The weather in {city} is {description}. "
                f"Temperature is {temp} degrees celsius, "
                f"feels like {feels_like} degrees. "
                f"Humidity is {humidity} percent and "
                f"wind speed is {wind_speed} kilometers per hour sir."
            )

        except requests.exceptions.ConnectionError:
            return "No internet connection sir."
        except Exception as e:
            logger.error(f"Weather error: {e}")
            return "Could not fetch weather sir."

    # ── Clipboard ─────────────────────────────────────────────

    def read_clipboard(self) -> str:
        """Reads and returns clipboard content."""
        try:
            content = pyperclip.paste()
            if content:
                if len(content) > 100:
                    short = content[:100]
                    return (
                        f"Your clipboard contains: {short}"
                        f"... and more sir."
                    )
                return f"Your clipboard contains: {content} sir."
            return "Your clipboard is empty sir."
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return "Could not read clipboard sir."

    def copy_to_clipboard(self, text: str) -> str:
        """Copies text to clipboard."""
        try:
            pyperclip.copy(text)
            return "Copied to clipboard sir."
        except Exception:
            return "Could not copy to clipboard sir."

    # ── Reminders ─────────────────────────────────────────────

    def set_reminder(self, message: str, seconds: int,
                     speaker=None) -> str:
        """Set a reminder that fires after given seconds."""
        def reminder_thread():
            import time
            time.sleep(seconds)
            reminder_msg = f"Reminder sir: {message}"
            print(f"\n*** REMINDER: {message} ***\n")
            if speaker:
                speaker.speak(reminder_msg)

        thread = threading.Thread(
            target=reminder_thread,
            daemon=True
        )
        thread.start()
        self.reminders.append(message)

        if seconds < 60:
            time_str = f"{seconds} seconds"
        elif seconds < 3600:
            mins = seconds // 60
            time_str = f"{mins} minutes"
        else:
            hours = seconds // 3600
            time_str = f"{hours} hours"

        return (
            f"Reminder set for {time_str} from now sir. "
            f"I will remind you to {message}."
        )

    def parse_reminder(self, command: str, speaker=None) -> str:
        """Parse a reminder voice command."""
        import re

        pattern = r"(\d+)\s*(second|seconds|minute|minutes|hour|hours)"
        match = re.search(pattern, command.lower())

        if not match:
            return (
                "Please specify the time. "
                "For example: remind me in 5 minutes to drink water sir."
            )

        amount = int(match.group(1))
        unit = match.group(2)

        if "second" in unit:
            seconds = amount
        elif "minute" in unit:
            seconds = amount * 60
        else:
            seconds = amount * 3600

        to_pattern = r"(?:to|about|for)\s+(.+)$"
        to_match = re.search(to_pattern, command.lower())
        message = to_match.group(1).strip() if to_match else "your reminder"

        return self.set_reminder(message, seconds, speaker)

    # ── Jokes ─────────────────────────────────────────────────

    def tell_joke(self) -> str:
        """Fetches a random joke."""
        fallback_jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs sir.",
            "Why did the developer go broke? Because he used up all his cache sir.",
            "How many programmers does it take to change a light bulb? None, that is a hardware problem sir.",
            "Why do Java developers wear glasses? Because they do not C sharp sir.",
            "A SQL query walks into a bar and asks two tables: Can I join you sir?",
        ]

        try:
            data = self._request_json_with_retries(
                "https://official-joke-api.appspot.com/random_joke",
                timeout=3,
                attempts=3
            )
            if data and "setup" in data and "punchline" in data:
                return f"{data['setup']} ... {data['punchline']}"
        except Exception:
            pass

        import random
        return random.choice(fallback_jokes)