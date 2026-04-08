# Algeria AgriData Pipeline 🌾
 ## go directly to Every Code job chapter professor hayi please, to make you understand the logic and the thinkning behind every line ##
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
   git clone https://github.com/tahar-irki/Algeria-AgriData-Pipeline.git

## 💡 Every Code Job
1. fetch_alg_dataframe :
   this code is fetching the data from two APIs "soil grid" & "open-meteo", conf: we gave the lat and lon of north algeria basically from the south of tlemcen to tebessa and from the shores of annaba to south cost of spain (rectangle) "soil API was temperarly down for two months so we reduced the space of research, and we were shorten in time, thank you for your understanding Sir", max_workers is the number of worker that code splits the fetch's work on, TIMEOUT is the time the code wait for the API to respond, retries is the number of times the code retries to request the same point from the API.
   🧱 functions 
      fetch_json to fetch the data and with in the function we put some print to humenize the errors.
      derive_soil_type is function that determine why type of soil we have in lat, lon point.
      scrape_point is function that fetch with lat, lon point with time sleep of 4 seconds between eatch api requast 'even between soil and meteo APIs', there is some calculation the purpose of them is to convert the APi units to the units we are working with them in the first dataset, and the program saves every 50 points and if it rerun again it'll start where it stopped.
      this dataset is used to predict or recommend the best suitable crop for algeria's soil, after training the model with dataset from kaggle that can be fetch from their website using the file crop_dataframe.
2. crop_dataframe :
   this code is dedicated to fetch the dataset of the crop that we'll train the model with, it's directly dowmload the dataset to data folder using some os libreries.



