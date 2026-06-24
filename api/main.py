"""
GoPredict FastAPI Backend

This FastAPI application provides REST API endpoints for the GoPredict machine learning project.
It connects all the ML functions from the src directory with a web interface.

Endpoints:
- /weather: Get weather data for specific location and time
- /predict: Make trip duration predictions
- /distance: Calculate Manhattan and Euclidean distances
- /time-features: Extract time-based features
- /geolocation: Perform geolocation clustering
- /models: Model management endpoints
- /data: Data preprocessing endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import ML modules
from features.weather_api import get_weather_for_trip
from features.distance import calc_distance
from features.time import extract_time_features
from features.geolocation import clustering
from model.models import run_regression_models, predict_duration, normalize_features
from complete_pipeline import CompleteMLPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Initialize FastAPI app
app = FastAPI(
    title="GoPredict API",
    description="Machine Learning API for Trip Duration Prediction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model management
trained_models = {}
pipeline_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize the ML pipeline on startup"""
    global pipeline_instance
    try:
        pipeline_instance = CompleteMLPipeline()
        logging.info("✅ GoPredict API initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize pipeline: {e}")

# ===============================
# WEATHER API ENDPOINTS
# ===============================

@app.get("/weather")
async def get_weather(
    latitude: float,
    longitude: float,
    timestamp: str
):
    """
    Get weather data for a specific location and time.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        timestamp: ISO format timestamp (e.g., "2016-01-01T17:00:00")
    
    Returns:
        Weather data dictionary
    """
    try:
        # Parse timestamp
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Get weather data
        weather_data = get_weather_for_trip(latitude, longitude, dt)
        
        if not weather_data:
            raise HTTPException(status_code=404, detail="No weather data found for the specified location and time")
        
        return {
            "success": True,
            "data": weather_data,
            "location": {"latitude": latitude, "longitude": longitude},
            "timestamp": timestamp
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {e}")
    except Exception as e:
        logging.error(f"Weather API error: {e}")
        raise HTTPException(status_code=500, detail=f"Weather data retrieval failed: {e}")

# ===============================
# DISTANCE CALCULATION ENDPOINTS
# ===============================

@app.post("/distance")
async def calculate_distance(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    method: str = "both"
):
    """
    Calculate Manhattan and/or Euclidean distances between two points.
    
    Args:
        start_lat: Starting latitude
        start_lng: Starting longitude
        end_lat: Ending latitude
        end_lng: Ending longitude
        method: "manhattan", "euclidean", or "both"
    
    Returns:
        Distance calculation results
    """
    try:
        # Create a simple dataframe for the distance calculation
        df = pd.DataFrame({
            'start_lat': [start_lat],
            'start_lng': [start_lng],
            'end_lat': [end_lat],
            'end_lng': [end_lng]
        })
        
        results = {}
        
        if method in ["manhattan", "both"]:
            manhattan_dist = calc_distance(df, method='manhattan')[0]
            results["manhattan_distance"] = float(manhattan_dist)
        
        if method in ["euclidean", "both"]:
            euclidean_dist = calc_distance(df, method='euclidean')[0]
            results["euclidean_distance"] = float(euclidean_dist)
        
        return {
            "success": True,
            "data": results,
            "start_location": {"latitude": start_lat, "longitude": start_lng},
            "end_location": {"latitude": end_lat, "longitude": end_lng}
        }
    
    except Exception as e:
        logging.error(f"Distance calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Distance calculation failed: {e}")

# ===============================
# TIME FEATURES ENDPOINTS
# ===============================

@app.post("/time-features")
async def extract_time_features_api(
    datetime_str: str
):
    """
    Extract time-based features from a datetime string.
    
    Args:
        datetime_str: ISO format datetime string
    
    Returns:
        Time features dictionary
    """
    try:
        # Parse datetime
        dt = pd.to_datetime(datetime_str)
        
        # Extract features
        weekday = dt.weekday() + 1
        hour = dt.hour
        date = dt.date()
        
        # Check if it's a holiday (simplified 2015 holidays)
        holidays_2015 = {
            datetime.date(2015, 1, 1),   # New Years Day
            datetime.date(2015, 1, 19),  # Martin Luther King Day
            datetime.date(2015, 4, 4),   # Easter Saturday
            datetime.date(2015, 4, 5),   # Easter Sunday
            datetime.date(2015, 5, 24),  # Memorial Sunday
            datetime.date(2015, 5, 25),  # Memorial Day
            datetime.date(2015, 7, 3),   # Independence Pre-day
            datetime.date(2015, 7, 4),   # Independence Day
            datetime.date(2015, 7, 5),   # Independence Post-day
            datetime.date(2015, 9, 7),   # Labor Day
            datetime.date(2015, 11, 26), # Thanksgiving Day
            datetime.date(2015, 11, 27), # Thanksgiving Post-day
            datetime.date(2015, 11, 28), # Thanksgiving Post-post-day
            datetime.date(2015, 12, 24), # Christmas Eve
            datetime.date(2015, 12, 25), # Christmas Day
            datetime.date(2015, 12, 26), # Christmas Post-day
            datetime.date(2015, 12, 31), # New Years Eve
        }
        
        is_holiday = 1 if date in holidays_2015 else 0
        
        return {
            "success": True,
            "data": {
                "weekday": int(weekday),
                "hour": int(hour),
                "date": str(date),
                "holiday": is_holiday
            },
            "original_datetime": datetime_str
        }
    
    except Exception as e:
        logging.error(f"Time features extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Time features extraction failed: {e}")

# ===============================
# PREDICTION ENDPOINTS
# ===============================

class LocationModel(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    lat: float
    lon: float


class PredictRequest(BaseModel):
    from_: LocationModel = Field(..., alias="from")
    to: LocationModel
    startTime: str
    city: Optional[str] = "new_york"
    model_name: Optional[str] = "XGBoost"


@app.post("/predict")
async def predict_trip_duration(
    # allow either a JSON body (new frontend) or legacy query params
    payload: Optional[PredictRequest] = Body(None),
    start_lat: Optional[float] = None,
    start_lng: Optional[float] = None,
    end_lat: Optional[float] = None,
    end_lng: Optional[float] = None,
    datetime_str: Optional[str] = None,
    model_name: str = "XGBoost",
):
    """
    Predict trip duration using trained ML models.

    Supports two input styles:
    - JSON body matching the frontend (from, to, startTime, city)
    - Legacy query params (start_lat, start_lng, end_lat, end_lng, datetime_str)
    Returns a simple top-level JSON with minutes, confidence and distance_km.
    """
    try:
        # If payload provided (frontend JSON), extract values
        if payload is not None:
            start_lat = payload.from_.lat
            start_lng = payload.from_.lon
            end_lat = payload.to.lat
            end_lng = payload.to.lon
            datetime_str = payload.startTime
            model_name = payload.model_name or model_name
            city = payload.city or "new_york"

        # Basic validation
        if any(v is None for v in [start_lat, start_lng, end_lat, end_lng, datetime_str]):
            raise HTTPException(status_code=400, detail="Missing required trip parameters")

        # Try using trained model if available
        minutes = None
        distance_km = None

        # compute distance using existing helper (euclidean) -> returns METERS; convert to KM
        try:
            distance_m = float(calc_distance(pd.DataFrame({
                'start_lat': [start_lat], 'start_lng': [start_lng], 'end_lat': [end_lat], 'end_lng': [end_lng]
            }), method='euclidean')[0])
            distance_km = distance_m / 1000.0
        except Exception:
            distance_km = None

        if trained_models and model_name in trained_models:
            model = trained_models[model_name]
            features = await create_feature_vector(start_lat, start_lng, end_lat, end_lng, datetime_str)
            try:
                pred = model.predict([features])[0]
                minutes = float(pred) / 60.0
            except Exception:
                minutes = None

        # Fallback estimate if model not available or failed
        if minutes is None:
            # Use computed distance_km if available, otherwise 0
            km = distance_km or 0.0
            base_speed = 25.0
            minutes = max(5.0, (km / base_speed) * 60.0)

        response = {
            "minutes": round(minutes, 1),
            "confidence": 0.75,
            "model_version": model_name,
            "distance_km": round(distance_km or 0.0, 1),
            "city": payload.city if payload is not None else (locals().get('city', None) or "unknown")
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

async def create_feature_vector(start_lat, start_lng, end_lat, end_lng, datetime_str):
    """Create a feature vector for prediction"""
    try:
        # Calculate distances
        df = pd.DataFrame({
            'start_lat': [start_lat],
            'start_lng': [start_lng],
            'end_lat': [end_lat],
            'end_lng': [end_lng]
        })
        
        manhattan_dist = calc_distance(df, method='manhattan')[0]
        euclidean_dist = calc_distance(df, method='euclidean')[0]
        
        # Extract time features
        dt = pd.to_datetime(datetime_str)
        weekday = dt.weekday() + 1
        hour = dt.hour
        
        # Create feature vector (simplified - you may need to adjust based on your model's expected features)
        features = [
            start_lat, start_lng, end_lat, end_lng,
            manhattan_dist, euclidean_dist,
            weekday, hour,
            0, 0, 0, 0, 0, 0  # Placeholder for other features
        ]
        
        return features
    
    except Exception as e:
        logging.error(f"Feature vector creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Feature vector creation failed: {e}")

# ===============================
# MODEL MANAGEMENT ENDPOINTS
# ===============================

@app.post("/models/train")
async def train_models(
    background_tasks: BackgroundTasks,
    models_to_run: List[str] = ["XGBoost", "Random Forest"]
):
    """
    Train ML models in the background.
    
    Args:
        models_to_run: List of models to train
        background_tasks: FastAPI background tasks
    
    Returns:
        Training status
    """
    try:
        if not pipeline_instance:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        # Start training in background
        background_tasks.add_task(train_models_background, models_to_run)
        
        return {
            "success": True,
            "message": "Model training started in background",
            "models_to_train": models_to_run
        }
    
    except Exception as e:
        logging.error(f"Model training initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Model training initiation failed: {e}")

async def train_models_background(models_to_run):
    """Background task for training models"""
    global trained_models
    try:
        logging.info(f"Starting background training for models: {models_to_run}")
        
        # Load feature engineered data
        train_df = pd.read_csv("data/processed/feature_engineered_train.csv")
        
        # Train models
        models = run_regression_models(train_df, models_to_run)
        trained_models.update(models)
        
        logging.info(f"✅ Successfully trained {len(models)} models")
    
    except Exception as e:
        logging.error(f"❌ Background training failed: {e}")

@app.get("/models")
async def list_models():
    """List all available trained models"""
    return {
        "success": True,
        "models": list(trained_models.keys()),
        "count": len(trained_models)
    }

@app.get("/models/{model_name}")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    if model_name not in trained_models:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    model = trained_models[model_name]
    
    return {
        "success": True,
        "model_name": model_name,
        "model_type": type(model).__name__,
        "has_feature_names": hasattr(model, 'feature_names_in_'),
        "feature_names": getattr(model, 'feature_names_in_', None)
    }

# ===============================
# DATA PROCESSING ENDPOINTS
# ===============================

@app.post("/data/preprocess")
async def preprocess_data(background_tasks: BackgroundTasks):
    """Start data preprocessing in the background"""
    try:
        if not pipeline_instance:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        background_tasks.add_task(preprocess_data_background)
        
        return {
            "success": True,
            "message": "Data preprocessing started in background"
        }
    
    except Exception as e:
        logging.error(f"Data preprocessing initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Data preprocessing initiation failed: {e}")

async def preprocess_data_background():
    """Background task for data preprocessing"""
    try:
        logging.info("Starting background data preprocessing")
        
        # Run preprocessing steps
        train_df, test_df = pipeline_instance.step1_data_preprocessing()
        
        logging.info("✅ Data preprocessing completed")
    
    except Exception as e:
        logging.error(f"❌ Background preprocessing failed: {e}")

@app.post("/data/feature-engineering")
async def feature_engineering(background_tasks: BackgroundTasks):
    """Start feature engineering in the background"""
    try:
        if not pipeline_instance:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        background_tasks.add_task(feature_engineering_background)
        
        return {
            "success": True,
            "message": "Feature engineering started in background"
        }
    
    except Exception as e:
        logging.error(f"Feature engineering initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Feature engineering initiation failed: {e}")

async def feature_engineering_background():
    """Background task for feature engineering"""
    try:
        logging.info("Starting background feature engineering")
        
        # Run feature engineering steps
        train_df, test_df = pipeline_instance.step2_feature_engineering()
        
        logging.info("✅ Feature engineering completed")
    
    except Exception as e:
        logging.error(f"❌ Background feature engineering failed: {e}")

# ===============================
# PIPELINE ENDPOINTS
# ===============================

@app.post("/pipeline/run")
async def run_complete_pipeline(
    background_tasks: BackgroundTasks,
    models_to_run: List[str] = ["XGBoost", "Random Forest"]
):
    """Run the complete ML pipeline in the background"""
    try:
        if not pipeline_instance:
            raise HTTPException(status_code=500, detail="Pipeline not initialized")
        
        background_tasks.add_task(run_pipeline_background, models_to_run)
        
        return {
            "success": True,
            "message": "Complete pipeline started in background",
            "models_to_run": models_to_run
        }
    
    except Exception as e:
        logging.error(f"Pipeline initiation error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline initiation failed: {e}")

async def run_pipeline_background(models_to_run):
    """Background task for running complete pipeline"""
    global trained_models
    try:
        logging.info(f"Starting complete pipeline with models: {models_to_run}")
        
        # Run complete pipeline
        results = pipeline_instance.run_complete_pipeline(models_to_run=models_to_run)
        
        # Update global models
        if 'models' in results:
            trained_models.update(results['models'])
        
        logging.info("✅ Complete pipeline finished successfully")
    
    except Exception as e:
        logging.error(f"❌ Complete pipeline failed: {e}")

# ===============================
# HEALTH AND STATUS ENDPOINTS
# ===============================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GoPredict API",
        "version": "1.0.0",
        "models_loaded": len(trained_models),
        "pipeline_initialized": pipeline_instance is not None
    }


@app.get("/")
async def root_redirect():
    """Root endpoint - simple status to avoid 404 on HEAD/GET /"""
    return {
        "status": "ok",
        "message": "GoPredict API - see /health for details",
        "health": f"{os.environ.get('ROOT_URL', '')}/health" if os.environ.get('ROOT_URL') else "/health"
    }

@app.get("/status")
async def get_status():
    """Get detailed status of the API"""
    return {
        "success": True,
        "status": {
            "api_version": "1.0.0",
            "models_available": list(trained_models.keys()),
            "models_count": len(trained_models),
            "pipeline_ready": pipeline_instance is not None,
            "data_files_exist": {
                "train_data": os.path.exists("data/raw/train.csv"),
                "test_data": os.path.exists("data/raw/test.csv"),
                "feature_train": os.path.exists("data/processed/feature_engineered_train.csv"),
                "feature_test": os.path.exists("data/processed/feature_engineered_test.csv")
            }
        }
    }

# ===============================
# MAIN APPLICATION
# ===============================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
