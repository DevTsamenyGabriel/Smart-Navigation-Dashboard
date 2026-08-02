import requests
import base64
import os
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from dotenv import load_dotenv

load_dotenv()
## tHIS IS HOW I RETRIEVED THE VOICE FROM INWORLD

class GabbyVoice(QObject):
    finished_speaking = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.cache_dir = "Assets/voice_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        # Setup Player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        # Retrieve the API key from environment variables
        self.api_token = os.getenv("INWORLD_AUTH_TOKEN")

    def speak(self, text, filename):
        file_path = os.path.join(self.cache_dir, f"{filename}.mp3")

        # 1. Check if we already have this audio
        if os.path.exists(file_path):
            print(f"Gabby: Loading '{filename}' from cache...")
            self._play_file(file_path)
        else:
            # 2. If not, ask Inworld
            print(f"Gabby: Requesting new audio for '{text}'...")
            self._fetch_from_inworld(text, file_path)

    def _fetch_from_inworld(self, text, save_path):
        url = "https://api.inworld.ai/tts/v1/voice"
        headers = {
            "Authorization": f"Basic {self.api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "voiceId": "Olivia",
            "modelId": "inworld-tts-1.5-mini",
            "speakingRate": 1.1
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            result = response.json()
            audio_content = base64.b64decode(result['audioContent'])

            with open(save_path, "wb") as f:
                f.write(audio_content)

            self._play_file(save_path)
        except Exception as e:
            print(f"Inworld Error: {e}")

    def _play_file(self, path):
        self.player.setSource(QUrl.fromLocalFile(os.path.abspath(path)))
        self.player.play()