# EgyptAgri-Pulse Wizard V2.0 - Docker Quick Start

## 🚀 ONE COMMAND TO RUN EVERYTHING

```bash
docker-compose up --build
```

That's it! Everything will automatically:
- ✅ Train ML models with real data
- ✅ Start backend API (port 5000)
- ✅ Start Plant Doctor API (port 8000)
- ✅ Start wizard dashboard (port 8501)
- ✅ Set up networking between services

---

## 📍 ACCESS THE WIZARD

Once running, open your browser:

**Wizard Dashboard**: http://localhost:8501

**Plant Doctor API (New)**: http://localhost:8000

**API Health Check**: http://localhost:5000/api/health

---

## 🛑 STOP EVERYTHING

```bash
docker-compose down
```

---

## 🔄 REBUILD & RESTART

If you make changes to code:

```bash
docker-compose up --build
```

---

## 📊 VIEW LOGS

See what's happening:

```bash
# All services
docker-compose logs -f

# Just frontend
docker-compose logs -f frontend

# Just backend
docker-compose logs -f backend

# Just model trainer
docker-compose logs -f model-trainer
```

---

## ⚙️ WHAT HAPPENS AUTOMATICALLY

### 1. Model Trainer (First)
- Loads real datasets from `data/` folder
- Trains XGBoost model (98.86% accuracy)
- Trains Random Forest model (99.55% accuracy)
- Trains 14 yield forecasting models
- Saves all models to `models/` folder
- Takes ~2-3 minutes
- Then stops (runs only once)

### 2. Backend API (After Models Ready)
- Starts Flask server on port 5000
- Loads trained models
- Ready to serve predictions
- Health check: http://localhost:5000/api/health

### 3. Frontend Wizard (After Backend Ready)
- Starts Streamlit on port 8501
- Loads models and data
- Ready for user interaction
- Open: http://localhost:8501

---

## 📁 FOLDER STRUCTURE NEEDED

```
egypt-agri-pulse/
├── app_wizard.py              ← Wizard dashboard
├── backend.py                 ← API server
├── retrain_models.py          ← Model training
├── docker-compose.yml         ← This file
├── Dockerfile.model-trainer   ← Model trainer image
├── Dockerfile.backend         ← Backend image
├── Dockerfile.frontend        ← Frontend image
│
├── data/
│   ├── Crop_recommendation.csv
│   └── Egypt_Crop_Yield_Processed_Pivot.csv
│
└── models/
    (auto-created by model-trainer)
```

---

## 🔧 ENVIRONMENT VARIABLES (Optional)

Create `.env` file in project root:

```env
OPENWEATHER_API_KEY=your_api_key_here
```

If not set, uses demo data.

---

## 🚨 TROUBLESHOOTING

### Models not training
```bash
docker-compose logs model-trainer
```

### Backend won't start
```bash
docker-compose logs backend
```

### Frontend won't load
```bash
docker-compose logs frontend
```

### Port already in use
```bash
# Change in docker-compose.yml:
ports:
  - "8000:5000"  # Use 8000 instead of 5000
  - "8080:8501"  # Use 8080 instead of 8501
```

### Clean everything and restart
```bash
docker-compose down -v
docker-compose up --build
```

---

## 📊 EXPECTED OUTPUT

When you run `docker-compose up --build`, you should see:

```
Creating egyptagri-model-trainer ... done
Creating egyptagri-backend ... done
Creating egyptagri-frontend ... done

model-trainer_1  | ======================================================================
model-trainer_1  | RETRAINING ML MODELS WITH REAL DATASETS
model-trainer_1  | ======================================================================
model-trainer_1  | [PHASE 1] Training Crop Recommendation Models...
model-trainer_1  | ✓ XGBoost Accuracy: 0.9886
model-trainer_1  | ✓ Random Forest Accuracy: 0.9955
model-trainer_1  | [PHASE 2] Training Yield Forecasting Models...
model-trainer_1  | ✓ Saved all yield models
model-trainer_1  | ======================================================================
model-trainer_1  | MODEL TRAINING COMPLETE
model-trainer_1  | ======================================================================

backend_1        | [2026-04-28 12:00:00] Starting Flask server...
backend_1        | [2026-04-28 12:00:01] Server running on http://0.0.0.0:5000

frontend_1       | [2026-04-28 12:00:05] Welcome to Streamlit!
frontend_1       | [2026-04-28 12:00:10] Server running on http://0.0.0.0:8501
```

---

## ✅ WIZARD WORKFLOW

Once running, the wizard has 4 steps:

1. **Select Governorate** (Interactive Map)
   - Choose your location
   - See weather data

2. **Enter Soil Data** (Soil Input)
   - Adjust N, P, K, pH sliders
   - Get top 3 crop recommendations
   - Read detailed explanations

3. **Yield Forecast** (2026 Predictions)
   - View yield predictions
   - Compare with historical average
   - Check model reliability

4. **Generate Report** (Export)
   - Review complete analysis
   - Export PDF/CSV
   - Start over

---

## 🎯 COMMON TASKS

### Run wizard only (no backend)
```bash
docker-compose up frontend
```

### Run backend API only
```bash
docker-compose up backend
```

### Retrain models
```bash
docker-compose up model-trainer
```

### Remove all containers
```bash
docker-compose down
```

### Remove all data (fresh start)
```bash
docker-compose down -v
```

### View service status
```bash
docker-compose ps
```

---

## 📈 PERFORMANCE

- **Model Training**: 2-3 minutes (first run only)
- **Backend Startup**: 10-15 seconds
- **Frontend Startup**: 15-20 seconds
- **Crop Prediction**: <100ms
- **Yield Forecast**: <50ms

---

## 🔐 SECURITY NOTES

For production:
- Change API keys in `.env`
- Use HTTPS/TLS certificates
- Implement authentication
- Use environment-specific configs
- Keep images updated

---

## 📚 DOCUMENTATION

- **WIZARD_GUIDE.md** - Complete user guide
- **WIZARD_SUMMARY.txt** - Project overview
- **README.md** - Technical documentation
- **DOCKER.md** - Advanced Docker guide

---

## 🌾 YOU'RE READY!

Just run:

```bash
docker-compose up --build
```

Then open: **http://localhost:8501**

Enjoy the wizard! 🎉

---

**Version**: 2.0 | **Date**: April 28, 2026

🌾 **EgyptAgri-Pulse Wizard: Precision Agriculture for National Food Security** 🌾
