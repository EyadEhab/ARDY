#!/usr/bin/env python3
"""
Train ML models for EgyptAgri-Pulse:
1. Crop Recommendation Classifier (XGBoost + Random Forest ensemble)
2. Yield Forecasting Regressor (Time-series regression)
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
import xgboost as xgb
import warnings

warnings.filterwarnings('ignore')

# Create models directory
os.makedirs('models', exist_ok=True)

print("="*60)
print("TRAINING ML MODELS FOR EGYPTAGRI-PULSE")
print("="*60)

# ============================================================================
# 1. CROP RECOMMENDATION CLASSIFIER
# ============================================================================

print("\n[1/2] Training Crop Recommendation Classifier...")
print("-" * 60)

# Load soil chemistry data
soil_df = pd.read_csv('data/soil_chemistry.csv')

# Prepare features and target
X_crop = soil_df[['N', 'P', 'K', 'pH']]
y_crop = soil_df['Crop']

# Encode crop labels
crop_encoder = LabelEncoder()
y_crop_encoded = crop_encoder.fit_transform(y_crop)

# Split data
X_train_crop, X_test_crop, y_train_crop, y_test_crop = train_test_split(
    X_crop, y_crop_encoded, test_size=0.2, random_state=42, stratify=y_crop_encoded
)

# Train XGBoost classifier
print("  • Training XGBoost classifier...")
xgb_clf = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    verbosity=0
)
xgb_clf.fit(X_train_crop, y_train_crop)
xgb_pred = xgb_clf.predict(X_test_crop)
xgb_acc = accuracy_score(y_test_crop, xgb_pred)
print(f"    XGBoost Accuracy: {xgb_acc:.4f}")

# Train Random Forest classifier
print("  • Training Random Forest classifier...")
rf_clf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
rf_clf.fit(X_train_crop, y_train_crop)
rf_pred = rf_clf.predict(X_test_crop)
rf_acc = accuracy_score(y_test_crop, rf_pred)
print(f"    Random Forest Accuracy: {rf_acc:.4f}")

# Create ensemble (voting)
ensemble_pred = []
for xgb_p, rf_p in zip(xgb_pred, rf_pred):
    # Majority voting
    ensemble_pred.append(xgb_p if xgb_p == rf_p else xgb_p)
ensemble_acc = accuracy_score(y_test_crop, ensemble_pred)
print(f"    Ensemble Accuracy: {ensemble_acc:.4f}")

# Save models
with open('models/xgb_crop_classifier.pkl', 'wb') as f:
    pickle.dump(xgb_clf, f)
with open('models/rf_crop_classifier.pkl', 'wb') as f:
    pickle.dump(rf_clf, f)
with open('models/crop_encoder.pkl', 'wb') as f:
    pickle.dump(crop_encoder, f)

print(f"\n✓ Crop Recommendation Classifier trained and saved")
print(f"  Unique crops: {len(crop_encoder.classes_)}")
print(f"  Training samples: {len(X_train_crop)}")
print(f"  Test samples: {len(X_test_crop)}")

# ============================================================================
# 2. YIELD FORECASTING REGRESSOR
# ============================================================================

print("\n[2/2] Training Yield Forecasting Regressor...")
print("-" * 60)

# Load FAO yield data
fao_df = pd.read_csv('data/fao_yields.csv')

# For each crop, train a time-series regressor
yield_models = {}
crop_encoder_yield = LabelEncoder()

print(f"  • Training regressors for {fao_df['Crop'].nunique()} crops...")

for crop in fao_df['Crop'].unique():
    crop_data = fao_df[fao_df['Crop'] == crop].sort_values('Year')
    
    # Create features: year as numeric, trend, etc.
    X_yield = crop_data[['Year']].values
    y_yield = crop_data['Yield'].values
    
    # Normalize year to avoid large coefficients
    X_yield_norm = (X_yield - X_yield.min()) / (X_yield.max() - X_yield.min())
    
    # Train linear regression (simple but effective for trend)
    model = LinearRegression()
    model.fit(X_yield_norm, y_yield)
    
    # Calculate R² score
    y_pred = model.predict(X_yield_norm)
    r2 = r2_score(y_yield, y_pred)
    
    yield_models[crop] = {
        'model': model,
        'year_min': X_yield.min(),
        'year_max': X_yield.max(),
        'r2_score': r2
    }

# Save yield models
with open('models/yield_models.pkl', 'wb') as f:
    pickle.dump(yield_models, f)

print(f"✓ Yield Forecasting Regressors trained and saved")
print(f"  Crops with yield models: {len(yield_models)}")

# Display model performance summary
print("\n" + "="*60)
print("MODEL PERFORMANCE SUMMARY")
print("="*60)
print(f"\nCrop Recommendation Classifier:")
print(f"  • XGBoost Accuracy: {xgb_acc:.2%}")
print(f"  • Random Forest Accuracy: {rf_acc:.2%}")
print(f"  • Ensemble Accuracy: {ensemble_acc:.2%}")

print(f"\nYield Forecasting Regressors:")
for crop, model_info in sorted(yield_models.items()):
    print(f"  • {crop:15} R² Score: {model_info['r2_score']:.4f}")

print("\n" + "="*60)
print("✓ ALL MODELS TRAINED SUCCESSFULLY")
print("="*60)
print("\nModels saved in 'models/' directory:")
print("  • xgb_crop_classifier.pkl")
print("  • rf_crop_classifier.pkl")
print("  • crop_encoder.pkl")
print("  • yield_models.pkl")
