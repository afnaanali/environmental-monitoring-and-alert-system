# Historical Graph Feature Guide 📊

## Overview
The Historical Graph section displays real-time data collected from your database, showing trends for **Temperature**, **Humidity**, and **PM2.5** air quality over customizable time periods.

---

## ✨ Features

### 1. **Interactive Time Range Selection**
Choose different time periods to view:
- **6 hours** (default) - Recent trends
- **12 hours** - Half-day overview
- **24 hours** - Full day analysis
- **48 hours** - Two-day comparison

### 2. **Multi-Metric Visualization**
Toggle visibility of three key environmental parameters:
- 🌡️ **Temperature (°C)** - Red line with left Y-axis
- 💧 **Humidity (%)** - Blue line with right Y-axis  
- 🌫️ **PM2.5 (µg/m³)** - Yellow line with right Y-axis

### 3. **Real-Time Database Integration**
- Displays actual readings stored in your SQLite database
- Auto-updates when you search for a location
- Shows data collection status and reading count
- Automatic refresh with new data every 5 minutes

---

## 🚀 How to Use

### Step 1: Search for a Location
1. Enter a city name in the search bar (e.g., "Mumbai", "Delhi", "London")
2. Click the search button or press Enter
3. The system will load current weather + historical data

### Step 2: View Historical Graph
The **"Historical Data from Database"** section will automatically:
- ✅ Display readings if data exists in database
- ⚠️ Show a warning if no data is available yet
- 📊 Plot temperature, humidity, and PM2.5 trends

### Step 3: Customize Your View
**Select Time Range:**
- Click any time button (6h, 12h, 24h, 48h) to change the period
- Active button is highlighted in blue

**Toggle Metrics:**
- Check/uncheck boxes to show/hide specific metrics
- Temperature, Humidity, PM2.5 can be toggled independently
- Chart updates instantly when you change selections

---

## 📈 Understanding the Graph

### Chart Elements
```
┌─────────────────────────────────────────────┐
│  🌡️ Temperature (Red)      ← Left Y-axis   │
│  💧 Humidity (Blue)        ← Right Y-axis   │
│  🌫️ PM2.5 (Yellow)         ← Right Y-axis   │
│                                              │
│  X-axis → Time (HH:MM format)               │
└─────────────────────────────────────────────┘
```

### Status Messages
- **Blue (Info)**: "Search for a location to view historical data"
- **Green (Success)**: "✓ Displaying X readings from database (last Yh)"
- **Orange (Warning)**: "No historical data available for [location]"

---

## 🎯 Tips for Best Results

### 1. **Wait for Data Collection**
The system collects data every **5 minutes** for monitored locations:
- London, Mumbai, Delhi, New York, Tokyo

If you search for these cities, you'll see historical data immediately!

### 2. **New Locations**
For new (non-monitored) locations:
- First search: May show "no data available"
- System will start collecting data for that location
- Check back after 15-30 minutes for historical trends

### 3. **Compare Metrics**
- **Temperature + Humidity**: See inverse relationships (high temp = low humidity)
- **PM2.5 + Humidity**: High humidity often reduces PM2.5 (rain effect)
- **All Three**: Comprehensive environmental overview

### 4. **Time Range Selection**
- **6h**: Best for current conditions and immediate trends
- **12h**: Good for half-day pattern analysis
- **24h**: Full daily cycle (day/night variations)
- **48h**: Compare today vs yesterday

---

## 🔧 Technical Details

### Data Source
```
Flask Backend → SQLite Database → Historical API Endpoint
         ↓
   Chart.js Visualization
```

### API Endpoint Used
```
GET /api/historical/<location>?hours=<time_range>
```

### Database Table
- **Table Name**: `weather_readings`
- **Update Frequency**: Every 5 minutes (background scheduler)
- **Columns Used**: timestamp, temp_c, humidity, pm2_5, location_name

