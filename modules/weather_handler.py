import requests
from PyQt6.QtCore import QThread, pyqtSignal
#loading API key from .env file
from dotenv import load_dotenv
import os



class WeatherWorker(QThread):
    # This signal carries the full dictionary back to Main.py
    weather_data_ready = pyqtSignal(dict)

    def __init__(self, api_key, lat="5.5593", lon="-0.1974"):
        super().__init__()
        self.api_key = api_key
        self.lat = lat
        self.lon = lon
        #load_dotenv()

        #getting API key from .env file
        #self.api_key = os.getenv('WEATHER_API_KEY')


    def run(self):
        # OneCall 3.0 URL
        baseUrl = f"https://api.openweathermap.org/data/3.0/onecall?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric"

        try:
            print("Weather Engine: Fetching data for Accra...")
            response = requests.get(baseUrl, timeout=15)
            response.raise_for_status()
            data = response.json()
            self.weather_data_ready.emit(data)
        except Exception as error:
            print(f"Weather Engine Error: {error}")
            self.weather_data_ready.emit({"error": str(error)})