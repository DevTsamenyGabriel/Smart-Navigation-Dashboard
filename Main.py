import hashlib
import os
import sys
import time
# FORCE GPU ACCELERATION -
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu-rasterization --ignore-gpu-blocklist --num-raster-threads=4"

from PyQt6 import QtGui
from PyQt6.QtWidgets import (
    QApplication, QLabel, QFileDialog, QMessageBox, QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QWidget, QGridLayout, QLineEdit, QTextEdit, QMainWindow
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal
# Importing QwebEngineView for displaying the web content
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QPixmap, QIcon
from datetime import datetime

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

###IMporting of modules
from mapgui import Ui_MainWindow
from modules.ev_finder import get_ev_stations, build_map_html
from modules.music_handler import MusicLogic
from modules.weather_handler import WeatherWorker
from modules.Gabby_AI_Assistant_Voice_Over import GabbyVoice
from modules.connection_battery import SystemMonitorLogic
from modules.road_risk_checker import RoadRiskWorker

## Gabby Ai worker
import speech_recognition as sr


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)













class GabbyAssistant(QThread):
    getting_command = pyqtSignal(str)
    feedback = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.recognizer = sr.Recognizer()
        self.microphone = None


        # --- NEW CAR SETTINGS ---
        self.recognizer.dynamic_energy_threshold = False  # STOP auto-adjusting
        self.recognizer.energy_threshold = 150  # Lock sensitivity
        self.recognizer.pause_threshold = 0.5  # Speak faster
        self.is_running = True

    def run(self):
        self.feedback.emit("Calibrating the mic")

        # with sr.Microphone() as source:
        # self.recognizer.adjust_for_ambient_noise(source)
        if self.microphone is None:
            self.microphone = sr.Microphone()

        self.feedback.emit("Assistance is ready")

        with sr.Microphone() as source:

            while self.is_running:
                try:
                    print("kauuuu")
                    self.feedback.emit("listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    self.feedback.emit("Processing your voice...")
                    text = self.recognizer.recognize_google(audio).lower()
                    print(f"Recognized Text: {text}")
                    self.getting_command.emit(text)


                except sr.WaitTimeoutError:
                    # User didn't say anything within the 5-second window
                    print("Gabby: Silence detected.")
                    self.feedback.emit("Error: No speech detected.")


                except sr.UnknownValueError:
                    # User spoke, but Google couldn't turn it into text
                    print("Gabby: Speech unclear.")
                    self.feedback.emit("Error: Could not understand audio.")


                except sr.RequestError:
                    # Internet is down or Google API limit reached
                    print("Gabby: Network/Service Issue.")
                    self.feedback.emit("Error: Speech Service unavailable.")


                except Exception as e:
                    # Any other random crash (Mic unplugged, etc.)
                    print(f"Gabby: Critical System Error: {e}")
                    self.feedback.emit(f"Error: {str(e)}")

    def stop(self):
        self.is_running = False


class EVWorker(QThread):
    finished = pyqtSignal(list)

    def run(self):
        stations = get_ev_stations()
        self.finished.emit(stations)


class MainWindow(QMainWindow):
    ready_to_show = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("SmartNav - Gabby AI Assistant")

        # Optional: You can also set the window icon here so it shows in the top-left corner


        self.ai_status_label = QLabel("...", self.ui.gabe_AI_listener)

        # 2. Position it on the right side of the button
        # Assuming your button is 90px wide, we put the text at x=45
        self.ai_status_label.setGeometry(55, 0, 27, 39)

        #road Safty toggler
        self.road_is_currently_clear = True

        # 3. Style it so it looks like part of the button
        self.ai_status_label.setStyleSheet("""
            background: transparent; 
            color: #a855f7; 
            font-weight: bold; 
            font-size: 16px;
        """)
        self.ai_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 4. CRITICAL: Tell the label to ignore mouse clicks
        # This way, if you click the text, the BUTTON still gets clicked
        self.ai_status_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # --- 1. DEFINE THE BRAIN OF THE PATHS ---
        # This is the ONLY line that matters for the folder location
        self.base_dir = resource_path("Assets")

        # --- 2. DEFINE SUB-FOLDERS ---
        # We join paths relative to the 'Assets' folder
        icon_folder = os.path.join(self.base_dir, "icons").replace("\\", "/")
        image_folder = os.path.join(self.base_dir, "images").replace("\\", "/")
        map_folder = os.path.join(self.base_dir, "maps", "maphtml").replace("\\", "/")

        # --- 3. APPLY BACKGROUNDS ---
        self.ui.Motherframe.setStyleSheet(
            f"#Motherframe{{ border-image: url('{image_folder}/8033685_12232.jpg') 0 0 0 0; }}")
        self.ui.MusicImageframe.setStyleSheet(
            f"#MusicImageframe{{ border-image: url('{image_folder}/istockphoto-1483833011-612x612.jpg'); border-radius: 15px; }}")
        self.ui.Weatherframe.setStyleSheet(
            f"#Weatherframe{{ border-image: url('{image_folder}/sky-clouds-background.jpg'); }}")

        # --- 4. APPLY SETTINGS THUMBNAILS ---
        self.ui.map3dframe.setStyleSheet(
            f"#map3dframe{{ border-image: url('{image_folder}/3d-view-map.jpg'); border-radius:20px; }}")
        self.ui.styletrafficFrame.setStyleSheet(
            f"#styletrafficFrame{{ border-image: url('{image_folder}/trafficstyle.jpg'); border-radius:20px; }}")
        self.ui.styleNightFrame.setStyleSheet(
            f"#styleNightFrame{{ border-image: url('{image_folder}/AdobeStock_523843430.jpeg'); border-radius:20px; }}")

        # --- 5. APPLY ICONS ---
        self.ui.btnPrevious.setIcon(QIcon(f"{icon_folder}/icons8-back-to-48.png"))
        self.ui.btnPlay.setIcon(QIcon(f"{icon_folder}/icons8-play-67.png"))
        self.ui.btnForward_2.setIcon(QIcon(f"{icon_folder}/icons8-forward-48.png"))
        self.ui.gabe_AI_listener.setIcon(QIcon(f"{icon_folder}/geminico.png"))

        #Gabby TOGGLE AI
        # Create the paths to your toggle images
        # Grab the file directly from the base
        on_path_ON = os.path.join(self.base_dir, "icons", "toggle_ON.png").replace("\\", "/")
        on_path_OFF = os.path.join(self.base_dir, "icons", "toggle_OFF.png").replace("\\", "/")

        self.ui.btnVoiceToggle.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 60px;
                height: 30px;
            }}
            /* What to show when OFF */
            QCheckBox::indicator:unchecked {{
                image: url({on_path_OFF});
            }}
            /* What to show when ON */
            QCheckBox::indicator:checked {{
                image: url({on_path_ON});
            }}
        """)

        # Set the starting state to ON (Checked)
        self.ui.btnVoiceToggle.setChecked(True)















        # Gabby Voice Setup
        self.gabby_voice = GabbyVoice()
        self.first_run = True  # Flag to track the first run for the greeting message
        self.isGabbyTalking = False  # Flag to track if Gabby is currently speaking
        #Loadin EV
        self.worker = EVWorker()

        #Loading default lat,lon,ev
        self.current_car_lat = 5.6506  # Default: near University of Ghana
        self.current_car_lon = -0.1870
        # 2. PLACE THE CLICK HANDLER CONNECTION HERE:
        self.ui.webEngineView.urlChanged.connect(self.handle_map_click)
        self.ui.webEngineView_2.urlChanged.connect(self.handle_map_click)

        #Initializin YouTube TV
        self.youtubeEngine = self.ui.youtubeWebEngine


        #Scrollbar
        self.ui.MymusiclistWidget.verticalScrollBar().setStyleSheet("width: 0px; background: transparent;")

        # Optional: If you also want to hide the horizontal one just in case
        self.ui.MymusiclistWidget.horizontalScrollBar().setStyleSheet("height: 0px; background: transparent;")

        # This line ensures the scrollbar doesn't reserve any "empty white space" on the right
        self.ui.MymusiclistWidget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ui.MymusiclistWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        #A.I dot listener
        # --- Inside MainWindow.__init__ ---
        self.dot_count = 0
        self.listen_timer = QTimer(self)
        self.listen_timer.timeout.connect(self.update_listening_dots)
        #self.ui.gabe_AI_listener.setFixedWidth(90)

        #System Monitor


        self.sys_mon = SystemMonitorLogic()


        #Images UNHARDCODEING######
        # 1. Define the base directories
        #self.base_dir = os.path.dirname(os.path.abspath(__file__))
        #icon_folder = os.path.join(self.base_dir, "Assets", "icons").replace("\\", "/")
        #image_folder = os.path.join(self.base_dir, "Assets", "images").replace("\\", "/")

        # 2. Fix the Backgrounds (Overriding the hardcoded UI paths)
        self.ui.Motherframe.setStyleSheet(
            f"#Motherframe{{ border-image: url('{image_folder}/8033685_12232.jpg') 0 0 0 0; }}")
        self.ui.MusicImageframe.setStyleSheet(
            f"#MusicImageframe{{ border-image: url('{image_folder}/istockphoto-1483833011-612x612.jpg'); border-radius: 15px; }}")
        self.ui.Weatherframe.setStyleSheet(
            f"#Weatherframe{{ border-image: url('{image_folder}/sky-clouds-background.jpg'); }}")

        # 3. Fix the Settings Page Thumbnails
        self.ui.map3dframe.setStyleSheet(
            f"#map3dframe{{ border-image: url('{image_folder}/3d-view-map.jpg'); border-radius:20px; }}")
        self.ui.styletrafficFrame.setStyleSheet(
            f"#styletrafficFrame{{ border-image: url('{image_folder}/trafficstyle.jpg'); border-radius:20px; }}")
        self.ui.styleNightFrame.setStyleSheet(
            f"#styleNightFrame{{ border-image: url('{image_folder}/AdobeStock_523843430.jpeg'); border-radius:20px; }}")

        # 4. Fix ALL Icons manually
        self.ui.btnPrevious.setIcon(QIcon(f"{icon_folder}/icons8-back-to-48.png"))
        self.ui.btnPlay.setIcon(QIcon(f"{icon_folder}/icons8-play-67.png"))
        self.ui.btnForward_2.setIcon(QIcon(f"{icon_folder}/icons8-forward-48.png"))
        # ... do this for all nav buttons too ...
        # Final Navigation Icon Overrides
        self.ui.BtnSettingsPage.setIcon(QIcon(f"{icon_folder}/setting (1).png"))
        self.ui.BtnYoutube.setIcon(QIcon(f"{icon_folder}/youtube.png"))
        self.ui.BtnMusicPage.setIcon(QIcon(f"{icon_folder}/music.png"))
        self.ui.btnEvFinderPage.setIcon(QIcon(f"{icon_folder}/electric.png"))
        self.ui.btnWeatherPage.setIcon(QIcon(f"{icon_folder}/rainy.png"))
        self.ui.BtnHomePage.setIcon(QIcon(f"{icon_folder}/home.png"))
        self.ui.gabe_AI_listener.setIcon(QIcon(f"{icon_folder}/geminico.png"))

        # 2. Fix the Backgrounds (Including the layout fix for MusicImageframe)
        self.ui.Motherframe.setStyleSheet(
            f"#Motherframe{{ border-image: url('{image_folder}/8033685_12232.jpg') 0 0 0 0; }}"
        )

        # Added the margin-right: 95px back here so it doesn't move!
        self.ui.MusicImageframe.setStyleSheet(f"""
            #MusicImageframe{{ 
                border-image: url('{image_folder}/istockphoto-1483833011-612x612.jpg'); 
                border-radius: 15px; 
                border: 2px solid red;
                margin-right: 95px; 
            }}
        """)

        self.ui.Weatherframe.setStyleSheet(
            f"#Weatherframe{{ border-image: url('{image_folder}/sky-clouds-background.jpg'); }}"
        )

        # ============ FINAL ASSET & LAYOUT OVERRIDES ============
        #self.base_dir = os.path.dirname(os.path.abspath(__file__))
        #icon_folder = os.path.join(self.base_dir, "Assets", "icons").replace("\\", "/")
        #image_folder = os.path.join(self.base_dir, "Assets", "images").replace("\\", "/")

        # Fix Backgrounds + Keep Layout Spacing
        self.ui.Motherframe.setStyleSheet(
            f"#Motherframe{{ border-image: url('{image_folder}/8033685_12232.jpg') 0 0 0 0; }}")

        # 2. Fix the Hardcoded Map Style Images (Settings Page)
        self.ui.map3dframe.setStyleSheet(
            f"#map3dframe{{ border-image: url('{image_folder}/3d-view-map.jpg'); border-radius:20px; }}")
        self.ui.styletrafficFrame.setStyleSheet(
            f"#styletrafficFrame{{ border-image: url('{image_folder}/trafficstyle.jpg'); border-radius:20px; }}")
        self.ui.styleNightFrame.setStyleSheet(
            f"#styleNightFrame{{ border-image: url('{image_folder}/AdobeStock_523843430.jpeg'); border-radius:20px; }}")

        # 5. Fix Play/Prev/Next Icons inside Music Page
        self.ui.btnPrevious.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-back-to-48.png"))
        self.ui.btnPlay.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-play-67.png"))
        self.ui.btnForward_2.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-forward-48.png"))

        # BTN WEATHER ICONS
        self.ui.btnwind.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-wind-50.png"))
        self.ui.btnUvindex.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-visibility-32.png"))
        self.ui.btnVisibility.setIcon(QtGui.QIcon(f"{icon_folder}/icons8-uv-index-64.png"))





        # Music Frame: Spacing (95px) + Image
        self.ui.MusicImageframe.setStyleSheet(f"""
            #MusicImageframe{{ 
                border-image: url('{image_folder}/istockphoto-1483833011-612x612.jpg'); 
                border-radius: 15px; 
                margin-right: 95px; 
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)

        # Weather + Settings Page Overrides
        self.ui.Weatherframe.setStyleSheet(
            f"#Weatherframe{{ border-image: url('{image_folder}/sky-clouds-background.jpg'); }}")
        self.ui.map3dframe.setStyleSheet(
            f"#map3dframe{{ border-image: url('{image_folder}/3d-view-map.jpg'); border-radius:20px; }}")
        self.ui.styletrafficFrame.setStyleSheet(
            f"#styletrafficFrame{{ border-image: url('{image_folder}/trafficstyle.jpg'); border-radius:20px; }}")
        self.ui.styleNightFrame.setStyleSheet(
            f"#styleNightFrame{{ border-image: url('{image_folder}/AdobeStock_523843430.jpeg'); border-radius:20px; }}")

        # Ensure all Navigation Icons load
        nav_icons = {
            self.ui.BtnSettingsPage: "setting (1).png",
            self.ui.BtnYoutube: "youtube.png",
            self.ui.BtnMusicPage: "music.png",
            self.ui.btnEvFinderPage: "electric.png",
            self.ui.btnWeatherPage: "rainy.png",
            self.ui.BtnHomePage: "home.png"
        }
        for btn, icon_name in nav_icons.items():
            btn.setIcon(QtGui.QIcon(f"{icon_folder}/{icon_name}"))









        # 2. Setup a Timer to refresh the labels
        #self.sys_timer = QTimer(self)
        #self.sys_timer.timeout.connect(self.update_system_status)
        #self.sys_timer.start(5000)  # Update every 5 seconds (saves CPU)

        # Initial call
        self.update_system_status()


        # ==========================
        # Gabby AI Setup
        # ==========================
        # If default mic is wrong on your PC, set mic_device_index to the correct one:
        # self.assistant = GabbyAssistant(mic_device_index=1)
        self.assistant = GabbyAssistant()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.assistant.getting_command.connect(self.handle_voice_commands)
        self.assistant.feedback.connect(self.adjust_volume_for_voice)
        self.assistant.start()

        # 1. First, tell Python these buttons ARE allowed to be 'Checked'
        from PyQt6.QtWidgets import QButtonGroup  # Ensure this is at the top with other imports

        # --- EXCLUSIVE GROUP LOGIC ---
        self.map_style_group = QButtonGroup(self)
        self.map_style_group.addButton(self.ui.btn_3d)
        self.map_style_group.addButton(self.ui.btn_traffic)
        self.map_style_group.addButton(self.ui.btn_night)
        self.map_style_group.setExclusive(True)

        style_btns = [self.ui.btn_3d, self.ui.btn_traffic, self.ui.btn_night]
        for btn in style_btns:
            btn.setCheckable(True)
            btn.setAutoExclusive(True)

        self.ui.btn_3d.setChecked(True)

        forced_qss = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            /* Use !important to override any background-image conflicts */
            QPushButton:checked {

                border: 2px solid rgb(255, 0, 0) !important;
            }
        """

        self.ui.btn_3d.setStyleSheet(forced_qss)
        self.ui.btn_traffic.setStyleSheet(forced_qss)
        self.ui.btn_night.setStyleSheet(forced_qss)

        # MAP STYLE BUTTONS
        self.ui.btn_traffic.clicked.connect(self.enable_traffic_mode)
        self.ui.btn_3d.clicked.connect(self.enable_3d_mode)
        self.ui.btn_night.clicked.connect(self.enable_night_mode)


        #self.ui.btn_3d.clicked.connect(lambda: self.update_mapbox_style("mapbox://styles/mapbox/streets-v12"))
        #self.ui.btn_traffic.clicked.connect(
        #lambda: self.update_mapbox_style("mapbox://styles/mapbox/navigation-day-v1"))
        #self.ui.btn_night.clicked.connect(lambda: self.update_mapbox_style("mapbox://styles/mapbox/dark-v11"))

        # ==========================
        # WEATHER WIDGET (FIXED)
        # ==========================
        self.weather_api_key = self.api_key = os.getenv('WEATHER_API_KEY')
        self.weather_worker = WeatherWorker(self.weather_api_key)
        self.weather_worker.weather_data_ready.connect(self.process_weather_data)
        self.weather_worker.start()

        # LIVE CLOCK SETUP
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_live_clock)
        self.clock_timer.start(1000)

        # TYPEWRITER SETUP
        self.full_summary_text = ""
        self.char_index = 0
        self.type_timer = QTimer()
        self.type_timer.timeout.connect(self.typewriter_step)

        # ==========================
        # MUSIC PLAYER (FIXED)
        # ==========================
        self.music_engine = MusicLogic(self.ui)
        self.music_engine.load_music_list()

        self.ui.btnPlay.clicked.connect(self.music_engine.toggle_playback)
        self.ui.btnPrevious.clicked.connect(self.music_engine.handle_prev)
        self.ui.btnForward_2.clicked.connect(self.music_engine.handle_next)
        self.ui.MymusiclistWidget.itemDoubleClicked.connect(self.music_engine.play_music)

        self.ui.MusichorizontalSlider.setRange(0, 0)
        self.ui.MusichorizontalSlider.setValue(0)

        self.music_engine.player.durationChanged.connect(
            lambda d: self.ui.MusichorizontalSlider.setRange(0, d)
        )

        self.ui.MusichorizontalSlider.sliderPressed.connect(self.music_engine.on_slider_pressed)
        self.ui.MusichorizontalSlider.sliderReleased.connect(self.music_engine.on_slider_released)

        # ==========================
        # ASSETS / MAPBOX
        # ==========================
        #self.base_dir = os.path.dirname(os.path.abspath(__file__))

        #icon_folder = os.path.join(self.base_dir, "Assets", "icons")
        #image_folder = os.path.join(self.base_dir, "Assets", "images")
        #map_folder = os.path.join(self.base_dir, "Assets", "maps", "maphtml")

        bg_file = os.path.join(image_folder, "8033685_12232.jpg").replace("\\", "/")
        self.ui.Motherframe.setStyleSheet(f"""
                    #Motherframe {{
                        border-image: url("{bg_file}") 0 0 0 0;
                    }}
                """)

        self.ui.BtnSettingsPage.setIcon(QIcon(os.path.join(icon_folder, "setting (1).png")))
        self.ui.BtnYoutube.setIcon(QIcon(os.path.join(icon_folder, "youtube.png")))
        self.ui.BtnMusicPage.setIcon(QIcon(os.path.join(icon_folder, "music.png")))
        self.ui.btnEvFinderPage.setIcon(QIcon(os.path.join(icon_folder, "electric.png")))
        self.ui.btnWeatherPage.setIcon(QIcon(os.path.join(icon_folder, "rainy.png")))
        self.ui.BtnHomePage.setIcon(QIcon(os.path.join(icon_folder, "home.png")))

        # BUTTON NAVIGATION
        self.ui.BtnHomePage.clicked.connect(lambda: self.ui.QStacked.setCurrentWidget(self.ui.mapBoxMappage))
        self.ui.BtnMusicPage.clicked.connect(lambda: self.ui.QStacked.setCurrentWidget(self.ui.mapmusicpage))
        #self.ui.BtnYoutube.clicked.connect(lambda: self.ui.QStacked.setCurrentWidget(self.ui.YoutubeLoadPage))
        self.ui.btnWeatherPage.clicked.connect(lambda: self.ui.QStacked.setCurrentWidget(self.ui.WeatherPage))
        self.ui.btnEvFinderPage.clicked.connect(self.start_ev_finder)
        self.ui.BtnYoutube.clicked.connect(self.load_Youtube_Player)

        self.ui.BtnSettingsPage.clicked.connect(lambda: self.ui.QStacked.setCurrentWidget(self.ui.SettingsPage))
        self.ui.QStacked.setCurrentWidget(self.ui.mapBoxMappage)

        # MAP LOADING
        self.map_path = os.path.join(map_folder, "index.html")
        self.load_map()

        settings = self.ui.webEngineView.settings()
        attr = settings.WebAttribute

        settings.setAttribute(attr.JavascriptEnabled, True)
        settings.setAttribute(attr.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(attr.LocalContentCanAccessFileUrls, True)

        try:
            settings.setAttribute(attr.ShowScrollBars, True)
            if hasattr(attr, 'DeveloperExtrasEnabled'):
                settings.setAttribute(attr.DeveloperExtrasEnabled, True)
        except Exception as e:
            print(f"Non-critical: {e}")

        self.ui.webEngineView.loadFinished.connect(self.on_load_finished)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.base_dir, "icons", "smart_nav.ico")))

        #USE TO MAKE AI SPEAK TRAFFIC
        self.User_in_traffic_mode = False




        #self.showFullScreen()




    #MAP STYLE LOGIC Function###########
    def enable_traffic_mode(self):
        # FIRST: Change the map to the Traffic Style (The Visuals)
        self.update_mapbox_style("mapbox://styles/mapbox/navigation-day-v1")
        self.User_in_traffic_mode = True

        # SECOND: Tell the JavaScript code inside the map to use 'driving'
        # (Your JS 'fetchRoute' will then see 'driving' and use 'driving-traffic' data)
        self.ui.webEngineView.page().runJavaScript("setActiveProfile('driving');")

        print("🚦 Traffic Mode Enabled: Map updated and AI traffic logic activated.")

    def enable_3d_mode(self):
        self.update_mapbox_style("mapbox://styles/mapbox/streets-v12")
        self.ui.webEngineView.page().runJavaScript("setActiveProfile('driving');")
        self.User_in_traffic_mode = False

    def enable_night_mode(self):
        self.update_mapbox_style("mapbox://styles/mapbox/dark-v11")
        self.ui.webEngineView.page().runJavaScript("setActiveProfile('driving');")
        self.User_in_traffic_mode = False







    # ============Battery-WIFI SYSTEM LOgic========================
    def update_system_status(self):
        # Update Wi-Fi Label (Make sure you have a label named 'wifiLabel' in Designer)
        wifi_status = self.sys_mon.get_wifi_info()
        self.ui.wifi_label.setText(f"📶 {wifi_status}")

        # Update Battery Label (Make sure you have a label named 'batteryLabel' in Designer)
        battery_status = self.sys_mon.get_battery_info()
        self.ui.battery_label.setText(f"🔋 {battery_status}")







    # ==========================
    # MAP BOX LOADING LOGIC
    # ==========================
    def load_map(self):
        if os.path.exists(self.map_path):
            self.ui.webEngineView.load(QUrl.fromLocalFile(self.map_path))
        else:
            QMessageBox.critical(self, "Error", f"Could not find map.html at {self.map_path}")
            return

    def on_load_finished(self, success):
        if success:
            print("Python confirmed: index.html loaded successfully.")


        else:
            print("Python confirmed: Failed to load index.html.")

    # ==========================
    # EV Finder LOADING LOGIC
    # ==========================

    def start_ev_finder(self):
        self.ui.QStacked.setCurrentWidget(self.ui.EVpage)
        self.worker.finished.connect(self.on_ev_data_ready)
        self.worker.start()

    def handle_map_click(self, url):
        # 1. Convert the URL to a string
        url_str = url.toString()
        print(f"URL: {url_str}")

        # 2. Check if the "Fragment" (the part after #) contains our data
        if "#loc:" in url_str:
            try:
                # We split the string to get the numbers
                # Example: "data:text/html...#loc:5.60:-0.18"
                data_part = url_str.split("#loc:")[1]
                lat_str, lon_str = data_part.split(":")

                # 3. Update the global variables
                self.current_car_lat = float(lat_str)
                self.current_car_lon = float(lon_str)

                print(f"🚀 Logic Triggered: Car moved to {self.current_car_lat}")

                # 4. Refresh the EV Finder to draw the new road route
                #self.start_ev_finder()

            except Exception as e:
                print(f"Error parsing coordinates: {e}")

            # --- NEW: THE SAFETY CHECK BRIDGE ---

        if "#safety_check:" in url_str:
            try:
                    # Data format: callback:safety_check:lat:lng:name
                    # Example: ["callback", "safety_check", "5.5", "-0.4", "Kasoa"]
                data_part = url_str.split("#safety_check:")[1]
                parts = data_part.split(":")

                dest_lat = parts[0]
                dest_lng = parts[1]
                dest_name = parts[2]
                #traffic_level = parts[3]
                traffic_status = parts[3] if len(parts) > 3 else "low"
                print(f"Traffic 🌉  Traffic recieved {traffic_status}")


                filtered_dest_name = ""
                text = dest_name

                filtered_dest_name = text.split(",")[0]
                print(f"🌉 Bridge Received: {filtered_dest_name}")


                # Start the background thread so the UI doesn't freeze
                self.risk_thread = RoadRiskWorker(self.weather_api_key, filtered_dest_name, dest_lat, dest_lng, self.road_is_currently_clear, traffic_status, self.User_in_traffic_mode)
                self.risk_thread.risk_data_ready.connect(self.play_safety_audio)
                self.risk_thread.start()

                # Cleaner console output for your demo
                print(f"--- SmartNav Intelligence ---")
                print(f"📍 Target: {dest_name.split(',')[0]}")
                print(f"🚦 Traffic Condition: {traffic_status.upper()}")


            except Exception as e:
                print(f"Python Bridge Error: {e}")






    def play_safety_audio(self, message, cache_name, new_state):

        self.road_is_currently_clear = new_state
        if not self.isGabbyTalking:
            self.isGabbyTalking = True
            self.gabby_voice.speak(message, cache_name)
            # Reset talking flag after Gabby is done (approx 7 seconds)
            QTimer.singleShot(7000, lambda: setattr(self, 'isGabbyTalking', False))






    def on_ev_data_ready(self, stations):
        html = build_map_html(stations , self.current_car_lat, self.current_car_lon)
        self.ui.webEngineView_2.setHtml(html)

    # ==========================
    # WEATHER WIDGET LOGIC
    # ==========================
    def process_weather_data(self, data):
        if "error" in data:
            self.ui.descriptionLabel.setText("System Offline")
            return

        current = data.get("current", {})
        temp = round(current.get("temp", 0))
        feels = round(current.get("feels_like", 0))
        desc = current.get("weather", [{}])[0].get("description", "").title()

        self.ui.labelDegress.setText(f"{temp}°")
        self.ui.descriptionLabel.setText(desc)
        self.ui.labelFeelsLike.setText(f"Feels Like {feels}°")

        wind = current.get("wind_speed", 0)
        vis = current.get("visibility", 0) / 1000
        uvi = current.get("uvi", 0)

        self.ui.btnwind.setText(f"Wind Speed {wind} m/s")
        self.ui.btnVisibility.setText(f"Visibility {vis} km")
        self.ui.btnUvindex.setText(f" UV Index {uvi}")

        icon_code = current.get("weather", [{}])[0].get("icon", "01d")
        self.update_weather_background(icon_code)

        daily = data.get("daily", [])
        if daily:
            summary = daily[0].get("summary", "No summary available today.")
            self.start_ai_typing(summary)
            self.setup_forecast(daily)

    def update_weather_background(self, icon_id):
        img_name = "sunny.jpeg"

        if icon_id.startswith("01"):
            img_name = "sunny.jpeg"
        elif icon_id.startswith("02"):
            img_name = "partlycloud.jpeg"
        elif icon_id.startswith(("03", "04")):
            img_name = "clouds.jpeg"
        elif icon_id.startswith(("09", "10", "11")):
            img_name = "stormy.jpeg"
        else:
            img_name = "scatteredclouds.jpeg"

        path = os.path.join(self.base_dir, "images", img_name).replace("\\", "/")

        style = f"""
            #weatherImageFrame {{
                border-image: url('{path}') 0 0 0 0 stretch stretch;
                border-radius: 10px;
            }}
        """
        self.ui.weatherImageFrame.setStyleSheet(style)

    def start_ai_typing(self, text):
        self.full_summary_text = text
        self.char_index = 0
        self.ui.AI_Summery_data.setText("AI SUMMARY: ")
        self.type_timer.start(25)

    def typewriter_step(self):
        if self.char_index < len(self.full_summary_text):
            current_txt = self.ui.AI_Summery_data.text()
            self.ui.AI_Summery_data.setText(current_txt + self.full_summary_text[self.char_index])
            self.char_index += 1
        else:
            self.type_timer.stop()

    def update_live_clock(self):
        current_time = datetime.now().strftime("%I:%M %p")
        self.ui.timeLabel.setText(current_time)

    def setup_forecast(self, daily_data):
        from datetime import datetime

        for i in range(1, 8):
            day_info = daily_data[i - 1]
            dt = datetime.fromtimestamp(day_info.get('dt'))
            day_name = "Today" if i == 1 else dt.strftime('%a')
            temp = round(day_info.get('temp', {}).get('day', 0))

            btn_name = f"daily{i}"
            if hasattr(self.ui, btn_name):
                button = getattr(self.ui, btn_name)
                button.setText(f"{day_name}\n{temp}°")

                if i == 1:
                    button.setStyleSheet("""
                             QPushButton {
                                 background-color: rgba(170, 85, 255, 0.7);
                                 border: 1px solid rgba(255, 255, 255, 0.8);
                                 width: 80px;
                             }
                         """)

                summary = day_info.get('summary', 'No summary available.')

                try:
                    button.clicked.disconnect()
                except Exception:
                    pass

                button.clicked.connect(lambda checked, s=summary: self.start_ai_typing(s))

        if hasattr(self.ui, "daily1"):
            first_summary = daily_data[0].get('summary', 'Weather data loaded.')
            self.start_ai_typing(first_summary)

    # ==========================
    # MAP STYLE LOGIC
    # ==========================
    def update_mapbox_style(self, style_url):
        js_code = f"window.changeMapStyle('{style_url}');"
        self.ui.webEngineView.page().runJavaScript(js_code)

    # ==========================
    # GABBY AI LOGIC
    # ==========================

    def handle_voice_commands(self, command):
        if not self.ui.btnVoiceToggle.isChecked():
            print("Muted Gabby")
            return
        cmd = command.lower()
        print(f"DEBUG: Google heard -> '{cmd}'")
        if self.isGabbyTalking:
            print("DEBUG: Gabby is currently talking. Ignoring command to prevent overlap.")
            return

        # 1. THE WAKE WORD (Check this first!)
        wake_words = ["gabby", "gaby", "gabe", "gab", "hey gaby", "hey gabby","hi gabriel"
                      "gabriel", "gabrie", "gabr", "hey gabriel"]
        if any(word == cmd.strip() for word in wake_words):
            self.isGabbyTalking = True
            self.gabby_voice.speak("Uh-huh?, I'm listening.", "wake_response")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))

            return








        elif "open" in cmd:
            if "map" in cmd or "home" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Switching to the map page.", "map_page")
                self.ui.QStacked.setCurrentWidget(self.ui.mapBoxMappage)
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            elif "audio" in cmd or "player" in cmd or "gabe player" in cmd or "gab player" in cmd or "gabby player" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Switching to the music page.", "music_page")
                self.ui.QStacked.setCurrentWidget(self.ui.mapmusicpage)
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            elif "weather" in cmd or "climate" in cmd or "where" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Switching to the weather page.", "weather_page")
                self.ui.QStacked.setCurrentWidget(self.ui.WeatherPage)
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            elif "charger" in cmd or "open electric" in cmd or "find ev station" in cmd or "station" in cmd or "find" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Finding nearby EV charging stations.", "ev_finder")
                self.start_ev_finder()
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))

            elif "settings" in cmd or "setting" in cmd or "set" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Switching to the settings page.", "settings_page")
                self.ui.QStacked.setCurrentWidget(self.ui.SettingsPage)
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))


            elif "youtube" in cmd or "tube" in cmd or "you tube" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Switching to the Youtube page.", "Youtube_page")
                self.load_Youtube_Player()
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))


            else:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Sorry, I couldn't understand which page to open. Please try again.",
                                       "open_error")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))




        # 2. Music Control

        elif "music" in cmd:

            if "play" in cmd or "resume" in cmd or "start" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Playing your music.", "play_control")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
                if not self.music_engine.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.music_engine.play_music()
            elif "pause" in cmd or "stop" in cmd:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Pausing the music.", "pause_control")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
                if self.music_engine.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.music_engine.toggle_playback()
            elif "next" in cmd or "skip" in cmd or "change" in cmd or "change music" in cmd:
                self.isGabbyTalking = True

                self.gabby_voice.speak("Skipping to the next track.", "next_control")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
                self.music_engine.handle_next()

            elif "prev" in cmd or "back" in cmd or "previous":
                self.isGabbyTalking = True
                self.gabby_voice.speak("Going back to the previous track.", "prev_control")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
                self.music_engine.handle_prev()

            else:
                self.isGabbyTalking = True
                self.gabby_voice.speak("Sorry, I couldn't understand the music command. Please try again.",
                                       "music_command_error")
                QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))




        elif "volume up" in cmd or "increase volume" in cmd or "raise volume" in cmd or "louder" in cmd:

            current_vol = self.music_engine.audio_output.volume()
            new_vol = min(current_vol + 0.5, 1.0)

            self.music_engine.audio_output.setVolume(new_vol)
            self.isGabbyTalking = True
            newvol = str(int(new_vol * 100))
            self.gabby_voice.speak(f"Increasing volume to {newvol} percent.", "volume_up")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))




        elif "volume down" in cmd or "decrease volume" in cmd or "lower volume" in cmd or "lower" in cmd:


            current_vol = self.music_engine.audio_output.volume()
            new_vol = max(current_vol - 0.1, 0.0)

            self.music_engine.audio_output.setVolume(new_vol)
            self.isGabbyTalking = True
            strlowvol = str(int(new_vol * 100))
            self.gabby_voice.speak(f"Decreasing volume to {strlowvol} percent.", "volume_down")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))




        # 3. Theme Control
        elif "dark" in cmd or "night" in cmd or "dark mode" in cmd:
            self.isGabbyTalking = True
            self.gabby_voice.speak("Switching to night mode.", "night_mode")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            #self.update_mapbox_style("mapbox://styles/mapbox/dark-v11")
            self.enable_night_mode()
            self.ui.btn_night.setChecked(True)

        # 4. checkers
        elif "3d" in cmd or "default" in  cmd:
            self.isGabbyTalking = True
            self.gabby_voice.speak("Switching to default map style.", "default_mode")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            #self.update_mapbox_style("mapbox://styles/mapbox/streets-v12")
            self.enable_3d_mode()
            self.ui.btn_3d.setChecked(True)
        elif "traffic" in cmd:
            self.isGabbyTalking = True
            self.gabby_voice.speak("Switching to traffic mode.", "traffic_mode")
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))
            #self.update_mapbox_style("mapbox://styles/mapbox/navigation-day-
            self.enable_traffic_mode()
            self.ui.btn_traffic.setChecked(True)




        elif "check" in cmd:
                weather_keywords = ["check todays weather", "today", "check weather", "today's weather", "current weather"]


                if any(word in cmd for word in weather_keywords):
                    # 2. Get the data from your UI labels
                    current_desc = self.ui.descriptionLabel.text()  # e.g., "Clear Sky"
                    current_temp = self.ui.labelDegress.text()  # e.g., "32°"
                    ai_summary = self.ui.AI_Summery_data.text()
                    # Your AI summary text
                    ai_summary_data = ai_summary[11:]

                    # 3. Construct a beautiful sentence

                    weather_sentence = f"Currently in Accra, it's {current_desc} with a temperature of {current_temp}. {ai_summary_data}"
                    file_for_weather = weather_sentence.encode()
                    to_hashlib = hashlib.md5(file_for_weather)
                    to_hex = to_hashlib.hexdigest()[:10]
                    cache_name = f"weather_{to_hex}"


                    self.isGabbyTalking = True
                    self.gabby_voice.speak(weather_sentence, cache_name)
                    QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))

                if "time" in cmd or "check time" in cmd or "the time" in cmd:
                    current_time = datetime.now().strftime("%I:%M %p")
                    timerTostring = 'time' + str(current_time)
                    self.isGabbyTalking = True
                    self.gabby_voice.speak(f"The current time is {current_time}", timerTostring)
                    QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))



    def update_listening_dots(self):
        self.dot_count = (self.dot_count % 3) + 1
        dots = "." * self.dot_count
        self.ai_status_label.setText(dots)






    def adjust_volume_for_voice(self, feedback):
        print(f"Feedback received for volume adjustment: {feedback}")
        f_low = feedback.lower()

        if self.isGabbyTalking:
            return

            # --- ANIMATION LOGIC ---
        if "listening" in f_low:
            if not self.listen_timer.isActive():
              self.listen_timer.start(500)
              self.update_listening_dots()

        elif "processing" in f_low:
              self.listen_timer.stop()
              self.ai_status_label.setText("....")  # Or use your GIF here!
              self.ai_status_label.setStyleSheet("color: #00FF00;")  # Turn green so you know it heard you
              # Update every 500ms
        else:
            self.listen_timer.stop()
            self.ai_status_label.setText("")
            self.ai_status_label.setStyleSheet("color: #a855f7")






        if "assistance is ready" in f_low and self.first_run:
            self.first_run = False
            # We give it a tiny 300ms delay to make sure the audio channel is clear
            self.isGabbyTalking = True
            QTimer.singleShot(500, lambda: self.gabby_voice.speak(
                "Hello there! Let me Initialize the Map for you sit down comfortably. I'm Gabby, your car assistant. How can I help you today? ",
                "greeting"
            ))
            QTimer.singleShot(5000, lambda: setattr(self, 'isGabbyTalking', False))

        if "listening" in f_low or "processing" in f_low:
            # 0.1 is 10% volume.
            self.music_engine.audio_output.setVolume(0.05)

            print("Music Ducking: 0.05%")
        elif "error" in f_low or "assistance is ready" in f_low:
            # 1.0 is 100% volume.
            self.music_engine.audio_output.setVolume(1.0)

            print("Music Restored: 100%")




    #YOUTUBE TV PLAYER LOGIC
    def load_Youtube_Player(self):
        if self.music_engine.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.music_engine.toggle_playback()
        self.ui.QStacked.setCurrentWidget(self.ui.YoutubeLoadPage)
        youtube_url = "https://www.youtube.com/"
        self.youtubeEngine.load(QUrl(youtube_url))









if __name__ == "__main__":
    app = QApplication(sys.argv)
    from splash_Screen_gui import SPLASHSCREEN

    window = SPLASHSCREEN()
    sys.exit(app.exec())
    #app = QApplication(sys.argv)


####AI WAS USED TO IMPROVE THE EFFICEINCY and optimization OF THE CODE BUT NOT TO GENERATE AN ENTIRE CODE AS I USED QT DESIGNER AND DESIGNED EVERYTHING MYSELF

