import pandas as pd
import numpy as np
import requests
import time

# ---------------- FETCH JSON ----------------
def fetch_json(url, timeout=20):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        else:
            print("STATUS:", r.status_code)
    except Exception as e:
        print("Request error:", e)
    return {}

# ---------------- SOIL TYPE ----------------
def derive_soil_type(clay, sand):
    if np.isnan(clay) and np.isnan(sand):
        return "Unknown"
    if clay > 40:
        return "Clayey"
    if sand > 70:
        return "Sandy"
    if 20 <= clay <= 40:
        return "Loamy"
    return "Red"

def scrape_point(lat, lon):

    # -------- WEATHER --------
    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,relative_humidity_2m_max"
        "&forecast_days=7"
        "&timezone=auto"
    )

    w = fetch_json(weather_url)
    daily = w.get("daily", {})

    temperature = np.nan
    humidity = np.nan

    if daily:
        temperature = np.nanmean(daily.get("temperature_2m_max", [np.nan]))
        humidity = np.nanmean(daily.get("relative_humidity_2m_max", [np.nan]))

    moisture = 0.2

    # -------- SOIL --------
    nitrogen = np.nan
    clay = np.nan
    sand = np.nan
    cec = np.nan

    #  Corrected API properties
    soil_url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lat={lat}&lon={lon}"
        "&property=nitrogen"
        "&property=clay"
        "&property=sand"
        "&property=cec"
        "&depth=15-30cm"
        "&value=mean"
    )

    s = fetch_json(soil_url)
    layers = s.get("properties", {}).get("layers", [])

    for layer in layers:
        try:
            val = layer["depths"][0]["values"]["mean"]
            if val is None:
                continue

            if layer["name"] == "nitrogen":
                nitrogen = val
            elif layer["name"] == "clay":
                clay = val
            elif layer["name"] == "sand":
                sand = val
            elif layer["name"] == "cec":
                cec = val
        except:
            pass

    soil_type = derive_soil_type(clay, sand)

    phosphorus = nitrogen * 0.4 if not np.isnan(nitrogen) else np.nan
    potassium = cec * 0.5 if not np.isnan(cec) else np.nan

    return {
        "Temperature": temperature,
        "Humidity": humidity,
        "Moisture": moisture,
        "Soil Type": soil_type,
        "Nitrogen": nitrogen,
        "Phosphorus": phosphorus,
        "Potassium": potassium,
        "Latitude": lat,
        "Longitude": lon
    }

# ---------------- RUN SCRAPER ----------------

# Northern Algeria 
lats = np.linspace(32.0, 37.5, 8)
lons = np.linspace(-8.7, 12.0, 8)

rows = []

print("🚀 Starting scrape...")
cnt = 1
for lat in lats:
    for lon in lons:
        print(f"{cnt}📍 {lat:.2f}, {lon:.2f}")
        rows.append(scrape_point(lat, lon))
        time.sleep(1)
        cnt += 1

df = pd.DataFrame(rows)

print("\nROWS:", len(df))
print(df.head())

df.to_csv("algeria_crop_features.csv", index=False)
print("\n✅ Saved: algeria_crop_features.csv")