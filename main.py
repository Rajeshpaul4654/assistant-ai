"""
main.py - JARVIS Phase 5: Final Production Version.

Usage:
    python main.py           -> text mode
    python main.py --voice   -> voice mode
"""
import sys
from brain.llm import JarvisBrain
from voice.speaker import Speaker
from voice.listener import Listener
from actions.executor import Executor, APPS, WEBSITES
from utils.logger import get_logger
from config import JARVIS_NAME, validate_startup_config

logger = get_logger(__name__)


def ask_voice_confirmation(
    speaker: Speaker,
    listener: Listener,
    prompt: str,
    retries: int = 2
) -> bool:
    """Ask for spoken yes/no confirmation before sensitive actions."""
    yes_words = {"yes", "yeah", "yup", "confirm", "do it", "proceed"}
    no_words = {"no", "nope", "cancel", "stop", "don't", "do not"}

    for _ in range(retries + 1):
        speaker.speak(prompt)
        reply = listener.listen()
        if not reply:
            continue

        text = reply.lower().strip()
        if any(word in text for word in yes_words):
            return True
        if any(word in text for word in no_words):
            return False

        speaker.speak("Please say yes or no sir.")

    return False


def ask_text_confirmation(prompt: str, retries: int = 2) -> bool:
    """Ask for typed yes/no confirmation in text mode."""
    yes_words = {"yes", "y", "confirm", "do it", "proceed"}
    no_words = {"no", "n", "cancel", "stop"}

    for _ in range(retries + 1):
        reply = input(f"{JARVIS_NAME}: {prompt}\nYou (yes/no): ").strip().lower()
        if reply in yes_words:
            return True
        if reply in no_words:
            return False
        print(f"{JARVIS_NAME}: Please type yes or no.\n")

    return False


def print_banner(mode: str = "text"):
    """Display startup banner."""
    print("\n" + "="*50)
    print(f"  {JARVIS_NAME} - AI Personal Assistant")
    print(f"  Mode: {mode.upper()}")
    print("="*50)
    print("  Commands:")
    print("    'quit' or 'exit'  -> Shutdown JARVIS")
    print("    'reset'           -> Clear memory")
    print("    'memory'          -> Show memory status")
    if mode == "voice":
        print(f"    Say '{JARVIS_NAME.lower()}' -> Opens mic for your command")
    print("="*50 + "\n")


def run_text_mode():
    """Phase 1 mode - text only."""
    print_banner("text")
    brain = JarvisBrain()
    print(f"{JARVIS_NAME}: Online. How may I assist you?\n")

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                confirmed = ask_text_confirmation(
                    "Do you want to shut down now?"
                )
                if not confirmed:
                    print(f"{JARVIS_NAME}: Shutdown cancelled.\n")
                    continue
                print(f"\n{JARVIS_NAME}: Shutting down. Goodbye.")
                break

            elif user_input.lower() == "reset":
                confirmed = ask_text_confirmation(
                    "This will clear session memory. Confirm reset?"
                )
                if not confirmed:
                    print(f"{JARVIS_NAME}: Memory reset cancelled.\n")
                    continue
                brain.reset_memory()
                print(f"{JARVIS_NAME}: Memory cleared. Starting fresh.\n")
                continue

            elif user_input.lower() == "memory":
                print(f"{JARVIS_NAME}: {brain.get_history_summary()}\n")
                continue

            response = brain.think(user_input)
            print(f"\n{JARVIS_NAME}: {response}\n")

        except KeyboardInterrupt:
            print(f"\n\n{JARVIS_NAME}: Emergency shutdown. Goodbye.")
            break


