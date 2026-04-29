"""
EgyptAgri-Pulse: Step-by-Step Wizard Dashboard
A multi-step interactive guide for crop selection and yield forecasting
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="EgyptAgri-Pulse Wizard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: 600;
    }
    .step-header {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .step-number {
        font-size: 3rem;
        font-weight: bold;
        color: #2ecc71;
    }
    .crop-card {
        background: linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%);
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2ecc71;
    }
    .confidence-high {
        color: #27ae60;
        font-weight: bold;
    }
    .confidence-medium {
        color: #f39c12;
        font-weight: bold;
    }
    .confidence-low {
        color: #e74c3c;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD MODELS AND DATA
# ============================================================================
@st.cache_resource
def load_models():
    """Load trained ML models"""
    with open('models/xgb_crop_classifier.pkl', 'rb') as f:
        xgb_model = pickle.load(f)
    with open('models/rf_crop_classifier.pkl', 'rb') as f:
        rf_model = pickle.load(f)
    with open('models/crop_encoder.pkl', 'rb') as f:
        crop_encoder = pickle.load(f)
    with open('models/yield_models.pkl', 'rb') as f:
        yield_models = pickle.load(f)
    with open('models/crop_features.pkl', 'rb') as f:
        crop_features = pickle.load(f)
    
    return xgb_model, rf_model, crop_encoder, yield_models, crop_features

@st.cache_data
def load_datasets():
    """Load reference datasets"""
    governorates_df = pd.read_csv('data/egyptian_governorates.csv')
    crop_rec_df = pd.read_csv('data/Crop_recommendation.csv')
    yield_df = pd.read_csv('data/Egypt_Crop_Yield_Processed_Pivot.csv')
    
    return governorates_df, crop_rec_df, yield_df

# Load models and data
xgb_model, rf_model, crop_encoder, yield_models, crop_features = load_models()
governorates_df, crop_rec_df, yield_df = load_datasets()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_weather_data(governorate):
    """Get real weather data from OpenWeatherMap API"""
    try:
        # Get governorate coordinates
        gov_row = governorates_df[governorates_df['Governorate'] == governorate]
        if gov_row.empty:
            return None
        
        lat = gov_row['Latitude'].values[0]
        lon = gov_row['Longitude'].values[0]
        
        # OpenWeather API call
        api_key = os.getenv('OPENWEATHER_API_KEY')
        
        # Check if API key exists
        if not api_key or api_key == '' or len(api_key) < 10:
            raise ValueError(f"API key invalid (length: {len(api_key) if api_key else 0})")
        
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            raise ValueError(f"API Error: Status {response.status_code} - {response.text[:100]}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract weather data
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            
            # Get rainfall from API (only contains data when currently raining)
            rainfall = data.get('rain', {}).get('1h', 0) * 1000
            
            # Estimate pH based on region (Egypt average is ~7.5)
            ph = 7.5
            
            return {
                'temperature': temp,
                'humidity': humidity,
                'rainfall': rainfall,
                'ph': ph,
                'source': 'OpenWeatherMap API',
                'location': f"{lat}, {lon}"
            }
        else:
            # Fallback to dataset average if API fails
            # Use FIXED average from entire dataset (not random sample)
            return {
                'temperature': crop_rec_df['temperature'].mean(),
                'humidity': crop_rec_df['humidity'].mean(),
                'rainfall': crop_rec_df['rainfall'].mean(),
                'ph': crop_rec_df['ph'].mean(),
                'source': 'Dataset Average (API failed)'
            }
    except Exception as e:
        # Fallback to dataset average if API fails
        # Use FIXED average from entire dataset (not random sample)
        return {
            'temperature': crop_rec_df['temperature'].mean(),
            'humidity': crop_rec_df['humidity'].mean(),
            'rainfall': crop_rec_df['rainfall'].mean(),
            'ph': crop_rec_df['ph'].mean(),
            'source': 'Dataset Average (Error)'
        }

def predict_crops(n, p, k, temperature, humidity, ph, rainfall):
    """Predict top 3 crops with confidence scores and explanations"""
    
    # Prepare input features
    input_data = np.array([[n, p, k, temperature, humidity, ph, rainfall]])
    
    # Get predictions from both models
    xgb_proba = xgb_model.predict_proba(input_data)[0]
    rf_proba = rf_model.predict_proba(input_data)[0]
    
    # Ensemble voting (average probabilities)
    ensemble_proba = (xgb_proba + rf_proba) / 2
    
    # Get top 3 crops
    top_3_indices = np.argsort(ensemble_proba)[-3:][::-1]
    
    predictions = []
    for idx in top_3_indices:
        crop_name = crop_encoder.classes_[idx]
        confidence = ensemble_proba[idx]
        
        # Generate explanation
        explanation = generate_explanation(
            crop_name, n, p, k, temperature, humidity, ph, rainfall
        )
        
        predictions.append({
            'crop': crop_name,
            'confidence': confidence,
            'xgb_confidence': xgb_proba[idx],
            'rf_confidence': rf_proba[idx],
            'explanation': explanation
        })
    
    return predictions

def generate_explanation(crop, n, p, k, temp, humidity, ph, rainfall):
    """Generate explanation for crop recommendation"""
    
    # Get crop-specific statistics from training data
    crop_data = crop_rec_df[crop_rec_df['label'] == crop]
    
    if len(crop_data) == 0:
        return "Crop recommended based on soil and weather conditions."
    
    crop_avg_n = crop_data['N'].mean()
    crop_avg_p = crop_data['P'].mean()
    crop_avg_k = crop_data['K'].mean()
    crop_avg_temp = crop_data['temperature'].mean()
    crop_avg_humidity = crop_data['humidity'].mean()
    crop_avg_ph = crop_data['ph'].mean()
    crop_avg_rainfall = crop_data['rainfall'].mean()
    
    reasons = []
    
    # Nitrogen explanation
    if n >= crop_avg_n * 0.8:
        reasons.append(f"✓ Nitrogen level ({n}) is suitable for {crop}")
    else:
        reasons.append(f"⚠ Nitrogen level ({n}) is lower than optimal ({crop_avg_n:.0f}) for {crop}")
    
    # Phosphorus explanation
    if p >= crop_avg_p * 0.8:
        reasons.append(f"✓ Phosphorus level ({p}) supports {crop} growth")
    else:
        reasons.append(f"⚠ Phosphorus level ({p}) could be higher for {crop}")
    
    # Potassium explanation
    if k >= crop_avg_k * 0.8:
        reasons.append(f"✓ Potassium level ({k}) is appropriate for {crop}")
    else:
        reasons.append(f"⚠ Potassium level ({k}) is lower than ideal")
    
    # Temperature explanation
    if abs(temp - crop_avg_temp) < 5:
        reasons.append(f"✓ Temperature ({temp:.1f}°C) is ideal for {crop}")
    else:
        reasons.append(f"⚠ Temperature ({temp:.1f}°C) differs from optimal ({crop_avg_temp:.1f}°C)")
    
    # Humidity explanation
    if abs(humidity - crop_avg_humidity) < 10:
        reasons.append(f"✓ Humidity ({humidity:.1f}%) is suitable for {crop}")
    else:
        reasons.append(f"⚠ Humidity ({humidity:.1f}%) differs from optimal ({crop_avg_humidity:.1f}%)")
    
    # Rainfall explanation
    if abs(rainfall - crop_avg_rainfall) < 50:
        reasons.append(f"✓ Rainfall ({rainfall:.1f}mm) matches {crop} requirements")
    else:
        reasons.append(f"⚠ Rainfall ({rainfall:.1f}mm) differs from typical ({crop_avg_rainfall:.1f}mm)")
    
    # pH explanation
    if abs(ph - crop_avg_ph) < 1:
        reasons.append(f"✓ Soil pH ({ph:.2f}) is optimal for {crop}")
    else:
        reasons.append(f"⚠ Soil pH ({ph:.2f}) differs from optimal ({crop_avg_ph:.2f})")
    
    return "\n".join(reasons)

# Crop name mapping from recommendation model to yield models
CROP_NAME_MAPPING = {
    'muskmelon': 'Cantaloupes and other melons',
    'chickpea': 'Chick peas, dry',
    'mothbeans': 'Beans, dry',
    'wheat': 'Barley',
    'rice': 'Barley',
    'maize': 'Barley',
    'cotton': 'Spices & Herbs',
    'sugarcane': 'Spices & Herbs',
    'groundnut': 'Beans, dry',
    'lentil': 'Chick peas, dry',
    'orange': 'Apricots',
    'banana': 'Bananas',
    'papaya': 'Bananas',
    'coconut': 'Spices & Herbs',
    'watermelon': 'Cantaloupes and other melons',
    'pomegranate': 'Apricots',
    'apple': 'Apples',
    'grapes': 'Apricots',
    'mango': 'Bananas',
    'onion': 'Carrots and turnips',
    'potato': 'Cabbages',
    'tomato': 'Cabbages',
    'blackgram': 'Beans, dry',
    'coffee': 'Spices & Herbs',
    'jute': 'Spices & Herbs',
    'kidneybeans': 'Beans, dry',
    'mungbean': 'Beans, dry',
    'pigeonpeas': 'Chick peas, dry',
}

def predict_yield(crop, year=2026):
    """Predict yield for a crop in a given year"""
    
    # Map crop name if needed
    mapped_crop = CROP_NAME_MAPPING.get(crop, crop)
    
    if mapped_crop not in yield_models:
        return None
    
    model_data = yield_models[mapped_crop]
    model = model_data['model']
    
    # Predict yield
    predicted_yield = model.predict([[year]])[0]
    
    return {
        'crop': crop,
        'year': year,
        'predicted_yield': predicted_yield,
        'r2_score': model_data['r2_score'],
        'avg_yield': model_data['avg_yield'],
        'latest_yield': model_data['latest_yield'],
        'min_year': model_data['min_year'],
        'max_year': model_data['max_year']
    }

def create_yield_chart(crop_predictions):
    """Create yield forecast chart"""
    
    crops = [p['crop'] for p in crop_predictions]
    yields = [p['predicted_yield'] for p in crop_predictions]
    avg_yields = [p['avg_yield'] for p in crop_predictions]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=crops,
        y=yields,
        name='2026 Predicted Yield',
        marker_color='#2ecc71',
        text=[f'{y:.0f}' for y in yields],
        textposition='auto'
    ))
    
    fig.add_trace(go.Bar(
        x=crops,
        y=avg_yields,
        name='Historical Average',
        marker_color='#95a5a6',
        text=[f'{y:.0f}' for y in avg_yields],
        textposition='auto'
    ))
    
    fig.update_layout(
        title='Yield Forecast for Recommended Crops (2026)',
        xaxis_title='Crop',
        yaxis_title='Yield (Tonnes/Hectare)',
        barmode='group',
        height=400,
        hovermode='x unified'
    )
    
    return fig

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

if 'current_step' not in st.session_state:
    st.session_state.current_step = 1

if 'wizard_data' not in st.session_state:
    st.session_state.wizard_data = {
        'governorate': None,
        'weather': None,
        'n': None,
        'p': None,
        'k': None,
        'ph': None,
        'crop_predictions': None
    }

# ============================================================================
# MAIN APP
# ============================================================================

st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1>🌾 EgyptAgri-Pulse Wizard</h1>
        <p style="font-size: 1.1rem; color: #7f8c8d;">
            Step-by-step guide to optimal crop selection and yield forecasting
        </p>
    </div>
""", unsafe_allow_html=True)

