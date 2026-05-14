"""
voice/speaker.py - JARVIS Text-to-Speech module.
Fixed version for Windows — handles pyttsx3 conflicts.
"""
import pyttsx3
import threading
from utils.logger import get_logger

logger = get_logger(__name__)


class Speaker:
    """
    Handles all voice output for JARVIS.
    Uses threading to prevent pyttsx3 freezing on Windows.
    """

    def __init__(self):
        self.rate = 175
        self.volume = 1.0
        self.voice_index = 0
        logger.info("Speaker initialized.")

    def speak(self, text: str, wait: bool = True):
        """
        Speak the given text out loud.
        Runs speech engine work in a separate thread to prevent
        pyttsx3 engine-state issues on Windows.

        Args:
            text: The text JARVIS will say
            wait: If True, block until speech completes
        """
        if not text:
            return

        logger.info(f"Speaking: {text[:50]}...")
        print(f"JARVIS: {text}\n")

        # Run speech in separate thread
        # This prevents pyttsx3 from blocking the main loop
        thread = threading.Thread(
            target=self._speak_thread,
            args=(text,),
            daemon=True
        )
        thread.start()
        if wait:
            thread.join()  # Wait for speech to finish

    def _speak_thread(self, text: str):
        """
        Internal method — runs in a thread.
        Creates fresh engine each time to avoid Windows conflicts.
        """
        try:
            # Fresh engine every time — fixes Windows freezing
            engine = pyttsx3.init()

            # Get voices
            voices = engine.getProperty('voices')

            # Set male voice
            if voices and len(voices) > self.voice_index:
                engine.setProperty('voice', voices[self.voice_index].id)

            # Set speed and volume
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)

            # Speak
            engine.say(text)
            engine.runAndWait()

            # Clean up
            engine.stop()

        except RuntimeError as e:
            # Sometimes pyttsx3 throws RuntimeError on Windows
            # Try alternative method
            logger.warning(f"pyttsx3 RuntimeError: {e}. Trying fallback...")
            self._speak_fallback(text)

        except Exception as e:
            logger.error(f"Speaker thread error: {e}")

    def _speak_fallback(self, text: str):
        """
        Fallback using Windows built-in speech (SAPI).
        Works even when pyttsx3 fails.
        """
        try:
            import subprocess
            # Use PowerShell's built-in speech synthesizer
            # This always works on Windows
            command = (
                f'powershell -Command "Add-Type -AssemblyName System.speech; '
                f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                f'$speak.Rate = 1; '
                f'$speak.Speak(\'{text.replace("'", "")}\');"'
            )
            subprocess.run(command, shell=True)
            logger.info("Fallback speech used successfully.")
        except Exception as e:
            logger.error(f"Fallback speech error: {e}")

    def set_rate(self, rate: int):
        """Change speaking speed. 150=slow, 200=normal, 250=fast"""
        self.rate = rate
        logger.debug(f"Speech rate set to {rate}")

    def set_volume(self, volume: float):
        """Change volume. 0.0=silent, 1.0=maximum"""
        self.volume = volume
        logger.debug(f"Volume set to {volume}")

    def set_voice(self, index: int):
        """
        Change voice.
        0 = first voice (usually male)
        1 = second voice (usually female)
        """
        self.voice_index = index
        logger.debug(f"Voice index set to {index}")