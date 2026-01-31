# Environmental Monitoring & Alert System

A comprehensive web-based environmental monitoring system that provides real-time data on air quality, weather conditions, and environmental risk assessment.

## Features

✅ **Real-time Environmental Data**
- Temperature and humidity monitoring
- Wind speed and direction
- Atmospheric pressure
- Visibility metrics
- UV index

✅ **Air Quality Monitoring**
- Air Quality Index (AQI)
- PM2.5 and PM10 particulate matter
- Ozone (O₃) levels
- Nitrogen Dioxide (NO₂) levels

✅ **Intelligent Risk Assessment**
- Multi-factor environmental risk scoring
- Correlation analysis between environmental factors
- Contextual alerts for high-risk conditions
- Pattern detection (e.g., high PM2.5 + low wind = pollution accumulation)

✅ **Data Visualization**
- Interactive map with location markers
- 24-hour temperature and humidity trend charts
- Real-time data updates
- Responsive design for all devices

✅ **User-Friendly Interface**
- Search by city name or coordinates
- Automatic geolocation support
- Clean, modern dark theme
- Intuitive dashboard layout

## How to Use

1. **Open the Website**
   - Simply open `index.html` in any modern web browser
   - No installation or server setup required

2. **Search for a Location**
   - Enter a city name (e.g., "London", "New York", "Tokyo")
   - Or enter coordinates (e.g., "51.5074,-0.1278")
   - Click "Monitor Location" or press Enter

3. **Use Current Location**
   - Click the location button (📍) to automatically detect your location
   - Grant location permission when prompted

4. **View Environmental Data**
   - Current conditions (temperature, humidity, wind, etc.)
   - Air quality index and pollutant levels
   - Environmental risk score
   - Correlation analysis
   - Historical trends chart
   - Interactive map

## API Configuration

The system uses the following free APIs:

### WeatherAPI.com (Primary Data Source)
- **Free Tier**: 1,000,000 calls/month
- Provides: Weather data, forecasts, and air quality
- Current API key is included (free tier)

To use your own API key:
1. Sign up at [weatherapi.com](https://www.weatherapi.com/)
2. Get your free API key
3. Replace the API key in `script.js`:
```javascript
const API_KEY = 'YOUR_API_KEY_HERE';
```

## Technical Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Mapping**: Leaflet.js
- **Charts**: Chart.js
- **APIs**: WeatherAPI.com
- **Icons**: Font Awesome

## Features Breakdown

### Risk Scoring Algorithm
The system calculates environmental risk based on:
- Temperature extremes (>35°C or <-10°C)
- Humidity levels (<20% or >80%)
- Wind speed (>50 km/h)
- Air quality (EPA Index)
- UV index (>8)

Risk levels:
- **Low Risk**: 0-30
- **Moderate Risk**: 31-60
- **High Risk**: 61-100

### Correlation Analysis
The system detects:
- High PM2.5 + Low wind = Poor air dispersion
- High temperature + High PM2.5 = Ozone formation risk
- High humidity + High temperature = Heat stress
- High UV + Clear skies = Sun protection needed
- Low pressure = Weather changes likely

### Auto-Refresh
- Data automatically refreshes every 5 minutes
- Real-time clock updates every second
- Manual refresh available via search

## Browser Compatibility

✅ Chrome/Edge (recommended)
✅ Firefox
✅ Safari
✅ Opera

Requires JavaScript enabled and internet connection.

## Project Structure

```
jjj/
├── index.html      # Main HTML structure
├── style.css       # Styling and responsive design
├── script.js       # Core functionality and API integration
└── README.md       # This file
```

## Future Enhancements

Potential additions:
- Historical data storage (using IndexedDB)
- Comparison between multiple locations
- Email/SMS alerts for critical conditions
- More data sources (OpenAQ, PurpleAir)
- Predictive analytics using machine learning
- Export data to CSV/PDF
- Weather radar overlay
- Air quality forecast

## Troubleshooting

**Problem**: Location not found
- **Solution**: Check spelling, try coordinates instead

**Problem**: No data displayed
- **Solution**: Check internet connection, try a different location

**Problem**: Geolocation not working
- **Solution**: Grant location permission in browser settings

**Problem**: Map not loading
- **Solution**: Check internet connection, refresh page

## License

This project is open source and available for educational and personal use.

## Credits

- Weather data: [WeatherAPI.com](https://www.weatherapi.com/)
- Maps: [OpenStreetMap](https://www.openstreetmap.org/) & [Leaflet.js](https://leafletjs.com/)
- Charts: [Chart.js](https://www.chartjs.org/)
- Icons: [Font Awesome](https://fontawesome.com/)

## Contact & Support

For issues, suggestions, or contributions, please contact the development team.

---

**Built with ❤️ for environmental awareness**

Last Updated: January 2026
