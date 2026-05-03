#!/usr/bin/env python3
"""
EgyptAgri-Pulse: Streamlit Interactive Dashboard
An AI-driven Decision Support System for Egyptian Agriculture
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="EgyptAgri-Pulse",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3em;
        color: #1f4788;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 1.2em;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f4788;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# BACKEND CONFIGURATION
# ============================================================================

import os
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
PLANT_DOCTOR_URL = os.getenv("PLANT_DOCTOR_URL", "http://localhost:8000")

@st.cache_resource
def get_governorates():
    """Fetch list of Egyptian governorates"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/governorates", timeout=5)
        if response.status_code == 200:
            return response.json()['governorates']
    except:
        pass
    return ['Cairo', 'Giza', 'Alexandria', 'Aswan', 'Luxor']

# ============================================================================
# MAIN INTERFACE
# ============================================================================

# Header
st.markdown('<div class="main-header">🌾 EgyptAgri-Pulse</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Driven Decision Support System for Egyptian Agriculture</div>', unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("## 📊 Navigation")
page = st.sidebar.radio(
    "Select a module:",
    ["🏠 Dashboard", "🌡️ Weather & Environment", "🌱 Crop Recommendation", "📈 Yield Forecasting", "🩺 Plant Doctor (AI Diagnosis)", "📋 Report Generator"]
)

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================

if page == "🏠 Dashboard":
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("System Status", "🟢 Active", "All models loaded")
    
    with col2:
        st.metric("Crops Supported", "22", "Egyptian & strategic crops")
    
    with col3:
        st.metric("Historical Data", "1990-2024", "34 years of FAO data")
    
    st.markdown("---")
    
    st.markdown("### 📖 About EgyptAgri-Pulse")
    st.write("""
    EgyptAgri-Pulse is a comprehensive **Digital Twin of the Egyptian agricultural landscape**, 
    bridging the gap between:
    
    - **🌍 Real-time Environmental Intelligence** - Live weather data from OpenWeatherMap
    - **🧪 Biochemical Soil Science** - Precision analysis of N, P, K, and pH levels
    - **📊 Macro-economic Historical Trends** - 34 years of FAO yield data (1990-2024)
    
    ### 🎯 Key Features
    
    1. **Live Environmental Telemetry** - Real-time weather integration by governorate
    2. **Precision Crop Recommendation** - Ensemble ML models (XGBoost + Random Forest)
    3. **National Yield Forecasting** - Time-series regression for 2026 predictions
    4. **Explainable AI (SHAP)** - Transparent reasoning for recommendations
    5. **Geospatial Mapping** - Interactive maps of Egyptian governorates
    6. **Automated Reporting** - PDF export with complete analysis
    
    ### 🏗️ Technical Architecture
    
    **Layer 1: Live Environmental Telemetry**
    - Fetches current temperature, humidity, and rainfall
    - Localized to Egyptian governorates
    
    **Layer 2: Precision Crop Recommendation**
    - Ensemble of XGBoost and Random Forest classifiers
    - Processes N, P, K levels and pH values
    - Recommends optimal crop from 22 species
    
    **Layer 3: National Yield Forecasting**
    - Time-series regression analysis
    - 34 years of historical productivity data
    - Predicts expected yield for 2026
    
    **Layer 4: Intelligent Interactive Dashboard**
    - Streamlit-based deployment
    - Folium geospatial mapping
    - SHAP explainability integration
    - PDF report generation
    """)
    
    st.markdown("---")
    st.markdown("### 📈 System Overview")
    
    # Create a simple architecture diagram
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🌡️ Layer 1</h3>
            <p><b>Weather Telemetry</b></p>
            <p>Real-time API integration</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🌱 Layer 2</h3>
            <p><b>Crop Recommendation</b></p>
            <p>ML Ensemble Models</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Layer 3</h3>
            <p><b>Yield Forecasting</b></p>
            <p>Time-Series Analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📋 Layer 4</h3>
            <p><b>Dashboard & Reports</b></p>
            <p>Visualization & Export</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE 2: WEATHER & ENVIRONMENT
# ============================================================================

elif page == "🌡️ Weather & Environment":
    st.markdown("---")
    st.markdown("### 🌍 Live Weather Data by Governorate")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        governorate = st.selectbox(
            "Select Egyptian Governorate:",
            get_governorates(),
            key="weather_gov"
        )
    
    with col2:
        if st.button("🔄 Refresh Weather Data"):
            st.rerun()
    
    # Fetch weather data
    try:
        response = requests.get(f"{BACKEND_URL}/api/weather/{governorate}", timeout=5)
        if response.status_code == 200:
            weather = response.json()
            
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🌡️ Temperature", f"{weather['temperature']:.1f}°C")
            
            with col2:
                st.metric("💧 Humidity", f"{weather['humidity']:.1f}%")
            
            with col3:
                st.metric("🌧️ Rainfall", f"{weather['rainfall']:.2f}mm")
            
            with col4:
                st.metric("📍 Location", governorate)
            
            st.markdown("---")
            
            # Display map
            st.markdown("### 📍 Governorate Location")
            m = folium.Map(
                location=[weather['latitude'], weather['longitude']],
                zoom_start=8,
                tiles="OpenStreetMap"
            )
            folium.Marker(
                location=[weather['latitude'], weather['longitude']],
                popup=f"{governorate}<br>Weather Station",
                icon=folium.Icon(color='blue', icon='cloud')
            ).add_to(m)
            st_folium(m, width=700, height=500)
            
            # Weather interpretation
            st.markdown("---")
            st.markdown("### 🌤️ Weather Analysis")
            
            temp = weather['temperature']
            humidity = weather['humidity']
            
            if temp < 10:
                temp_status = "❄️ Cold - Suitable for winter crops"
            elif 10 <= temp < 20:
                temp_status = "🌤️ Cool - Optimal for many crops"
            elif 20 <= temp < 30:
                temp_status = "☀️ Warm - Good growing conditions"
            else:
                temp_status = "🔥 Hot - May require irrigation"
            
            if humidity < 30:
                humidity_status = "🏜️ Dry - Irrigation recommended"
            elif 30 <= humidity < 60:
                humidity_status = "✅ Moderate - Good conditions"
            else:
                humidity_status = "💧 Humid - Monitor for diseases"
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Temperature:** {temp_status}")
            with col2:
                st.info(f"**Humidity:** {humidity_status}")
        else:
            st.error("Could not fetch weather data")
    except Exception as e:
        st.error(f"Error: {e}")

# ============================================================================
# PAGE 3: CROP RECOMMENDATION
# ============================================================================

elif page == "🌱 Crop Recommendation":
    st.markdown("---")
    st.markdown("### 🌱 Precision Crop Recommendation System")
    st.write("Enter soil properties to get AI-powered crop recommendations")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n = st.slider(
            "Nitrogen (N) - mg/kg",
            min_value=0.0,
            max_value=200.0,
            value=50.0,
            step=1.0,
            help="Nitrogen content in soil"
        )
        p = st.slider(
            "Phosphorus (P) - mg/kg",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=0.5,
            help="Phosphorus content in soil"
        )
    
    with col2:
        k = st.slider(
            "Potassium (K) - mg/kg",
            min_value=0.0,
            max_value=500.0,
            value=150.0,
            step=5.0,
            help="Potassium content in soil"
        )
        ph = st.slider(
            "pH Level",
            min_value=4.0,
            max_value=9.0,
            value=7.0,
            step=0.1,
            help="Soil pH (4=acidic, 7=neutral, 9=alkaline)"
        )
    
    st.markdown("---")
    
    if st.button("🔍 Get Crop Recommendation", key="recommend_btn"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/recommend-crop",
                json={'n': n, 'p': p, 'k': k, 'ph': ph},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                
                st.markdown("### ✅ Recommendation Result")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="success-box">
                        <h2>🌾 {result['crop']}</h2>
                        <p><b>Confidence Score:</b> {result['confidence']:.1%}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("Model Confidence", f"{result['confidence']:.1%}")
                
                st.markdown("---")
                st.markdown("### 🏆 Top 5 Alternative Crops")
                
                top_crops = pd.DataFrame(result['top_5_crops'])
                
                fig = px.bar(
                    top_crops,
                    x='crop',
                    y='probability',
                    title='Crop Recommendation Probabilities',
                    labels={'crop': 'Crop', 'probability': 'Probability'},
                    color='probability',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Get SHAP explanation
                st.markdown("---")
                st.markdown("### 🧠 Explainable AI (SHAP) Analysis")
                
                try:
                    shap_response = requests.post(
                        f"{BACKEND_URL}/api/shap-explanation",
                        json={'n': n, 'p': p, 'k': k, 'ph': ph},
                        timeout=5
                    )
                    
                    if shap_response.status_code == 200:
                        shap_result = shap_response.json()
                        
                        st.info(shap_result['explanation'])
                        
                        # Feature importance
                        features_df = pd.DataFrame(shap_result['feature_importance'])
                        
                        fig = px.bar(
                            features_df,
                            x='feature',
                            y='shap_value',
                            title='Feature Importance (SHAP Values)',
                            labels={'feature': 'Soil Property', 'shap_value': 'SHAP Value'},
                            color='shap_value',
                            color_continuous_scale='RdBu'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                except:
                    pass
            else:
                st.error("Error getting recommendation")
        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================================
# PAGE 4: YIELD FORECASTING
# ============================================================================

elif page == "📈 Yield Forecasting":
    st.markdown("---")
    st.markdown("### 📈 National Yield Forecasting for 2026")
    st.write("Predict crop yields based on 34 years of historical FAO data")
    
    st.markdown("---")
    
    # Load available crops
    try:
        fao_df = pd.read_csv('data/fao_yields.csv')
        available_crops = sorted(fao_df['Crop'].unique().tolist())
    except:
        available_crops = ['Wheat', 'Rice', 'Maize', 'Sugarcane', 'Tomato']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_crop = st.selectbox(
            "Select Crop for Yield Forecast:",
            available_crops,
            key="yield_crop"
        )
    
    with col2:
        forecast_year = st.number_input(
            "Forecast Year:",
            min_value=2025,
            max_value=2030,
            value=2026,
            step=1
        )
    
    st.markdown("---")
    
    if st.button("📊 Generate Yield Forecast", key="forecast_btn"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/forecast-yield",
                json={'crop': selected_crop, 'year': forecast_year},
                timeout=5
            )
            
            if response.status_code == 200:
                forecast = response.json()
                
                st.markdown("### ✅ Yield Forecast Result")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Predicted Yield (2026)",
                        f"{forecast['predicted_yield']:.2f}",
                        f"tonnes/hectare"
                    )
                
                with col2:
                    st.metric(
                        "Historical Average",
                        f"{forecast['historical_avg']:.2f}",
                        f"tonnes/hectare"
                    )
                
                with col3:
                    st.metric(
                        "Model Confidence (R²)",
                        f"{forecast['r2_score']:.4f}",
                        "Coefficient of determination"
                    )
                
                st.markdown("---")
                st.markdown("### 📊 Historical Yield Trends")
                
                # Create visualization
                crop_data = fao_df[fao_df['Crop'] == selected_crop].sort_values('Year')
                
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=crop_data['Year'],
                    y=crop_data['Yield'],
                    mode='lines+markers',
                    name='Historical Yield',
                    line=dict(color='#1f4788', width=3),
                    marker=dict(size=8)
                ))
                
                # Forecast point
                fig.add_trace(go.Scatter(
                    x=[forecast_year],
                    y=[forecast['predicted_yield']],
                    mode='markers',
                    name='Forecast (2026)',
                    marker=dict(size=15, color='#ff6b6b', symbol='star')
                ))
                
                fig.update_layout(
                    title=f"Yield Forecast for {selected_crop}",
                    xaxis_title="Year",
                    yaxis_title="Yield (tonnes/hectare)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                st.markdown("---")
                st.markdown("### 📊 Yield Statistics")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **Minimum Yield:** {forecast['historical_min']:.2f} tonnes/hectare
                    
                    **Maximum Yield:** {forecast['historical_max']:.2f} tonnes/hectare
                    """)
                
                with col2:
                    change = forecast['predicted_yield'] - forecast['historical_avg']
                    change_pct = (change / forecast['historical_avg']) * 100
                    
                    if change >= 0:
                        st.success(f"""
                        **Expected Change:** +{change:.2f} tonnes/hectare
                        
                        **Percentage Change:** +{change_pct:.1f}%
                        """)
                    else:
                        st.warning(f"""
                        **Expected Change:** {change:.2f} tonnes/hectare
                        
                        **Percentage Change:** {change_pct:.1f}%
                        """)
            else:
                st.error("Error generating forecast")
        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================================
# PAGE 5: PLANT DOCTOR (AI DIAGNOSIS)
# ============================================================================

elif page == "🩺 Plant Doctor (AI Diagnosis)":
    st.markdown("---")
    st.markdown("### 🩺 Plant Doctor: AI Crop Disease Diagnosis")
    st.write("Upload a photo of your crop leaf to identify diseases and get treatment recommendations.")
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader("📸 Choose a leaf image...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Display the uploaded image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(uploaded_file, caption="Uploaded Leaf Image", use_container_width=True)
        
        with col2:
            st.info("🔄 Processing image with EfficientNetB0...")
            
            if st.button("🔍 Run AI Diagnosis"):
                try:
                    # Prepare the file for sending
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    # Call Plant Doctor API
                    response = requests.post(f"{PLANT_DOCTOR_URL}/predict", files=files, timeout=20)
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display Results
                        st.markdown(f"### 📋 Diagnosis: **{result['disease']}**")
                        st.progress(float(result['confidence'].replace('%', '')) / 100)
                        st.write(f"**Confidence Level:** {result['confidence']}")
                        
                        st.markdown("---")
                        st.markdown("### 💊 Recommended Treatment")
                        st.success(result['treatment'])
                        
                        # Visual feedback based on health
                        if "Healthy" in result['disease']:
                            st.balloons()
                    else:
                        st.error(f"Error from API: {response.text}")
                except Exception as e:
                    st.error(f"Could not connect to Plant Doctor API. Make sure the Docker container is running on port 8000. Error: {e}")

# ============================================================================
# PAGE 6: REPORT GENERATOR
# ============================================================================

elif page == "📋 Report Generator":
    st.markdown("---")
    st.markdown("### 📋 Generate Comprehensive Analysis Report")
    st.write("Create a PDF report with complete soil analysis, weather data, and yield forecasts")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        governorate = st.selectbox(
            "Select Governorate:",
            get_governorates(),
            key="report_gov"
        )
        
        n = st.slider(
            "Nitrogen (N) - mg/kg",
            min_value=0.0,
            max_value=200.0,
            value=50.0,
            step=1.0,
            key="report_n"
        )
        
        p = st.slider(
            "Phosphorus (P) - mg/kg",
            min_value=0.0,
            max_value=100.0,
            value=25.0,
            step=0.5,
            key="report_p"
        )
    
    with col2:
        k = st.slider(
            "Potassium (K) - mg/kg",
            min_value=0.0,
            max_value=500.0,
            value=150.0,
            step=5.0,
            key="report_k"
        )
        
        ph = st.slider(
            "pH Level",
            min_value=4.0,
            max_value=9.0,
            value=7.0,
            step=0.1,
            key="report_ph"
        )
    
    st.markdown("---")
    
    if st.button("📥 Generate PDF Report", key="report_btn"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/generate-report",
                json={
                    'governorate': governorate,
                    'n': n,
                    'p': p,
                    'k': k,
                    'ph': ph
                },
                timeout=10
            )
            
            if response.status_code == 200:
                st.success("✅ Report generated successfully!")
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=response.content,
                    file_name=f"egyptagri_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Error generating report")
        except Exception as e:
            st.error(f"Error: {e}")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 50px;">
    <p><b>EgyptAgri-Pulse v1.0.0</b></p>
    <p>An AI-driven Decision Support System for National Food Security in Egypt</p>
    <p style="font-size: 0.9em;">© 2026 | Powered by Machine Learning & Geospatial Intelligence</p>
</div>
""", unsafe_allow_html=True)
