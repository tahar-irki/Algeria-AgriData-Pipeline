import asyncio
import aiohttp
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

#/////////////////////
#/// CONFIGURATION ///
#///////////////////// 

#the original coordinates, reduced because of the time and rate limit of the APIs
# STEP_SIZE = 0.08
# LAT_START, LAT_END = 34.5, 37.2
# LON_START, LON_END = -1.5, 8.5

STEP_SIZE  = 0.06
LAT_START, LAT_END = 35.1, 37.0
LON_START, LON_END = 1.8, 4.1
BATCH_SIZE = 30

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "mid_algeria_agro_data.csv")
os.makedirs(DATA_DIR, exist_ok=True)

WEATHER_SEM = asyncio.Semaphore(2)
SOIL_LOCK   = asyncio.Lock()
SOIL_DELAY  = 2

RETRIES = 5

#//////////////////
#/// CORE FETCH ///
#//////////////////

async def fetch(session: aiohttp.ClientSession, url: str,
                sem, lat: float, lon: float) -> dict:
    async with sem:
        for attempt in range(RETRIES):
            try:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as r:
                    if r.status == 200:
                        return await r.json(content_type=None)
                    elif r.status == 429:
                        wait = 2 ** attempt + 5
                        print(f"⏳  429 at ({lat:.2f},{lon:.2f}) "
                              f"→ sleeping {wait}s [attempt {attempt+1}/{RETRIES}]")
                        await asyncio.sleep(wait)
                    else:
                        print(f"⚠️  HTTP {r.status} at ({lat:.2f},{lon:.2f})")
                        await asyncio.sleep(2)
            except asyncio.TimeoutError:
                wait = 2 ** attempt
                print(f"⏱  Timeout at ({lat:.2f},{lon:.2f}) → retry in {wait}s")
                await asyncio.sleep(wait)
            except Exception as e:
                wait = 2 ** attempt
                print(f"❌  {type(e).__name__}: {e} at ({lat:.2f},{lon:.2f}) "
                      f"→ retry in {wait}s")
                await asyncio.sleep(wait)
    print(f"🚫  Giving up on ({lat:.2f},{lon:.2f}) after {RETRIES} attempts")
    return {}

#/////////////////////
#/// WEATHER AGENT ///
#/////////////////////

async def weather_agent(session, lat: float, lon: float) -> dict | None:
    await asyncio.sleep(0.5)
    end   = datetime.now().date() - timedelta(days=5)
    start = end - timedelta(days=365)

    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_mean,relative_humidity_2m_mean,"
        "precipitation_sum&timezone=auto"
    )

    data = (await fetch(session, url, WEATHER_SEM, lat, lon)).get("daily", {})

    temps    = np.array(data.get("temperature_2m_mean")       or [], dtype=float)
    humidity = np.array(data.get("relative_humidity_2m_mean") or [], dtype=float)
    rain     = np.array(data.get("precipitation_sum")         or [], dtype=float)

    if len(temps) == 0:
        print(f"⚠️  No weather data at ({lat:.2f},{lon:.2f})")
        return None

    return {
        "Temperature": round(float(np.nanmean(temps)),    2),
        "Humidity":    round(float(np.nanmean(humidity)), 2),
        "Rainfall":    round(float(np.nansum(rain)),      2),
    }

#//////////////////#
#/// SOIL AGENT ///#
#//////////////////#

def _derive_soil_type(clay, sand, silt) -> str:
    if None in (clay, sand, silt):
        return "Unknown"
    if sand >= 500:
        return "Sandy"
    if silt >= 500:
        return "Silt"
    if clay >= 300:
        return "Clay"
    return "Loamy"

