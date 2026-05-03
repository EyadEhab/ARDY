import os
import pandas as pd

print("Checking paths...")
print(f"Current Dir: {os.getcwd()}")
print(f"Files in /app: {os.listdir('.')}")

data_dir = 'data'
if os.path.exists(data_dir):
    print(f"Files in {data_dir}: {os.listdir(data_dir)}")
else:
    print(f"Error: {data_dir} not found")

plant_dir = 'Plant Doctor/Dataset'
if os.path.exists(plant_dir):
    print(f"Files in {plant_dir}: {os.listdir(plant_dir)[:5]} (showing 5)")
else:
    print(f"Error: {plant_dir} not found")

try:
    import tensorflow as tf
    print(f"TensorFlow version: {tf.__version__}")
except Exception as e:
    print(f"TensorFlow error: {e}")

try:
    import xgboost as xgb
    print(f"XGBoost version: {xgb.__version__}")
except Exception as e:
    print(f"XGBoost error: {e}")
