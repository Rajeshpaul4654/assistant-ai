"""
voice/listener.py - JARVIS Speech-to-Text module.
Uses sounddevice instead of pyaudio.
Works perfectly on Python 3.14.
"""
import io
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from utils.logger import get_logger

logger = get_logger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16


class Listener:
    """
    Handles all voice input for JARVIS.
    Records audio via sounddevice, converts to text
    via Google's free speech recognition service.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.pause_threshold = 0.8
        logger.info("Listener initialized with sounddevice.")
        print("Microphone ready.\n")

    def _record_audio(self, duration: int = 5) -> sr.AudioData:
        """
        Record audio from microphone for given duration.

        Args:
            duration: How many seconds to record

        Returns:
            AudioData object ready for speech recognition
        """
        audio_np = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE
        )
        sd.wait()

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(audio_np.tobytes())

        wav_buffer.seek(0)

        with sr.AudioFile(wav_buffer) as source:
            audio_data = self.recognizer.record(source)

        return audio_data

    def listen(self) -> str | None:
        """
        Record audio and convert to text.

        Returns:
            Spoken text as string, or None if not understood
        """
        print("Listening...")

        try:
            audio_data = self._record_audio(duration=5)
            print("Processing speech...")

            text = self.recognizer.recognize_google(
                audio_data,
                language="en-IN"
            )

            logger.info(f"Heard: {text}")
            return text.lower()

        except sr.UnknownValueError:
            print("Could not understand. Please speak clearly.\n")
            logger.debug("Speech not understood.")
            return None

        except sr.RequestError as e:
            print("Speech recognition service unavailable.")
            logger.error(f"Speech recognition error: {e}")
            return None

        except Exception as e:
            logger.error(f"Listener error: {e}", exc_info=True)
            return None

    def _command_after_wake(self, text: str, wake_word: str) -> str | None:
        """
        If wake word appears in transcript, return text after it (may be empty).
        Returns None if wake word is not in the transcript.
        """
        t = text.lower().strip()
        w = wake_word.lower().strip()
        if not w or w not in t:
            return None
        idx = t.find(w)
        after = t[idx + len(w):].strip().lstrip(",.!? ")
        return after

    def listen_for_wake_word(
        self, wake_word: str = "jarvis"
    ) -> tuple[bool, str | None]:
        """
        Listen for the wake word in a short clip.

        Returns:
            (False, None) — wake not heard
            (True, None) — wake heard alone; open mic for a follow-up command
            (True, str) — wake + command in one phrase (e.g. "jarvis what time")
        """
        try:
            audio_np = sd.rec(
                int(3 * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE
            )
            sd.wait()

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(audio_np.tobytes())
            wav_buffer.seek(0)

            with sr.AudioFile(wav_buffer) as source:
                audio_data = self.recognizer.record(source)

            text = self.recognizer.recognize_google(
                audio_data,
                language="en-IN"
            )
            text = text.lower()
            logger.debug(f"Wake word check heard: {text}")

            after = self._command_after_wake(text, wake_word)
            if after is None:
                return False, None

            logger.info(f"Wake word '{wake_word}' detected!")
            if after:
                logger.info(f"Command in same utterance: {after[:80]}")
                return True, after
            return True, None

        except sr.UnknownValueError:
            return False, None

        except Exception as e:
            logger.error(f"Wake word error: {e}")
            return False, None