# Step indicator
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div style='text-align: center; padding: 10px; background: {'#2ecc71' if st.session_state.current_step >= 1 else '#bdc3c7'}; color: white; border-radius: 5px;'><b>Step 1</b><br>Location</div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div style='text-align: center; padding: 10px; background: {'#2ecc71' if st.session_state.current_step >= 2 else '#bdc3c7'}; color: white; border-radius: 5px;'><b>Step 2</b><br>Soil Data</div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div style='text-align: center; padding: 10px; background: {'#2ecc71' if st.session_state.current_step >= 3 else '#bdc3c7'}; color: white; border-radius: 5px;'><b>Step 3</b><br>Yield</div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div style='text-align: center; padding: 10px; background: {'#2ecc71' if st.session_state.current_step >= 4 else '#bdc3c7'}; color: white; border-radius: 5px;'><b>Step 4</b><br>Report</div>", unsafe_allow_html=True)

st.divider()

# ============================================================================
# STEP 1: SELECT GOVERNORATE AND VIEW WEATHER
# ============================================================================

if st.session_state.current_step == 1:
    st.markdown("<div class='step-header'><div class='step-number'>1</div><h2>Select Your Governorate</h2><p>Choose your location to see weather conditions</p></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 Egypt Map")
        
        # Create Folium map
        m = folium.Map(
            location=[26.8206, 30.8025],  # Egypt center
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add governorate markers
        for idx, row in governorates_df.iterrows():
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=8,
                popup=row['Governorate'],
                color='#2ecc71',
                fill=True,
                fillColor='#2ecc71',
                fillOpacity=0.7,
                tooltip=row['Governorate']
            ).add_to(m)
        
        map_data = st_folium(m, width=500, height=500)
    
    with col2:
        st.subheader("🌍 Select Governorate")
        
        selected_gov = st.selectbox(
            "Choose a governorate:",
            governorates_df['Governorate'].unique(),
            key='gov_select'
        )
        
        if selected_gov:
            st.session_state.wizard_data['governorate'] = selected_gov

            # Get real weather data from API
            weather_data = get_weather_data(selected_gov)
            st.session_state.wizard_data['weather'] = weather_data

            st.success(f"✓ Selected: **{selected_gov}**")

            # Display weather information
            st.subheader("🌤️ Weather & Climate Data")
            
            # Data source indicator
            source = weather_data.get('source', 'Unknown')
            if source == 'OpenWeatherMap API':
                st.success(f"✅ Data Source: {source}")
            else:
                st.warning(f"ℹ️ Data Source: {source} - Using historical averages")

            # Refresh button
            if st.button("🔄 Refresh Live Data", key='refresh_weather', use_container_width=True):
                st.rerun()

            col_w1, col_w2 = st.columns(2)
            with col_w1:
                st.metric("🌡️ Temperature", f"{weather_data['temperature']:.1f}°C")
                st.metric("💧 Rainfall", f"{weather_data['rainfall']:.1f} mm")

            with col_w2:
                st.metric("💨 Humidity", f"{weather_data['humidity']:.1f}%")

            # Next button
            st.divider()
            if st.button("➡️ Next: Enter Soil Data", key='next_step1', use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()

# ============================================================================
# STEP 2: ENTER SOIL DATA AND GET CROP RECOMMENDATIONS
# ============================================================================

elif st.session_state.current_step == 2:
    st.markdown("<div class='step-header'><div class='step-number'>2</div><h2>Enter Soil Properties</h2><p>Selected Governorate: <b>" + st.session_state.wizard_data['governorate'] + "</b></p></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🧪 Soil Nutrients")
        
        n = st.slider("Nitrogen (N)", min_value=0, max_value=140, value=50, step=1)
        p = st.slider("Phosphorus (P)", min_value=5, max_value=145, value=50, step=1)
        k = st.slider("Potassium (K)", min_value=5, max_value=205, value=100, step=1)
        ph = st.slider("Soil pH", min_value=3.5, max_value=10.0, value=6.5, step=0.1)
        
        st.session_state.wizard_data['n'] = n
        st.session_state.wizard_data['p'] = p
        st.session_state.wizard_data['k'] = k
        st.session_state.wizard_data['ph'] = ph
    
    with col2:
        st.subheader("📊 Current Values")
        
        data_summary = pd.DataFrame({
            'Parameter': ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 'pH'],
            'Value': [n, p, k, f'{ph:.2f}'],
            'Unit': ['mg/kg', 'mg/kg', 'mg/kg', '-']
        })
        
        st.table(data_summary)
        
        st.info("💡 Tip: Adjust sliders to match your soil test results for accurate recommendations.")
    
    st.divider()
    
    # Get crop predictions
    if st.button("🔍 Get Crop Recommendations", use_container_width=True, key='get_recommendations'):
        weather = st.session_state.wizard_data['weather']
        
        predictions = predict_crops(
            n, p, k,
            weather['temperature'],
            weather['humidity'],
            ph,  # Use pH from Layer 2 slider (user-controlled)
            weather['rainfall']
        )
        
        st.session_state.wizard_data['crop_predictions'] = predictions
    
    # Display recommendations
    if st.session_state.wizard_data['crop_predictions']:
        st.subheader("🎯 Top 3 Recommended Crops")
        
        for i, pred in enumerate(st.session_state.wizard_data['crop_predictions'], 1):
            with st.expander(f"#{i} {pred['crop'].upper()} - Confidence: {pred['confidence']*100:.1f}%", expanded=(i==1)):
                
                # Confidence scores
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ensemble", f"{pred['confidence']*100:.1f}%")
                with col2:
                    st.metric("XGBoost", f"{pred['xgb_confidence']*100:.1f}%")
                with col3:
                    st.metric("Random Forest", f"{pred['rf_confidence']*100:.1f}%")
                
                # Explanation
                st.subheader("📝 Why This Crop?")
                st.write(pred['explanation'])
        
        st.divider()
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back", use_container_width=True, key='back_step2'):
                st.session_state.current_step = 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Next: View Yield Forecast", use_container_width=True, key='next_step2'):
                st.session_state.current_step = 3
                st.rerun()

