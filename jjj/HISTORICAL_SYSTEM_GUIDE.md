# Historical Data & Prediction System - Complete Guide

## 🎯 Overview

The system now includes **automated data collection**, **database storage**, and **predictive analytics** for environmental monitoring.

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE SYSTEM FLOW                      │
└─────────────────────────────────────────────────────────────┘

1. AUTOMATIC DATA COLLECTION (Every 5 minutes)
   ┌──────────────┐
   │  Background  │──→ Fetches data for 5 cities
   │  Scheduler   │    (London, Mumbai, Delhi, NYC, Tokyo)
   └──────────────┘
         ↓
   ┌──────────────┐
   │  WeatherAPI  │──→ Real-time weather + air quality
   └──────────────┘
         ↓
   ┌──────────────┐
   │   Database   │──→ Stores: temp, humidity, PM2.5, etc.
   │  (SQLite)    │    with timestamps
   └──────────────┘

2. USER SEARCHES FOR LOCATION
   ┌──────────────┐
   │   Frontend   │──→ Searches "Kochi"
   └──────────────┘
         ↓
   ┌──────────────┐
   │   Backend    │──→ Fetches current data + saves to DB
   └──────────────┘
         ↓
   ┌──────────────┐
   │  Historical  │──→ Retrieves last 24 hours of data
   │     API      │
   └──────────────┘
         ↓
   ┌──────────────┐
   │  Prediction  │──→ Analyzes trends, predicts next hour
   │   Engine     │
   └──────────────┘
         ↓
   ┌──────────────┐
   │    Chart     │──→ Shows historical + predicted values
   └──────────────┘

```

## 🗄️ Database Structure

### `weather_readings` Table
Stores all weather measurements with timestamps

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| location_name | TEXT | City name (e.g., "London") |
| location_lat | REAL | Latitude |
| location_lon | REAL | Longitude |
| timestamp | DATETIME | When data was recorded |
| temp_c | REAL | Temperature in Celsius |
| humidity | INTEGER | Humidity percentage |
| wind_kph | REAL | Wind speed |
| pm2_5 | REAL | PM2.5 air pollution |
| pm10 | REAL | PM10 air pollution |
| o3 | REAL | Ozone level |
| no2 | REAL | Nitrogen dioxide |
| risk_score | INTEGER | Calculated risk (0-100) |

### `predictions` Table
Stores AI predictions for future values

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| location_name | TEXT | City name |
| prediction_for | DATETIME | When prediction is for |
| predicted_temp_c | REAL | Predicted temperature |
| predicted_humidity | INTEGER | Predicted humidity |
| predicted_pm2_5 | REAL | Predicted pollution |
| confidence_score | REAL | 0.0-1.0 confidence |
| algorithm | TEXT | Prediction method used |

## 🔄 Automatic Data Collection

### How It Works
1. **Background Scheduler** runs every 5 minutes
2. Fetches data for all monitored locations
3. Saves to database with timestamp
4. Logs success/failure for each location

### Monitored Locations (Default)
- London
- Mumbai
- Delhi
- New York
- Tokyo

### Viewing Collection Status
Check Flask terminal output:
```
🔄 [14:23:15] Fetching data for monitored locations...
  ✅ London: Reading #42 saved
  ✅ Mumbai: Reading #43 saved
  ✅ Delhi: Reading #44 saved
  ✅ New York: Reading #45 saved
  ✅ Tokyo: Reading #46 saved
