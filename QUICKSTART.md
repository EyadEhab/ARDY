# EgyptAgri-Pulse: Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Step 1: Navigate to Project Directory
```bash
cd egypt-agri-pulse
```

### Step 2: Create Virtual Environment (First Time Only)
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

### Step 4: Generate Datasets and Train Models (First Time Only)
```bash
python generate_datasets.py
python train_models.py
```

### Step 5: Run the Application

**Option A: Automatic (Recommended)**
```bash
./run.sh
```

**Option B: Manual (Two Terminals)**

Terminal 1 - Start Backend:
```bash
source venv/bin/activate
python backend.py
```

Terminal 2 - Start Frontend:
```bash
source venv/bin/activate
streamlit run app.py
```

### Step 6: Access the Application

- **Dashboard**: http://localhost:8501
- **API Health**: http://localhost:5000/api/health

---

## 📊 Dashboard Features

### 🏠 Dashboard
- System overview and architecture
- Key metrics and feature descriptions

### 🌡️ Weather & Environment
- Live weather data for Egyptian governorates
- Interactive map with weather station location
- Weather interpretation and recommendations

### 🌱 Crop Recommendation
- Input soil properties (N, P, K, pH)
- AI-powered crop recommendation with confidence
- Top 5 alternative crops
- Feature importance analysis

### 📈 Yield Forecasting
- Select crop and forecast year
- Predict yield for 2026
- Historical trends visualization
- Yield statistics

### 📋 Report Generator
- Generate comprehensive PDF reports
- Includes soil analysis, weather, recommendations, forecasts
- One-click download

---

## 🧪 Testing the API

Run the test suite:
```bash
python test_api.py
```

This will test all endpoints and generate a sample PDF report.

---

## 📁 Project Structure

```
egypt-agri-pulse/
├── app.py                      # Streamlit dashboard
├── backend.py                  # Flask API
├── train_models.py             # Model training
├── generate_datasets.py        # Data generation
├── test_api.py                 # API tests
├── run.sh                      # Startup script
├── requirements.txt            # Dependencies
├── README.md                   # Full documentation
├── QUICKSTART.md              # This file
├── data/
│   ├── soil_chemistry.csv     # 2000 soil samples
│   ├── fao_yields.csv         # Historical yields
│   └── egyptian_governorates.csv  # Governorate data
└── models/
    ├── xgb_crop_classifier.pkl
    ├── rf_crop_classifier.pkl
    ├── crop_encoder.pkl
    └── yield_models.pkl
```

---

## 🔧 Configuration

### Optional: Set OpenWeatherMap API Key

Create a `.env` file in the project root:
```env
OPENWEATHER_API_KEY=your_api_key_here
```

Without this, the system uses synthetic weather data for demo purposes.

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check if port 5000 is in use
lsof -i :5000
# Kill the process if needed
kill -9 <PID>
```

### Streamlit won't connect
```bash
# Verify backend is running
curl http://localhost:5000/api/health
```

### Models not found
```bash
# Regenerate datasets and train models
python generate_datasets.py
python train_models.py
```

### Port already in use
```bash
# Change Streamlit port
streamlit run app.py --server.port=8502
```

---

## 📊 Example Workflow

1. **Open Dashboard** → http://localhost:8501
2. **Select Weather Module** → Choose "Cairo" governorate
3. **View Current Weather** → See temperature, humidity, rainfall
4. **Go to Crop Recommendation** → Adjust soil properties with sliders
5. **Get Recommendation** → See recommended crop with confidence
6. **View Yield Forecast** → Predict 2026 yield for recommended crop
7. **Generate Report** → Download PDF with complete analysis

---

## 📈 API Endpoints Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | System health check |
| `/api/governorates` | GET | List all governorates |
| `/api/weather/<gov>` | GET | Get weather for governorate |
| `/api/recommend-crop` | POST | Get crop recommendation |
| `/api/forecast-yield` | POST | Forecast crop yield |
| `/api/shap-explanation` | POST | Get feature importance |
| `/api/generate-report` | POST | Generate PDF report |

---

## 🎓 Learning Resources

- **Machine Learning**: XGBoost, Random Forest, Linear Regression
- **Web Framework**: Flask (Backend), Streamlit (Frontend)
- **Explainability**: Feature importance analysis
- **Geospatial**: Folium maps, Egyptian governorate data
- **Data Science**: Pandas, NumPy, Scikit-learn

---

## 💡 Tips

- Use the test script to verify everything is working
- Check backend logs if frontend can't connect
- Adjust soil property sliders to see different recommendations
- Export PDF reports for offline analysis
- Modify datasets in `data/` to customize predictions

---

## 🆘 Need Help?

1. Check the full README.md for detailed documentation
2. Run `python test_api.py` to verify API functionality
3. Check terminal output for error messages
4. Ensure Python 3.10+ is installed: `python --version`

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: April 2026

🌾 **EgyptAgri-Pulse: Precision Agriculture for National Food Security** 🌾
