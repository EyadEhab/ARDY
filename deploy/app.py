import os
import json
import logging
import io
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager
from contextvars import ContextVar

import numpy as np
import tensorflow as tf
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from PIL import Image
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

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
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-for-plant-doctor-saas")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

# DB Config - Defaults match docker-compose service names
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:plant_doctor_secure@ardy-db:5432/plant_doctor_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# App Config
REDIS_URL = os.getenv("REDIS_URL", "redis://ardy-redis:6379/0")
MODEL_PATH = os.getenv("MODEL_PATH", "models/crop_model.h5")
TREATMENTS_PATH = os.getenv("TREATMENTS_PATH", "models/treatments.json")
MAX_FILE_SIZE = 5 * 1024 * 1024
IMG_SIZE = (224, 224)

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ==========================================
# 3. DATABASE MODELS
# ==========================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tier = Column(String, default="Free")

class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    disease = Column(String)
    confidence = Column(Float)
    treatment = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ==========================================
# 4. GLOBAL STATE & LIFECYCLE
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
# 5. MIDDLEWARE
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
# 6. AUTH & DB DEPENDENCIES
# ==========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(status_code=401)
    except JWTError: raise HTTPException(status_code=401)
    user = db.query(User).filter(User.username == username).first()
    if user is None: raise HTTPException(status_code=401)
    return user

# ==========================================
# 7. ENDPOINTS
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

@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user: raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": create_access_token(data={"sub": user.username}), "token_type": "bearer"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Predict plant disease from uploaded image."""
    if not state["is_ready"]:
        raise HTTPException(status_code=503, detail="Model not ready")

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

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

@app.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve scan history for the authenticated user."""
    return db.query(ScanHistory).filter(ScanHistory.user_id == current_user.id).all()