# ============================================================================
# STEP 3: YIELD FORECASTING
# ============================================================================

elif st.session_state.current_step == 3:
    st.markdown("<div class='step-header'><div class='step-number'>3</div><h2>Yield Forecast 2026</h2><p>Predictions for your recommended crops</p></div>", unsafe_allow_html=True)
    
    # Get yield predictions for recommended crops
    crop_predictions = []
    if st.session_state.wizard_data['crop_predictions']:
        for pred in st.session_state.wizard_data['crop_predictions']:
            yield_pred = predict_yield(pred['crop'])
            if yield_pred:
                crop_predictions.append(yield_pred)
    
    if crop_predictions and len(crop_predictions) > 0:
        # Display yield forecast chart
        fig = create_yield_chart(crop_predictions)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No yield predictions available. Please go back and select crops first.")
        
        st.divider()
        
        # Detailed yield information
        st.subheader("📊 Detailed Yield Forecast")
        
        for pred in crop_predictions:
            with st.expander(f"{pred['crop'].upper()} - {pred['predicted_yield']:.0f} Tonnes/Ha"):
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("2026 Prediction", f"{pred['predicted_yield']:.0f} T/Ha")
                with col2:
                    st.metric("Historical Avg", f"{pred['avg_yield']:.0f} T/Ha")
                with col3:
                    change = ((pred['predicted_yield'] - pred['avg_yield']) / pred['avg_yield'] * 100)
                    st.metric("Change", f"{change:+.1f}%")
                
                st.info(f"📈 Model R² Score: {pred['r2_score']:.4f} (Historical data: {pred['min_year']}-{pred['max_year']})")
    
    st.divider()
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key='back_step3'):
            st.session_state.current_step = 2
            st.rerun()
    
    with col2:
        if st.button("➡️ Next: Generate Report", use_container_width=True, key='next_step3'):
            st.session_state.current_step = 4
            st.rerun()