### Chart Library
- **Library**: Chart.js v3
- **Type**: Multi-axis Line Chart
- **Features**: Tooltips, responsive, smooth curves (tension: 0.4)

---

## 🐛 Troubleshooting

### Issue: "No historical data available"
**Solution:**
- ✅ Ensure Flask server is running (`python app.py`)
- ✅ Wait 5-15 minutes for data collection
- ✅ Check monitored locations first (London, Mumbai, Delhi, etc.)
- ✅ Verify database has data: http://localhost:5000/api/stats

### Issue: Graph not updating after search
**Solution:**
- 🔄 Refresh the page (Ctrl+R or F5)
- 🔄 Check browser console for errors (F12)
- 🔄 Verify API response: http://localhost:5000/api/historical/Mumbai

### Issue: Chart shows only one or two metrics
**Solution:**
- ✓ Check metric toggle checkboxes (Temperature, Humidity, PM2.5)
- ✓ Ensure all boxes are checked to show all metrics

### Issue: Time range buttons not working
**Solution:**
- 🔄 Clear browser cache and reload
- 🔄 Check for JavaScript errors in console
- 🔄 Verify location has data for selected time range

---

## 📊 Example Use Cases

### 1. Daily Temperature Pattern Analysis
```
1. Search for "Delhi"
2. Select "24h" time range
3. Observe morning/afternoon/evening temperature changes
4. Notice peak temperatures around 2-3 PM
```

### 2. Air Quality Monitoring
```
1. Search for "Mumbai"
2. Enable only PM2.5 checkbox
3. Select "48h" to compare yesterday vs today
4. Identify pollution peaks (usually morning/evening rush hours)
```

### 3. Humidity-Temperature Correlation
```
1. Search for any tropical location
2. Enable Temperature + Humidity
3. Select "24h" time range
4. Observe inverse relationship (T↑ → H↓)
```

### 4. Multi-City Comparison
```
1. Search "London" → Note temperatures
2. Switch to "12h" range → Observe patterns
3. Search "Tokyo" → Compare with London
4. Analyze different climate behaviors
```

---

## 🌟 Advanced Features

### Auto-Refresh
The graph automatically reloads when:
- You search for a new location
- You change the time range
- Background scheduler adds new readings (every 5 minutes)

### Smart Fallback
If no historical data exists:
- Shows informative message instead of error
- Suggests waiting for data collection
- Maintains user experience

### Performance Optimization
- Charts use Canvas rendering (smooth 60fps)
- Data is cached on backend (5-minute TTL)
- Only visible metrics are rendered
- Efficient database queries with indexed columns

---

## 📚 Related Documentation

- [HISTORICAL_SYSTEM_GUIDE.md](./HISTORICAL_SYSTEM_GUIDE.md) - Complete system documentation
- [dashboard.html](./dashboard.html) - System monitoring dashboard
- [app.py](./app.py) - Backend API implementation
- [database.py](./database.py) - Database operations

---

## 🎨 Customization

### Change Default Time Range
Edit `script.js`:
```javascript
let selectedTimeRange = 6; // Change to 12, 24, or 48
```

### Modify Chart Colors
Edit the color values in `script.js`:
```javascript
borderColor: '#ff6384',  // Temperature (red)
borderColor: '#36a2eb',  // Humidity (blue)
borderColor: '#ffce56',  // PM2.5 (yellow)
```

### Adjust Data Collection Frequency
Edit `app.py`:
```python
scheduler.add_job(
    fetch_and_store_data,
    'interval',
    minutes=5  # Change to desired interval
)
```

---

## 📞 Support

For issues or questions:
1. Check Flask server terminal for error logs
2. Open browser console (F12) for frontend errors
3. Verify API endpoints at http://localhost:5000/api/stats
4. Check database has data: http://localhost:5000/dashboard.html

---

**Last Updated**: January 31, 2026
**Version**: 1.0
**Status**: ✅ Fully Operational
