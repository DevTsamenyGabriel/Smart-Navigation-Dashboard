import hashlib
import requests
from PyQt6.QtCore import QThread, pyqtSignal



class RoadRiskWorker(QThread):
    # This signal sends the (warning_text, cache_name) back to Main.py
    risk_data_ready = pyqtSignal(str, str, bool)

    def __init__(self, api_key, dest_name, lat, lon, clear_state, traffic_status, user_in_traffic):
        super().__init__()
        self.api_key = api_key
        self.dest_name = dest_name
        self.lat = lat
        self.lon = lon
        self.is_clear = clear_state
        self.traffic_status = traffic_status
        self.intraffic_mode = user_in_traffic



    def run(self):
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.lat}&lon={self.lon}&appid={self.api_key}&units=metric"

        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            weather_main = data.get("weather", [{}])[0].get("main", "")



            # Logic: Determine the message based on rain
            message = ""

            if not self.intraffic_mode:

                if "Rain" in weather_main or "Thunderstorm" in weather_main:
                    message = f"Heads up Bro! I've detected rainfall at {self.dest_name}. Please drive carefully as you approach your destination."
                else:
                    if self.is_clear:
                       message = f"The road to {self.dest_name} is safe. I will be updating you of any road risks. Safe drive!"
                       self.is_clear = False

                    else:
                        message = f"The road to {self.dest_name} is Clear. Enjoy Your ride!"
                        self.is_clear = True


            if self.intraffic_mode:
                if self.traffic_status.lower() == "high":
                    message = f"Heads up Bro! I've detected heavy traffic on the route to {self.dest_name}, you might delay for a while."

                elif self.traffic_status.lower() == "moderate":
                    message = f"Just a heads up, {self.dest_name} has a bit of traffic right now. Nothing too crazy, but we might slow down a little."




            final_message = f"{message}"

            # Create the unique Hash for this specific message
            unique_id = hashlib.md5(final_message.encode()).hexdigest()[:10]
            cache_name = f"safety_{unique_id}"

            # Send the result back to the Main Window
            self.risk_data_ready.emit(final_message, cache_name, self.is_clear)

        except Exception as e:
            print(f"Road Risk Worker Error: {e}")