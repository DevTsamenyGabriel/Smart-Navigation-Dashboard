# music_handler.py
import os
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class MusicLogic:
    def __init__(self, ui_object):
        self.ui = ui_object

        # --- Audio Engine ---
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        # --- Music Folder ---
        self.music_dir = os.path.expanduser("~/Music")

        # --- Slider update timer (UI only) ---
        # Make it smoother than 1s so slider doesn't "jump"
        self.timer = QTimer()
        self.timer.setInterval(200)  # was 1000
        self.timer.timeout.connect(self.update_slider_ui)

        # Optional: track if user is scrubbing (prevents UI fighting)
        self.user_scrubbing = False

    def load_music_list(self):
        if os.path.exists(self.music_dir):
            songs = [
                f for f in os.listdir(self.music_dir)
                if f.lower().endswith((".mp3", ".wav"))
            ]
            self.ui.MymusiclistWidget.clear()
            self.ui.MymusiclistWidget.addItems(songs)
        else:
            self.ui.MymusiclistWidget.clear()

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.timer.stop()
        else:
            self.play_music()

    def play_music(self):
        try:
            if self.ui.MymusiclistWidget.count() == 0:
                print("No music Found")
                return

            selected_item = self.ui.MymusiclistWidget.currentItem()

            # If nothing selected, select first
            if not selected_item and self.ui.MymusiclistWidget.count() > 0:
                self.ui.MymusiclistWidget.setCurrentRow(3)
                selected_item = self.ui.MymusiclistWidget.item(3)

            if not selected_item:
                return

            file_path = os.path.abspath(os.path.join(self.music_dir, selected_item.text()))
            media_url = QUrl.fromLocalFile(file_path)

            # Only reset source if different
            if self.player.source() != media_url:
                self.player.setSource(media_url)

                title = selected_item.text()
                if len(title) > 40:
                    title = title[:40] + "..."
                self.ui.songTitle.setText(title)

            self.player.play()
            self.timer.start()

        except Exception as e:
            print(f"Playback Error: {e}")

    def update_slider_ui(self):
        """Update slider + timer label safely."""
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return

        # If user is dragging slider, don't override their movement
        if self.user_scrubbing:
            return

        pos = self.player.position()

        # Update slider without emitting signals
        self.ui.MusichorizontalSlider.blockSignals(True)
        self.ui.MusichorizontalSlider.setValue(pos)
        self.ui.MusichorizontalSlider.blockSignals(False)

        # Update timer label
        if hasattr(self.ui, "musicTimerLabel"):
            seconds = (pos // 1000) % 60
            minutes = (pos // 60000)
            self.ui.musicTimerLabel.setText(f"{minutes:02d}:{seconds:02d}")

    def handle_next(self):
        curr = self.ui.MymusiclistWidget.currentRow()
        if curr < self.ui.MymusiclistWidget.count() - 1:
            self.ui.MymusiclistWidget.setCurrentRow(curr + 1)
            self.play_music()

    def handle_prev(self):
        curr = self.ui.MymusiclistWidget.currentRow()
        if curr > 0:
            self.ui.MymusiclistWidget.setCurrentRow(curr - 1)
            self.play_music()

    # --- Optional scrubbing helpers (use with sliderPressed/sliderReleased in main.py) ---
    def on_slider_pressed(self):
        self.user_scrubbing = True

    def on_slider_released(self):
        # seek only once when user releases slider (stable)
        self.player.setPosition(self.ui.MusichorizontalSlider.value())
        self.user_scrubbing = False