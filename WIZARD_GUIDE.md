# EgyptAgri-Pulse Wizard: Step-by-Step User Guide

## Overview

The EgyptAgri-Pulse Wizard is an interactive, step-by-step guide that helps Egyptian farmers make data-driven decisions about crop selection and yield forecasting. The wizard uses real datasets and advanced ML models to provide personalized recommendations.

---

## 🚀 Quick Start

### Run the Wizard

```bash
cd egypt-agri-pulse
source venv/bin/activate
streamlit run app_wizard.py
```

Then open: **http://localhost:8501**

---

## 📋 Wizard Steps

### **Step 1: Select Your Governorate** 🗺️

**What You Do:**
- View an interactive map of Egypt
- Select your governorate by clicking on the map or using the dropdown
- View real-time weather and climate data for your location

**What You See:**
- 🌡️ Temperature (°C)
- 💨 Humidity (%)
- 💧 Rainfall (mm)
- 🧪 Soil pH

**Data Carried Forward:**
- Selected governorate
- Weather/climate conditions

**Next Step:** Click "➡️ Next: Enter Soil Data"

---

### **Step 2: Enter Soil Properties** 🧪

**What You Do:**
- Adjust sliders for your soil nutrients:
  - **Nitrogen (N)**: 0-140 mg/kg
  - **Phosphorus (P)**: 5-145 mg/kg
  - **Potassium (K)**: 5-205 mg/kg
  - **Soil pH**: 3.5-10.0

**Tip:** Use soil test results from your local agricultural extension office for accurate values.

**What You Get:**
- **Top 3 Recommended Crops** with confidence scores
- **Detailed Explanations** for each recommendation
- Comparison of your soil conditions vs. crop requirements

**Example Explanation:**
```
✓ Nitrogen level (60) is suitable for Cotton
✓ Phosphorus level (30) supports Cotton growth
⚠ Potassium level (200) is higher than ideal
✓ Temperature (22°C) is ideal for Cotton
✓ Humidity (82%) is suitable for Cotton
✓ Rainfall (203mm) matches Cotton requirements
✓ Soil pH (6.5) is optimal for Cotton
```

**Data Carried Forward:**
- Soil nutrients (N, P, K, pH)
- Top 3 crop recommendations
- Confidence scores and explanations

**Next Step:** Click "➡️ Next: View Yield Forecast"

---

### **Step 3: Yield Forecasting** 📊

**What You See:**
- **2026 Yield Predictions** for your 3 recommended crops
- **Historical Average** yield for comparison
- **Percentage Change** (vs. historical average)
- **Model Reliability** (R² Score)

**Chart Interpretation:**
- Green bars = 2026 predicted yield
- Gray bars = Historical average yield
- Taller green bars = Better expected performance

**Example:**
```
Cotton:
- 2026 Prediction: 3,500 Tonnes/Ha
- Historical Avg: 3,200 Tonnes/Ha
- Change: +9.4% (better than average!)
- Model R²: 0.7823 (highly reliable)
```

**Data Carried Forward:**
- Yield predictions for all 3 crops
- Historical context and trends

**Next Step:** Click "➡️ Next: Generate Report"

---

### **Step 4: Generate Report** 📄

**What You See:**
- Complete summary of your analysis:
  - Location & weather data
  - Soil properties
  - Recommended crops
  - Yield forecasts

**Export Options:**
- 📄 **PDF Report**: Download professional report
- 📊 **CSV Data**: Export raw data for analysis

**Report Contents:**
1. Executive Summary
2. Location & Weather Analysis
3. Soil Properties Assessment
4. Crop Recommendations (with explanations)
5. Yield Forecasts (2026)
6. Historical Context
7. Recommendations & Next Steps

---

## 🎯 Key Features

### 1. **Interactive Map** 🗺️
- Folium-based interactive Egypt map
- 22 governorate markers with coordinates
- Click to select or use dropdown
- Real-time weather overlay

### 2. **Soil Input Interface** 🧪
- Intuitive sliders for soil nutrients
- Real-time value display
- Comparison with crop requirements
- Validation and guidance

