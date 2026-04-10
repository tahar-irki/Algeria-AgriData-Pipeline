# ============================================================
# PART 0: IMPORTS
# ============================================================
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import folium

# ============================================================
# PART 1: DATA CLEANING (TRAINING DATASET)
# ============================================================

# Load dataset
train_df = pd.read_csv("data/crop_remmendation_dataset.csv")

train_df = train_df.rename(columns={
    'N': 'Nitrogen',
    'P': 'Phosphorus',
    'K': 'Potassium',
    'Organic_Carbon': 'Organic_C'
})


# ---------------- REMOVE UNWANTED COLUMNS ----------------
# 👉 EDIT THESE COLUMN NAMES YOURSELF
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

newOrder= ['Temperature','Humidity','Rainfall','Soil_pH','Nitrogen','Phosphorus','Potassium','Organic_C','Soil_Type','Recommended_Crop']

train_df= train_df[newOrder]

# ---------------- TYPE HANDLING ----------------


# 👉 Soil type (categorical)
soil_encoder = LabelEncoder()
train_df["Soil_Type"] = soil_encoder.fit_transform(train_df["Soil_Type"])

# ---------------- BASIC CLEANING ----------------
train_df = train_df.dropna()
train_df = train_df[(train_df != 0).all(axis=1)]

# 👉 TARGET COLUMN (EDIT NAME)
target_column = "Recommended_Crop"

X = train_df.drop(columns=[target_column])
y = train_df[target_column]

# ============================================================
# PART 2: MODEL TRAINING (RANDOM FOREST)
# ============================================================
# ============================================================

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# ---------------- METRICS ----------------
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')
cm = confusion_matrix(y_test, y_pred)

# Specificity calculation (multi-class handled approximately)
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

# ---------------- CONFUSION MATRIX PLOT ----------------
import matplotlib.pyplot as plt

plt.figure()
plt.imshow(cm)
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")

# Show values inside matrix
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(j, i, cm[i, j], ha='center', va='center')

plt.colorbar()
plt.show()

# ============================================================
# PART 3: APPLY MODEL ON ALGERIA DATASET
# ============================================================

algeria_df = pd.read_csv("data/midAlgeria_agro_data.csv")

# ---------------- CLEANING ----------------
# 👉 EDIT COLUMN NAMES
columns_to_remove_2 = [
    "coord_key",
]

algeria_df = algeria_df.drop(columns=columns_to_remove_2, errors='ignore')

# Remove unknown soil types (edit value)
algeria_df = algeria_df[algeria_df["Soil_Type"] != "unknown"]

# Remove NaN and 0
algeria_df = algeria_df.dropna()
algeria_df = algeria_df[(algeria_df != 0).all(axis=1)]
algeria_df["Soil_Type"] = soil_encoder.transform(algeria_df["Soil_Type"])
# Keep coordinates
coords = algeria_df[["Latitude", "Longitude"]].copy()

# Drop non-feature columns before prediction
features_df = algeria_df.drop(columns=["Latitude", "Longitude"], errors='ignore')

# Predict crops
predictions = model.predict(features_df)

# Save results
algeria_df["recommended_crop"] = predictions
algeria_df[["Latitude", "Longitude"]] = coords
algeria_df.to_csv("data/algeria_crop_recommendations.csv", index=False)

print("\nSaved predictions to data folder as algeria_crop_recommendations.csv")

# ============================================================
# PART 4: VISUALIZATION ON MAP
# ============================================================

# Create map centered in Algeria
map_center = [28.0, 2.6]
m = folium.Map(location=map_center, zoom_start=6)

# Function to assign color/icon per crop
# 👉 You can customize this mapping
crop_icons = {
    "Barley": "grain",
    "Cotton": "cloud",
    "Maize": "certificate",  # Closest to a corn-cob shape
    "Millet": "align-justify",
    "Potato": "record",
    "Pulses": "adjust",
    "Rice": "tint",          # Best for crops grown in water
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

# Save map
m.save("src/algeria_crop_map.html")

print("Map saved as algeria_crop_map.html")
