"""
actions/spotify.py - JARVIS Spotify Integration.

Control Spotify by voice:
"JARVIS play music"
"JARVIS pause music"
"JARVIS next song"
"JARVIS previous song"
"JARVIS play song Believer"

Uses spotipy for full Spotify control.
Requires Spotify Premium for playback control.
Free accounts can only open Spotify.
"""
import subprocess
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.logger import get_logger

logger = get_logger(__name__)

# Spotify app credentials
# Get these from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"

# Spotify app path on Windows
SPOTIFY_PATH = r"C:\Users\DELL\AppData\Local\Microsoft\WindowsApps\Spotify.exe"


class SpotifyManager:
    """
    Controls Spotify playback for JARVIS.
    Requires Spotify Premium for full control.
    """

    def __init__(self):
        self.sp = None
        self._setup_spotify()

    def _setup_spotify(self):
        """
        Initialize Spotify connection.
        Only works if credentials are configured.
        """
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            logger.warning("Spotify credentials not configured.")
            return

        try:
            # Setup OAuth with required permissions
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=(
                    "user-read-playback-state "
                    "user-modify-playback-state "
                    "user-read-currently-playing "
                    "streaming"
                )
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Spotify connected successfully.")

        except Exception as e:
            logger.error(f"Spotify setup error: {e}")
            self.sp = None

    def _get_active_device(self):
        """Get the first active Spotify device."""
        try:
            devices = self.sp.devices()
            if devices and devices["devices"]:
                return devices["devices"][0]["id"]
            return None
        except Exception:
            return None

    def open_spotify(self) -> str:
        """Open the Spotify application."""
        try:
            if os.path.exists(SPOTIFY_PATH):
                subprocess.Popen(SPOTIFY_PATH)
                return "Opening Spotify sir."
            else:
                # Try opening via command
                subprocess.Popen("spotify")
                return "Opening Spotify sir."
        except Exception as e:
            logger.error(f"Open Spotify error: {e}")
            return "Could not open Spotify sir."

    def play(self) -> str:
        """Resume or start playback."""
        if not self.sp:
            return self.open_spotify()

        try:
            device_id = self._get_active_device()
            if device_id:
                self.sp.start_playback(device_id=device_id)
                return "Playing music sir."
            else:
                return (
                    "No active Spotify device found. "
                    "Please open Spotify first sir."
                )
        except Exception as e:
            logger.error(f"Spotify play error: {e}")
            return "Could not play music sir."

    def pause(self) -> str:
        """Pause playback."""
        if not self.sp:
            return "Spotify is not connected sir."

        try:
            self.sp.pause_playback()
            return "Music paused sir."
        except Exception as e:
            logger.error(f"Spotify pause error: {e}")
            return "Could not pause music sir."

    def next_track(self) -> str:
        """Skip to next track."""
        if not self.sp:
            return "Spotify is not connected sir."

        try:
            self.sp.next_track()
            return "Playing next song sir."
        except Exception as e:
            logger.error(f"Spotify next error: {e}")
            return "Could not skip song sir."

    def previous_track(self) -> str:
        """Go to previous track."""
        if not self.sp:
            return "Spotify is not connected sir."

        try:
            self.sp.previous_track()
            return "Playing previous song sir."
        except Exception as e:
            logger.error(f"Spotify previous error: {e}")
            return "Could not go to previous song sir."

    def play_song(self, song_name: str) -> str:
        """
        Search and play a specific song.

        Args:
            song_name: Name of song to play

        Returns:
            Status message
        """
        if not self.sp:
            # Open Spotify and tell user to search manually
            self.open_spotify()
            return (
                f"Opening Spotify. "
                f"Please search for {song_name} manually sir. "
                f"For automatic song search, configure Spotify "
                f"credentials in your .env file."
            )

        try:
            # Search for the song
            results = self.sp.search(
                q=song_name,
                limit=1,
                type="track"
            )

            tracks = results["tracks"]["items"]
            if not tracks:
                return f"Could not find song {song_name} sir."

            # Get song URI and play it
            track = tracks[0]
            track_uri = track["uri"]
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]

            device_id = self._get_active_device()
            if device_id:
                self.sp.start_playback(
                    device_id=device_id,
                    uris=[track_uri]
                )
                return (
                    f"Playing {track_name} by "
                    f"{artist_name} sir."
                )
            else:
                return (
                    "No active Spotify device. "
                    "Please open Spotify first sir."
                )

        except Exception as e:
            logger.error(f"Spotify play song error: {e}")
            return f"Could not play {song_name} sir."

    def get_current_song(self) -> str:
        """Returns currently playing song info."""
        if not self.sp:
            return "Spotify is not connected sir."

        try:
            current = self.sp.current_playback()
            if current and current["is_playing"]:
                track = current["item"]
                name = track["name"]
                artist = track["artists"][0]["name"]
                return f"Currently playing {name} by {artist} sir."
            return "Nothing is playing on Spotify right now sir."
        except Exception as e:
            logger.error(f"Spotify current song error: {e}")
            return "Could not get current song sir."

    def set_volume(self, volume: int) -> str:
        """
        Set Spotify volume.

        Args:
            volume: 0 to 100
        """
        if not self.sp:
            return "Spotify is not connected sir."

        try:
            volume = max(0, min(100, volume))
            self.sp.volume(volume)
            return f"Spotify volume set to {volume} percent sir."
        except Exception as e:
            logger.error(f"Spotify volume error: {e}")
            return "Could not change volume sir."