### 3. **AI-Powered Recommendations** 🤖
- **Ensemble ML Models:**
  - XGBoost: 98.86% accuracy
  - Random Forest: 99.55% accuracy
  - Ensemble voting for final prediction
- **22 Crop Types Supported**
- **Confidence Scores** (0-100%)

### 4. **Detailed Explanations** 📝
- Why each crop was recommended
- Soil factor analysis
- Weather suitability
- Nutrient level assessment
- pH compatibility

### 5. **Yield Forecasting** 📈
- Time-series analysis (1990-2024)
- Per-crop regression models
- 2026 predictions
- Historical trend comparison
- R² reliability scores

### 6. **Report Generation** 📋
- Professional PDF export
- Comprehensive data analysis
- Actionable recommendations
- CSV data export

---

## 📊 Data Sources

### Crop Recommendation Dataset
- **2,200 samples** with soil and weather data
- **22 crop types** with balanced distribution
- Features: N, P, K, temperature, humidity, pH, rainfall

### Yield Dataset
- **2,645 historical records** (1990-2024)
- **78 crop varieties** with production data
- Area harvested, production, and yield metrics

### Governorate Data
- **22 Egyptian governorates** with coordinates
- Latitude/longitude for map visualization
- Weather data integration

---

## 🔍 Understanding the Recommendations

### Confidence Scores

**How They Work:**
- Ensemble of XGBoost and Random Forest models
- Average of both model probabilities
- Range: 0% (unlikely) to 100% (highly likely)

**Interpretation:**
- **90-100%**: Excellent match for your conditions
- **75-89%**: Good match, recommended
- **60-74%**: Acceptable match, consider
- **<60%**: Poor match, not recommended

### Explanations

Each recommendation includes 7 factors:

1. **Nitrogen (N)** - Plant protein synthesis
2. **Phosphorus (P)** - Root development and energy
3. **Potassium (K)** - Water regulation and disease resistance
4. **Temperature** - Growth rate and crop development
5. **Humidity** - Water availability and disease risk
6. **Rainfall** - Water supply for crop growth
7. **Soil pH** - Nutrient availability and uptake

---

## 📈 Yield Forecast Interpretation

### R² Score
- Measures model reliability
- Range: 0 (unreliable) to 1 (perfect)
- **>0.7**: Highly reliable
- **0.5-0.7**: Moderately reliable
- **<0.5**: Use with caution

### Prediction Accuracy
- Based on 35 years of historical data
- Accounts for trends and seasonal patterns
- Considers crop-specific factors

### Historical Context
- Shows 5-year average for comparison
- Identifies trends (increasing/decreasing)
- Provides confidence intervals

---

## 💡 Tips for Best Results

### 1. **Accurate Soil Testing**
- Get soil tested by local agricultural extension
- Use recent test results (within 1 year)
- Test multiple locations if field is large

### 2. **Consider Local Conditions**
- Account for irrigation availability
- Consider market demand
- Factor in pest/disease history

### 3. **Use Multiple Recommendations**
- Don't rely solely on top crop
- Consider #2 and #3 options
- Diversify if possible

### 4. **Monitor Predictions**
- Track actual yields vs. predictions
- Adjust inputs based on results
- Provide feedback for model improvement

### 5. **Combine with Expert Advice**
- Consult local agricultural experts
- Consider traditional knowledge
- Validate recommendations with experience

---

## ⚙️ Technical Details

### Models Used

**Crop Recommendation:**
- **XGBoost**: Gradient boosting classifier
  - 100 estimators, max depth 6
  - Accuracy: 98.86%
  
- **Random Forest**: Ensemble classifier
  - 100 trees, max depth 15
  - Accuracy: 99.55%

**Yield Forecasting:**
- **Linear Regression**: Time-series models
  - One model per crop
  - R² scores: 0.42-0.84

### Data Processing

