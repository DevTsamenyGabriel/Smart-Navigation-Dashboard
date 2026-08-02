import json
import requests
import os
from math import radians, cos, sin, asin, sqrt
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv('EV_API_KEY')
COUNTRY_CODE = "GH"
DEFAULT_LAT = 5.567774
DEFAULT_LON =  -0.214651
RADIUS_KM = 80
MAX_RESULTS = 200


def get_ev_stations():
    """Fetches charging station data from the OpenChargeMap API"""
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        "output": "json",
        "compact": "true",
        "key": API_KEY,
        "countrycode": COUNTRY_CODE,
        "latitude": DEFAULT_LAT,
        "longitude": DEFAULT_LON,
        "distance": RADIUS_KM,
        "distanceunit": "KM",
        "maxresults": MAX_RESULTS,
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"API Error: {e}")
        return []


def build_map_html(stations, car_lat=DEFAULT_LAT, car_lon=DEFAULT_LON):
    processed_stations = []
    for s in stations:
        a = s.get("AddressInfo") or {}
        lat, lon = a.get("Latitude"), a.get("Longitude")
        if lat is None or lon is None: continue
        processed_stations.append({
            "lat": float(lat),
            "lon": float(lon),
            "title": a.get("Title", "Station")
        })

    stations_json = json.dumps(processed_stations)

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css" />

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>

  <style>
    html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; }}
    #map {{ height: 100vh; width: 100vw; background: white; }}

    /* Hide the text instructions panel for a clean Car OS look */
    .leaflet-routing-container {{ display: none !important; }}

    .ev-pin {{
      width: 28px; height: 28px; background: #16a34a; border: 2px solid #fff;
      border-radius: 50% 50% 50% 0; transform: rotate(-45deg);
      box-shadow: 0 2px 8px rgba(0,0,0,0.35);
    }}
    .ev-pin-icon {{
      position: absolute; inset: 0; display: flex; align-items: center;
      justify-content: center; color: #fff; font-size: 14px; transform: rotate(45deg);
    }}
    .car-pin {{
      width: 32px; height: 32px; background: #2563eb; border: 2px solid #fff;
      border-radius: 50%; box-shadow: 0 0 15px rgba(37, 99, 235, 0.6);
      display: flex; align-items: center; justify-content: center; color: white;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
   const map = L.map('map').setView([{car_lat}, {car_lon}], 14);
   L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }}).addTo(map);

    const stations = {stations_json};
    let routingControl = null;

    const evIcon = L.divIcon({{
      className: "custom-div-icon",
      html: '<div class="ev-pin"><div class="ev-pin-icon">⚡</div></div>',
      iconSize: [28, 28], iconAnchor: [14, 28]
    }});

    const carIcon = L.divIcon({{
      className: "custom-div-icon",
      html: '<div class="car-pin">🚗</div>',
      iconSize: [32, 32], iconAnchor: [16, 16]
    }});

    stations.forEach(s => {{
      L.marker([s.lat, s.lon], {{ icon: evIcon }}).addTo(map).bindPopup(s.title);
    }});

    const carMarker = L.marker([{car_lat}, {car_lon}], {{ 
        icon: carIcon, 
        draggable: true 
    }}).addTo(map);

    function getDist(lat1, lon1, lat2, lon2) {{
        const R = 6371;
        const dLat = (lat2-lat1) * Math.PI / 180;
        const dLon = (lon2-lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }}

    function updateRoute() {{
        const pos = carMarker.getLatLng();
        let closest = null;
        let minDist = Infinity;

        stations.forEach(s => {{
            const d = getDist(pos.lat, pos.lng, s.lat, s.lon);
            if (d < minDist) {{
                minDist = d;
                closest = s;
            }}
        }});

        if (routingControl) map.removeControl(routingControl);

        if (closest) {{
            routingControl = L.Routing.control({{
                waypoints: [
                    L.latLng(pos.lat, pos.lng),
                    L.latLng(closest.lat, closest.lon)
                ],
                routeWhileDragging: false,
                addWaypoints: false,
                draggableWaypoints: false,
                fitSelectedRoutes: false,
                show: false,
                lineOptions: {{
                    styles: [{{ color: '#ef4444', opacity: 0.8, weight: 6 }}]
                }},
                createMarker: function() {{ return null; }}
            }}).addTo(map);
        }}
    }}

    carMarker.on('dragend', updateRoute);
    map.on('click', function(e) {{
        carMarker.setLatLng(e.latlng);
        updateRoute();
        window.location.hash = "loc:" + e.latlng.lat + ":" + e.latlng.lng;
    }});

    updateRoute();
  </script>
</body>
</html>"""