✅ Data collection completed at 14:23:18
```

## 🔮 Prediction Algorithm

### Method: Linear Trend + Moving Average

**Step 1: Collect Recent Data**
- Uses last 12 readings (1 hour of data at 5-min intervals)
- Minimum 3 readings required

**Step 2: Calculate Trends**
```python
Temperature Trend = (Change in temp) / (Time period)
Humidity Trend = (Change in humidity) / (Time period)
PM2.5 Trend = (Change in pollution) / (Time period)
```

**Step 3: Project Forward**
```
Predicted Value = Last Value + (Trend × Time Ahead)
```

**Step 4: Calculate Confidence**
- Based on data variance (consistency)
- More stable data = higher confidence
- Range: 50% to 95%

### Example Prediction Output
```json
{
  "prediction_for": "2026-01-31T15:30:00",
  "predicted_temp_c": 28.5,
  "predicted_humidity": 72,
  "predicted_pm2_5": 45.2,
  "confidence_score": 0.87,
  "algorithm": "Linear Trend + Moving Average",
  "data_points_used": 12,
  "trends": {
    "temperature_trend": +0.3,
    "humidity_trend": -1.2,
    "pm25_trend": +2.1
  }
}
```

## 🌐 New API Endpoints

### 1. Get Historical Data
```
GET /api/historical/<location>?hours=24
```
**Response:**
```json
{
  "success": true,
  "location": "Kochi",
  "data_points": 48,
  "data": [
    {
      "timestamp": "2026-01-31 13:00:00",
      "temp_c": 28.3,
      "humidity": 75,
      "pm2_5": 42.1,
      "wind_kph": 12.5
    }
  ]
}
```

### 2. Get Prediction (Next Hour)
```
GET /api/predict/<location>
```
**Response:**
```json
{
  "success": true,
  "location": "Kochi",
  "prediction": {
    "predicted_temp_c": 28.5,
    "predicted_humidity": 72,
    "confidence_score": 0.87
  }
}
```

### 3. Get Multi-Hour Predictions
```
GET /api/predict/<location>/multi?hours=6
```
Returns array of predictions for next 6 hours

### 4. Pattern Analysis
```
GET /api/analysis/<location>?hours=48
```
Returns statistical analysis:
- Temperature trends
- Humidity patterns
- Pollution anomalies
- Data quality metrics

### 5. Database Statistics
```
GET /api/stats
```
**Response:**
```json
{
  "database": {
    "total_readings": 1250,
    "unique_locations": 5,
    "oldest_reading": "2026-01-30 08:00:00",
    "newest_reading": "2026-01-31 14:30:00"
  },
  "monitored_locations": ["London", "Mumbai", "Delhi", "New York", "Tokyo"]
}
```

### 6. Get Monitored Locations
```
GET /api/locations/monitored
```
Lists all auto-monitored cities with latest readings

### 7. Database Cleanup
```
POST /api/database/cleanup
Body: { "days": 30 }
```
Deletes readings older than 30 days

## 📈 Frontend Integration

### Chart Enhancement
The historical chart now shows:

1. **Blue Line**: Historical temperature (from database)
2. **Light Blue Line**: Historical humidity (from database)
3. **Predicted Point**: Next hour prediction (marked)

### Prediction Display
When prediction is available, shows alert:
```
🔮 Next hour prediction: 28.5°C, 72% humidity (87% confidence)
```

## 🚀 How to Use

### Start the System
```bash
python app.py
```

**What Happens:**
1. ✅ Database initialized
2. ✅ Initial data fetch for 5 cities
3. ✅ Background scheduler starts
4. ✅ Server ready at http://localhost:5000

### Search for Location
1. Go to http://localhost:5000
2. Type city name (e.g., "Mumbai")
3. Click "Monitor Location"

**What You Get:**
- Current weather conditions
- Historical chart (24 hours from database)
- Prediction for next hour (if data available)
- Pattern analysis and trends

### View Historical Trends
- Chart automatically shows database data if available
- Falls back to forecast data if no history exists
- Prediction added as final point on chart

## 📊 Data Flow Example

### Scenario: User Searches "Mumbai"

**Step 1: Backend Fetches Current Data**
```
WeatherAPI → Backend → Database (saves reading #123)
```

**Step 2: Backend Retrieves History**
```
Database → Last 48 readings (24 hours) → Backend
```

**Step 3: Backend Generates Prediction**
```
Analyze 48 readings → Calculate trends → Predict next hour
Temperature: 32°C → 32.3°C (trend: +0.3°C/hour)
Humidity: 68% → 66% (trend: -2%/hour)
Confidence: 89% (data very consistent)
```

**Step 4: Frontend Displays**
```
Chart: 48 historical points + 1 predicted point
Alert: "🔮 Next hour: 32.3°C, 66% humidity (89% confidence)"
```

## 🔧 Configuration

### Change Monitored Locations
Edit `app.py`:
```python
MONITORED_LOCATIONS = ['London', 'Mumbai', 'Delhi', 'Kochi', 'Chennai']
```

### Change Collection Interval
Edit scheduler configuration:
```python
scheduler.add_job(func=fetch_and_store_data, trigger="interval", minutes=5)
```
Change `minutes=5` to desired interval

### Database Retention
Set automatic cleanup in `app.py`:
```python
# Add to scheduler
scheduler.add_job(func=lambda: cleanup_old_data(30), trigger="cron", hour=2)
```
Runs daily at 2 AM, deletes data older than 30 days

## 📁 File Structure

```
jjj/
├── app.py                 # Main Flask application (updated)
├── database.py            # Database operations (NEW)
├── predictions.py         # Prediction algorithms (NEW)
├── script.js              # Frontend JS (updated)
├── index.html             # HTML interface
├── style.css              # Styling
├── weather_data.db        # SQLite database (auto-created)
└── requirements.txt       # Python dependencies (updated)
```

## 🎯 Key Benefits

### Before (Old System)
❌ Only shows forecast data
❌ No historical trends
❌ No predictions
❌ Manual data refresh only

### After (New System)
✅ Automatic data collection every 5 minutes
✅ Stores all readings in database
✅ Shows real historical trends (not just forecasts)
✅ AI predictions for next hour
✅ Pattern analysis and anomaly detection
✅ Confidence scores for predictions
✅ Multi-location monitoring

## 🧪 Testing the System

### 1. Check Data Collection
Watch Flask terminal for 5 minutes:
```
🔄 [14:30:00] Fetching data for monitored locations...
  ✅ London: Reading #50 saved
```

### 2. Verify Database
After 30 minutes, search for a monitored city:
- Chart should show historical data points
- Prediction should appear

### 3. Test Prediction API
```bash
curl http://localhost:5000/api/predict/Mumbai
```

### 4. View Database Stats
```bash
curl http://localhost:5000/api/stats
```

## 🐛 Troubleshooting

### No Historical Data Showing
**Problem:** Chart shows forecast instead of history
**Solution:** 
- Wait 15-30 minutes for data collection
- Check if location is in MONITORED_LOCATIONS
- Manually trigger: search for location to save first reading

### Prediction Error: "Insufficient Data"
**Problem:** Need at least 3 readings
**Solution:** 
- Wait for 3-4 data collection cycles (15-20 minutes)
- Or search location 3 times manually

### Database Not Created
**Problem:** weather_data.db missing
**Solution:**
- Check file permissions
- Restart Flask server
- Database auto-creates on first run

## 📝 Summary

**What You Built:**
1. ✅ Automatic background data collector
2. ✅ SQLite database for historical storage
3. ✅ Prediction engine with confidence scores
4. ✅ Enhanced charts with real + predicted data
5. ✅ 8 new API endpoints
6. ✅ Pattern analysis system

**Result:**
➡️ Complete historical trend analysis + AI predictions
➡️ Real-time monitoring with automated updates
➡️ Data-driven insights for 5+ cities continuously

**Next Steps:**
- Add more locations to MONITORED_LOCATIONS
- Implement more sophisticated ML models
- Add data export functionality
- Create admin dashboard for database management
