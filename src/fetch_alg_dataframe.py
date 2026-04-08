import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ---------------- CONFIGURATION ----------------
STEP_SIZE = 0.08
LAT_START, LAT_END = 34.5, 37.2
LON_START, LON_END = -1.5, 8.5
MAX_WORKERS = 1
TIMEOUT = 20
RETRIES = 3

# Resolve project root (agro_alg/) from src/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "algeria_agro_data.csv")
os.makedirs(DATA_DIR, exist_ok=True)

write_lock = Lock()  # prevent race conditions when writing

# ---------------- API HELPER ----------------
def fetch_json(url ,lat ,lon):
    for i in range(RETRIES):
        current_time = datetime.now().strftime('%H:%M:%S')
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 429:
                wait = 5 * (i + 1)
                print(f"🕒 [{current_time}] ⚠️ 429 rate limit → sleep {wait}s at {lat} ,{lon}")
                time.sleep(wait)
            else:
                print(f"🕒 [{current_time}] ⚠️ HTTP {r.status_code} at {lat} ,{lon}")
        except Exception as e:
            print(f"🕒 [{current_time}] ❌ Connection Error: {e} at {lat} ,{lon}")
    return {}

# ---------------- SOIL TYPE ----------------
def derive_soil_type(clay, sand,silt):
    if clay is None or sand is None or silt is None:
        return "unknown"
    if sand >= 450:
        return "Sandy"
    if silt >= 450:
        return "Silt"
    if clay >= 300:
        return "Clay"
    
    return "Loamy"

# ---------------- CORE FUNCTION ----------------
def scrape_point(lat, lon):
    coord_key = f"{lat:.4f}_{lon:.4f}"

    end_date = datetime.now().date() - timedelta(days=5)
    start_date = end_date - timedelta(days=365)

    # WEATHER
    w_url = (
        f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
        f"&start_date={start_date}&end_date={end_date}"
        "&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum&timezone=auto"
    )

    w_resp = fetch_json(w_url, lat, lon)
    w_data = w_resp.get("daily", {})

    temps = np.array(w_data.get("temperature_2m_mean", []))
    humidity = np.array(w_data.get("relative_humidity_2m_mean", []))
    rain = np.array(w_data.get("precipitation_sum", []))

    if len(temps) == 0:
        print(f"⚠️ No weather data @ {lat:.2f},{lon:.2f}")
        return None

    temp_mean = np.nanmean(temps)
    humidity_mean = np.nanmean(humidity)
    rain_total = np.nansum(rain)
    time.sleep(4)
    # SOIL
    s_url = (
        f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}"
        "&property=nitrogen&property=clay&property=sand&property=phh2o&property=soc&property=cec&property=silt"
        "&depth=15-30cm&value=mean"
    )

    s_resp = fetch_json(s_url, lat, lon)
    layers = s_resp.get("properties", {}).get("layers", [])

    s_v = {}
    for l in layers:
        try:
            s_v[l["name"]] = l["depths"][0]["values"]["mean"]
        except:
            continue

    if not s_v:
        print(f"⚠️ No soil data @ {lat:.2f},{lon:.2f}")
        return None

    # SCALING (approximate)
# Using 'or 0' AFTER the get() ensures that if the result is None, it becomes 0
    nitrogen = (s_v.get("nitrogen") or 0) / 10
    phosphorus = nitrogen * 0.5
    potassium = ((s_v.get("cec") or 0) / 10) * 0.8

    ph = (s_v.get("phh2o") or 0) / 10
    organic_c = (s_v.get("soc") or 0) / 10

    soil_type = derive_soil_type(s_v.get("clay"), s_v.get("sand"), s_v.get("silt"))
    time.sleep(4)
    return {
        "coord_key": coord_key,
        "Latitude": round(lat, 4),
        "Longitude": round(lon, 4),
        "Temperature": round(temp_mean, 2),
        "Humidity": round(humidity_mean, 2),
        "Rainfall": round(rain_total, 2),
        "Soil_pH": round(ph, 2),
        "Nitrogen": round(nitrogen, 2),
        "Phosphorus": round(phosphorus, 2),
        "Potassium": round(potassium, 2),
        "Organic_C": round(organic_c, 2),
        "Soil_Type": soil_type
    }

# ---------------- LOAD EXISTING ----------------
if os.path.exists(OUTPUT_FILE):
    existing_df = pd.read_csv(OUTPUT_FILE)
    finished_coords = set(existing_df['coord_key'])
    print(f"🔄 Resuming: {len(finished_coords)} points loaded")
else:
    finished_coords = set()
    print("🆕 Starting new dataset")

# ---------------- GRID ----------------
lat_range = np.arange(LAT_START, LAT_END, STEP_SIZE)
lon_range = np.arange(LON_START, LON_END, STEP_SIZE)
points = [(lat, lon) for lat in lat_range for lon in lon_range]

points_to_process = [
    (lat, lon) for lat, lon in points
    if f"{lat:.4f}_{lon:.4f}" not in finished_coords
]

print(f"📍 Remaining points: {len(points_to_process)}")

# ---------------- SAVE ----------------
def save_row(row):
    with write_lock:
        df = pd.DataFrame([row])
        df.to_csv(OUTPUT_FILE, mode='a', header=not os.path.exists(OUTPUT_FILE), index=False)

# ---------------- EXECUTION ----------------
count_saved = 0
count_processed = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(scrape_point, lat, lon): (lat, lon) for lat, lon in points_to_process}

    for future in as_completed(futures):
        count_processed += 1
        try:
            result = future.result()
        except Exception as e:
            print(f"❌ Worker error: {e}")
            continue

        if result:
            save_row(result)
            count_saved += 1

        if count_processed % 50 == 0:
            print(f"⚙️ Processed: {count_processed} | Saved: {count_saved}")

print(f"✅ Done. Total saved: {count_saved}")