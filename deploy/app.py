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

import numpy as np
import tensorflow as tf
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from PIL import Image
from sqlalchemy import create_all, Column, Integer, String, Float, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# ==========================================
# 1. ENTERPRISE CONFIGURATION
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PlantDoctorAPI")

# Auth Config
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-for-plant-doctor-saas")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 Week

# DB Config
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:plant_doctor_secure@db:5432/plant_doctor_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# App Config
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MODEL_PATH = os.getenv("MODEL_PATH", "models/crop_model.h5")
TREATMENTS_PATH = os.getenv("TREATMENTS_PATH", "models/treatments.json")
MAX_FILE_SIZE = 5 * 1024 * 1024
IMG_SIZE = (224, 224)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ==========================================
# 2. DATABASE MODELS
# ==========================================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    tier = Column(String, default="Free") # Free, Pro, Business

class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    disease = Column(String)
    confidence = Column(Float)
    treatment = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. GLOBAL STATE & LIFECYCLE
# ==========================================
state = {
    "model": None,
    "treatment_data": {},
    "redis": None,
    "is_ready": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["redis"] = redis.from_url(REDIS_URL, decode_responses=True)
        with open(TREATMENTS_PATH, 'r') as f:
            state["treatment_data"] = json.load(f)
        state["model"] = tf.keras.models.load_model(MODEL_PATH, compile=False)
        state["model"](tf.zeros((1, *IMG_SIZE, 3))) # Warmup
        state["is_ready"] = True
        logger.info("Enterprise SaaS Backend Ready.")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise e
    yield
    state["is_ready"] = False

app = FastAPI(title="Plant Doctor AI SaaS", lifespan=lifespan)

# ==========================================
# 4. AUTH & DB DEPENDENCIES
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
# 5. SAAS ENDPOINTS (AUTH, HISTORY, PREDICT)
# ==========================================

@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user: raise HTTPException(status_code=400, detail="User exists")
    new_user = User(username=username, hashed_password=pwd_context.hash(password))
    db.add(new_user)
    db.commit()
    return {"message": "Success"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": create_access_token(data={"sub": user.username}), "token_type": "bearer"}

@app.post("/predict")
def predict(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not state["is_ready"]: raise HTTPException(status_code=503)
    
    # 1. SaaS Tier Limit (MVP Logic)
    if current_user.tier == "Free":
        today_scans = db.query(ScanHistory).filter(
            ScanHistory.user_id == current_user.id,
            ScanHistory.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        if today_scans >= 3:
            raise HTTPException(status_code=402, detail="Free limit reached. Upgrade to Pro!")

    try:
        contents = file.file.read(MAX_FILE_SIZE + 1)
        if len(contents) > MAX_FILE_SIZE: raise HTTPException(status_code=413)

        # Cache Check
        img_hash = hashlib.md5(contents).hexdigest()
        cache_key = f"p:{img_hash}"
        cached = state["redis"].get(cache_key)
        if cached:
            result = json.loads(cached)
        else:
            # Inference
            img = Image.open(io.BytesIO(contents)).convert('RGB').resize(IMG_SIZE)
            inp = tf.expand_dims(tf.convert_to_tensor(np.array(img, dtype=np.float32)), 0)
            preds = state["model"](inp, training=False)
            idx = np.argmax(preds[0])
            conf = float(np.max(preds[0]))
            
            name = state["treatment_data"]["class_names"][idx]
            treat = state["treatment_data"]["treatments"].get(name, "Consult specialist.")
            result = {"disease": name, "confidence": f"{conf*100:.2f}%", "treatment": treat}
            state["redis"].setex(cache_key, 3600, json.dumps(result))

        # 2. Save to History
        history = ScanHistory(
            user_id=current_user.id, 
            disease=result["disease"], 
            confidence=float(result["confidence"].replace('%','')), 
            treatment=result["treatment"]
        )
        db.add(history)
        db.commit()
        
        return result
    except Exception as e:
        logger.error(f"Predict error: {e}")
        raise HTTPException(status_code=500)

@app.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ScanHistory).filter(ScanHistory.user_id == current_user.id).all()
