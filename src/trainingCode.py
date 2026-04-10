import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import folium
import sys

#////////////////////////#
#/// 1- DATA CLEANING ///#
#////////////////////////#

# Load dataset you need to run crop_dataframe.py before running this code so the dataset is loaded

try:
    train_df = pd.read_csv("data/crop_remmendation_dataset.csv")

except FileNotFoundError:
    print("\nError: The file 'data/crop_remmendation_dataset.csv' was not found.")
    print("Please run crop_dataframe.py first to load kaggle dataset.")
    print("then retry thank you for your understanding <3 \n")
    sys.exit() 

# sys.exit to stop the program 

except Exception as e:

    print(f"An unexpected error occurred: {e}")
    sys.exit()

# renaming some essential columns so they are the same with algeria dataset

train_df = train_df.rename(columns={
    'N': 'Nitrogen',
    'P': 'Phosphorus',
    'K': 'Potassium',
    'Organic_Carbon': 'Organic_C'
})


# remove unwanted columns that are not included in the model training

columns_to_remove = [
    "Soil_Moisture",
    "Electrical_Conductivity",
    "Sunlight_Hours",
    'Wind_Speed',
    'Region',
    'Altitude',
    'Season',
    'Irrigation_Type',
    'Fertilizer_Used',
    'Previous_Crop'
]

train_df = train_df.drop(columns=columns_to_remove, errors='ignore')

# rearrange the columns so they are match in both 1st dataset and 2nd dataset.

rearrange_columns= ['Temperature','Humidity','Rainfall','Soil_pH','Nitrogen','Phosphorus','Potassium','Organic_C','Soil_Type','Recommended_Crop']
train_df= train_df[rearrange_columns]

# Soil type (categorical) and unsuring they are the same code with the algerian dataset

soil_encoder = LabelEncoder()
train_df["Soil_Type"] = soil_encoder.fit_transform(train_df["Soil_Type"])

# more cleaning 

train_df = train_df.dropna()
train_df = train_df[(train_df != 0).all(axis=1)]

# TARGET COLUMN 

target_column = "Recommended_Crop"

X = train_df.drop(columns=[target_column])
y = train_df[target_column]

#////////////////////////////////////////////////////////#
#/// 2- MODEL TRAINING  using RANDOM FOREST algorithm ///#
#////////////////////////////////////////////////////////#

# Split data to training '80%' and testing parts '20%'

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train the model

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predictions

y_pred = model.predict(X_test)

# confusion matrix

accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')
cm = confusion_matrix(y_test, y_pred)

# Specificity calculation 

specificity_list = []
for i in range(len(cm)):
    tn = np.sum(cm) - (np.sum(cm[i, :]) + np.sum(cm[:, i]) - cm[i, i])
    fp = np.sum(cm[:, i]) - cm[i, i]
    specificity = tn / (tn + fp) if (tn + fp) != 0 else 0
    specificity_list.append(specificity)

specificity = np.mean(specificity_list)

print("Accuracy:", accuracy)
print("F1 Score:", f1)
print("Specificity:", specificity)
print("Confusion Matrix:", cm)

# confusion matrix  PLOT

import matplotlib.pyplot as plt

plt.figure()
plt.imshow(cm)
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")

# to show the values in the matrix

for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, cm[i, j], ha='center', va='center')

plt.colorbar()
plt.show()

#///////////////////////////////////////////////#
#///3- applying the model on algeria dataset ///#
#///////////////////////////////////////////////#


try:
    algeria_df = pd.read_csv("data/mid_algeria_agro_data.csv")

except FileNotFoundError:
    print("\nError: The file 'data/mid_algeria_agro_data.csv' was not found.")
    print("Please run fetch_alg_dataframe.py first to fetch the dataset.")
    print("or just redownload the file from github.com/tahar-irki/Algeria-AgriData-Pipeline <3 \n")
    sys.exit() 

# cleaning the dataset /remove coordinate key/
 
columns_to_remove_2 = [
    "coord_key",
]

algeria_df = algeria_df.drop(columns=columns_to_remove_2, errors='ignore')

# Remove unknown soil types in case the fetch data was missing values that can lead to unknown type of soil

algeria_df = algeria_df[algeria_df["Soil_Type"] != "unknown"]

# Remove NaN and 0

algeria_df = algeria_df.dropna()
algeria_df = algeria_df[(algeria_df != 0).all(axis=1)]
algeria_df["Soil_Type"] = soil_encoder.transform(algeria_df["Soil_Type"])

# Keep coordinates to use them in the map 

coords = algeria_df[["Latitude", "Longitude"]].copy()

# Drop non-feature columns before prediction because Longitude and latitude were not included in the training 

features_df = algeria_df.drop(columns=["Latitude", "Longitude"], errors='ignore')

# Predict crops

predictions = model.predict(features_df)

# Save results

algeria_df["recommended_crop"] = predictions

#readd the coordinates so we can know where we should put the icon in the map

algeria_df[["Latitude", "Longitude"]] = coords
algeria_df.to_csv("data/algeria_crop_recommendations.csv", index=False)

print("\nSaved predictions to data folder as algeria_crop_recommendations.csv")

#///////////////////////////////#
#/// 4- VISUALIZATION ON MAP ///#
#///////////////////////////////#

# Create map centered in Algeria

map_center = [28.0, 2.6]
m = folium.Map(location=map_center, zoom_start=6)

# Function to assign color/icon per crop
# array that attach crops to icons

crop_icons = {
    "Barley": "grain",
    "Cotton": "cloud",
    "Maize": "certificate",
    "Millet": "align-justify",
    "Potato": "record",
    "Pulses": "adjust",
    "Rice": "tint",        
    "Sugarcane": "tree-deciduous",
    "Tomato": "cutlery",
    "Wheat": "leaf",
    "default": "info-sign"
}

for i in range(len(algeria_df)):
    crop = algeria_df.iloc[i]["recommended_crop"]
    lat = algeria_df.iloc[i]["Latitude"]
    lon = algeria_df.iloc[i]["Longitude"]

    icon_name = crop_icons.get(crop, crop_icons["default"])

    folium.Marker(
        location=[lat, lon],
        popup=f"Crop: {crop}",
        icon=folium.Icon(icon=icon_name)
    ).add_to(m)

# Save map in src folder you need to run it to see the result

m.save("src/algeria_crop_map.html")

print("Map saved as algeria_crop_map.html in src folder.")