def run_voice_mode():
    """Phase 5 mode - voice + AI + system + permanent memory."""
    print_banner("voice")

    brain = JarvisBrain()
    speaker = Speaker()
    listener = Listener()
    executor = Executor()

    speaker.speak("JARVIS online and ready. Say JARVIS to activate me.")

    intent_handlers = {
        "open_app": lambda i: executor.open_application(i.get("target", "")),
        "open_website": lambda i: executor.open_website(i.get("target", "")),
        "search": lambda i: executor.web_search(i.get("query", "")),
        "time": lambda i: executor.get_time(),
        "date": lambda i: executor.get_date(),
        "screenshot": lambda i: executor.take_screenshot(),
        "battery": lambda i: executor.get_battery(),
        "system_info": lambda i: executor.get_system_info(),
        "weather": lambda i: executor.get_weather(i.get("city")),
        "reminder": lambda i: executor.parse_reminder(
            i.get("command", ""),
            speaker=speaker
        ),
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
        "whatsapp": lambda i: executor.whatsapp.parse_command(
            i.get("command", "")
        ),
    }

    while True:
        try:
            print("Say 'JARVIS' to activate...", end="\r")

            awake, trailing_command = listener.listen_for_wake_word(
                wake_word=JARVIS_NAME.lower()
            )

            if not awake:
                continue

            print("\nWake word detected — microphone open for your command.\n")

            # Open mic immediately: no spoken prompt before listen (avoids delay
            # and keeps the mic path clear for the user).
            if trailing_command:
                command = trailing_command.strip()
                print(f"Heard with wake word: {command}\n")
            else:
                print("Speak your command now...\n")
                command = listener.listen()

            if not command:
                speaker.speak("I did not catch that. Please try again.")
                continue

            print(f"You said: {command}\n")

            # Shutdown
            if any(w in command for w in ["exit", "quit", "shutdown", "bye"]):
                confirmed = ask_voice_confirmation(
                    speaker,
                    listener,
                    "Do you want me to shut down now sir? Say yes or no."
                )
                if not confirmed:
                    speaker.speak("Shutdown cancelled sir.")
                    continue
                speaker.speak("Shutting down. Goodbye sir.")
                break

            # Reset session memory
            elif "reset" in command or "clear memory" in command:
                confirmed = ask_voice_confirmation(
                    speaker,
                    listener,
                    "This will clear session memory. Confirm reset? Say yes or no."
                )
                if not confirmed:
                    speaker.speak("Memory reset cancelled sir.")
                    continue
                brain.reset_memory()
                speaker.speak("Memory cleared sir.")
                continue

            # Memory status
            elif "memory" in command:
                summary = brain.get_history_summary()
                speaker.speak(summary)
                continue

            # Classify intent
            intent = brain.classify_intent(command)
            logger.info(f"Intent detected: {intent}")

            if intent["intent"] == "whatsapp":
                confirmed = ask_voice_confirmation(
                    speaker,
                    listener,
                    "Do you want me to send this WhatsApp message now sir? "
                    "Say yes or no."
                )
                if not confirmed:
                    speaker.speak("WhatsApp action cancelled sir.")
                    continue

            if intent["intent"] == "open_app":
                target = (intent.get("target") or "").strip().lower()
                if target and target not in APPS:
                    confirmed = ask_voice_confirmation(
                        speaker,
                        listener,
                        f"{target} is not in your trusted app list. "
                        "Do you still want to open it? Say yes or no."
                    )
                    if not confirmed:
                        speaker.speak("Open app cancelled sir.")
                        continue

            if intent["intent"] == "open_website":
                target = (intent.get("target") or "").strip().lower()
                if target and target not in WEBSITES:
                    confirmed = ask_voice_confirmation(
                        speaker,
                        listener,
                        f"{target} is not in your trusted website list. "
                        "Do you still want to open it? Say yes or no."
                    )
                    if not confirmed:
                        speaker.speak("Open website cancelled sir.")
                        continue

            handler = intent_handlers.get(intent["intent"])
            if handler:
                response = handler(intent)
                speaker.speak(response)
            else:
                print("JARVIS is thinking...")
                response = brain.think(command)
                speaker.speak(response)

        except KeyboardInterrupt:
            print(f"\n\nEmergency shutdown.")
            speaker.speak("Emergency shutdown. Goodbye sir.")
            break


def main():
    """
    Entry point - decide which mode to run.

    python main.py           -> text mode
    python main.py --voice   -> voice mode
    """
    validation = validate_startup_config()
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"Startup warning: {warning}")

    if not validation["ok"]:
        for error in validation["errors"]:
            logger.error(f"Startup config error: {error}")
        print(
            f"{JARVIS_NAME}: Startup configuration error. "
            "Please fix your .env/config and restart."
        )
        return

    if "--voice" in sys.argv:
        run_voice_mode()
    else:
        run_text_mode()


if __name__ == "__main__":
    main()