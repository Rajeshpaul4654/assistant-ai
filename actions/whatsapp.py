"""
actions/whatsapp.py - JARVIS WhatsApp Integration.

Send WhatsApp messages by voice:
"JARVIS send whatsapp to Mom hello how are you"
"JARVIS whatsapp John I am on my way"

Uses pywhatkit which sends via WhatsApp Web.
Requires WhatsApp Web to be logged in on your browser.
"""
import pywhatkit as kit
import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Contact name → phone number mapping ─────────────────────
# Add your contacts here
# Format: "name": "+91xxxxxxxxxx"
CONTACTS = {
    "mom":      "+91xxxxxxxxxx",
    "dad":      "+91xxxxxxxxxx",
    "john":     "+91xxxxxxxxxx",
    "friend":   "+91xxxxxxxxxx",
    # Add more contacts here
}


class WhatsAppManager:
    """
    Handles WhatsApp messaging for JARVIS.
    Uses pywhatkit to send messages via WhatsApp Web.
    """

    def send_message(self, contact: str, message: str) -> str:
        """
        Send a WhatsApp message to a contact.

        Args:
            contact: Contact name (must be in CONTACTS dict)
            message: Message to send

        Returns:
            Status message
        """
        # Clean contact name
        contact = contact.lower().strip()

        # Look up phone number
        if contact not in CONTACTS:
            available = ", ".join(CONTACTS.keys())
            return (
                f"I don't have {contact} in my contacts. "
                f"Available contacts are: {available}. "
                f"You can add more in actions/whatsapp.py sir."
            )

        phone = CONTACTS[contact]

        # Validate phone number
        if "xxxxxxxxxx" in phone:
            return (
                f"Please update the phone number for {contact} "
                f"in actions/whatsapp.py sir."
            )

        try:
            # Get current time and add 2 minutes
            # pywhatkit needs a future time to schedule
            now = datetime.datetime.now()
            send_hour = now.hour
            send_minute = now.minute + 2

            # Handle minute overflow
            if send_minute >= 60:
                send_minute -= 60
                send_hour += 1

            # Send message via WhatsApp Web
            # wait_time=15 gives browser time to open
            # tab_close=True closes tab after sending
            kit.sendwhatmsg(
                phone,
                message,
                send_hour,
                send_minute,
                wait_time=15,
                tab_close=True,
                close_time=3
            )

            logger.info(f"WhatsApp sent to {contact}: {message[:30]}")
            return (
                f"Sending WhatsApp message to {contact}. "
                f"Please keep WhatsApp Web open in your browser sir."
            )

        except Exception as e:
            logger.error(f"WhatsApp error: {e}")
            return f"Failed to send WhatsApp message to {contact} sir."

    def parse_command(self, command: str) -> str:
        """
        Parse a voice command and send WhatsApp message.

        Handles commands like:
        "send whatsapp to mom hello"
        "whatsapp john I am on my way"
        "send message to dad good morning"

        Args:
            command: Full voice command string

        Returns:
            Status message
        """
        command = command.lower().strip()

        # Extract contact and message from supported patterns:
        # - "send whatsapp to mom hello"
        # - "whatsapp john I am on my way"
        # - "send message to dad good morning"
        contact = None
        message = None

        if " to " in command:
            # Split on "to" keyword
            parts = command.split(" to ", 1)
            rest = parts[1].strip()

            # First word after "to" is contact name
            words = rest.split(" ", 1)
            if len(words) >= 2:
                contact = words[0].strip()
                message = words[1].strip()
            elif len(words) == 1:
                contact = words[0].strip()
                message = "Hello"
        else:
            # Pattern without "to": e.g., "whatsapp john hello there"
            prefixes = ["send whatsapp ", "whatsapp ", "send message "]
            for prefix in prefixes:
                if command.startswith(prefix):
                    rest = command[len(prefix):].strip()
                    words = rest.split(" ", 1)
                    if len(words) >= 1 and words[0]:
                        contact = words[0].strip()
                        message = words[1].strip() if len(words) == 2 else "Hello"
                    break

        if not contact:
            return (
                "Please say who to send to. "
                "For example: send whatsapp to mom hello sir."
            )

        if not message:
            message = "Hello"

        return self.send_message(contact, message)