1. **Feature Normalization**: Standardized to 0-1 range
2. **Train-Test Split**: 80-20 stratified split
3. **Ensemble Voting**: Average probability method
4. **Time-Series Analysis**: Trend extraction and forecasting

---

## 🐛 Troubleshooting

### Map Not Loading
- Refresh the page
- Check internet connection
- Try a different browser

### Recommendations Not Appearing
- Ensure all soil inputs are filled
- Check that values are within valid ranges
- Try adjusting values slightly

### Yield Forecast Not Available
- Crop may not have historical data
- Try a different crop from top 3
- Check model R² score for reliability

### Export Not Working
- Check browser download settings
- Ensure pop-ups are not blocked
- Try a different browser

---

## 📞 Support & Feedback

### Report Issues
- Document the issue with screenshots
- Note the step where issue occurred
- Provide soil data and location

### Provide Feedback
- Share your experience
- Suggest improvements
- Report inaccurate predictions

### Request Features
- Additional crops
- More detailed analysis
- Integration with other tools

---

## 🌾 Agricultural Best Practices

### Soil Management
- Rotate crops annually
- Add organic matter regularly
- Test soil every 2-3 years
- Maintain proper pH (6.0-7.5 for most crops)

### Nutrient Management
- Balance N, P, K ratios
- Use organic and inorganic fertilizers
- Monitor nutrient deficiencies
- Consider slow-release options

### Water Management
- Irrigate based on rainfall
- Maintain soil moisture (60-80%)
- Prevent waterlogging
- Mulch to retain moisture

### Pest & Disease Management
- Monitor crops regularly
- Use integrated pest management
- Rotate crops to break pest cycles
- Use resistant varieties

---

## 📚 Additional Resources

### Egyptian Agricultural Resources
- Ministry of Agriculture & Land Reclamation
- Agricultural Research Center (ARC)
- Local Extension Offices
- Farmer Cooperatives

### Online Resources
- FAO Crop Information
- CGIAR Research Programs
- Agricultural Databases
- Weather Services

---

## 🔄 Workflow Example

### Scenario: Farmer in Fayoum Governorate

**Step 1: Location**
- Select Fayoum from map
- View weather: 22°C, 82% humidity, 203mm rainfall

**Step 2: Soil Input**
- Enter soil test: N=60, P=30, K=200, pH=6.5
- Get recommendations: Cotton (95%), Wheat (87%), Maize (76%)

**Step 3: Yield Forecast**
- Cotton 2026: 3,500 T/Ha (vs. 3,200 avg) = +9.4%
- Wheat 2026: 8,200 T/Ha (vs. 7,900 avg) = +3.8%
- Maize 2026: 9,100 T/Ha (vs. 8,800 avg) = +3.4%

**Step 4: Decision**
- Choose Cotton (highest confidence + yield increase)
- Plan irrigation for rainfall deficit
- Prepare field for planting

---

## 📊 Expected Outcomes

### Crop Selection
- More accurate crop choice
- Better alignment with soil conditions
- Reduced crop failure risk
- Improved yield potential

### Yield Optimization
- Data-driven forecasting
- Historical context
- Trend analysis
- Risk assessment

### Resource Efficiency
- Optimal nutrient use
- Water management
- Labor planning
- Cost reduction

---

## 🎓 Learning Resources

### Understanding Soil Nutrients
- **Nitrogen (N)**: Leaf growth, protein synthesis
- **Phosphorus (P)**: Root development, energy transfer
- **Potassium (K)**: Water regulation, disease resistance

### Interpreting Weather Data
- **Temperature**: Affects growth rate and crop development
- **Humidity**: Influences disease risk and water availability
- **Rainfall**: Determines irrigation needs
- **pH**: Affects nutrient availability

### Reading Yield Forecasts
- Compare 2026 prediction vs. historical average
- Check R² score for model reliability
- Consider trend direction (increasing/decreasing)
- Factor in local conditions

---

**Version**: 2.0 | **Last Updated**: April 28, 2026

🌾 **EgyptAgri-Pulse Wizard: Precision Agriculture for National Food Security** 🌾
