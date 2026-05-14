"""
Retrain ML models using real user datasets
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier
from sklearn.linear_model import LinearRegression
import warnings

warnings.filterwarnings('ignore')

print("=" * 70)
print("RETRAINING ML MODELS WITH REAL DATASETS")
print("=" * 70)

# ============================================================================
# PHASE 1: CROP RECOMMENDATION MODEL
# ============================================================================
print("\n[PHASE 1] Training Crop Recommendation Models...")

# Load crop recommendation dataset
crop_data = pd.read_csv('data/Crop_recommendation.csv')
print(f"✓ Loaded crop recommendation dataset: {crop_data.shape}")

# Prepare features and labels
X_crop = crop_data[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y_crop = crop_data['label']

print(f"  Features: {list(X_crop.columns)}")
print(f"  Target crops: {y_crop.nunique()} unique crops")
print(f"  Crop distribution:\n{y_crop.value_counts()}")

# Encode labels
crop_encoder = LabelEncoder()
y_crop_encoded = crop_encoder.fit_transform(y_crop)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_crop, y_crop_encoded, test_size=0.2, random_state=42, stratify=y_crop_encoded
)

print(f"\n  Training set: {X_train.shape[0]} samples")
print(f"  Test set: {X_test.shape[0]} samples")

# Train XGBoost
print("\n  Training XGBoost classifier...")
xgb_model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    verbosity=0
)
xgb_model.fit(X_train, y_train)
xgb_score = xgb_model.score(X_test, y_test)
print(f"  ✓ XGBoost Accuracy: {xgb_score:.4f}")

# Train Random Forest
print("  Training Random Forest classifier...")
rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
rf_score = rf_model.score(X_test, y_test)
print(f"  ✓ Random Forest Accuracy: {rf_score:.4f}")

# Save crop models
with open('models/xgb_crop_classifier.pkl', 'wb') as f:
    pickle.dump(xgb_model, f)
print("  ✓ Saved XGBoost model")

with open('models/rf_crop_classifier.pkl', 'wb') as f:
    pickle.dump(rf_model, f)
print("  ✓ Saved Random Forest model")

with open('models/crop_encoder.pkl', 'wb') as f:
    pickle.dump(crop_encoder, f)
print("  ✓ Saved crop label encoder")

# Store feature names for later use
with open('models/crop_features.pkl', 'wb') as f:
    pickle.dump(X_crop.columns.tolist(), f)
print("  ✓ Saved feature names")

# ============================================================================
# PHASE 2: YIELD FORECASTING MODELS
# ============================================================================
print("\n[PHASE 2] Training Yield Forecasting Models...")

# Load yield dataset
yield_data = pd.read_csv('data/Egypt_Crop_Yield_Processed_Pivot.csv')
print(f"✓ Loaded yield dataset: {yield_data.shape}")

# Clean and prepare yield data
yield_data = yield_data.dropna(subset=['Yield', 'Year'])
yield_data = yield_data[yield_data['Yield'] > 0]

print(f"  Crops in dataset: {yield_data['Item'].nunique()}")
print(f"  Year range: {yield_data['Year'].min()} - {yield_data['Year'].max()}")

# Train individual models for each crop
yield_models = {}
crop_yield_stats = {}

crops_to_train = yield_data['Item'].unique()[:15]  # Train for top crops
print(f"\n  Training models for {len(crops_to_train)} crops...")

for crop in crops_to_train:
    crop_yield = yield_data[yield_data['Item'] == crop].sort_values('Year')
    
    if len(crop_yield) < 5:
        continue
    
    X_yield = crop_yield[['Year']].values
    y_yield = crop_yield['Yield'].values
    
    # Normalize year to avoid large coefficients
    year_min = X_yield.min()
    year_max = X_yield.max()
    X_yield_norm = (X_yield - year_min) / (year_max - year_min)
    
    # Train Linear Regression
    lr_model = LinearRegression()
    lr_model.fit(X_yield_norm, y_yield)
    lr_r2 = lr_model.score(X_yield_norm, y_yield)
    
    # Train Random Forest Regressor
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_yield_norm, y_yield)
    rf_r2 = rf_model.score(X_yield_norm, y_yield)
    
    # Pick best model
    if rf_r2 > lr_r2:
        best_model = rf_model
        best_r2 = rf_r2
        best_name = 'RandomForestRegressor'
        other_name = 'LinearRegression'
        other_r2 = lr_r2
    else:
        best_model = lr_model
        best_r2 = lr_r2
        best_name = 'LinearRegression'
        other_name = 'RandomForestRegressor'
        other_r2 = rf_r2
    
    # Store model and stats
    yield_models[crop] = {
        'model': best_model,
        'r2_score': best_r2,
        'lr_model': lr_model,
        'lr_r2': lr_r2,
        'rf_model': rf_model,
        'rf_r2': rf_r2,
        'best_model': best_name,
        'min_year': int(year_min),
        'max_year': int(year_max),
        'avg_yield': float(y_yield.mean()),
        'latest_yield': float(y_yield[-1])
    }
    
    # Predict 2026 yield using best model (in kg/ha)
    year_2026_norm = (2026 - year_min) / (year_max - year_min)
    pred_2026 = best_model.predict([[year_2026_norm]])[0]
    
    print(f"  ✓ {crop}")
    print(f"    LinearRegression R²:            {lr_r2:.4f}")
    print(f"    RandomForestRegressor R²:        {rf_r2:.4f}")
    print(f"    → Using {best_name} (R²={best_r2:.4f}) because its accuracy is better than {other_name} (R²={other_r2:.4f})")
    print(f"    → 2026 Predicted Yield: {pred_2026:.2f} kg/ha")

# Save yield models
with open('models/yield_models.pkl', 'wb') as f:
    pickle.dump(yield_models, f)
print("\n  ✓ Saved all yield models")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print("MODEL TRAINING COMPLETE")
print("=" * 70)
print(f"\n✓ Crop Recommendation Models:")
print(f"  - XGBoost Accuracy: {xgb_score:.4f}")
print(f"  - Random Forest Accuracy: {rf_score:.4f}")
print(f"  - Crops: {len(crop_encoder.classes_)}")
print(f"\n✓ Yield Forecasting Models:")
print(f"  - Models trained: {len(yield_models)}")
print(f"  - Average R² Score: {np.mean([m['r2_score'] for m in yield_models.values()]):.4f}")
print(f"\n✓ All models saved to models/ directory")
print("=" * 70)
