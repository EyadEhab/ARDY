import os
import json
import logging
import io
import uuid
import hashlib
from datetime import datetime
from contextlib import asynccontextmanager
from contextvars import ContextVar

import numpy as np
import tensorflow as tf
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from PIL import Image

# ==========================================
# 1. ENTERPRISE LOGGING CONFIGURATION
# ==========================================
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="SYSTEM")

# Global LogRecord factory to ensure 'request_id' is ALWAYS present
old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    try:
        record.request_id = request_id_ctx.get()
    except Exception:
        record.request_id = "SYSTEM"
    return record

logging.setLogRecordFactory(record_factory)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s',
    force=True
)

logger = logging.getLogger("PlantDoctorAPI")

# ==========================================
# 2. CONFIGURATION & ENVIRONMENT
# ==========================================
REDIS_URL = os.getenv("REDIS_URL", "redis://ardy-redis:6379/0")
MODEL_PATH = os.getenv("MODEL_PATH", "crop_model.h5")
TREATMENTS_PATH = os.getenv("TREATMENTS_PATH", "treatments.json")
MAX_FILE_SIZE = 5 * 1024 * 1024
IMG_SIZE = (224, 224)

# ==========================================
# 3. GLOBAL STATE & LIFECYCLE
# ==========================================
state = {
    "model": None,
    "treatment_data": {"class_names": [], "treatments": {}},
    "redis": None,
    "is_ready": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    try:
        logger.info("Starting up Plant Doctor API...")
        
        # Initialize Redis
        state["redis"] = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Load Treatment Data
        if os.path.exists(TREATMENTS_PATH):
            with open(TREATMENTS_PATH, 'r') as f:
                state["treatment_data"] = json.load(f)
            logger.info("Treatment data loaded.")
        else:
            logger.warning(f"TREATMENTS_PATH not found: {TREATMENTS_PATH}")

        # Load AI Model
        if os.path.exists(MODEL_PATH):
            logger.info(f"Loading model from {MODEL_PATH}...")
            state["model"] = tf.keras.models.load_model(MODEL_PATH, compile=False)
            state["model"](tf.zeros((1, *IMG_SIZE, 3))) # Warmup
            state["is_ready"] = True
            logger.info("Enterprise SaaS Backend Ready.")
        else:
            logger.error(f"MODEL_PATH not found: {MODEL_PATH}")
            state["is_ready"] = False
            
    except Exception as e:
        logger.error(f"Startup error: {e}")
        state["is_ready"] = False
    
    yield
    state["is_ready"] = False

app = FastAPI(title="Plant Doctor AI SaaS", lifespan=lifespan)

# ==========================================
# 4. MIDDLEWARE
# ==========================================
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Injects request_id into every log record during the request lifecycle."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(token)

# ==========================================
# 5. ENDPOINTS
# ==========================================

@app.get("/")
@app.get("/health")
def health_check():
    """Health check endpoint for Docker and monitoring."""
    if not state["is_ready"]:
        raise HTTPException(status_code=503, detail="System initializing or model missing")
    return {
        "status": "online",
        "model_loaded": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Predict plant disease from uploaded image."""
    if not state["is_ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        # Validate image format
        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Invalid image format. Please upload a JPEG or PNG file.")

        # MD5 Cache check
        img_hash = hashlib.md5(contents).hexdigest()
        cache_key = f"p:{img_hash}"
        cached = state["redis"].get(cache_key)
        
        if cached:
            return json.loads(cached)

        # Inference logic
        img = Image.open(io.BytesIO(contents)).convert('RGB').resize(IMG_SIZE)
        img_array = np.array(img, dtype=np.float32) / 255.0
        inp = tf.expand_dims(tf.convert_to_tensor(img_array), 0)
        
        preds = state["model"](inp, training=False)
        idx = np.argmax(preds[0])
        conf = float(np.max(preds[0]))
        
        class_names = state["treatment_data"].get("class_names", [])
        if not class_names:
            raise ValueError("Class names not loaded in treatment data")
            
        name = class_names[idx]
        treat = state["treatment_data"].get("treatments", {}).get(name, "Consult an agricultural expert for detailed treatment.")
        
        result = {
            "disease": name,
            "confidence": f"{conf*100:.2f}%",
            "treatment": treat
        }
        
        state["redis"].setex(cache_key, 3600, json.dumps(result))
        return result

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
