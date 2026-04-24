import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import folium
import sys

#////////////////////////#
#/// 1- DATA CLEANING ///#
#////////////////////////#


def find__dir(start_path,filename):
    curr = os.path.abspath(start_path)
    while curr != os.path.dirname(curr):
        potential_data_path = os.path.join(curr, filename)
        if os.path.isdir(potential_data_path):
            return potential_data_path
        curr = os.path.dirname(curr)
    return None

# Get paths dynamically
DATA_DIR = find__dir(__file__, 'data')
SRC_DIR = find__dir(__file__, 'src')
INPUT_FILE = os.path.join(DATA_DIR, "crop_remmendation_dataset.csv")

# Load dataset you need to run crop_dataframe.py before running this code so the dataset is loaded

try:
    train_df = pd.read_csv(INPUT_FILE)

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
    'P': 'Phosphorus_est',
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

rearrange_columns= ['Temperature','Humidity','Rainfall','Soil_pH','Nitrogen','Phosphorus_est','Potassium','Organic_C','Soil_Type','Recommended_Crop']
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

from sklearn.metrics import ConfusionMatrixDisplay
crop_names = model.classes_
# Create the display object using the model's internal classes
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=crop_names)
# Set up the figure size (larger for 10 crops)
fig, ax = plt.subplots(figsize=(12, 10))
# Plot the matrix
# xticks_rotation=45 prevents the crop names from overlapping
disp.plot(ax=ax, cmap='YlGnBu', xticks_rotation=45, values_format='d')
plt.title("Random Forest: Crop Recommendation Confusion Matrix")
ax.grid(False)
plt.show()

# to show the values in the matrix



#///////////////////////////////////////////////#
#///3- applying the model on algeria dataset ///#
#///////////////////////////////////////////////#

INPUT_FILEE = os.path.join(DATA_DIR, "north_algeria_agro_data.csv")

try:
    algeria_df = pd.read_csv(INPUT_FILEE)



except FileNotFoundError:
    print("\nError: The file 'data/north_algeria_agro_data.csv' was not found.")
    print("Please run fetch_alg_dataframe.py first to fetch the dataset.")
    print("or just download the file from github.com/tahar-irki/Algeria-AgriData-Pipeline <3 \n")
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
algeria_df["Soil_Type"] = soil_encoder.inverse_transform(algeria_df["Soil_Type"])
output_path = os.path.join(DATA_DIR, "north_algeria_crop_recommendations.csv")
algeria_df.to_csv(output_path, index=False)

print("\nSaved predictions to data folder as north_algeria_crop_recommendations.csv")

#///////////////////////////////#
#/// 4- VISUALIZATION ON MAP ///#
#///////////////////////////////#


#first we need to reduce the number of point so the map does not freeze

reduced_algeria_df= algeria_df.copy()

LAT_START = 32.0
LON_START = -2.2

LAT_STEP = 0.08
LON_STEP = 0.08

BLOCK_SIZE = 3   # 3 → ~27 km 

reduced_algeria_df["i"] = ((reduced_algeria_df["Latitude"] - LAT_START) / LAT_STEP).round().astype(int)
reduced_algeria_df["j"] = ((reduced_algeria_df["Longitude"] - LON_START) / LON_STEP).round().astype(int)

reduced_algeria_df["block_i"] = reduced_algeria_df["i"] // BLOCK_SIZE
reduced_algeria_df["block_j"] = reduced_algeria_df["j"] // BLOCK_SIZE

counts = reduced_algeria_df["recommended_crop"].value_counts()

# Assign priority: rarer crop → higher value so not just one crop dominates the others

priority = {crop: rank for rank, crop in enumerate(counts.index)}
numeric_cols = [
    "Temperature", "Humidity", "Rainfall",
    "Soil_pH", "Nitrogen", "Phosphorus_est", "Potassium", "Organic_C"
]

numeric_cols = [col for col in numeric_cols if col in reduced_algeria_df.columns]
def aggregate_block(group):
    result = {}

    # ---- Average numeric values ----
    for col in numeric_cols:
        result[col] = group[col].mean()

    # ---- Priority crop selection ----
    best_idx = group["recommended_crop"].map(priority).idxmax()
    result["recommended_crop"] = group.loc[best_idx, "recommended_crop"]

    # ---- keep soil type ----
    if "Soil_Type" in group.columns:
        result["Soil_Type"] = group["Soil_Type"].mode()[0]

    return pd.Series(result)

reduced_df = (
    reduced_algeria_df.groupby(["block_i", "block_j"])
      .apply(aggregate_block)
      .reset_index()
)
reduced_df["Latitude"] = LAT_START + (
    reduced_df["block_i"] * BLOCK_SIZE + BLOCK_SIZE / 2
) * LAT_STEP

reduced_df["Longitude"] = LON_START + (
    reduced_df["block_j"] * BLOCK_SIZE + BLOCK_SIZE / 2
) * LON_STEP

reduced_df = reduced_df.drop(columns=["block_i", "block_j"])

# Reorder columns 
cols = ["Latitude", "Longitude", "recommended_crop"] + numeric_cols
other_cols = [c for c in reduced_df.columns if c not in cols]
reduced_df = reduced_df[cols + other_cols]


# SAVE CSV


output_file = os.path.join(DATA_DIR, "reduced_north_algeria_crop_recommendations.csv")


reduced_df.to_csv(output_file, index=False)


print("Original size:", len(reduced_algeria_df))
print("Reduced size:", len(reduced_df))

print("\nCrop distribution after reduction:")
print(reduced_df["recommended_crop"].value_counts())

print(f"\nSaved to: {output_file}")




# Create map centered in Algeria

map_center = [28.0, 2.6]
m = folium.Map(location=map_center, zoom_start=6)

# Function to assign color/icon per crop
# array that attach crops to icons and color

crop_styles = {
    "Barley": {"icon": "grain", "color": "orange"},
    "Cotton": {"icon": "cloud", "color": "gray"},
    "Maize": {"icon": "certificate", "color": "cadetblue"},
    "Millet": {"icon": "align-justify", "color": "lightgreen"},
    "Potato": {"icon": "record", "color": "beige"},
    "Pulses": {"icon": "adjust", "color": "purple"},
    "Rice": {"icon": "tint", "color": "lightblue"},
    "Sugarcane": {"icon": "tree-deciduous", "color": "darkgreen"},
    "Tomato": {"icon": "cutlery", "color": "red"},
    "Wheat": {"icon": "leaf", "color": "darkred"},
    "default": {"icon": "info-sign", "color": "black"}
}

for i in range(len(reduced_df)):
    crop = reduced_df.iloc[i]["recommended_crop"]
    lat = reduced_df.iloc[i]["Latitude"]
    lon = reduced_df.iloc[i]["Longitude"]

    # Get style from dict, fallback to default
    style = crop_styles.get(crop, crop_styles["default"])

    folium.Marker(
        location=[lat, lon],
        popup=f"Crop: {crop}",
        icon=folium.Icon(
            icon=style["icon"], 
            color=style["color"],
            icon_color="white" 
        )
    ).add_to(m)
# Save map in src folder you need to run it to see the result

m.save(os.path.join(SRC_DIR, "north_algeria_crop_map.html"))

print("Map saved as north_algeria_crop_map.html in src folder.")
