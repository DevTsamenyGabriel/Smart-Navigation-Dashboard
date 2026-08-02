import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFrame, QHBoxLayout, \
    QToolButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import speech_recognition as sr


class GabbyAssistant(QThread):
    # Signals to talk to the UI
    state_changed = pyqtSignal(bool)  # True = Active, False = Sleeping
    command_received = pyqtSignal(str)  # The actual command (e.g., "dark mode")
    feedback_message = pyqtSignal(str)  # Status text for the label

    def __init__(self):
        super().__init__()
        self.is_active = False
        self.is_running = True
        self.recognizer = sr.Recognizer()
        # We make the recognizer a bit faster for car environments
        self.recognizer.dynamic_energy_threshold = True

    def run(self):
        with sr.Microphone() as source:
            self.feedback_message.emit("Calibrating background noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.feedback_message.emit("Gabby OS: Ready (Say 'Hey Gabby')")

            while self.is_running:
                try:
                    # We only print this to your console to see it's alive
                    print("Listening for wake word or command...")

                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio).lower()

                    # ONLY call this. Let this function decide what to emit.
                    self.process_logic(text)

                except Exception as e:
                    continue

    def process_logic(self, text):
        # State: SLEEPING (Looking for Wake Word)
        if not self.is_active:
            if "hey gabe" in text or "gabby" in text or "hey gab" in text or "gab" in text or "gaby" in text:
                self.is_active = True
                self.state_changed.emit(True)
                self.feedback_message.emit("Uhu? I'm listening...")
                print(f"WAKE WORD DETECTED: {text}")
            else:
                print(f"Ignored background noise: {text}")

        # State: ACTIVE (Looking for Command)
        else:
            print(f"COMMAND DETECTED: {text}")
            self.command_received.emit(text)

            # Reset to Sleep mode after processing
            self.is_active = False
            self.state_changed.emit(False)
            self.feedback_message.emit("Gabe OS: Standing by...")



class MainWindows(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gabby OS - Car Assistant")
        self.setGeometry(100, 100, 530, 400)
        self.setStyleSheet("background-color: #1e1e1e; color: #fff; font-family: 'Roboto';")

        self.Assistant = GabbyAssistant()
        self.Assistant.state_changed.connect(self.on_state_changed)
        self.Assistant.command_received.connect(self.on_command_received)
        self.Assistant.feedback_message.connect(self.update_feedback)
        self.Assistant.start()


    def on_state_changed(self,  is_active):
        print("State changed:", "ActiveSleeping")


    def on_command_received(self,command):
        # Here we would parse the command and trigger actions
        # For now, we just show a message box with the command
        print("command")


    def update_feedback(self, text):
        # This function can be used to update a label in the UI with status messages
        print(text)




if __name__== "__main__":
    app = QApplication(sys.argv)
    window = MainWindows()
    window.show()
    sys.exit(app.exec())


