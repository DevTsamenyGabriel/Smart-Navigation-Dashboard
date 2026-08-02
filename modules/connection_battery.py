import psutil
import pywifi
from pywifi import const
from datetime import datetime

class SystemMonitorLogic:
    def __init__(self):
        self.wifi = pywifi.PyWiFi()
        try:
            self.iface = self.wifi.interfaces()[0]
        except:
            self.iface = None

    def get_wifi_info(self):
        if not self.iface: return "No Adapter"
        status = self.iface.status()
        if status == const.IFACE_CONNECTED: return "Connected"
        if status == const.IFACE_CONNECTING: return "Connecting..."
        return "Disconnected"

    def get_battery_info(self):
        battery = psutil.sensors_battery()
        if battery:
            status = "Charging" if battery.power_plugged else "Discharging"
            return f"{battery.percent}% ({status})"
        return "AC Power"