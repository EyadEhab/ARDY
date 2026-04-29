#!/usr/bin/env python3
"""
Test script for EgyptAgri-Pulse API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    print_section("Testing Health Endpoint")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    print("✓ Health check passed")

def test_governorates():
    print_section("Testing Governorates Endpoint")
    response = requests.get(f"{BASE_URL}/api/governorates")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total governorates: {data['count']}")
    print(f"First 5: {data['governorates'][:5]}")
    assert response.status_code == 200
    assert data['count'] == 22
    print("✓ Governorates endpoint passed")

def test_weather():
    print_section("Testing Weather Endpoint")
    response = requests.get(f"{BASE_URL}/api/weather/Cairo")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert 'temperature' in data
    assert 'humidity' in data
    print("✓ Weather endpoint passed")

def test_crop_recommendation():
    print_section("Testing Crop Recommendation Endpoint")
    payload = {
        'n': 60,
        'p': 30,
        'k': 200,
        'ph': 7.2
    }
    print(f"Input: {payload}")
    response = requests.post(f"{BASE_URL}/api/recommend-crop", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert 'crop' in data
    assert 'confidence' in data
    assert 'top_5_crops' in data
    print(f"✓ Crop recommendation passed - Recommended: {data['crop']}")

def test_yield_forecast():
    print_section("Testing Yield Forecast Endpoint")
    payload = {
        'crop': 'Wheat',
        'year': 2026
    }
    print(f"Input: {payload}")
    response = requests.post(f"{BASE_URL}/api/forecast-yield", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert 'predicted_yield' in data
    assert 'historical_avg' in data
    print(f"✓ Yield forecast passed - Predicted: {data['predicted_yield']:.2f} tonnes/hectare")

def test_shap_explanation():
    print_section("Testing SHAP Explanation Endpoint")
    payload = {
        'n': 60,
        'p': 30,
        'k': 200,
        'ph': 7.2
    }
    print(f"Input: {payload}")
    response = requests.post(f"{BASE_URL}/api/shap-explanation", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    assert response.status_code == 200
    assert 'base_value' in data
    assert 'feature_importance' in data
    print(f"✓ SHAP explanation passed")

def test_pdf_report():
    print_section("Testing PDF Report Generation")
    payload = {
        'governorate': 'Cairo',
        'n': 60,
        'p': 30,
        'k': 200,
        'ph': 7.2
    }
    print(f"Input: {payload}")
    response = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {len(response.content)} bytes")
    assert response.status_code == 200
    assert 'pdf' in response.headers.get('content-type', '').lower()
    
    # Save PDF for inspection
    with open('/tmp/test_report.pdf', 'wb') as f:
        f.write(response.content)
    print(f"✓ PDF report generated and saved to /tmp/test_report.pdf")

def main():
    print("\n" + "="*60)
    print("  EgyptAgri-Pulse API Test Suite")
    print("="*60)
    
    try:
        test_health()
        test_governorates()
        test_weather()
        test_crop_recommendation()
        test_yield_forecast()
        test_shap_explanation()
        test_pdf_report()
        
        print_section("All Tests Passed! ✓")
        print("\nAPI is working correctly and ready for use.")
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
