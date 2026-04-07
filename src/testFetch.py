import ee
import pandas as pd
import numpy as np
import time

# ==========================================================
# 1. INITIALIZATION 
# Replace 'your-actual-project-id' with the ID you just registered
PROJECT_ID = 'GEE-CODE-NEEDED' 

try:
    ee.Initialize(project=PROJECT_ID)
    print(f"✅ Success! Connected to Project: {PROJECT_ID}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("If you just registered, wait 2-3 minutes for Google to sync.")
    exit()

# ==========================================================
# 2. THE SCRAPER
# ==========================================================
def get_soil_data(lat, lon):
    try:
        point = ee.Geometry.Point([lon, lat])
        
        # Loading images
        clay_img = ee.Image("projects/soilgrids-isric/clay_mean").select('clay_15-30cm_mean')
        sand_img = ee.Image("projects/soilgrids-isric/sand_mean").select('sand_15-30cm_mean')
        nitro_img = ee.Image("projects/soilgrids-isric/nitrogen_mean").select('nitrogen_15-30cm_mean')
        cec_img = ee.Image("projects/soilgrids-isric/cec_mean").select('cec_15-30cm_mean')

        combined = ee.Image([clay_img, sand_img, nitro_img, cec_img])
        sample = combined.sample(point, 250).first().getInfo()
        
        if not sample or 'properties' not in sample:
            return None

        p = sample['properties']
        
        # --- CONVERSION SCALE FACTORS ---
        # SoilGrids v2 units: 
        # Clay/Sand: g/kg. Divide by 10 to get %
        # Nitrogen: cg/kg. Divide by 100 to get g/kg
        # CEC: mmol(c)/kg. Divide by 10 to get cmol(c)/kg
        clay = p.get('clay_15-30cm_mean', 0) / 10.0
        sand = p.get('sand_15-30cm_mean', 0) / 10.0
        nitro = p.get('nitrogen_15-30cm_mean', 0) / 100.0
        cec = p.get('cec_15-30cm_mean', 0) / 10.0

        return {
            "Latitude": lat, "Longitude": lon,
            "Clay_pct": clay, "Sand_pct": sand,
            "Nitrogen_gkg": nitro, "Cec_cmolkg": cec,
            "Phosphorus_est": nitro * 0.4, # Rough estimate
            "Potassium_est": cec * 0.5     # Rough estimate
        }
    except:
        return None

# ==========================================================
# 3. RUN THE GRID
# ==========================================================
lats = np.linspace(32.0, 37.5, 8)
lons = np.linspace(-8.7, 12.0, 8)
rows = []

print("🛰️  Fetching data from Google Earth Engine...")
for lat in lats:
    for lon in lons:
        data = get_soil_data(lat, lon)
        if data:
            rows.append(data)
            print(f"📍 Saved: {lat:.2f}, {lon:.2f}")
        time.sleep(0.05) # Very fast

df = pd.DataFrame(rows)
df.to_csv("final_soil_results.csv", index=False)
print("\n🔥 All done! Check 'final_soil_results.csv'")