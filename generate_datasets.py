#!/usr/bin/env python3
"""
Generate synthetic datasets for EgyptAgri-Pulse ML models.
This script creates:
1. Soil chemistry dataset (N, P, K, pH) with crop recommendations
2. FAO yield time-series data for Egypt (1990-2024)
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Set random seed for reproducibility
np.random.seed(42)

# Create data directory
os.makedirs('data', exist_ok=True)

# ============================================================================
# 1. SOIL CHEMISTRY & CROP DATASET
# ============================================================================

# 22 Egyptian and strategic crops
CROPS = [
    'Wheat', 'Rice', 'Maize', 'Barley', 'Sorghum',
    'Cotton', 'Sugarcane', 'Alfalfa', 'Clover',
    'Tomato', 'Onion', 'Potato', 'Lettuce', 'Cucumber',
    'Citrus', 'Date Palm', 'Olive', 'Grape',
    'Bean', 'Lentil', 'Chickpea', 'Pea'
]

# Generate synthetic soil chemistry data
n_samples = 2000
soil_data = {
    'N': np.random.uniform(10, 100, n_samples),  # Nitrogen (mg/kg)
    'P': np.random.uniform(5, 50, n_samples),    # Phosphorus (mg/kg)
    'K': np.random.uniform(50, 300, n_samples),  # Potassium (mg/kg)
    'pH': np.random.uniform(5.5, 8.5, n_samples),  # pH level
}

# Create crop recommendations based on soil properties
# This is a simplified rule-based system for demonstration
def recommend_crop(n, p, k, ph):
    """Simple rule-based crop recommendation"""
    # Cereals prefer neutral to slightly alkaline pH
    if 6.5 <= ph <= 7.5 and n > 40:
        if k > 150:
            return 'Wheat'
        else:
            return 'Barley'
    
    # Rice prefers higher N and P
    if ph >= 6.0 and n > 50 and p > 20:
        return 'Rice'
    
    # Vegetables prefer slightly acidic to neutral
    if 6.0 <= ph <= 7.0:
        if n > 60:
            return 'Tomato'
        elif n > 40:
            return 'Onion'
        else:
            return 'Lettuce'
    
    # Legumes prefer neutral pH
    if 6.5 <= ph <= 7.5 and n < 40:
        return 'Bean'
    
    # Fruits prefer slightly acidic
    if 6.0 <= ph < 6.5:
        return 'Citrus'
    
    # Default fallback
    return np.random.choice(CROPS)

# Apply crop recommendation
soil_data['Crop'] = [
    recommend_crop(n, p, k, ph) 
    for n, p, k, ph in zip(soil_data['N'], soil_data['P'], soil_data['K'], soil_data['pH'])
]

# Create DataFrame
soil_df = pd.DataFrame(soil_data)

# Save to CSV
soil_df.to_csv('data/soil_chemistry.csv', index=False)
print(f"✓ Generated soil chemistry dataset: {len(soil_df)} samples")
print(f"  Crops: {soil_df['Crop'].nunique()} unique crops")
print(f"  N range: {soil_df['N'].min():.1f} - {soil_df['N'].max():.1f} mg/kg")
print(f"  P range: {soil_df['P'].min():.1f} - {soil_df['P'].max():.1f} mg/kg")
print(f"  K range: {soil_df['K'].min():.1f} - {soil_df['K'].max():.1f} mg/kg")
print(f"  pH range: {soil_df['pH'].min():.2f} - {soil_df['pH'].max():.2f}")

# ============================================================================
# 2. FAO YIELD TIME-SERIES DATA (1990-2024)
# ============================================================================

# Historical yield data for Egypt (tonnes/hectare)
# These are realistic estimates based on FAO patterns
years = np.arange(1990, 2025)
fao_data = {
    'Year': [],
    'Crop': [],
    'Yield': []  # tonnes/hectare
}

# Realistic yield trends for Egyptian crops
yield_trends = {
    'Wheat': (2.0, 2.8, 0.02),      # (base, max, growth_rate)
    'Rice': (4.5, 6.5, 0.015),
    'Maize': (3.0, 4.5, 0.025),
    'Sugarcane': (40, 55, 0.02),
    'Tomato': (25, 40, 0.03),
    'Onion': (15, 25, 0.02),
    'Citrus': (8, 12, 0.015),
    'Cotton': (1.5, 2.5, 0.02),
    'Potato': (12, 18, 0.025),
    'Bean': (1.2, 2.0, 0.02),
}

# Generate time-series data
for crop in yield_trends.keys():
    base, max_yield, growth = yield_trends[crop]
    for year in years:
        years_since_1990 = year - 1990
        # Exponential growth with some noise
        trend = base + (max_yield - base) * (1 - np.exp(-growth * years_since_1990))
        noise = np.random.normal(0, trend * 0.05)  # 5% noise
        yield_val = max(base * 0.8, trend + noise)  # Ensure minimum yield
        
        fao_data['Year'].append(year)
        fao_data['Crop'].append(crop)
        fao_data['Yield'].append(yield_val)

fao_df = pd.DataFrame(fao_data)
fao_df.to_csv('data/fao_yields.csv', index=False)
print(f"\n✓ Generated FAO yield time-series dataset: {len(fao_df)} records")
print(f"  Years: {fao_df['Year'].min()} - {fao_df['Year'].max()}")
print(f"  Crops: {fao_df['Crop'].nunique()} unique crops")
print(f"  Yield range: {fao_df['Yield'].min():.2f} - {fao_df['Yield'].max():.2f} tonnes/hectare")

# ============================================================================
# 3. EGYPTIAN GOVERNORATES REFERENCE DATA
# ============================================================================

governorates = {
    'Cairo': {'lat': 30.0444, 'lon': 31.2357},
    'Giza': {'lat': 30.0131, 'lon': 31.2089},
    'Alexandria': {'lat': 31.2001, 'lon': 29.9187},
    'Aswan': {'lat': 24.0889, 'lon': 32.8992},
    'Luxor': {'lat': 25.6872, 'lon': 32.6396},
    'Qena': {'lat': 26.1597, 'lon': 32.7262},
    'Assiut': {'lat': 27.1806, 'lon': 31.1857},
    'Sohag': {'lat': 26.5567, 'lon': 31.6948},
    'Minya': {'lat': 28.1132, 'lon': 30.7485},
    'Beni Suef': {'lat': 29.0588, 'lon': 31.1857},
    'Fayoum': {'lat': 29.3084, 'lon': 30.8428},
    'Ismailia': {'lat': 30.5938, 'lon': 32.2725},
    'Port Said': {'lat': 31.2565, 'lon': 32.2841},
    'Suez': {'lat': 29.9668, 'lon': 32.5498},
    'North Sinai': {'lat': 31.0461, 'lon': 33.3661},
    'South Sinai': {'lat': 28.2156, 'lon': 33.6314},
    'Red Sea': {'lat': 27.2539, 'lon': 33.7931},
    'Matrouh': {'lat': 31.3425, 'lon': 27.2373},
    'Beheira': {'lat': 30.7617, 'lon': 30.4243},
    'Kafr El-Sheikh': {'lat': 31.1089, 'lon': 30.9425},
    'Damietta': {'lat': 31.4158, 'lon': 31.8144},
    'Dakahlia': {'lat': 30.9753, 'lon': 31.5078},
}

gov_df = pd.DataFrame([
    {'Governorate': name, 'Latitude': data['lat'], 'Longitude': data['lon']}
    for name, data in governorates.items()
])

gov_df.to_csv('data/egyptian_governorates.csv', index=False)
print(f"\n✓ Generated Egyptian governorates reference: {len(gov_df)} governorates")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*60)
print("DATASET GENERATION COMPLETE")
print("="*60)
print(f"✓ Soil chemistry dataset: data/soil_chemistry.csv")
print(f"✓ FAO yield time-series: data/fao_yields.csv")
print(f"✓ Governorates reference: data/egyptian_governorates.csv")
print(f"\nDatasets ready for ML model training!")
