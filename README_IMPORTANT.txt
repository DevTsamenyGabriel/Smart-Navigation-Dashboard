#VERY IMPORTANT    - Go to the 'dist/SmartNav' folder
PREREQUISITES (Run these commands in your Terminal/CMD):
-------------------------------------------------------
The app requires Python 3.10+ and the following libraries:

1. GUI & Web Engine: 
   pip install PyQt6 PyQt6-WebEngine PyQt6-Multimedia

2. AI & Voice:
   pip install speechrecognition pyaudio

3. System & Data:
   pip install python-dotenv requests psutil

4. Math & Physics (For distance calculations):
   (Included in standard Python library: math, json, os)

NOTE: If 'pyaudio' fails to install, Windows users should use:
pip install pipwin
pipwin install pyaudio







HOW TO RUN THE SMARTNAV APP
===========================

1. INSTALLATION: 
   Ensure you have all the modules listed in the "PREREQUISITES" section 
   above installed if you are running from source.

2. THE .ENV SECRET:
  If it shows "System Offline" as they cannot access the cloud APIs kindly check my .env file and make sure to run the application in the current folder.

3. LAUNCHING:
   - Go to the 'dist/SmartNav' folder.
   - Right-click 'SmartNav.exe' and select "Pin to Taskbar" for quick access.
   - Double-click to launch.

4. USER INTERFACE TIPS:
   - FULLSCREEN: The app is designed as a Car OS. It launches in 
     fullscreen to mimic a Tesla/Smart dashboard. 
   - EXITING: There is no 'X' button by design. To exit, press the 
     'Windows Key' on your keyboard, right-click the app icon on the 
     Taskbar, and select "Close Window".

5. TROUBLESHOOTING:
   - SYSTEM OFFLINE: Check your internet connection. 
   - GABBY NOT LISTENING: Ensure your microphone is plugged in and 
     set as the 'Default Communication Device' in Windows Sound Settings.
   - MAP NOT LOADING: If the map is white, ensure you are not behind 
     a school/corporate firewall that blocks Mapbox or OpenStreetMap.

6. HARDWARE SAFETY:
   - This app uses GPU acceleration for the 3D maps. If your computer 
     fans start spinning fast, this is normal—it's the 'Chromium Engine' 
     providing high-definition visuals.