# ============================================================================
# STEP 4: GENERATE REPORT
# ============================================================================

elif st.session_state.current_step == 4:
    st.markdown("<div class='step-header'><div class='step-number'>4</div><h2>Generate Report</h2><p>Create a comprehensive PDF report</p></div>", unsafe_allow_html=True)
    
    st.subheader("📋 Report Summary")
    
    # Summary information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Location & Weather:**")
        st.write(f"- Governorate: {st.session_state.wizard_data['governorate']}")
        st.write(f"- Temperature: {st.session_state.wizard_data['weather']['temperature']:.1f}°C")
        st.write(f"- Humidity: {st.session_state.wizard_data['weather']['humidity']:.1f}%")
        st.write(f"- Rainfall: {st.session_state.wizard_data['weather']['rainfall']:.1f} mm")
    
    with col2:
        st.write("**Soil Properties:**")
        st.write(f"- Nitrogen (N): {st.session_state.wizard_data['n']} mg/kg")
        st.write(f"- Phosphorus (P): {st.session_state.wizard_data['p']} mg/kg")
        st.write(f"- Potassium (K): {st.session_state.wizard_data['k']} mg/kg")
        st.write(f"- pH: {st.session_state.wizard_data['ph']:.2f}")
    
    st.divider()
    
    st.subheader("🎯 Recommended Crops")
    
    for i, pred in enumerate(st.session_state.wizard_data['crop_predictions'], 1):
        st.write(f"**#{i} {pred['crop'].upper()}** - Confidence: {pred['confidence']*100:.1f}%")
    
    st.divider()
    
    # Export options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate PDF Report", use_container_width=True, key='generate_pdf'):
            st.info("📄 PDF generation feature coming soon!")
    
    with col2:
        if st.button("📊 Download Data as CSV", use_container_width=True, key='download_csv'):
            st.info("📊 CSV export feature coming soon!")
    
    st.divider()
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key='back_step4'):
            st.session_state.current_step = 3
            st.rerun()
    
    with col2:
        if st.button("🔄 Start Over", use_container_width=True, key='restart'):
            st.session_state.current_step = 1
            st.session_state.wizard_data = {
                'governorate': None,
                'weather': None,
                'n': None,
                'p': None,
                'k': None,
                'ph': None,
                'crop_predictions': None
            }
            st.rerun()
    
    with col3:
        st.success("✅ Wizard Complete!")

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
    <div style='text-align: center; color: #7f8c8d; font-size: 0.9rem; padding: 20px;'>
        <p>🌾 <b>EgyptAgri-Pulse</b> | Precision Agriculture for National Food Security</p>
        <p>Version 2.0 | Step-by-Step Wizard | Real Data | Real Models</p>
    </div>
""", unsafe_allow_html=True)