async def soil_agent(session, lat: float, lon: float) -> dict | None:
    async with SOIL_LOCK:
        await asyncio.sleep(SOIL_DELAY)

        url = (
            f"https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lon={lon}&lat={lat}&number_1km=1"
            "&property=nitrogen&property=clay&property=sand"
            "&property=phh2o&property=soc&property=cec&property=silt"
            "&depth=15-30cm&value=mean"
        )

        resp = await fetch(session, url, asyncio.Semaphore(1), lat, lon)

    layers = resp.get("properties", {}).get("layers", [])

    sv: dict = {}
    for layer in layers:
        try:
            sv[layer["name"]] = layer["depths"][0]["values"]["mean"]
        except (KeyError, IndexError, TypeError):
            continue

    if not sv:
        print(f"⚠️  No soil data at ({lat:.2f},{lon:.2f})")
        return None

    def g(k):
        return sv.get(k) or 0

    clay, sand, silt = sv.get("clay"), sv.get("sand"), sv.get("silt")

    return {
        "Soil_pH":        round(g("phh2o")    / 10, 2),
        "Nitrogen":       round(g("nitrogen") / 10, 2),
        "Phosphorus_est": round((g("nitrogen") / 10) * 0.5, 2),
        "Potassium":      round((g("cec")      / 10) * 0.8, 2),
        "Organic_C":      round(g("soc")       / 10, 2),
        "Soil_Type":      _derive_soil_type(clay, sand, silt),
    }

#//////////////////////////#
#/// POINT ORCHESTRATOR ///#
#//////////////////////////#

async def process_point(session, lat: float, lon: float) -> dict | None:
    weather, soil = await asyncio.gather(
        weather_agent(session, lat, lon),
        soil_agent(session, lat, lon),
    )

    if weather is None or soil is None:
        return None

    return {
        "coord_key": f"{lat:.4f}_{lon:.4f}",
        "Latitude":  round(lat, 4),
        "Longitude": round(lon, 4),
        **weather,
        **soil,
    }

#////////////#
#/// MAIN ///#
#////////////#

async def main():
    finished: set[str] = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            finished = set(pd.read_csv(OUTPUT_FILE)["coord_key"].astype(str))
            print(f"🔄  Resuming — {len(finished)} points already done")
        except Exception as e:
            print(f"⚠️  Could not read existing CSV ({e}), starting fresh")
    else:
        print("🆕  Starting new dataset")

    lat_range = np.arange(LAT_START, LAT_END, STEP_SIZE)
    lon_range = np.arange(LON_START, LON_END, STEP_SIZE)
    points = [
        (round(float(lat), 4), round(float(lon), 4))
        for lat in lat_range
        for lon in lon_range
        if f"{lat:.4f}_{lon:.4f}" not in finished
    ]
    total = len(points)
    print(f"📍  Points remaining: {total}")
    print(f"⏱   Estimated time: ~{round(total * SOIL_DELAY / 60)} minutes minimum\n")

    if total == 0:
        print("✅  Nothing to do.")
        return

    saved = 0
    connector = aiohttp.TCPConnector(limit=12, ttl_dns_cache=300)

    async with aiohttp.ClientSession(connector=connector) as session:
        for batch_start in range(0, total, BATCH_SIZE):
            batch = points[batch_start : batch_start + BATCH_SIZE]
            tasks = [process_point(session, lat, lon) for lat, lon in batch]
            results = await asyncio.gather(*tasks)

            rows = [r for r in results if r is not None]
            if rows:
                df = pd.DataFrame(rows)
                write_header = not os.path.exists(OUTPUT_FILE)
                df.to_csv(OUTPUT_FILE, mode="a", header=write_header, index=False)
                saved += len(rows)

            batch_num     = batch_start // BATCH_SIZE + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            pct           = round(saved / total * 100, 1)
            print(
                f"⚙️   Batch {batch_num}/{total_batches} | "
                f"this batch: {len(rows)}/{len(batch)} saved | "
                f"total: {saved}/{total} ({pct}%)"
            )

    print(f"\n✅  Finished. Total rows saved: {saved}")
    print(f"📁  Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())