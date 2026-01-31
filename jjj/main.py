"""
Environmental Monitoring & Alert System - FastAPI Backend
Author: Environmental Monitoring Team
Date: January 2026
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import re
from datetime import datetime, timedelta
import os
from functools import lru_cache
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

# Import database and prediction modules
from database import (
    init_database, insert_weather_reading, get_historical_data,
    get_latest_reading, get_database_stats, insert_prediction, cleanup_old_data
)
from predictions import predict_next_hour, predict_multiple_hours, analyze_patterns

app = FastAPI(
    title="Environmental Monitoring & Alert System",
    description="A comprehensive web-based environmental monitoring system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

# Configuration
# SECURITY NOTE: API keys are loaded from environment variables to prevent accidental commits
# Never hardcode API keys in source code - always use environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_API_BASE = os.getenv("WEATHER_API_BASE", "https://api.weatherapi.com/v1")
OPENAQ_API_BASE = os.getenv("OPENAQ_API_BASE", "https://api.openaq.org/v2")

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
USE_AI_API = True  # AI-powered responses enabled!

# Cache for API responses (5 minutes)
cache = {}
CACHE_DURATION = 300  # seconds

# Initialize database
init_database()

# Monitored locations for automatic data collection
MONITORED_LOCATIONS = ['London', 'Mumbai', 'New Delhi', 'New York', 'Tokyo']

# ═══════════════════════════════════════════════════════════════════
# BACKGROUND SCHEDULER FOR AUTOMATIC DATA COLLECTION
# ═══════════════════════════════════════════════════════════════════

def fetch_and_store_data():
    """Background task to fetch and store weather data for monitored locations"""
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Fetching data for monitored locations...")

    for location in MONITORED_LOCATIONS:
        try:
            url = f"{WEATHER_API_BASE}/current.json"
            params = {
                'key': WEATHER_API_KEY,
                'q': location,
                'aqi': 'yes'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                reading_id = insert_weather_reading(data)
                if reading_id:
                    print(f"  ✅ {location}: Reading #{reading_id} saved")
                else:
                    print(f"  ⚠️ {location}: Failed to save reading")
            else:
                print(f"  ❌ {location}: API error {response.status_code}")

        except Exception as e:
            print(f"  ❌ {location}: Error - {str(e)}")

    print(f"✅ Data collection completed at {datetime.now().strftime('%H:%M:%S')}\n")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_data, 'interval', minutes=15)
scheduler.start()

# Shut down scheduler on exit
atexit.register(lambda: scheduler.shutdown())

# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_cached_data(key):
    """Get data from cache if not expired"""
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now().timestamp() - timestamp < CACHE_DURATION:
            return data
        else:
            del cache[key]
    return None

def set_cached_data(key, data):
    """Store data in cache"""
    cache[key] = (data, datetime.now().timestamp())

def calculate_risk_metrics(weather_data):
    """Calculate additional risk metrics from weather data"""
    current = weather_data.get('current', {})
    air_quality = current.get('air_quality', {})

    metrics = {
        'timestamp': datetime.now().isoformat(),
        'air_quality_index': None,
        'risk_level': 'low',
        'recommendations': []
    }

    # Calculate AQI if air quality data available
    if air_quality:
        pm25 = air_quality.get('pm2_5', 0)
        pm10 = air_quality.get('pm10', 0)
        no2 = air_quality.get('no2', 0)
        o3 = air_quality.get('o3', 0)

        # Simple AQI calculation based on PM2.5
        if pm25 <= 12:
            aqi = pm25 * 50 / 12
            risk = 'good'
        elif pm25 <= 35:
            aqi = 50 + (pm25 - 12) * 50 / 23
            risk = 'moderate'
        elif pm25 <= 55:
            aqi = 100 + (pm25 - 35) * 50 / 20
            risk = 'unhealthy_sensitive'
        elif pm25 <= 150:
            aqi = 150 + (pm25 - 55) * 50 / 95
            risk = 'unhealthy'
        elif pm25 <= 250:
            aqi = 200 + (pm25 - 150) * 100 / 100
            risk = 'very_unhealthy'
        else:
            aqi = 300 + (pm25 - 250) * 100 / 100
            risk = 'hazardous'

        metrics['air_quality_index'] = round(aqi)
        metrics['risk_level'] = risk

        # Generate recommendations based on risk level
        if risk in ['unhealthy', 'very_unhealthy', 'hazardous']:
            metrics['recommendations'].append('Avoid outdoor activities')
            metrics['recommendations'].append('Use air purifiers indoors')
        elif risk == 'moderate':
            metrics['recommendations'].append('Sensitive groups should limit outdoor exposure')

    return metrics

# ═══════════════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Serve the main index.html file"""
    return FileResponse("index.html")

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard.html file"""
    return FileResponse("dashboard.html")

@app.get("/api/weather")
async def get_weather(location: str = Query(..., description="Location to get weather for")):
    """
    Get current weather data for a location
    Query params: location
    """
    if not location:
        raise HTTPException(status_code=400, detail="Location parameter is required")

    # Check cache
    cache_key = f"weather_{location}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return {
            'success': True,
            'data': cached_data,
            'cached': True,
            'timestamp': datetime.now().isoformat()
        }

    # Make API request
    url = f"{WEATHER_API_BASE}/current.json"
    params = {
        'key': WEATHER_API_KEY,
        'q': location,
        'aqi': 'yes'
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get('error', {}).get('message', 'Failed to fetch weather data')
            )

        weather_data = response.json()

        # Calculate additional metrics
        metrics = calculate_risk_metrics(weather_data)
        weather_data['calculated_metrics'] = metrics

        # Cache the response
        set_cached_data(cache_key, weather_data)

        return {
            'success': True,
            'data': weather_data,
            'cached': False,
            'timestamp': datetime.now().isoformat()
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f'API request failed: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/weather/forecast")
async def get_weather_forecast(
    location: str = Query(..., description="Location to get forecast for"),
    days: int = Query(1, description="Number of days to forecast", ge=1, le=10)
):
    """
    Get weather forecast for a location
    Query params: location, days (optional, default 1)
    """
    if not location:
        raise HTTPException(status_code=400, detail="Location parameter is required")

    # Check cache
    cache_key = f"forecast_{location}_{days}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return {
            'data': cached_data,
            'cached': True
        }

    # Make API request
    url = f"{WEATHER_API_BASE}/forecast.json"
    params = {
        'key': WEATHER_API_KEY,
        'q': location,
        'days': days,
        'aqi': 'yes'
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            raise HTTPException(
                status_code=response.status_code,
                detail=error_data.get('error', {}).get('message', 'Failed to fetch forecast data')
            )

        weather_data = response.json()

        # Calculate additional metrics
        metrics = calculate_risk_metrics(weather_data)
        weather_data['calculated_metrics'] = metrics

        # Cache the response
        set_cached_data(cache_key, weather_data)

        return {
            'success': True,
            'data': weather_data,
            'cached': False,
            'timestamp': datetime.now().isoformat()
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f'API request failed: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/weather/history")
async def get_weather_history(
    location: str = Query(..., description="Location to get history for"),
    days: int = Query(7, description="Number of days of history", ge=1, le=30)
):
    """
    Get historical weather data for a location
    Query params: location, days (optional, default 7)
    """
    if not location:
        raise HTTPException(status_code=400, detail="Location parameter is required")

    if days > 30:
        days = 30  # API limitation

    # Check cache
    cache_key = f"history_{location}_{days}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return {
            'data': cached_data,
            'cached': True
        }

    # Make API request
    url = f"{WEATHER_API_BASE}/history.json"

    history_data = []
    end_date = datetime.now()

    for i in range(days):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        params = {
            'key': WEATHER_API_KEY,
            'q': location,
            'dt': date
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                history_data.append(response.json())
        except:
            continue

    # Cache the response
    set_cached_data(cache_key, history_data)

    return {
        'data': history_data,
        'cached': False,
        'days': len(history_data)
    }

@app.get("/api/locations/search")
async def search_locations(q: str = Query(..., description="Search query for locations")):
    """
    Search for locations by name
    Query params: q (search query)
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    # Check cache
    cache_key = f"search_{q}"
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return {
            'data': cached_data,
            'cached': True
        }

    # Make API request
    url = f"{WEATHER_API_BASE}/search.json"
    params = {
        'key': WEATHER_API_KEY,
        'q': q
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail='Failed to search locations')

        locations = response.json()

        # Cache the response
        set_cached_data(cache_key, locations)

        return {
            'data': locations,
            'cached': False
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f'API request failed: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/correlation/analyze")
async def analyze_correlation(request: Request):
    """
    Perform correlation analysis on weather data
    Body: weather data JSON
    """
    try:
        weather_data = await request.json()
        if not weather_data:
            raise HTTPException(status_code=400, detail="Weather data is required")

        current = weather_data.get('current', {})
        location = weather_data.get('location', {})
        correlations = []

        # Pollution sources database
        pollution_sources = {
            'london': {
                'industrial': {'direction': 'E', 'name': 'Thames Gateway Industrial Area', 'distance': '15km'},
                'traffic': {'direction': 'N', 'name': 'M25 Motorway', 'distance': '10km'},
                'airport': {'direction': 'W', 'name': 'Heathrow Airport', 'distance': '25km'}
            },
            'mumbai': {
                'industrial': {'direction': 'NE', 'name': 'Mahul Industrial Area', 'distance': '12km'},
                'traffic': {'direction': 'W', 'name': 'Western Express Highway', 'distance': '5km'},
                'port': {'direction': 'S', 'name': 'Mumbai Port', 'distance': '8km'}
            },
            'delhi': {
                'industrial': {'direction': 'W', 'name': 'Gurgaon Industrial Belt', 'distance': '20km'},
                'traffic': {'direction': 'S', 'name': 'Ring Road', 'distance': '3km'},
                'power': {'direction': 'E', 'name': 'Badarpur Power Plant', 'distance': '18km'}
            },
            'kannur': {
                'industrial': {'direction': 'S', 'name': 'KINFRA Industrial Park', 'distance': '8km'},
                'traffic': {'direction': 'E', 'name': 'NH66 Highway', 'distance': '3km'},
                'port': {'direction': 'W', 'name': 'Kannur International Airport', 'distance': '25km'}
            }
        }

        # Get location-specific pollution sources
        city_name = location.get('name', '').lower()
        sources = pollution_sources.get(city_name, None)

        # CORRELATION 1: High PM2.5 + Wind Direction Analysis
        air_quality = current.get('air_quality')
        if air_quality:
            pm25 = air_quality.get('pm2_5', 0)
            pm10 = air_quality.get('pm10', 0)
            windSpeed = current.get('wind_kph', 0)
            windDir = current.get('wind_dir', '')

            if pm25 > 35:
                if windSpeed < 10:
                    correlations.append({
                        'type': 'danger',
                        'category': 'Air Quality - Dispersion',
                        'message': f'🔴 <strong>HIGH RISK:</strong> PM2.5 at {pm25:.1f} μg/m³ (Unhealthy) with stagnant air ({windSpeed} km/h). Local pollution is accumulating - poor ventilation preventing dispersion.',
                        'recommendation': 'Avoid outdoor activities. Close windows. Use air purifiers indoors.'
                    })
                elif sources:
                    # Check if wind is from pollution source
                    source_detected = False
                    for source_type, source_info in sources.items():
                        correlations.append({
                            'type': 'warning' if pm25 < 75 else 'danger',
                            'category': 'Air Quality - Wind Pattern',
                            'message': f'🟡 Elevated PM2.5 ({pm25:.1f} μg/m³) with {windSpeed} km/h winds from {windDir}. Possible source: {source_info["name"]}.',
                            'recommendation': 'Monitor air quality. Consider indoor activities.'
                        })
                        source_detected = True
                        break

            # CORRELATION 2: PM2.5/PM10 Ratio Analysis
            if pm10 > 50:
                pmRatio = pm25 / pm10 if pm10 > 0 else 0
                if pmRatio > 0.8:
                    correlations.append({
                        'type': 'warning',
                        'category': 'Particle Analysis',
                        'message': f'🟡 <strong>COMBUSTION SOURCE DETECTED:</strong> High PM2.5/PM10 ratio ({pmRatio:.2f}). Fine particles dominate - likely from vehicle exhaust, industrial emissions, or biomass burning.',
                        'recommendation': 'Primary pollution from combustion processes. Reduce exposure to traffic.'
                    })
                elif pmRatio < 0.5:
                    correlations.append({
                        'type': 'info',
                        'category': 'Particle Analysis',
                        'message': f'🔵 Coarse particles dominant (PM2.5/PM10: {pmRatio:.2f}). Likely from dust, construction, or road resuspension rather than combustion.',
                        'recommendation': 'Consider dust sources. May be from construction or natural dust.'
                    })

            # CORRELATION 3: Ozone Formation
            temp = current.get('temp_c', 0)
            no2 = air_quality.get('no2', 0)
            o3 = air_quality.get('o3', 0)
            isDay = current.get('is_day', 0)
            uvIndex = current.get('uv', 0)

            if temp > 25 and no2 > 40 and isDay and uvIndex > 5:
                correlations.append({
                    'type': 'warning',
                    'category': 'Photochemical Reaction',
                    'message': f'🟡 <strong>OZONE FORMATION CONDITIONS:</strong> High temperature ({temp}°C), NO₂ ({no2:.1f} μg/m³), and UV index ({uvIndex}). Photochemical reactions producing ground-level ozone - current O₃: {o3:.1f} μg/m³.',
                    'recommendation': 'Peak ozone likely in afternoon. Avoid outdoor exercise during midday.'
                })

            # CORRELATION 4: Temperature Inversion Detection
            humidity = current.get('humidity', 0)
            if windSpeed < 5 and pm25 > 30 and humidity > 70:
                correlations.append({
                    'type': 'danger',
                    'category': 'Atmospheric Stability',
                    'message': f'🔴 <strong>TEMPERATURE INVERSION LIKELY:</strong> Calm winds ({windSpeed} km/h), high humidity ({humidity}%), elevated PM2.5 ({pm25:.1f} μg/m³). Stable atmosphere trapping pollutants near ground.',
                    'recommendation': 'Critical air quality event. Stay indoors. Avoid strenuous activities.'
                })

        # CORRELATION 5: Heat + Humidity = Heat Index
        temp = current.get('temp_c', 0)
        humidity = current.get('humidity', 0)
        if humidity > 70 and temp > 28:
            temp_f = (temp * 9/5) + 32
            hi = (-42.379 + 2.04901523*temp_f + 10.14333127*humidity 
                  - 0.22475541*temp_f*humidity - 0.00683783*temp_f*temp_f
                  - 0.05481717*humidity*humidity + 0.00122874*temp_f*temp_f*humidity
                  + 0.00085282*temp_f*humidity*humidity - 0.00000199*temp_f*temp_f*humidity*humidity)
            heatIndex = (hi - 32) * 5/9

            riskLevel = 'Caution'
            severity = 'warning'
            if heatIndex > 40:
                riskLevel = 'Extreme Danger'
                severity = 'danger'
            elif heatIndex > 32:
                riskLevel = 'Danger'
                severity = 'danger'

            correlations.append({
                'type': severity,
                'category': 'Heat Stress',
                'message': f'🟡 <strong>HEAT STRESS RISK:</strong> Temperature {temp}°C with {humidity}% humidity creates heat index of {heatIndex:.1f}°C. Risk Level: {riskLevel}.',
                'recommendation': 'Stay hydrated. Avoid outdoor activities during peak heat. Seek air conditioning.'
            })

        # CORRELATION 6: UV + Clear Skies
        uvIndex = current.get('uv', 0)
        cloud = current.get('cloud', 0)
        if uvIndex > 7 and cloud < 30:
            correlations.append({
                'type': 'warning',
                'category': 'UV Radiation',
                'message': f'🟡 <strong>HIGH UV EXPOSURE:</strong> UV index {uvIndex} with {cloud}% cloud cover. Unprotected skin can burn in <15 minutes.',
                'recommendation': 'Wear sunscreen (SPF 30+). Seek shade 10AM-4PM. Wear protective clothing.'
            })

        # CORRELATION 7: Low Pressure + Pollution
        pressure = current.get('pressure_mb', 0)
        if pressure < 1010 and air_quality and air_quality.get('pm2_5', 0) > 25:
            correlations.append({
                'type': 'info',
                'category': 'Weather-Pollution Interaction',
                'message': f'🔵 Low atmospheric pressure ({pressure} mb) with elevated PM2.5. Weather system approaching may bring precipitation to help clear pollutants.',
                'recommendation': 'Air quality may improve with approaching weather system.'
            })

        # CORRELATION 8: High Wind + Dry Conditions
        windSpeed = current.get('wind_kph', 0)
        if windSpeed > 30 and humidity < 40:
            correlations.append({
                'type': 'info',
                'category': 'Dust Transport',
                'message': f'🔵 Strong winds ({windSpeed} km/h) with low humidity ({humidity}%). Conditions favorable for dust resuspension and long-range transport.',
                'recommendation': 'Expect increased dust and coarse particles. Close windows.'
            })

        # CORRELATION 9: Night + High Humidity + Low Wind
        isDay = current.get('is_day', 1)
        if not isDay and humidity > 85 and windSpeed < 8:
            correlations.append({
                'type': 'info',
                'category': 'Visibility',
                'message': f'🔵 Night conditions with high humidity ({humidity}%) and calm winds ({windSpeed} km/h). Fog formation likely - reduced visibility expected.',
                'recommendation': 'Drive carefully. Expect reduced visibility in morning.'
            })

        return {
            'correlations': correlations,
            'count': len(correlations),
            'location': location.get('name'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/risk/calculate")
async def calculate_risk(request: Request):
    """
    Calculate multi-factor environmental risk score
    Body: weather data JSON
    """
    try:
        weather_data = await request.json()
        if not weather_data:
            raise HTTPException(status_code=400, detail="Weather data is required")

        current = weather_data.get('current', {})
        risk_score = 0
        risk_factors = []

        # FACTOR 1: Air Quality (PM2.5) - Weight: 50 points max
        air_quality = current.get('air_quality')
        if air_quality:
            pm25 = air_quality.get('pm2_5', 0)

            if pm25 > 250:
                risk_factors.append({
                    'name': 'Air Quality (PM2.5)',
                    'value': f'{pm25:.1f} μg/m³',
                    'score': 50,
                    'level': 'Hazardous',
                    'color': 'danger'
                })
                risk_score += 50
            elif pm25 > 150:
                risk_factors.append({
                    'name': 'Air Quality (PM2.5)',
                    'value': f'{pm25:.1f} μg/m³',
                    'score': 45,
                    'level': 'Very Unhealthy',
                    'color': 'danger'
                })
                risk_score += 45
            elif pm25 > 80:
                risk_factors.append({
                    'name': 'Air Quality (PM2.5)',
                    'value': f'{pm25:.1f} μg/m³',
                    'score': 30,
                    'level': 'Unhealthy',
                    'color': 'warning'
                })
                risk_score += 30
            elif pm25 > 50:
                risk_factors.append({
                    'name': 'Air Quality (PM2.5)',
                    'value': f'{pm25:.1f} μg/m³',
                    'score': 20,
                    'level': 'Moderate',
                    'color': 'warning'
                })
                risk_score += 20
            elif pm25 > 35:
                risk_factors.append({
                    'name': 'Air Quality (PM2.5)',
                    'value': f'{pm25:.1f} μg/m³',
                    'score': 10,
                    'level': 'Acceptable',
                    'color': 'info'
                })
                risk_score += 10

            # FACTOR 2: Nitrogen Dioxide (NO2) - Weight: 15 points max
            no2 = air_quality.get('no2', 0)
            if no2 > 200:
                risk_factors.append({
                    'name': 'Nitrogen Dioxide',
                    'value': f'{no2:.1f} μg/m³',
                    'score': 15,
                    'level': 'Very High',
                    'color': 'danger'
                })
                risk_score += 15
            elif no2 > 100:
                risk_factors.append({
                    'name': 'Nitrogen Dioxide',
                    'value': f'{no2:.1f} μg/m³',
                    'score': 10,
                    'level': 'High',
                    'color': 'warning'
                })
                risk_score += 10
            elif no2 > 50:
                risk_factors.append({
                    'name': 'Nitrogen Dioxide',
                    'value': f'{no2:.1f} μg/m³',
                    'score': 5,
                    'level': 'Moderate',
                    'color': 'info'
                })
                risk_score += 5

            # FACTOR 3: Ozone (O3) - Weight: 15 points max
            o3 = air_quality.get('o3', 0)
            if o3 > 180:
                risk_factors.append({
                    'name': 'Ozone Level',
                    'value': f'{o3:.1f} μg/m³',
                    'score': 15,
                    'level': 'Very High',
                    'color': 'danger'
                })
                risk_score += 15
            elif o3 > 120:
                risk_factors.append({
                    'name': 'Ozone Level',
                    'value': f'{o3:.1f} μg/m³',
                    'score': 10,
                    'level': 'High',
                    'color': 'warning'
                })
                risk_score += 10
            elif o3 > 80:
                risk_factors.append({
                    'name': 'Ozone Level',
                    'value': f'{o3:.1f} μg/m³',
                    'score': 5,
                    'level': 'Moderate',
                    'color': 'info'
                })
                risk_score += 5

        # FACTOR 4: Temperature Extremes - Weight: 15 points max
        temp = current.get('temp_c', 0)
        if temp > 40:
            risk_factors.append({
                'name': 'Extreme Heat',
                'value': f'{temp}°C',
                'score': 15,
                'level': 'Dangerous',
                'color': 'danger'
            })
            risk_score += 15
        elif temp > 35:
            risk_factors.append({
                'name': 'High Temperature',
                'value': f'{temp}°C',
                'score': 10,
                'level': 'Heat Stress',
                'color': 'warning'
            })
            risk_score += 10
        elif temp < -15:
            risk_factors.append({
                'name': 'Extreme Cold',
                'value': f'{temp}°C',
                'score': 15,
                'level': 'Dangerous',
                'color': 'danger'
            })
            risk_score += 15
        elif temp < -5:
            risk_factors.append({
                'name': 'Low Temperature',
                'value': f'{temp}°C',
                'score': 10,
                'level': 'Cold Stress',
                'color': 'warning'
            })
            risk_score += 10

        # FACTOR 5: Humidity Extremes - Weight: 10 points max
        humidity = current.get('humidity', 0)
        if humidity > 85 and temp > 28:
            risk_factors.append({
                'name': 'High Humidity + Heat',
                'value': f'{humidity}%',
                'score': 10,
                'level': 'Oppressive',
                'color': 'warning'
            })
            risk_score += 10
        elif humidity < 20:
            risk_factors.append({
                'name': 'Very Low Humidity',
                'value': f'{humidity}%',
                'score': 8,
                'level': 'Dry Air',
                'color': 'info'
            })
            risk_score += 8

        # FACTOR 6: Wind Speed (Storm Risk) - Weight: 15 points max
        wind_speed = current.get('wind_kph', 0)
        if wind_speed > 75:
            risk_factors.append({
                'name': 'Severe Wind',
                'value': f'{wind_speed} km/h',
                'score': 15,
                'level': 'Storm Force',
                'color': 'danger'
            })
            risk_score += 15
        elif wind_speed > 50:
            risk_factors.append({
                'name': 'High Wind',
                'value': f'{wind_speed} km/h',
                'score': 10,
                'level': 'Strong Gale',
                'color': 'warning'
            })
            risk_score += 10

        # FACTOR 7: UV Index - Weight: 10 points max
        uv_index = current.get('uv', 0)
        if uv_index > 10:
            risk_factors.append({
                'name': 'UV Radiation',
                'value': str(uv_index),
                'score': 10,
                'level': 'Extreme',
                'color': 'danger'
            })
            risk_score += 10
        elif uv_index > 7:
            risk_factors.append({
                'name': 'UV Radiation',
                'value': str(uv_index),
                'score': 7,
                'level': 'Very High',
                'color': 'warning'
            })
            risk_score += 7

        # FACTOR 8: Visibility - Weight: 10 points max
        visibility = current.get('vis_km', 10)
        if visibility < 1:
            risk_factors.append({
                'name': 'Poor Visibility',
                'value': f'{visibility} km',
                'score': 10,
                'level': 'Dense Fog/Smog',
                'color': 'danger'
            })
            risk_score += 10
        elif visibility < 5:
            risk_factors.append({
                'name': 'Reduced Visibility',
                'value': f'{visibility} km',
                'score': 6,
                'level': 'Fog/Haze',
                'color': 'warning'
            })
            risk_score += 6

        # FACTOR 9: Heat Index - Weight: 15 points max
        if temp > 25:
            temp_f = (temp * 9/5) + 32
            hi = (-42.379 + 2.04901523*temp_f + 10.14333127*humidity 
                  - 0.22475541*temp_f*humidity - 0.00683783*temp_f*temp_f
                  - 0.05481717*humidity*humidity + 0.00122874*temp_f*temp_f*humidity
                  + 0.00085282*temp_f*humidity*humidity - 0.00000199*temp_f*temp_f*humidity*humidity)
            heat_index = (hi - 32) * 5/9

            if heat_index > 41:
                risk_factors.append({
                    'name': 'Heat Index',
                    'value': f'{heat_index:.1f}°C',
                    'score': 15,
                    'level': 'Extreme Danger',
                    'color': 'danger'
                })
                risk_score += 15
            elif heat_index > 32:
                risk_factors.append({
                    'name': 'Heat Index',
                    'value': f'{heat_index:.1f}°C',
                    'score': 10,
                    'level': 'Danger',
                    'color': 'warning'
                })
                risk_score += 10

        # FACTOR 10: Air Stagnation - Weight: 10 points max
        if air_quality and wind_speed < 10 and air_quality.get('pm2_5', 0) > 30:
            risk_factors.append({
                'name': 'Air Stagnation',
                'value': f'{wind_speed} km/h wind',
                'score': 10,
                'level': 'Pollutant Trap',
                'color': 'danger'
            })
            risk_score += 10

        # Cap at 100
        risk_score = min(risk_score, 100)

        # Determine risk level
        if risk_score > 70:
            risk_level = 'HIGH RISK'
            label_class = 'high'
        elif risk_score > 40:
            risk_level = 'MODERATE RISK'
            label_class = 'moderate'
        else:
            risk_level = 'LOW RISK'
            label_class = 'low'

        # Sort factors by score
        risk_factors.sort(key=lambda x: x['score'], reverse=True)

        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'label_class': label_class,
            'factors': risk_factors,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/alerts/contextual")
async def generate_contextual_alerts(request: Request):
    """
    Generate comprehensive contextual alerts
    Body: weather data JSON
    """
    try:
        weather_data = await request.json()
        if not weather_data:
            raise HTTPException(status_code=400, detail="Weather data is required")

        alerts = []
        current = weather_data.get('current', {})
        location = weather_data.get('location', {})

        # ALERT 1: Poor Air Dispersion (High PM2.5 + Low Wind)
        air_quality = current.get('air_quality')
        if air_quality:
            pm25 = air_quality.get('pm2_5', 0)
            wind_speed = current.get('wind_kph', 0)

            if pm25 > 75 and wind_speed < 10:
                alerts.append({
                    'severity': 'critical',
                    'icon': '🔴',
                    'title': 'CRITICAL: Air Quality - Poor Dispersion',
                    'what': f'PM2.5 concentration is {pm25:.1f} μg/m³ (Unhealthy) with minimal air movement.',
                    'cause': f'Stagnant air conditions ({wind_speed} km/h wind) are preventing pollutant dispersion. Pollutants from traffic, industry, and combustion sources are accumulating near ground level. Temperature inversion may be trapping pollution.',
                    'action': '<strong>Immediate Actions:</strong><br>• Stay indoors and keep windows/doors closed<br>• Use HEPA air purifiers if available<br>• Avoid all outdoor physical activities<br>• Wear N95/KN95 mask if you must go outside<br>• Sensitive groups (children, elderly, respiratory patients) should remain indoors<br>• Monitor air quality continuously',
                    'sources': ['PM2.5', 'Wind Speed', 'Atmospheric Stability']
                })
            elif pm25 > 50 and wind_speed < 15:
                alerts.append({
                    'severity': 'high',
                    'icon': '🟠',
                    'title': 'HIGH ALERT: Elevated Air Pollution with Poor Ventilation',
                    'what': f'PM2.5 levels at {pm25:.1f} μg/m³ combined with low wind speed.',
                    'cause': f'Weak winds ({wind_speed} km/h) are insufficient to disperse local pollution. Emissions from nearby sources (traffic, cooking, industry) are building up. The air is not circulating effectively.',
                    'action': '<strong>Recommended Actions:</strong><br>• Limit outdoor activities, especially for sensitive groups<br>• Close windows during peak traffic hours<br>• Postpone outdoor exercise to when air quality improves<br>• Consider using air purifiers indoors<br>• Check air quality before outdoor activities',
                    'sources': ['PM2.5', 'Wind Speed']
                })

            # ALERT 2: Photochemical Smog
            temp = current.get('temp_c', 0)
            no2 = air_quality.get('no2', 0)
            o3 = air_quality.get('o3', 0)
            uv = current.get('uv', 0)
            is_day = current.get('is_day', 0)

            if temp > 28 and no2 > 50 and o3 > 100 and is_day and uv > 5:
                alerts.append({
                    'severity': 'high',
                    'icon': '☀️',
                    'title': 'HIGH ALERT: Photochemical Smog Formation',
                    'what': f'Ground-level ozone at {o3:.1f} μg/m³ with high NO₂ ({no2:.1f} μg/m³) under sunny conditions.',
                    'cause': f'Hot temperature ({temp}°C), strong sunlight (UV {uv}), and nitrogen dioxide from vehicle emissions are reacting to produce harmful ground-level ozone. This photochemical reaction is intensifying throughout the day and will peak in afternoon hours.',
                    'action': '<strong>Health Protection:</strong><br>• Avoid outdoor exercise, especially 12 PM - 4 PM<br>• Stay in air-conditioned spaces during peak heat<br>• Ozone levels typically highest in afternoon<br>• People with asthma/respiratory conditions take extra precaution<br>• Reduce vehicle use to minimize NO₂ emissions<br>• Conditions should improve after sunset',
                    'sources': ['Ozone', 'NO₂', 'Temperature', 'UV Index']
                })

            # ALERT 3: Temperature Inversion
            humidity = current.get('humidity', 0)
            if wind_speed < 5 and pm25 > 35 and humidity > 75:
                alerts.append({
                    'severity': 'critical',
                    'icon': '🌫️',
                    'title': 'CRITICAL: Temperature Inversion Event',
                    'what': f'Atmospheric conditions are trapping pollutants. PM2.5: {pm25:.1f} μg/m³, Wind: {wind_speed} km/h, Humidity: {humidity}%.',
                    'cause': f'A temperature inversion layer is preventing vertical air mixing. The combination of calm winds, high humidity ({humidity}%), and stable atmospheric conditions creates a "lid" that traps pollutants near the ground. This is a classic pollution episode scenario.',
                    'action': '<strong>Emergency Measures:</strong><br>• This is a significant air quality event - take seriously<br>• Minimize all outdoor exposure<br>• Keep vulnerable people (children, elderly) indoors<br>• Close all windows and external air vents<br>• Use indoor air filtration continuously<br>• Monitor for symptoms: coughing, throat irritation, breathing difficulty<br>• Situation will improve when weather pattern changes',
                    'sources': ['PM2.5', 'Wind Speed', 'Humidity', 'Atmospheric Stability']
                })

        # ALERT 4: Heat Stress
        temp = current.get('temp_c', 0)
        humidity = current.get('humidity', 0)
        if temp > 28 and humidity > 60:
            temp_f = (temp * 9/5) + 32
            hi = (-42.379 + 2.04901523*temp_f + 10.14333127*humidity 
                  - 0.22475541*temp_f*humidity - 0.00683783*temp_f*temp_f
                  - 0.05481717*humidity*humidity + 0.00122874*temp_f*temp_f*humidity
                  + 0.00085282*temp_f*humidity*humidity - 0.00000199*temp_f*temp_f*humidity*humidity)
            heat_index = (hi - 32) * 5/9

            if heat_index > 40:
                alerts.append({
                    'severity': 'critical',
                    'icon': '🌡️',
                    'title': 'EXTREME: Heat Index - Danger Level',
                    'what': f'Heat index is {heat_index:.1f}°C (feels like temperature) with actual temperature {temp}°C and humidity {humidity}%.',
                    'cause': f'High humidity prevents sweat evaporation, making it difficult for your body to cool itself. The combination of heat and humidity creates dangerous conditions for heat-related illness including heat exhaustion and heat stroke.',
                    'action': '<strong>Heat Safety - Urgent:</strong><br>• Stay in air conditioning - this is dangerous heat<br>• Drink water frequently (don\'t wait until thirsty)<br>• NEVER leave anyone in parked vehicles<br>• Avoid strenuous outdoor activities<br>• Wear light-colored, loose clothing<br>• Check on elderly neighbors and vulnerable people<br>• Watch for heat illness: dizziness, nausea, rapid heartbeat, confusion<br>• Call emergency services if someone shows heat stroke symptoms',
                    'sources': ['Temperature', 'Humidity', 'Heat Index']
                })
            elif heat_index > 32:
                alerts.append({
                    'severity': 'high',
                    'icon': '🔥',
                    'title': 'WARNING: High Heat Index',
                    'what': f'Heat index at {heat_index:.1f}°C creates heat stress risk. Temperature: {temp}°C, Humidity: {humidity}%.',
                    'cause': f'The combination of heat and humidity makes it feel much hotter than the actual temperature. Your body\'s cooling mechanism (sweating) is less effective in humid conditions, increasing risk of heat-related illness.',
                    'action': '<strong>Heat Precautions:</strong><br>• Limit outdoor activities during hottest hours (11 AM - 4 PM)<br>• Stay hydrated - drink before, during, and after outdoor activity<br>• Take frequent breaks in shade or air conditioning<br>• Wear sunscreen, hat, and breathable clothing<br>• Never leave children or pets in vehicles<br>• Watch for heat cramps, exhaustion, or dizziness',
                    'sources': ['Temperature', 'Humidity', 'Heat Index']
                })

        # ALERT 5: Extreme UV
        uv = current.get('uv', 0)
        cloud = current.get('cloud', 0)
        if uv > 8 and cloud < 40:
            burn_time = max(10, round(200 / (uv * 1.5)))
            alerts.append({
                'severity': 'critical' if uv > 10 else 'high',
                'icon': '☀️',
                'title': f'{"EXTREME" if uv > 10 else "HIGH"}: UV Radiation Warning',
                'what': f'UV index is {uv} with {cloud}% cloud cover.',
                'cause': f'Clear skies allow intense solar radiation to reach ground level. At this UV level, unprotected skin can burn in approximately {burn_time} minutes. UV radiation damages skin DNA and increases skin cancer risk. Eyes are also at risk from UV exposure.',
                'action': '<strong>Sun Protection Required:</strong><br>• Apply broad-spectrum SPF 30+ sunscreen every 2 hours<br>• Wear protective clothing: long sleeves, wide-brimmed hat<br>• Use UV-blocking sunglasses (100% UVA/UVB protection)<br>• Seek shade, especially 10 AM - 4 PM<br>• Reapply sunscreen after swimming or sweating<br>• Children need extra protection - they burn faster<br>• Check moles regularly for changes',
                'sources': ['UV Index', 'Cloud Cover']
            })

        # ALERT 6: High Wind
        wind_speed = current.get('wind_kph', 0)
        if wind_speed > 50:
            wind_category = 'Storm Force' if wind_speed > 75 else 'Gale Force'
            alerts.append({
                'severity': 'critical' if wind_speed > 75 else 'high',
                'icon': '💨',
                'title': f'{"SEVERE" if wind_speed > 75 else "HIGH"}: {wind_category} Winds',
                'what': f'Wind speed at {wind_speed} km/h from {current.get("wind_dir", "N")}. {wind_category} conditions present.',
                'cause': f'A strong weather system is producing dangerous winds. At these speeds, loose objects become projectiles, trees and power lines may fall, and structural damage is possible. Wind gusts may be even stronger than sustained winds.',
                'action': '<strong>Wind Safety:</strong><br>• Stay indoors and away from windows<br>• Secure or bring inside loose outdoor items<br>• Avoid driving, especially high-profile vehicles<br>• Stay away from trees, power lines, and unstable structures<br>• Be prepared for potential power outages<br>• Do not attempt outdoor repairs until winds subside<br>• If caught outside, seek substantial shelter immediately',
                'sources': ['Wind Speed', 'Weather System']
            })

        return {
            'alerts': alerts,
            'count': len(alerts),
            'location': location.get('name'),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/alerts/generate")
async def generate_alerts(request: Request):
    """
    Generate contextual alerts based on weather data
    Body: weather data JSON
    """
    try:
        weather_data = await request.json()
        if not weather_data:
            raise HTTPException(status_code=400, detail="Weather data is required")

        alerts = []
        current = weather_data.get('current', {})

        # Alert logic (simplified server-side version)
        air_quality = current.get('air_quality', {})
        if air_quality:
            pm25 = air_quality.get('pm2_5', 0)
            wind_speed = current.get('wind_kph', 0)

            if pm25 > 75 and wind_speed < 10:
                alerts.append({
                    'severity': 'critical',
                    'type': 'air_quality',
                    'title': 'Poor Air Dispersion',
                    'message': f'PM2.5 at {pm25} μg/m³ with low wind speed'
                })

        return {
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear the server cache"""
    global cache
    cache_size = len(cache)
    cache.clear()
    return {
        'message': 'Cache cleared successfully',
        'items_cleared': cache_size
    }

@app.get("/api/stats")
async def get_stats():
    """Get server statistics"""
    stats = get_database_stats()
    return {
        'cache_size': len(cache),
        'cache_duration_seconds': CACHE_DURATION,
        'database': stats,
        'monitored_locations': MONITORED_LOCATIONS,
        'timestamp': datetime.now().isoformat()
    }

# ═══════════════════════════════════════════════════════════════════
# HISTORICAL DATA & PREDICTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/historical/{location}")
async def get_historical(location: str, hours: int = Query(24, description="Number of hours of history", ge=1, le=168)):
    """
    Get historical weather data for a location
    Query params: hours (default 24)
    """
    try:
        hours = min(hours, 168)  # Max 7 days

        historical = get_historical_data(location, hours)

        if not historical:
            raise HTTPException(
                status_code=404,
                detail=f'No historical data found for {location}'
            )

        return {
            'success': True,
            'location': location,
            'hours': hours,
            'data_points': len(historical),
            'data': historical,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/predict/{location}")
async def predict_weather(location: str):
    """
    Generate weather prediction for next hour
    """
    try:
        # Get historical data
        historical = get_historical_data(location, hours=24)

        if not historical or len(historical) < 3:
            raise HTTPException(
                status_code=400,
                detail='Insufficient historical data for prediction. Need at least 3 readings.'
            )

        # Generate prediction
        prediction = predict_next_hour(historical)

        if prediction:
            # Store prediction in database
            insert_prediction(location, prediction)

            return {
                'success': True,
                'location': location,
                'prediction': prediction,
                'based_on_readings': len(historical),
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail='Failed to generate prediction')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/predict/{location}/multi")
async def predict_multi_hour(location: str, hours: int = Query(6, description="Number of hours to predict", ge=1, le=12)):
    """
    Generate multi-hour predictions
    Query params: hours (default 6, max 12)
    """
    try:
        hours = min(hours, 12)  # Max 12 hours ahead

        historical = get_historical_data(location, hours=24)

        if not historical or len(historical) < 3:
            raise HTTPException(status_code=400, detail='Insufficient historical data')

        predictions = predict_multiple_hours(historical, hours)

        return {
            'success': True,
            'location': location,
            'predictions': predictions,
            'hours_ahead': hours,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/analysis/{location}")
async def analyze_location(location: str, hours: int = Query(48, description="Number of hours for analysis", ge=1, le=168)):
    """
    Analyze historical patterns for a location
    """
    try:
        historical = get_historical_data(location, hours)

        if not historical:
            raise HTTPException(status_code=404, detail=f'No data available for {location}')

        analysis = analyze_patterns(historical)

        return {
            'success': True,
            'location': location,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.post("/api/database/cleanup")
async def cleanup_database(days: int = Query(30, description="Days to keep data", ge=1)):
    """
    Clean up old database entries
    Query params: days (default 30)
    """
    try:
        deleted = cleanup_old_data(days)

        return {
            'success': True,
            'deleted_records': deleted,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

@app.get("/api/locations/monitored")
async def get_monitored_locations():
    """
    Get list of monitored locations with coordinates and air quality for map display
    """
    # Define monitored cities with their coordinates
    CITY_COORDS = {
        'London': {'lat': 51.5074, 'lon': -0.1278},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
        'New Delhi': {'lat': 28.6139, 'lon': 77.2090},
        'New York': {'lat': 40.7128, 'lon': -74.0060},
        'Tokyo': {'lat': 35.6762, 'lon': 139.6503}
    }

    try:
        locations_data = []

        for location in MONITORED_LOCATIONS:
            try:
                print(f"📍 Fetching data for {location}...")

                # Fetch weather data using the same logic as get_weather endpoint
                url = f"{WEATHER_API_BASE}/current.json"
                params = {
                    'key': WEATHER_API_KEY,
                    'q': location,
                    'aqi': 'yes'
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    weather_data = response.json()
                    current = weather_data.get('current', {})
                    aqi = current.get('air_quality', {})

                    # Calculate risk score from air quality
                    pm25 = aqi.get('pm2_5', 0)
                    pm10 = aqi.get('pm10', 0)

                    # Simple risk score based on PM2.5 (main indicator)
                    if pm25 > 150:
                        risk_score = 90
                    elif pm25 > 100:
                        risk_score = 70
                    elif pm25 > 50:
                        risk_score = 50
                    elif pm25 > 25:
                        risk_score = 30
                    else:
                        risk_score = 10

                    print(f"  ✅ {location}: Temp={current.get('temp_c')}°C, PM2.5={pm25}, Risk={risk_score}")

                    locations_data.append({
                        'location_name': location,
                        'lat': CITY_COORDS[location]['lat'],
                        'lon': CITY_COORDS[location]['lon'],
                        'temp_c': current.get('temp_c'),
                        'humidity': current.get('humidity'),
                        'pm2_5': pm25,
                        'pm10': pm10,
                        'risk_score': risk_score,
                        'timestamp': current.get('last_updated', datetime.now().isoformat())
                    })
                else:
                    print(f"  ⚠️ {location}: API returned {response.status_code}")
                    locations_data.append({
                        'location_name': location,
                        'lat': CITY_COORDS[location]['lat'],
                        'lon': CITY_COORDS[location]['lon'],
                        'temp_c': None,
                        'humidity': None,
                        'pm2_5': None,
                        'pm10': None,
                        'risk_score': 0,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'unavailable'
                    })

            except Exception as loc_error:
                print(f"❌ Error fetching data for {location}: {loc_error}")
                locations_data.append({
                    'location_name': location,
                    'lat': CITY_COORDS[location]['lat'],
                    'lon': CITY_COORDS[location]['lon'],
                    'temp_c': None,
                    'humidity': None,
                    'pm2_5': None,
                    'pm10': None,
                    'risk_score': 0,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error'
                })

        print(f"✅ Returning {len(locations_data)} monitored locations")
        return {
            'success': True,
            'locations': locations_data,
            'count': len(locations_data),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Error in get_monitored_locations: {e}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

# ═══════════════════════════════════════════════════════════════════
# AI ASSISTANT - INTELLIGENT ANALYSIS & RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════

def analyze_air_quality(pm25, pm10, location):
    """Analyze air quality and provide detailed assessment"""
    if pm25 is None:
        return {'status': 'unknown', 'level': 'Unknown', 'score': 0, 'description': 'No data available'}

    # Air Quality Index calculation based on PM2.5
    if pm25 <= 12:
        status, level, color = 'excellent', 'Excellent', 'green'
    elif pm25 <= 35:
        status, level, color = 'good', 'Good', 'blue'
    elif pm25 <= 55:
        status, level, color = 'moderate', 'Moderate', 'yellow'
    elif pm25 <= 150:
        status, level, color = 'unhealthy', 'Unhealthy', 'orange'
    elif pm25 <= 250:
        status, level, color = 'very_unhealthy', 'Very Unhealthy', 'red'
    else:
        status, level, color = 'hazardous', 'Hazardous', 'purple'

    # Generate description
    descriptions = {
        'excellent': 'Air quality is excellent. Perfect conditions for outdoor activities.',
        'good': 'Air quality is good. Safe for all outdoor activities.',
        'moderate': 'Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exposure.',
        'unhealthy': 'Air quality is unhealthy. Everyone should reduce prolonged outdoor exertion.',
        'very_unhealthy': 'Air quality is very unhealthy. Avoid outdoor activities.',
        'hazardous': 'Air quality is hazardous. Stay indoors and keep windows closed.'
    }

    return {
        'status': status,
        'level': level,
        'color': color,
        'score': int((pm25 / 300) * 100),  # 0-100 scale
        'pm25': pm25,
        'pm10': pm10,
        'description': descriptions[status]
    }

def analyze_outdoor_safety(weather_data, air_quality):
    """Determine if it's safe to go outdoors based on multiple factors"""
    safety_score = 100
    warnings = []
    recommendations = []

    # Check air quality based on PM2.5 levels (using actual AQI standards)
    pm25 = air_quality.get('pm25', 0)

    if pm25 > 250:  # Hazardous
        safety_score -= 50
        warnings.append('🚨 HAZARDOUS air quality detected')
        recommendations.append('Stay indoors, close windows, use air purifiers')
    elif pm25 > 150:  # Very Unhealthy
        safety_score -= 40
        warnings.append('⚠️ Very unhealthy air quality')
        recommendations.append('Avoid all outdoor activities, especially for vulnerable groups')
    elif pm25 > 55:  # Unhealthy
        safety_score -= 30
        warnings.append('⚠️ Unhealthy air quality')
        recommendations.append('Limit outdoor exposure, especially for sensitive groups')
    elif pm25 > 35:  # Moderate
        safety_score -= 15
        warnings.append('⚡ Moderate air quality')
        recommendations.append('Sensitive individuals should consider reducing prolonged outdoor activities')
    elif pm25 > 12:  # Good
        safety_score -= 5
        warnings.append('✓ Air quality is acceptable')
        recommendations.append('Air quality is good for most activities')

    # Check temperature
    temp = weather_data.get('temp_c', 20)
    if temp < 0:
        safety_score -= 15
        warnings.append('🥶 Freezing temperatures')
        recommendations.append('Dress warmly if going outside')
    elif temp > 35:
        safety_score -= 15
        warnings.append('🌡️ Extreme heat')
        recommendations.append('Stay hydrated and avoid midday sun')

    # Check wind conditions
    wind_kph = weather_data.get('wind_kph', 0)
    if wind_kph > 40:
        safety_score -= 10
        warnings.append('💨 Strong winds')
        recommendations.append('Secure loose objects and take caution outdoors')

    # Check humidity
    humidity = weather_data.get('humidity', 50)
    if humidity > 85:
        safety_score -= 5
        warnings.append('💧 High humidity')
        recommendations.append('May feel uncomfortable, stay hydrated')

    # Check precipitation
    precip_mm = weather_data.get('precip_mm', 0)
    if precip_mm > 5:
        safety_score -= 10
        warnings.append('🌧️ Heavy rainfall')
        recommendations.append('Bring an umbrella or postpone outdoor activities')

    # Determine overall safety level
    safety_score = max(0, safety_score)
    if safety_score >= 80:
        safety_level = 'Safe'
        safety_color = 'green'
        overall_recommendation = '✅ Conditions are good for outdoor activities like walking, jogging, or exercising.'
    elif safety_score >= 60:
        safety_level = 'Moderate'
        safety_color = 'yellow'
        overall_recommendation = '⚡ You can go outside but take precautions. Monitor conditions if staying out long.'
    elif safety_score >= 40:
        safety_level = 'Caution'
        safety_color = 'orange'
        overall_recommendation = '⚠️ Consider postponing non-essential outdoor activities. If you must go out, limit exposure time.'
    else:
        safety_level = 'Unsafe'
        safety_color = 'red'
        overall_recommendation = '🚫 Not recommended to go outside. Stay indoors if possible.'

    return {
        'safety_score': safety_score,
        'safety_level': safety_level,
        'safety_color': safety_color,
        'overall_recommendation': overall_recommendation,
        'warnings': warnings,
        'recommendations': recommendations
    }

def predict_next_hour_conditions(location):
    """Predict environmental conditions for the next hour using historical data"""
    try:
        # Get last 24 hours of data
        historical = get_historical_data(location, hours=24)

        if not historical or len(historical) < 3:
            return None

        # Simple linear regression for prediction
        def simple_predict(values):
            if len(values) < 2:
                return values[-1] if values else None

            # Use last 6 readings for trend analysis
            recent = values[-6:]
            n = len(recent)

            # Calculate linear trend
            x_mean = (n - 1) / 2
            y_mean = sum(recent) / n

            numerator = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return recent[-1]

            slope = numerator / denominator
            # Predict one step ahead
            prediction = recent[-1] + slope
            return prediction

        # Extract time series
        temps = [h['temperature'] for h in historical if h['temperature'] is not None]
        humidity_values = [h['humidity'] for h in historical if h['humidity'] is not None]
        pm25_values = [h['pm2_5'] for h in historical if h['pm2_5'] is not None]

        predictions = {
            'temperature': round(simple_predict(temps), 1) if temps else None,
            'humidity': round(simple_predict(humidity_values), 0) if humidity_values else None,
            'pm2_5': round(simple_predict(pm25_values), 2) if pm25_values else None,
            'timestamp': (datetime.now() + timedelta(hours=1)).isoformat()
        }

        # Calculate trend direction
        predictions['temperature_trend'] = 'rising' if len(temps) >= 2 and temps[-1] > temps[-2] else 'falling'
        predictions['pm25_trend'] = 'rising' if len(pm25_values) >= 2 and pm25_values[-1] > pm25_values[-2] else 'falling'

        return predictions
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        return None

def analyze_correlation_factors(weather_data):
    """Analyze correlation between multiple environmental factors"""
    insights = []

    pm25 = weather_data.get('pm2_5', 0)
    wind_kph = weather_data.get('wind_kph', 0)
    humidity = weather_data.get('humidity', 50)
    temp = weather_data.get('temp_c', 20)

    # Low wind + high PM2.5 = pollutant accumulation
    if wind_kph < 10 and pm25 > 50:
        insights.append({
            'type': 'warning',
            'title': 'Pollutant Accumulation',
            'description': f'Low wind speed ({wind_kph} km/h) is causing pollutants to accumulate. PM2.5 levels are elevated at {pm25} µg/m³.',
            'factors': ['wind_speed', 'pm25']
        })

    # High humidity + high PM2.5 = worse air quality perception
    if humidity > 75 and pm25 > 35:
        insights.append({
            'type': 'info',
            'title': 'Humidity Effect',
            'description': f'High humidity ({humidity}%) combined with elevated PM2.5 may make air quality feel worse and affect visibility.',
            'factors': ['humidity', 'pm25']
        })

    # Temperature inversion risk
    if temp < 10 and wind_kph < 5:
        insights.append({
            'type': 'warning',
            'title': 'Temperature Inversion Risk',
            'description': f'Cold temperatures ({temp}°C) with minimal wind may trap pollutants near ground level.',
            'factors': ['temperature', 'wind_speed']
        })

    # Favorable conditions
    if wind_kph > 15 and pm25 < 25:
        insights.append({
            'type': 'positive',
            'title': 'Good Ventilation',
            'description': f'Strong winds ({wind_kph} km/h) are helping disperse pollutants, maintaining good air quality.',
            'factors': ['wind_speed', 'pm25']
        })

    return insights

def extract_location_from_query(query, default_location='Mumbai'):
    """Extract location name from user query using NLP patterns"""
    query_lower = query.lower().strip()

    # Detect casual conversation (greetings, help requests) - no location needed
    casual_patterns = [
        r'^(hi|hello|hey|greetings)\b',
        r'^(help|assist|what can you|how can you)',
        r'^(thanks|thank you|bye|goodbye)',
        r'^(how are you|what\'s up|sup)'
    ]

    for pattern in casual_patterns:
        if re.match(pattern, query_lower):
            return None  # Signal: no location needed, it's casual conversation

    # List of common non-location words to filter out (including greetings)
    non_locations = [
        'the', 'a', 'an', 'air', 'quality', 'weather', 'temperature', 
        'today', 'tomorrow', 'now', 'walk', 'jogging', 'running', 'about',
        'good', 'bad', 'safe', 'okay', 'fine', 'nice', 'great', 'terrible',
        'hi', 'hello', 'hey', 'help', 'thanks', 'bye', 'goodbye'
    ]

    # Common location patterns - ordered by specificity
    location_patterns = [
        r'(?:in|at|for|of)\s+([a-zA-Z][a-zA-Z\s]+?)(?:\s+is|\s+today|\s+now|\?|$)'
    ]

    for pattern in location_patterns:
        match = re.search(pattern, query_lower)
        if match:
            potential_location = match.group(1).strip()
            # Filter out non-location words (check each word in multi-word matches)
            words_in_location = potential_location.split()
            if all(word not in non_locations for word in words_in_location) and len(potential_location) > 2:
                # Capitalize properly (handle multi-word cities like "new delhi")
                return ' '.join(word.capitalize() for word in potential_location.split())

    # Check if query starts with a location name (e.g., "Tokyo weather", "Manali temperature")
    words = query.split()
    if len(words) > 0:
        first_word = words[0].strip('?.,!').lower()
        # Common question words that are NOT location names
        common_start_words = ['how', 'what', 'when', 'where', 'why', 'is', 'can', 'should', 'will', 'tell', 'show', 'give', 'does', 'do']
        if first_word not in common_start_words and first_word not in non_locations:
            return words[0].strip('?.,!').title()

    return default_location

def generate_ai_response_with_openai(user_query, weather_data, location, air_quality, safety_analysis, predictions, correlations):
    """Generate intelligent response using OpenAI GPT API"""

    if not OPENAI_API_KEY:
        return None  # Fall back to template-based response

    try:
        # For casual conversation without location context
        if location is None:
            context = f"""You are a friendly environmental monitoring AI assistant. 

User said: "{user_query}"

This is a casual greeting or conversational message. Respond warmly and naturally:
- If they greeted you (hi/hello), greet them back and briefly explain you can help with environmental data (air quality, weather, safety) for any location
- If they asked for help, explain your capabilities in a friendly way
- Keep it brief and conversational (2-3 sentences)
- End by asking what location they'd like to know about

Respond naturally:"""
        else:
            # Prepare context for AI - make it more conversational
            context = f"""You are a friendly and intelligent environmental monitoring AI assistant. Have a natural conversation with the user while helping them with environmental data.

User asked: "{user_query}"
Location detected: {location}

AVAILABLE DATA (only use what's relevant to answer the user's question):

Weather Now:
- Temperature: {weather_data.get('temp_c')}°C
- Feels like: {weather_data.get('condition', {}).get('text', 'Unknown')}
- Humidity: {weather_data.get('humidity')}%  
- Wind: {weather_data.get('wind_kph')} km/h

Air Quality:
- PM2.5: {weather_data.get('pm2_5')} µg/m³ ({air_quality['level']})
- Status: {air_quality['description']}

Safety Score: {safety_analysis['safety_score']}/100 - {safety_analysis['safety_level']}
Overall: {safety_analysis['overall_recommendation']}
"""
            # Only add predictions if available
            if predictions:
                context += f"""
Prediction (Next Hour):
- Temperature will be {predictions.get('temperature')}°C ({predictions.get('temperature_trend')})
- PM2.5 will be {predictions.get('pm2_5')} µg/m³ ({predictions.get('pm25_trend')})
"""

            context += """
IMPORTANT INSTRUCTIONS:
1. **Be conversational and natural** - respond like a helpful friend, not a robot
2. **Only mention data that's relevant** to what the user asked:
   - If they say "hi" or "hello", greet them warmly and ask how you can help
   - If they ask about air quality, focus on PM2.5 and air quality status
   - If they ask about temperature, focus on temperature
   - If they ask about safety/walking/outdoor activities, provide safety analysis
   - If they ask about predictions/future, use the prediction data
   - If they ask a general question, give a brief summary
3. **Don't dump all data** unless they ask for a complete summary
4. **Be engaging** - use emojis naturally, ask follow-up questions
5. **Keep it concise** - 1-3 sentences for simple queries, more only if needed
6. **Sound human** - vary your responses, don't be formulaic

Now respond naturally to the user's question:"""

        # Call OpenAI API
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a friendly, conversational environmental AI assistant. You chat naturally with users and only provide data they actually need. You are helpful but not robotic.'},
                    {'role': 'user', 'content': context}
                ],
                'temperature': 0.9,  # Higher temperature for more natural, varied responses
                'max_tokens': 300
            },
            timeout=15
        )

        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            return ai_response
        else:
            error_info = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ OpenAI API error: {response.status_code} - {error_info}")

            # If quota exceeded, provide helpful error message
            if response.status_code == 429:
                return "🔑 **API Quota Exceeded**: The OpenAI API key has run out of credits. You can:\n\n1. Add billing details at https://platform.openai.com/account/billing\n2. Use a different API key\n3. Switch to template mode (set USE_AI_API = False)\n\nFor now, I'll use my template-based responses!"
            return None

    except Exception as e:
        print(f"❌ AI generation error: {str(e)}")
        return None

def generate_ai_response(user_query, weather_data, location):
    """Generate intelligent response based on environmental data analysis"""

    # Extract key metrics
    temp_c = weather_data.get('temp_c')
    humidity = weather_data.get('humidity')
    pm25 = weather_data.get('pm2_5')
    pm10 = weather_data.get('pm10')
    wind_kph = weather_data.get('wind_kph')
    condition = weather_data.get('condition', {}).get('text', 'Unknown')

    # Analyze air quality
    air_quality = analyze_air_quality(pm25, pm10, location)

    # Analyze outdoor safety
    safety_analysis = analyze_outdoor_safety(weather_data, air_quality)

    # Get predictions
    predictions = predict_next_hour_conditions(location)

    # Analyze correlations
    correlations = analyze_correlation_factors(weather_data)

    # Try to use AI API first if enabled
    ai_generated_answer = None
    if USE_AI_API:
        ai_generated_answer = generate_ai_response_with_openai(
            user_query, weather_data, location, air_quality, 
            safety_analysis, predictions, correlations
        )

    # Build comprehensive response
    response = {
        'query': user_query,
        'location': location,
        'timestamp': datetime.now().isoformat(),
        'current_conditions': {
            'temperature': f"{temp_c}°C" if temp_c else 'N/A',
            'humidity': f"{humidity}%" if humidity else 'N/A',
            'wind_speed': f"{wind_kph} km/h" if wind_kph else 'N/A',
            'weather': condition,
            'pm2_5': f"{pm25} µg/m³" if pm25 else 'N/A',
            'pm10': f"{pm10} µg/m³" if pm10 else 'N/A'
        },
        'air_quality': air_quality,
        'safety_analysis': safety_analysis,
        'predictions': predictions,
        'correlations': correlations,
        'answer': '',
        'ai_powered': ai_generated_answer is not None
    }

    # Use AI-generated answer if available, otherwise use template-based
    if ai_generated_answer:
        response['answer'] = ai_generated_answer
        return response

    # FALLBACK: Template-based response generation
    query_lower = user_query.lower()

    if any(word in query_lower for word in ['walk', 'jog', 'run', 'exercise', 'outdoor', 'outside', 'go out']):
        # Safety-related query
        response['answer'] = f"{safety_analysis['overall_recommendation']}\n\n"
        response['answer'] += f"Current air quality is {air_quality['level']} with PM2.5 at {pm25} µg/m³. "
        response['answer'] += f"Temperature is {temp_c}°C with {humidity}% humidity.\n\n"

        if safety_analysis['warnings']:
            response['answer'] += "⚠️ **Warnings:**\n" + "\n".join(f"• {w}" for w in safety_analysis['warnings']) + "\n\n"

        if safety_analysis['recommendations']:
            response['answer'] += "💡 **Recommendations:**\n" + "\n".join(f"• {r}" for r in safety_analysis['recommendations'])

    elif any(word in query_lower for word in ['predict', 'forecast', 'next hour', 'later', 'future', 'after', 'will be']):
        # Prediction query
        if predictions:
            response['answer'] = f"📊 **Next Hour Forecast for {location}:**\n\n"
            response['answer'] += f"• Temperature: {predictions['temperature']}°C ({predictions['temperature_trend']})\n"
            response['answer'] += f"• Humidity: {predictions['humidity']}%\n"
            response['answer'] += f"• PM2.5: {predictions['pm2_5']} µg/m³ ({predictions['pm25_trend']})\n\n"

            if predictions['pm25_trend'] == 'rising':
                response['answer'] += "⚠️ Air quality is expected to worsen. Consider outdoor activities now rather than later."
            else:
                response['answer'] += "✅ Air quality is expected to improve. Conditions should get better."
        else:
            response['answer'] = "❌ Insufficient historical data to make predictions. Please check back later."

    else:
        # General query
        response['answer'] = f"🌤️ **Current conditions in {location}:**\n\n"
        response['answer'] += f"• Weather: {condition}\n"
        response['answer'] += f"• Temperature: {temp_c}°C\n"
        response['answer'] += f"• Humidity: {humidity}%\n"
        response['answer'] += f"• Wind Speed: {wind_kph} km/h\n"
        response['answer'] += f"• Air Quality: {air_quality['level']} (PM2.5: {pm25} µg/m³)\n\n"
        response['answer'] += f"**Safety Assessment:** {safety_analysis['safety_level']} ({safety_analysis['safety_score']}/100)\n\n"
        response['answer'] += safety_analysis['overall_recommendation']

    return response

@app.post("/api/ai/assistant")
async def ai_assistant(request: Request):
    """
    AI-powered environmental assistant
    Body: {query: string, weather_data: object, location: string}
    """
    try:
        data = await request.json()
        user_query = data.get('query', '')
        weather_data = data.get('weather_data', {})
        location = data.get('location', 'Unknown')

        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Generate AI response
        ai_response = generate_ai_response(user_query, weather_data, location)

        return ai_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("  Environmental Monitoring & Alert System - FastAPI Backend")
    print("=" * 70)
    print(f"  Server starting at: http://localhost:8000")
    print(f"  API Base URL: http://localhost:8000")
    print(f"  Docs: http://localhost:8000/docs")
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000)