# Algeria AgriData Pipeline 🌾

An automated data collection pipeline that integrates live environmental APIs with soil property databases to assist in crop suitability analysis for Northern Algeria.

## 🚀 Overview
This project combines three distinct data sources:
1. **Open-Meteo API**: Fetches 7-day weather forecasts (Temp, Humidity).
2. **ISRIC SoilGrids API**: Extracts physical soil properties (Nitrogen, Clay, Sand, CEC) at a 15-30cm depth.
3. **Kaggle Datasets**: Integrates historical crop-soil data for model training.

## 🛠️ Features
- **Geospatial Scraper**: Iterates through a coordinate grid of Northern Algeria.
- **Soil Property Logic**: Derives soil types (Clayey, Sandy, Loamy, Red) based on physical composition.
- **Automated Integration**: Downloads and moves Kaggle datasets into the local workspace automatically.

## 📦 Installation & Usage
1. Clone the repository:
   ```bash
   git clone [https://github.com/tahar-irki/Algeria-AgriData-Pipeline.git](https://github.com/YOUR_USERNAME/Algeria-AgriData-Pipeline.git)