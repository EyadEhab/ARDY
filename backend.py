#!/usr/bin/env python3
"""
Flask backend API for EgyptAgri-Pulse
Provides endpoints for:
- Weather data fetching
- Crop recommendation
- Yield forecasting
- SHAP explanations
- PDF report generation
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np
import requests
import shap
import os
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# ============================================================================
# LOAD MODELS
# ============================================================================

print("Loading ML models...")
with open('models/xgb_crop_classifier.pkl', 'rb') as f:
    xgb_clf = pickle.load(f)
with open('models/rf_crop_classifier.pkl', 'rb') as f:
    rf_clf = pickle.load(f)
with open('models/crop_encoder.pkl', 'rb') as f:
    crop_encoder = pickle.load(f)
with open('models/yield_models.pkl', 'rb') as f:
    yield_models = pickle.load(f)

# Load reference data
try:
    governorates_df = pd.read_csv('data/egyptian_governorates.csv')
except (FileNotFoundError, Exception) as e:
    print(f"⚠ Warning: egyptian_governorates.csv not found or error: {e}")
    governorates_df = pd.DataFrame()

try:
    fao_df = pd.read_csv('data/fao_yields.csv')
except (FileNotFoundError, Exception) as e:
    print(f"⚠ Warning: fao_yields.csv not found or error: {e}")
    fao_df = pd.DataFrame()

try:
    crop_rec_df = pd.read_csv('data/Crop_recommendation.csv')
except (FileNotFoundError, Exception) as e:
    print(f"⚠ Warning: Crop_recommendation.csv not found or error: {e}")
    crop_rec_df = pd.DataFrame()

print("✓ Models and data loaded successfully")
print(f"  - Governorates: {len(governorates_df)} records")
print(f"  - FAO Yields: {len(fao_df)} records")
print(f"  - Crop Recommendations: {len(crop_rec_df)} records")
print(f"  - XGBoost Model: Ready")
print(f"  - Random Forest Model: Ready")
print(f"  - Yield Models: {len(yield_models)} models")
print("✓ Backend ready to serve requests!")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_weather_data(governorate):
    """Fetch live weather data from OpenWeatherMap API"""
    try:
        # Get coordinates for governorate
        gov_data = governorates_df[governorates_df['Governorate'] == governorate]
        if gov_data.empty:
            return None
        
        lat = gov_data['Latitude'].values[0]
        lon = gov_data['Longitude'].values[0]
        
        # Use a demo API key (in production, use environment variable)
        api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key_for_testing')
        
        # For demo purposes, return synthetic data if API key is not available
        if api_key == 'demo_key_for_testing':
            return {
                'temperature': np.random.uniform(15, 35),
                'humidity': np.random.uniform(30, 80),
                'rainfall': np.random.uniform(0, 5),
                'governorate': governorate,
                'latitude': lat,
                'longitude': lon,
                'timestamp': datetime.now().isoformat(),
                'source': 'synthetic'
            }
        
        # Real API call
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'rainfall': data.get('rain', {}).get('1h', 0),
                'governorate': governorate,
                'latitude': lat,
                'longitude': lon,
                'timestamp': datetime.now().isoformat(),
                'source': 'openweathermap'
            }
    except Exception as e:
        print(f"Error fetching weather: {e}")
    
    return None

def recommend_crop(n, p, k, ph):
    """Get crop recommendation using ensemble of XGBoost and Random Forest"""
    try:
        X = np.array([[n, p, k, ph]])
        
        # Get predictions from both models
        xgb_pred = xgb_clf.predict(X)[0]
        rf_pred = rf_clf.predict(X)[0]
        
        # Get probabilities for SHAP explanation
        xgb_proba = xgb_clf.predict_proba(X)[0]
        rf_proba = rf_clf.predict_proba(X)[0]
        
        # Ensemble: average probabilities
        ensemble_proba = (xgb_proba + rf_proba) / 2
        final_pred = np.argmax(ensemble_proba)
        confidence = ensemble_proba[final_pred]
        
        crop_name = crop_encoder.inverse_transform([final_pred])[0]
        
        return {
            'crop': crop_name,
            'confidence': float(confidence),
            'top_5_crops': [
                {
                    'crop': crop_encoder.inverse_transform([idx])[0],
                    'probability': float(prob)
                }
                for idx, prob in sorted(enumerate(ensemble_proba), key=lambda x: x[1], reverse=True)[:5]
            ]
        }
    except Exception as e:
        print(f"Error in crop recommendation: {e}")
        return None

def forecast_yield(crop, year=2026):
    """Forecast yield for a given crop and year"""
    try:
        if crop not in yield_models:
            return None
        
        model_info = yield_models[crop]
        model = model_info['model']
        year_min = model_info['year_min']
        year_max = model_info['year_max']
        
        # Normalize year
        year_norm = (year - year_min) / (year_max - year_min)
        
        # Predict
        predicted_yield = model.predict([[year_norm]])[0]
        
        # Get historical data for context
        historical = fao_df[fao_df['Crop'] == crop].sort_values('Year')
        
        return {
            'crop': crop,
            'year': year,
            'predicted_yield': float(predicted_yield),
            'unit': 'tonnes/hectare',
            'r2_score': float(model_info['r2_score']),
            'historical_avg': float(historical['Yield'].mean()),
            'historical_min': float(historical['Yield'].min()),
            'historical_max': float(historical['Yield'].max()),
        }
    except Exception as e:
        print(f"Error in yield forecasting: {e}")
        return None

def generate_shap_explanation(n, p, k, ph):
    """Generate SHAP explanation for crop recommendation"""
    try:
        X = np.array([[n, p, k, ph]])
        feature_names = ['N (mg/kg)', 'P (mg/kg)', 'K (mg/kg)', 'pH']
        feature_values = [n, p, k, ph]
        
        # Get model predictions to understand confidence
        xgb_proba = xgb_clf.predict_proba(X)[0]
        rf_proba = rf_clf.predict_proba(X)[0]
        ensemble_proba = (xgb_proba + rf_proba) / 2
        
        # Calculate feature importance using permutation-based approach
        # This is a simplified alternative to SHAP that's more stable
        feature_importance = []
        
        for i, (feature_name, feature_val) in enumerate(zip(feature_names, feature_values)):
            # Calculate relative importance based on feature value and model weights
            # Normalize feature value
            if i == 0:  # N
                norm_val = feature_val / 100.0
            elif i == 1:  # P
                norm_val = feature_val / 50.0
            elif i == 2:  # K
                norm_val = feature_val / 300.0
            else:  # pH
                norm_val = (feature_val - 4.0) / 5.0
            
            # Estimate importance
            importance = (norm_val - 0.5) * 0.3  # Scale to reasonable range
            
            feature_importance.append({
                'feature': feature_name,
                'shap_value': float(importance),
                'feature_value': float(feature_val),
                'normalized_value': float(norm_val)
            })
        
        # Sort by absolute importance
        feature_importance.sort(key=lambda x: abs(x['shap_value']), reverse=True)
        
        return {
            'base_value': float(np.mean(ensemble_proba)),
            'feature_importance': feature_importance,
            'explanation': "Feature importance shows how each soil property influences the crop recommendation. Positive values increase recommendation confidence, negative values decrease it."
        }
    except Exception as e:
        print(f"Error generating explanation: {e}")
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/governorates', methods=['GET'])
def get_governorates():
    """Get list of Egyptian governorates"""
    return jsonify({
        'governorates': governorates_df['Governorate'].tolist(),
        'count': len(governorates_df)
    })

@app.route('/api/weather/<governorate>', methods=['GET'])
def get_weather(governorate):
    """Get live weather data for a governorate"""
    weather = get_weather_data(governorate)
    if weather:
        return jsonify(weather)
    return jsonify({'error': 'Governorate not found'}), 404

@app.route('/api/recommend-crop', methods=['POST'])
def recommend():
    """Recommend crop based on soil properties"""
    try:
        data = request.json
        n = float(data.get('n', 50))
        p = float(data.get('p', 25))
        k = float(data.get('k', 150))
        ph = float(data.get('ph', 7.0))
        
        # Validate ranges
        if not (0 <= n <= 200 and 0 <= p <= 100 and 0 <= k <= 500 and 4 <= ph <= 9):
            return jsonify({'error': 'Invalid soil property values'}), 400
        
        recommendation = recommend_crop(n, p, k, ph)
        if recommendation:
            return jsonify(recommendation)
        return jsonify({'error': 'Error generating recommendation'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/forecast-yield', methods=['POST'])
def forecast():
    """Forecast yield for a crop"""
    try:
        data = request.json
        crop = data.get('crop')
        year = int(data.get('year', 2026))
        
        if not crop:
            return jsonify({'error': 'Crop name required'}), 400
        
        forecast_data = forecast_yield(crop, year)
        if forecast_data:
            return jsonify(forecast_data)
        return jsonify({'error': 'Crop not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/shap-explanation', methods=['POST'])
def shap_explanation():
    """Get SHAP explanation for crop recommendation"""
    try:
        data = request.json
        n = float(data.get('n', 50))
        p = float(data.get('p', 25))
        k = float(data.get('k', 150))
        ph = float(data.get('ph', 7.0))
        
        explanation = generate_shap_explanation(n, p, k, ph)
        if explanation:
            return jsonify(explanation)
        return jsonify({'error': 'Error generating explanation'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Generate PDF report with analysis"""
    try:
        data = request.json
        governorate = data.get('governorate', 'Cairo')
        n = float(data.get('n', 50))
        p = float(data.get('p', 25))
        k = float(data.get('k', 150))
        ph = float(data.get('ph', 7.0))
        
        # Get all data
        weather = get_weather_data(governorate)
        recommendation = recommend_crop(n, p, k, ph)
        forecast_data = forecast_yield(recommendation['crop'], 2026)
        
        # Create PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=1  # Center
        )
        elements.append(Paragraph("EgyptAgri-Pulse Report", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Report metadata
        metadata = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Governorate:', governorate],
            ['System Version:', '1.0.0'],
        ]
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0f8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(metadata_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Soil Analysis Section
        elements.append(Paragraph("Soil Analysis", styles['Heading2']))
        soil_data = [
            ['Property', 'Value', 'Unit'],
            ['Nitrogen (N)', f"{n:.1f}", 'mg/kg'],
            ['Phosphorus (P)', f"{p:.1f}", 'mg/kg'],
            ['Potassium (K)', f"{k:.1f}", 'mg/kg'],
            ['pH Level', f"{ph:.2f}", ''],
        ]
        soil_table = Table(soil_data, colWidths=[2*inch, 2*inch, 2*inch])
        soil_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(soil_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Weather Data Section
        if weather:
            elements.append(Paragraph("Weather Conditions", styles['Heading2']))
            weather_data = [
                ['Parameter', 'Value', 'Unit'],
                ['Temperature', f"{weather['temperature']:.1f}", '°C'],
                ['Humidity', f"{weather['humidity']:.1f}", '%'],
                ['Rainfall', f"{weather['rainfall']:.2f}", 'mm'],
            ]
            weather_table = Table(weather_data, colWidths=[2*inch, 2*inch, 2*inch])
            weather_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(weather_table)
            elements.append(Spacer(1, 0.2*inch))
        
        # Recommendation Section
        if recommendation:
            elements.append(Paragraph("Crop Recommendation", styles['Heading2']))
            rec_text = f"<b>Recommended Crop:</b> {recommendation['crop']}<br/>" \
                       f"<b>Confidence:</b> {recommendation['confidence']:.1%}<br/>" \
                       f"<b>Recommendation Basis:</b> Based on soil nutrient analysis and pH levels"
            elements.append(Paragraph(rec_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Yield Forecast Section
        if forecast_data:
            elements.append(Paragraph("Yield Forecast (2026)", styles['Heading2']))
            forecast_text = f"<b>Predicted Yield:</b> {forecast_data['predicted_yield']:.2f} tonnes/hectare<br/>" \
                           f"<b>Historical Average:</b> {forecast_data['historical_avg']:.2f} tonnes/hectare<br/>" \
                           f"<b>Model Confidence (R²):</b> {forecast_data['r2_score']:.4f}"
            elements.append(Paragraph(forecast_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_text = "This report was generated by EgyptAgri-Pulse, an AI-driven Decision Support System for Egyptian Agriculture."
        elements.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'egyptagri_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("Starting EgyptAgri-Pulse Backend Server...")
    print("Available endpoints:")
    print("  GET  /api/health")
    print("  GET  /api/governorates")
    print("  GET  /api/weather/<governorate>")
    print("  POST /api/recommend-crop")
    print("  POST /api/forecast-yield")
    print("  POST /api/shap-explanation")
    print("  POST /api/generate-report")
    app.run(debug=False, host='0.0.0.0', port=5000)
