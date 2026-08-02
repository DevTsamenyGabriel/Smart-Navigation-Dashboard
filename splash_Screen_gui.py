import os
import socket
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QProgressBar, QLabel, QGridLayout, QFrame, \
    QGraphicsDropShadowEffect

from splash_screen import Ui_MainWindow
from Main import MainWindow  # Import your main app class


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path).replace("\\", "/")









counter = 0


def update_progress_bar():
    global counter


def is_connected_to_net():
    try:
        # Connect to Google's DNS to check if the internet is alive
        # 8.8.8.8 on port 53 is the fastest check possible
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False


class SPLASHSCREEN(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Smart Navigation")
        self.setWindowTitle("Smart Navigation")
        self.setWindowIcon(QIcon(resource_path("Assets/icons/smart_nav.ico")))

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint) # Remove title bar
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Make background transparent
        # --- THE FIX: Unhardcode the Splash Background ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Assuming teslastyleimage.jpeg is in Assets/images
        #splash_img = os.path.join(base_dir, "Assets", "images", "teslastyleimage.jpeg").replace("\\", "/")
        splash_img = resource_path("Assets/images/teslastyleimage.jpeg")
        self.ui.Splashframe.setStyleSheet(f"""
                    #Splashframe {{
                        border-image: url("{splash_img}");
                    }}
                """)
        # -


        #Drop shadow Effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.ui.Splashframe.setGraphicsEffect(self.shadow)

        #QT TIMER setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress_bar)
        self.timer.start(100)

        #has internet Access
        self.hasInternet = False
          # Create an instance of your main app



        self.show()

    def update_progress_bar(self):
        global counter
        self.ui.progressBar.setValue(counter)
        if counter >= 100:
            if self.hasInternet:
             self.timer.stop()
             self.close()
             print("Network Stable. Launching Gabby OS...")
              # 1. Create the Main App
             self.launch_main_window = MainWindow()
             self.launch_main_window.showFullScreen()  # 2. Show it

             self.close()
             # Close the splash screen
             # Here you can launch your main application window
            else:
                print("Network Error")
                self.ui.loaderLabel.setText("Offline: Please connect to the Internet.")
                self.timer.stop()



        elif counter == 30:
            self.ui.loaderLabel.setText("Checking Internet Connection...")




        elif counter == 50:

            response = is_connected_to_net()
            if response:
                self.hasInternet = True
                print("is connected to network...")
                self.ui.loaderLabel.setText("Network is Stable")


            else:
                self.hasInternet = False
                self.timer.stop()
                self.ui.loaderLabel.setText("Offline: Please connect to the Internet.")



        elif counter == 70 and self.hasInternet:
            self.ui.loaderLabel.setText("Loading...")


        counter += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SPLASHSCREEN()
    sys.exit(app.exec())