// Environmental Monitoring System - Main JavaScript

// API Configuration - Now using Flask Backend
// Check if we're running on file:// protocol (direct HTML) or http:// (Flask server)
const isFileProtocol = window.location.protocol === 'file:';
const BACKEND_URL = isFileProtocol ? 'http://localhost:5000' : window.location.origin;
const API_BASE = `${BACKEND_URL}/api`;

// ═══════════════════════════════════════════════════════════════════
// NOTIFICATION SOUND SYSTEM
// ═══════════════════════════════════════════════════════════════════

let alertSoundEnabled = true; // Default: sound enabled
let audioContext = null;

// Initialize Audio Context (for Web Audio API)
function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

// Play notification beep sound using Web Audio API
function playAlertSound(severity = 'medium') {
    if (!alertSoundEnabled) return;
    
    try {
        const ctx = initAudioContext();
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        
        // Different tones for different severity levels
        if (severity === 'high' || severity === 'critical') {
            // High priority: Double beep with urgent tone
            oscillator.frequency.setValueAtTime(800, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.2);
            
            // Second beep
            setTimeout(() => {
                const osc2 = ctx.createOscillator();
                const gain2 = ctx.createGain();
                osc2.connect(gain2);
                gain2.connect(ctx.destination);
                osc2.frequency.setValueAtTime(800, ctx.currentTime);
                gain2.gain.setValueAtTime(0.3, ctx.currentTime);
                gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
                osc2.start(ctx.currentTime);
                osc2.stop(ctx.currentTime + 0.2);
            }, 250);
        } else if (severity === 'medium') {
            // Medium priority: Single medium tone
            oscillator.frequency.setValueAtTime(600, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.3);
        } else {
            // Low priority: Gentle notification
            oscillator.frequency.setValueAtTime(440, ctx.currentTime);
            gainNode.gain.setValueAtTime(0.15, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.25);
        }
        
        oscillator.type = 'sine';
    } catch (error) {
        console.warn('Unable to play alert sound:', error);
    }
}

// Toggle sound on/off
function toggleAlertSound() {
    alertSoundEnabled = !alertSoundEnabled;
    const button = document.getElementById('soundToggle');
    if (button) {
        button.innerHTML = alertSoundEnabled 
            ? '<i class="fas fa-volume-up"></i>' 
            : '<i class="fas fa-volume-mute"></i>';
        button.title = alertSoundEnabled ? 'Mute alert sounds' : 'Unmute alert sounds';
    }
    
    // Play a test sound when enabling
    if (alertSoundEnabled) {
        playAlertSound('low');
    }
}

console.log('Running on:', window.location.protocol);
console.log('Backend URL:', BACKEND_URL);
console.log('API Base:', API_BASE);

// Global variables
let map;
let marker;
let weatherChart;
let currentLocationData = null;
let historicalData = {
    temperature: [],
    humidity: [],
    timestamps: []
};
let sensorMarkers = []; // Store sensor location markers

// Industrial zones and pollution sources database
const pollutionSources = {
    'london': {
        industrial: { direction: 'E', name: 'Thames Gateway Industrial Area', distance: '15km' },
        traffic: { direction: 'N', name: 'M25 Motorway', distance: '10km' },
        airport: { direction: 'W', name: 'Heathrow Airport', distance: '25km' }
    },
    'mumbai': {
        industrial: { direction: 'NE', name: 'Mahul Industrial Area', distance: '12km' },
        traffic: { direction: 'W', name: 'Western Express Highway', distance: '5km' },
        port: { direction: 'S', name: 'Mumbai Port', distance: '8km' }
    },
    'delhi': {
        industrial: { direction: 'W', name: 'Gurgaon Industrial Belt', distance: '20km' },
        traffic: { direction: 'S', name: 'Ring Road', distance: '3km' },
        power: { direction: 'E', name: 'Badarpur Power Plant', distance: '18km' }
    },
    'beijing': {
        industrial: { direction: 'S', name: 'Hebei Industrial Zone', distance: '50km' },
        traffic: { direction: 'E', name: 'Beijing Ring Roads', distance: '10km' },
        coal: { direction: 'SW', name: 'Coal Heating Plants', distance: '15km' }
    },
    'los angeles': {
        industrial: { direction: 'S', name: 'Long Beach Port', distance: '30km' },
        traffic: { direction: 'N', name: 'I-405 Freeway', distance: '8km' },
        refinery: { direction: 'SW', name: 'Oil Refineries', distance: '25km' }
    },
    'new york': {
        industrial: { direction: 'W', name: 'New Jersey Industrial Corridor', distance: '20km' },
        traffic: { direction: 'N', name: 'Cross Bronx Expressway', distance: '10km' },
        airport: { direction: 'E', name: 'JFK Airport', distance: '25km' }
    },
    'paris': {
        industrial: { direction: 'NE', name: 'Seine-Saint-Denis Industrial Zone', distance: '15km' },
        traffic: { direction: 'W', name: 'Périphérique Ring Road', distance: '5km' },
        airport: { direction: 'NE', name: 'Charles de Gaulle Airport', distance: '30km' }
    },
    'tokyo': {
        industrial: { direction: 'E', name: 'Tokyo Bay Industrial Area', distance: '20km' },
        traffic: { direction: 'W', name: 'Shuto Expressway', distance: '8km' },
        port: { direction: 'SE', name: 'Tokyo Port', distance: '15km' }
    },
    'shanghai': {
        industrial: { direction: 'N', name: 'Baoshan Industrial Zone', distance: '25km' },
        traffic: { direction: 'W', name: 'Inner Ring Road', distance: '10km' },
        port: { direction: 'E', name: 'Shanghai Port', distance: '30km' }
    }
};

// Wind direction mapping
const windDirections = {
    'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
    'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
    'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
    'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Update current time
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // Initialize map
    initializeMap();

    // Event listeners
    document.getElementById('searchBtn').addEventListener('click', searchLocation);
    document.getElementById('currentLocationBtn').addEventListener('click', getCurrentLocation);
    document.getElementById('locationInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchLocation();
    });

    // Initialize empty chart
    initializeChart();
}

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString('en-US', { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('currentTime').textContent = timeString;
}

// Initialize Leaflet Map
function initializeMap() {
    map = L.map('map').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Load sensor markers for monitored locations
    loadSensorMarkers();
}

// Load and display sensor markers for monitored locations
async function loadSensorMarkers() {
    try {
        console.log('🔄 Loading sensor markers...');
        const response = await fetch(`${API_BASE}/locations/monitored`);
        const result = await response.json();
        
        console.log('📡 API Response:', result);
        
        if (result.success && result.locations) {
            console.log(`✅ Found ${result.locations.length} locations`);
            for (const location of result.locations) {
                console.log('📍 Adding marker for:', location);
                await addSensorMarker(location);
            }
        } else {
            console.warn('⚠️ No locations data in response');
        }
    } catch (error) {
        console.error('❌ Error loading sensor markers:', error);
    }
}

// Add a sensor marker to the map
async function addSensorMarker(locationData) {
    console.log('🎯 addSensorMarker called with:', locationData);
    
    const { location_name, lat, lon, temp_c, humidity, pm2_5, risk_score, timestamp } = locationData;
    
    console.log(`📌 Coordinates: lat=${lat}, lon=${lon}, risk=${risk_score}`);
    
    // Validate coordinates
    if (!lat || !lon || isNaN(lat) || isNaN(lon)) {
        console.error(`❌ Invalid coordinates for ${location_name}: lat=${lat}, lon=${lon}`);
        return;
    }
    
    // Determine marker color based on risk score
    const markerColor = getRiskMarkerColor(risk_score);
    console.log(`🎨 Marker color for ${location_name}: ${markerColor} (risk: ${risk_score})`);
    
    // Create custom colored marker with larger size and solid circle
    const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
            background: ${markerColor};
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 4px solid white;
            box-shadow: 0 3px 10px rgba(0,0,0,0.5);
            position: relative;
        "></div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        popupAnchor: [0, -20]
    });
    
    console.log(`✅ Creating marker for ${location_name} at [${lat}, ${lon}]`);
    const sensorMarker = L.marker([lat, lon], { icon: markerIcon }).addTo(map);
    console.log(`✅ Marker added to map for ${location_name}`);
    
    // Format values for display
    const tempDisplay = (temp_c !== null && temp_c !== undefined) ? `${temp_c.toFixed(1)}°C` : 'Loading...';
    const humidityDisplay = (humidity !== null && humidity !== undefined) ? `${humidity}%` : 'Loading...';
    const pm25Display = (pm2_5 !== null && pm2_5 !== undefined) ? `${pm2_5.toFixed(1)} µg/m³` : 'Loading...';
    const riskDisplay = (risk_score !== null && risk_score !== undefined) ? `${risk_score}/100` : 'Loading...';
    
    // Create popup content with white text for better visibility
    const popupContent = `
        <div style="min-width: 220px; font-family: Arial, sans-serif; color: #ffffff;">
            <h3 style="margin: 0 0 12px 0; color: #fff; background: ${markerColor}; padding: 10px; border-radius: 5px; text-align: center; font-size: 18px;">
                📍 ${location_name}
            </h3>
            <div style="margin: 10px 0; color: #ffffff; line-height: 1.8; font-size: 14px;">
                <div style="margin: 6px 0;"><strong style="color: #ffd700;">🌡️ Temperature:</strong> ${tempDisplay}</div>
                <div style="margin: 6px 0;"><strong style="color: #87ceeb;">💧 Humidity:</strong> ${humidityDisplay}</div>
                <div style="margin: 6px 0;"><strong style="color: #ffeb3b;">🌫️ PM2.5:</strong> ${pm25Display}</div>
                <div style="margin: 6px 0;"><strong style="color: #ff6b6b;">⚠️ Risk Score:</strong> <span style="color: ${markerColor}; font-weight: bold; font-size: 16px;">${riskDisplay}</span></div>
            </div>
            <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.3); font-size: 11px; color: #ccc;">
                Last updated: ${timestamp ? new Date(timestamp).toLocaleTimeString() : 'N/A'}
            </div>
            <button onclick="loadLocationData('${location_name}')" style="
                width: 100%;
                padding: 12px;
                margin-top: 12px;
                background: ${markerColor};
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
                font-size: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                transition: all 0.3s;
            " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                📊 View Full Details
            </button>
        </div>
    `;
    
    sensorMarker.bindPopup(popupContent);
    
    // Click event to load full data
    sensorMarker.on('click', async function() {
        console.log(`Sensor clicked: ${location_name}`);
    });
    
    sensorMarkers.push(sensorMarker);
    
    return sensorMarker;
}

// Get marker color based on risk score
function getRiskMarkerColor(riskScore) {
    if (!riskScore) return '#95a5a6'; // Gray for no data
    if (riskScore >= 80) return '#e74c3c'; // Red - Very High
    if (riskScore >= 60) return '#e67e22'; // Orange - High
    if (riskScore >= 40) return '#f39c12'; // Yellow - Moderate
    if (riskScore >= 20) return '#3498db'; // Blue - Low
    return '#2ecc71'; // Green - Very Low
}

// Load full location data when sensor is clicked
async function loadLocationData(locationName) {
    document.getElementById('locationInput').value = locationName;
    await searchLocation();
    
    // Close all popups
    map.closePopup();
}

// Refresh sensor markers with latest data
async function refreshSensorMarkers() {
    // Remove existing markers
    sensorMarkers.forEach(marker => map.removeLayer(marker));
    sensorMarkers = [];
    
    // Reload with fresh data
    await loadSensorMarkers();
}

// Search for location
async function searchLocation() {
    const input = document.getElementById('locationInput').value.trim();
    
    if (!input) {
        showAlert('Please enter a location', 'warning');
        return;
    }

    showLoading(true);
    console.log('🔍 Searching for location:', input);
    
    try {
        // Check if input is coordinates (lat,lon) or city name
        const coordPattern = /^-?\d+\.?\d*,\s*-?\d+\.?\d*$/;
        let query = input;
        
        if (coordPattern.test(input)) {
            query = input;
        }
        
        const apiUrl = `${API_BASE}/weather?location=${encodeURIComponent(query)}`;
        console.log('📡 Making request to:', apiUrl);
        
        // Call Flask backend API
        const response = await fetch(apiUrl);

        console.log('📥 Response status:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('❌ API Error:', errorData);
            throw new Error(errorData.error || 'Location not found');
        }

        const result = await response.json();
        console.log('✅ Received data:', result);
        
        if (!result.success || !result.data) {
            throw new Error('Invalid response format from server');
        }
        
        const weatherData = result.data;
        currentLocationData = weatherData;

        // Update all displays
        updateLocationInfo(weatherData);
        updateCurrentConditions(weatherData);
        updateAirQuality(weatherData);
        updateMap(weatherData.location.lat, weatherData.location.lon, weatherData.location.name);
        updateHistoricalChart(weatherData);
        await calculateRiskScore(weatherData);
        await performCorrelationAnalysis(weatherData);
        await generateContextualAlerts(weatherData);
        updateLastUpdateTime();

        // Load historical database data for the new graph
        if (weatherData.location && weatherData.location.name) {
            setTimeout(() => {
                loadHistoricalData(weatherData.location.name, selectedTimeRange);
            }, 500);
        }

        showAlert(`Successfully loaded data for ${weatherData.location.name}`, 'success');
        
    } catch (error) {
        console.error('❌ Error fetching data:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            type: error.constructor.name
        });
        
        let errorMessage;
        if (error.message.includes('Failed to fetch')) {
            errorMessage = '⚠️ Cannot connect to backend server. Please ensure Flask server is running at http://localhost:5000';
        } else {
            errorMessage = error.message || 'Unable to fetch data. Please check the location and try again.';
        }
        showAlert(errorMessage, 'danger');
    } finally {
        showLoading(false);
    }
}

// Get user's current location
function getCurrentLocation() {
    if (navigator.geolocation) {
        showLoading(true);
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                document.getElementById('locationInput').value = `${latitude.toFixed(4)},${longitude.toFixed(4)}`;
                await searchLocation();
            },
            (error) => {
                showLoading(false);
                showAlert('Unable to get your location. Please enter manually.', 'warning');
            }
        );
    } else {
        showAlert('Geolocation is not supported by your browser.', 'warning');
    }
}

// Update location information
function updateLocationInfo(data) {
    const locationInfo = document.getElementById('locationInfo');
    locationInfo.innerHTML = `
        <p><strong>Location:</strong> ${data.location.name}, ${data.location.region}, ${data.location.country}</p>
        <p><strong>Coordinates:</strong> ${data.location.lat}°N, ${data.location.lon}°E</p>
        <p><strong>Local Time:</strong> ${data.location.localtime}</p>
        <p><strong>Timezone:</strong> ${data.location.tz_id}</p>
    `;
}

// Update current weather conditions
function updateCurrentConditions(data) {
    const current = data.current;
    
    document.getElementById('temperature').textContent = `${current.temp_c}°C / ${current.temp_f}°F`;
    document.getElementById('humidity').textContent = `${current.humidity}%`;
    document.getElementById('windSpeed').textContent = `${current.wind_kph} km/h`;
    document.getElementById('windDirection').textContent = `${current.wind_dir} (${current.wind_degree}°)`;
    document.getElementById('pressure').textContent = `${current.pressure_mb} mb`;
    document.getElementById('visibility').textContent = `${current.vis_km} km`;
}

// Update air quality display
function updateAirQuality(data) {
    if (data.current.air_quality) {
        const aqi = data.current.air_quality;
        
        // US EPA Index (1-6 scale)
        const epaIndex = aqi['us-epa-index'] || 1;
        const aqiValue = Math.round(epaIndex * 50);
        
        document.getElementById('aqiValue').textContent = aqiValue;
        
        // Determine AQI status
        let status = 'Good';
        let statusClass = 'good';
        
        if (aqiValue > 200) {
            status = 'Very Unhealthy';
            statusClass = 'unhealthy';
        } else if (aqiValue > 150) {
            status = 'Unhealthy';
            statusClass = 'unhealthy';
        } else if (aqiValue > 100) {
            status = 'Unhealthy for Sensitive Groups';
            statusClass = 'moderate';
        } else if (aqiValue > 50) {
            status = 'Moderate';
            statusClass = 'moderate';
        }
        
        const statusElement = document.getElementById('aqiStatus');
        statusElement.textContent = status;
        statusElement.className = `aqi-status ${statusClass}`;
        
        // Update pollutants
        document.getElementById('pm25').textContent = `${aqi.pm2_5.toFixed(1)} μg/m³`;
        document.getElementById('pm10').textContent = `${aqi.pm10.toFixed(1)} μg/m³`;
        document.getElementById('o3').textContent = `${aqi.o3.toFixed(1)} μg/m³`;
        document.getElementById('no2').textContent = `${aqi.no2.toFixed(1)} μg/m³`;
        
    } else {
        document.getElementById('aqiValue').textContent = '--';
        document.getElementById('aqiStatus').textContent = 'No AQI Data';
        document.getElementById('pm25').textContent = '--';
        document.getElementById('pm10').textContent = '--';
        document.getElementById('o3').textContent = '--';
        document.getElementById('no2').textContent = '--';
    }
}

// Update map with location marker
function updateMap(lat, lon, locationName) {
    map.setView([lat, lon], 10);
    
    // Remove previous search marker
    if (marker) {
        map.removeLayer(marker);
    }
    
    // Add blue marker for searched location (distinct from sensor markers)
    const searchIcon = L.divIcon({
        className: 'search-marker',
        html: `<div style="
            background-color: #3498db;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 4px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 20px;
            animation: pulse 2s infinite;
        ">🔍</div>
        <style>
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
        </style>`,
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });
    
    marker = L.marker([lat, lon], { icon: searchIcon }).addTo(map);
    marker.bindPopup(`<b>🔍 ${locationName}</b><br>Current Search Location`).openPopup();
    
    // Don't refresh sensor markers automatically - they're already on the map
    // setTimeout(() => refreshSensorMarkers(), 1000);
}

// Initialize chart
function initializeChart() {
    const ctx = document.getElementById('weatherChart').getContext('2d');
    weatherChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Humidity (%)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(22, 33, 62, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff'
                }
            },
            scales: {
                x: {
                    ticks: { color: '#b0b0b0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: { color: '#e74c3c' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    title: {
                        display: true,
                        text: 'Temperature (°C)',
                        color: '#e74c3c'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: '#3498db' },
                    grid: { drawOnChartArea: false },
                    title: {
                        display: true,
                        text: 'Humidity (%)',
                        color: '#3498db'
                    }
                }
            }
        }
    });
}

// Update chart with forecast data OR historical data
async function updateHistoricalChart(data) {
    const locationName = data.location.name;
    
    try {
        // Try to fetch historical data from our database first
        const response = await fetch(`${API_BASE}/historical/${encodeURIComponent(locationName)}?hours=24`);
        
        if (response.ok) {
            const result = await response.json();
            
            if (result.success && result.data && result.data.length > 0) {
                // Use our historical database data
                console.log(`📊 Using ${result.data_points} historical readings from database`);
                updateChartWithHistoricalData(result.data, locationName);
                return;
            }
        }
    } catch (error) {
        console.log('⚠️ Historical data not available, using forecast data');
    }
    
    // Fallback to forecast data
    const forecastHours = data.forecast.forecastday[0].hour;
    
    const labels = [];
    const temperatures = [];
    const humidity = [];
    
    forecastHours.forEach(hour => {
        const time = new Date(hour.time).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        labels.push(time);
        temperatures.push(hour.temp_c);
        humidity.push(hour.humidity);
    });
    
    weatherChart.data.labels = labels;
    weatherChart.data.datasets[0].data = temperatures;
    weatherChart.data.datasets[1].data = humidity;
    weatherChart.update();
}

// Update chart with actual historical database data
async function updateChartWithHistoricalData(historicalData, locationName) {
    const labels = [];
    const temperatures = [];
    const humidity = [];
    
    historicalData.forEach(reading => {
        const time = new Date(reading.timestamp).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        labels.push(time);
        temperatures.push(reading.temp_c);
        humidity.push(reading.humidity);
    });
    
    // Try to fetch prediction
    try {
        const predResponse = await fetch(`${API_BASE}/predict/${encodeURIComponent(locationName)}`);
        if (predResponse.ok) {
            const predResult = await predResponse.json();
            if (predResult.success && predResult.prediction) {
                const pred = predResult.prediction;
                const predTime = new Date(pred.prediction_for).toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
                
                // Add prediction to chart
                labels.push(predTime + ' (Predicted)');
                temperatures.push(pred.predicted_temp_c);
                humidity.push(pred.predicted_humidity);
                
                // Show prediction info
                showAlert(`🔮 Next hour prediction: ${pred.predicted_temp_c}°C, ${pred.predicted_humidity}% humidity (${Math.round(pred.confidence_score * 100)}% confidence)`, 'info');
            }
        }
    } catch (error) {
        console.log('Prediction not available');
    }
    
    weatherChart.data.labels = labels;
    weatherChart.data.datasets[0].data = temperatures;
    weatherChart.data.datasets[1].data = humidity;
    weatherChart.update();
}

// Calculate environmental risk score - Now calls backend
async function calculateRiskScore(data) {
    try {
        const response = await fetch(`${API_BASE}/risk/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to calculate risk score');
        }
        
        const result = await response.json();
        
        document.getElementById('riskValue').textContent = result.risk_score;
        document.getElementById('riskMeterFill').style.width = `${result.risk_score}%`;
        
        const labelElement = document.getElementById('riskLabel');
        labelElement.textContent = result.risk_level;
        labelElement.className = `risk-label ${result.label_class}`;
        
        displayRiskFactorBreakdown(result.factors, result.risk_score);
        
        if (result.risk_score > 70) {
            const topFactors = result.factors.slice(0, 3).map(f => f.name).join(', ');
            showAlert(`⚠️ HIGH ENVIRONMENTAL RISK (${result.risk_score}/100)! Major factors: ${topFactors}`, 'danger');
        } else if (result.risk_score > 40) {
            showAlert(`⚠️ Moderate environmental risk detected (${result.risk_score}/100). Monitor conditions.`, 'warning');
        }
        
    } catch (error) {
        console.error('Risk calculation error:', error);
        document.getElementById('riskValue').textContent = '--';
        document.getElementById('riskLabel').textContent = 'Error';
    }
}

// Display risk factor breakdown
function displayRiskFactorBreakdown(factors, totalScore) {
    const riskCard = document.querySelector('.risk-card .risk-score');
    let breakdownDiv = document.getElementById('riskBreakdown');
    
    if (!breakdownDiv) {
        breakdownDiv = document.createElement('div');
        breakdownDiv.id = 'riskBreakdown';
        breakdownDiv.className = 'risk-breakdown';
        riskCard.appendChild(breakdownDiv);
    }
    
    if (factors.length === 0) {
        breakdownDiv.innerHTML = '<p class="breakdown-empty">✅ All parameters within safe ranges</p>';
        return;
    }
    
    const sortedFactors = factors.sort((a, b) => b.score - a.score);
    
    let html = '<div class="breakdown-title">Risk Factor Breakdown:</div>';
    html += '<div class="breakdown-items">';
    
    sortedFactors.forEach(factor => {
        const percentage = ((factor.score / totalScore) * 100).toFixed(0);
        html += `
            <div class="breakdown-item ${factor.color}">
                <div class="breakdown-header">
                    <span class="breakdown-name">${factor.name}</span>
                    <span class="breakdown-score">+${factor.score} pts</span>
                </div>
                <div class="breakdown-details">
                    <span class="breakdown-value">${factor.value}</span>
                    <span class="breakdown-level">${factor.level}</span>
                </div>
                <div class="breakdown-bar">
                    <div class="breakdown-bar-fill ${factor.color}" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    breakdownDiv.innerHTML = html;
}

// Perform correlation analysis - Now calls backend
async function performCorrelationAnalysis(data) {
    const analysisDiv = document.getElementById('correlationAnalysis');
    
    try {
        const response = await fetch(`${API_BASE}/correlation/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to analyze correlations');
        }
        
        const result = await response.json();
        const correlations = result.correlations || [];
        
        if (correlations.length > 0) {
            analysisDiv.innerHTML = correlations.map(cor => 
                `<div class="correlation-item ${cor.type}">
                    <div class="correlation-header">${cor.category}</div>
                    <div class="correlation-message">${cor.message}</div>
                    ${cor.recommendation ? `<div class="correlation-action">💡 <strong>Action:</strong> ${cor.recommendation}</div>` : ''}
                </div>`
            ).join('');
        } else {
            analysisDiv.innerHTML = '<p class="placeholder-text">✅ No significant environmental correlations detected. All parameters within normal ranges.</p>';
        }
        
    } catch (error) {
        console.error('Correlation analysis error:', error);
        analysisDiv.innerHTML = '<p class="placeholder-text">⚠️ Unable to perform correlation analysis.</p>';
    }
}

// Identify pollution source
function identifyPollutionSource(windDir, windDegree, sources, pm25, pm10) {
    const detectedSources = [];
    
    for (const [type, source] of Object.entries(sources)) {
        const sourceDirDegree = windDirections[source.direction];
        const angleDiff = Math.abs(windDegree - sourceDirDegree);
        const normalizedDiff = angleDiff > 180 ? 360 - angleDiff : angleDiff;
        
        if (normalizedDiff < 45) {
            let confidence = 'High confidence';
            let action = 'Pollution likely from this source.';
            
            if (normalizedDiff < 22.5) {
                confidence = 'Very high confidence - direct alignment';
            } else if (normalizedDiff > 30) {
                confidence = 'Moderate confidence';
            }
            
            if (type === 'industrial') {
                action = 'Industrial emissions containing multiple pollutants.';
            } else if (type === 'traffic') {
                action = 'Vehicle emissions - NO₂ and fine particles.';
            } else if (type === 'airport') {
                action = 'Aircraft and ground vehicle emissions.';
            }
            
            detectedSources.push({
                name: source.name,
                distance: source.distance,
                direction: source.direction,
                confidence: confidence,
                action: action,
                angleDiff: normalizedDiff
            });
        }
    }
    
    return detectedSources.sort((a, b) => a.angleDiff - b.angleDiff);
}

// Calculate heat index
function calculateHeatIndex(tempC, humidity) {
    const tempF = (tempC * 9/5) + 32;
    const hi = -42.379 + 2.04901523*tempF + 10.14333127*humidity 
                - 0.22475541*tempF*humidity - 0.00683783*tempF*tempF
                - 0.05481717*humidity*humidity + 0.00122874*tempF*tempF*humidity
                + 0.00085282*tempF*humidity*humidity - 0.00000199*tempF*tempF*humidity*humidity;
    return (hi - 32) * 5/9;
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('lastUpdate').textContent = timeString;
}

// Show alert banner
function showAlert(message, type = 'warning') {
    const alertBanner = document.getElementById('alertBanner');
    const alertMessage = document.getElementById('alertMessage');
    
    alertMessage.textContent = message;
    alertBanner.className = `alert-banner ${type}`;
    alertBanner.classList.remove('hidden');
    
    // Play sound based on alert type
    if (type === 'danger') {
        playAlertSound('high');
    } else if (type === 'warning') {
        playAlertSound('medium');
    }
    // No sound for 'success' or 'info' alerts
    
    if (type === 'success') {
        setTimeout(() => {
            alertBanner.classList.add('hidden');
        }, 5000);
    }
}

// Close alert banner
function closeAlert() {
    document.getElementById('alertBanner').classList.add('hidden');
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

// Auto-refresh data every 5 minutes
setInterval(() => {
    if (currentLocationData) {
        const input = document.getElementById('locationInput').value;
        if (input) {
            console.log('Auto-refreshing data...');
            searchLocation();
        }
    }
}, 300000);

// Generate contextual alerts - Now calls backend
async function generateContextualAlerts(data) {
    try {
        const response = await fetch(`${API_BASE}/alerts/contextual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate alerts');
        }
        
        const result = await response.json();
        displayContextualAlerts(result.alerts);
        
    } catch (error) {
        console.error('Alert generation error:', error);
        document.getElementById('contextualAlertsSection').classList.add('hidden');
    }
}

function displayContextualAlerts(alerts) {
    const section = document.getElementById('contextualAlertsSection');
    const container = document.getElementById('contextualAlerts');
    const countBadge = document.getElementById('alertCount');
    
    if (alerts.length === 0) {
        section.classList.add('hidden');
        return;
    }
    
    // Play notification sound based on highest severity
    const hasHighAlert = alerts.some(a => a.severity === 'high' || a.severity === 'critical');
    const hasMediumAlert = alerts.some(a => a.severity === 'medium');
    
    if (hasHighAlert) {
        playAlertSound('high');
    } else if (hasMediumAlert) {
        playAlertSound('medium');
    } else {
        playAlertSound('low');
    }
    
    section.classList.remove('hidden');
    countBadge.textContent = alerts.length;
    
    const now = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const alertsHTML = alerts.map(alert => `
        <div class="contextual-alert-card severity-${alert.severity}">
            <div class="alert-header">
                <div class="alert-icon">${alert.icon}</div>
                <div class="alert-header-content">
                    <div class="alert-title">
                        ${alert.title}
                        <span class="alert-severity-badge ${alert.severity}">${alert.severity}</span>
                    </div>
                    <div class="alert-what">${alert.what}</div>
                </div>
            </div>
            
            <div class="alert-section">
                <div class="alert-section-title cause">
                    <i class="fas fa-brain"></i> WHY IS THIS HAPPENING?
                </div>
                <div class="alert-section-content">
                    ${alert.cause}
                </div>
            </div>
            
            <div class="alert-section">
                <div class="alert-section-title action">
                    <i class="fas fa-shield-alt"></i> WHAT SHOULD YOU DO?
                </div>
                <div class="alert-section-content">
                    ${alert.action}
                </div>
            </div>
            
            <div class="alert-timestamp">
                <i class="fas fa-clock"></i> Alert generated at ${now} | Based on: ${alert.sources.join(', ')}
            </div>
        </div>
    `).join('');
    
    container.innerHTML = alertsHTML;
    
    setTimeout(() => {
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 300);
}

// Helper functions
function getPM25Category(pm25) {
    if (pm25 > 250) return 'Hazardous';
    if (pm25 > 150) return 'Very Unhealthy';
    if (pm25 > 80) return 'Unhealthy';
    if (pm25 > 50) return 'Moderate';
    if (pm25 > 35) return 'Acceptable';
    return 'Good';
}

function getUVCategory(uv) {
    if (uv >= 11) return 'Extreme';
    if (uv >= 8) return 'Very High';
    if (uv >= 6) return 'High';
    if (uv >= 3) return 'Moderate';
    return 'Low';
}
// Historical Graph Functionality
let historicalChart = null;
let currentHistoricalLocation = null;
let selectedTimeRange = 6; // Default 6 hours
let visibleMetrics = {
    temperature: true,
    humidity: true,
    pm25: true
};

// Initialize Historical Graph on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeHistoricalGraph();
});

function initializeHistoricalGraph() {
    const timeButtons = document.querySelectorAll('.time-btn');
    const metricCheckboxes = {
        temperature: document.getElementById('showTemp'),
        humidity: document.getElementById('showHumidity'),
        pm25: document.getElementById('showPM25')
    };

    // Time range button handlers
    timeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            timeButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedTimeRange = parseInt(this.dataset.hours);
            
            if (currentHistoricalLocation) {
                loadHistoricalData(currentHistoricalLocation, selectedTimeRange);
            }
        });
    });

    // Metric checkbox handlers
    Object.keys(metricCheckboxes).forEach(metric => {
        const checkbox = metricCheckboxes[metric];
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                visibleMetrics[metric] = this.checked;
                if (historicalChart) {
                    updateHistoricalChartVisibility();
                }
            });
        }
    });

    // Create initial empty chart
    const ctx = document.getElementById('historicalChart');
    if (ctx) {
        historicalChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#ffffff',
                            font: { size: 12 },
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#3498db',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    if (context.dataset.label.includes('Temperature')) {
                                        label += context.parsed.y.toFixed(1) + '°C';
                                    } else if (context.dataset.label.includes('Humidity')) {
                                        label += context.parsed.y.toFixed(0) + '%';
                                    } else if (context.dataset.label.includes('PM2.5')) {
                                        label += context.parsed.y.toFixed(1) + ' µg/m³';
                                    }
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#ffffff' }
                    },
                    yTemp: {
                        type: 'linear',
                        position: 'left',
                        display: true,
                        title: {
                            display: true,
                            text: 'Temperature (°C)',
                            color: '#ff6384'
                        },
                        grid: { color: 'rgba(255, 99, 132, 0.1)' },
                        ticks: { color: '#ff6384' }
                    },
                    yHumidity: {
                        type: 'linear',
                        position: 'right',
                        display: true,
                        title: {
                            display: true,
                            text: 'Humidity (%)',
                            color: '#36a2eb'
                        },
                        grid: { display: false },
                        ticks: { color: '#36a2eb' }
                    },
                    yPM25: {
                        type: 'linear',
                        position: 'right',
                        display: true,
                        title: {
                            display: true,
                            text: 'PM2.5 (µg/m³)',
                            color: '#ffce56'
                        },
                        grid: { display: false },
                        ticks: { color: '#ffce56' }
                    }
                }
            }
        });
    }

    showHistoricalStatus('Search for a location to view historical data', 'info');
}

async function loadHistoricalData(locationName, hours = 6) {
    currentHistoricalLocation = locationName;
    showHistoricalStatus(`Loading ${hours}h of historical data for ${locationName}...`, 'info');

    try {
        const response = await fetch(`${API_BASE}/historical/${encodeURIComponent(locationName)}?hours=${hours}`);
        const result = await response.json();

        if (!result.success || !result.data || result.data.length === 0) {
            showHistoricalStatus(`No historical data available for ${locationName}. Data will appear after system collects readings (every 5 minutes).`, 'warning');
            return;
        }

        const data = result.data;
        showHistoricalStatus(`✓ Displaying ${data.length} readings from database (last ${hours}h)`, 'success');

        // Prepare data for chart
        const timestamps = data.map(reading => {
            const date = new Date(reading.timestamp);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });

        const temperatures = data.map(r => r.temp_c);
        const humidity = data.map(r => r.humidity);
        const pm25 = data.map(r => r.pm2_5);

        // Update chart
        updateHistoricalChartData(timestamps, temperatures, humidity, pm25);

    } catch (error) {
        console.error('Error loading historical data:', error);
        showHistoricalStatus('⚠ Error loading historical data. Make sure Flask server is running.', 'warning');
    }
}

function updateHistoricalChartData(timestamps, temperatures, humidity, pm25) {
    if (!historicalChart) return;

    const datasets = [];

    if (visibleMetrics.temperature) {
        datasets.push({
            label: 'Temperature',
            data: temperatures,
            borderColor: '#ff6384',
            backgroundColor: 'rgba(255, 99, 132, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            yAxisID: 'yTemp',
            pointRadius: 4,
            pointHoverRadius: 6
        });
    }

    if (visibleMetrics.humidity) {
        datasets.push({
            label: 'Humidity',
            data: humidity,
            borderColor: '#36a2eb',
            backgroundColor: 'rgba(54, 162, 235, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            yAxisID: 'yHumidity',
            pointRadius: 4,
            pointHoverRadius: 6
        });
    }

    if (visibleMetrics.pm25) {
        datasets.push({
            label: 'PM2.5',
            data: pm25,
            borderColor: '#ffce56',
            backgroundColor: 'rgba(255, 206, 86, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            yAxisID: 'yPM25',
            pointRadius: 4,
            pointHoverRadius: 6
        });
    }

    historicalChart.data.labels = timestamps;
    historicalChart.data.datasets = datasets;
    historicalChart.update('none');
}

function updateHistoricalChartVisibility() {
    if (!historicalChart || !historicalChart.data.labels.length) return;

    // Reconstruct datasets based on current visibility settings
    const allData = historicalChart.data.datasets;
    const newDatasets = [];

    if (visibleMetrics.temperature) {
        const tempDataset = allData.find(d => d.label === 'Temperature');
        if (tempDataset) newDatasets.push(tempDataset);
    }

    if (visibleMetrics.humidity) {
        const humDataset = allData.find(d => d.label === 'Humidity');
        if (humDataset) newDatasets.push(humDataset);
    }

    if (visibleMetrics.pm25) {
        const pm25Dataset = allData.find(d => d.label === 'PM2.5');
        if (pm25Dataset) newDatasets.push(pm25Dataset);
    }

    historicalChart.data.datasets = newDatasets;
    historicalChart.update();
}

function showHistoricalStatus(message, type = 'info') {
    const statusEl = document.getElementById('historicalGraphStatus');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `graph-status ${type}`;
        statusEl.style.display = 'block';
    }
}

// ═══════════════════════════════════════════════════════════════════
// AI ASSISTANT FUNCTIONALITY
// ═══════════════════════════════════════════════════════════════════

let aiChatHistory = [];

async function sendAIQuery(query) {
    const chatMessages = document.getElementById('chatMessages');
    const aiStatus = document.getElementById('aiStatus');
    const sendBtn = document.getElementById('aiSendBtn');
    const queryInput = document.getElementById('aiQueryInput');
    
    if (!query || query.trim() === '') return;
    
    // Get current location only as fallback - AI will extract from query
    const currentLocation = currentLocationData?.location?.name || null;
    
    // Add user message to chat
    const userMessage = createUserMessage(query);
    chatMessages.appendChild(userMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Clear input
    queryInput.value = '';
    
    // Show typing indicator
    const typingIndicator = createTypingIndicator();
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Update status
    aiStatus.textContent = 'Thinking...';
    aiStatus.classList.add('thinking');
    sendBtn.disabled = true;
    
    try {
        // Send query without forcing location - let AI extract it
        const requestBody = { query: query };
        
        // Only include location if user has searched for one
        if (currentLocation) {
            requestBody.location = currentLocation;
        }
        
        const response = await fetch(`${API_BASE}/ai/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `API returned ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        chatMessages.removeChild(typingIndicator);
        
        // Add AI response to chat
        const aiMessage = createAIMessage(data);
        chatMessages.appendChild(aiMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Store in history
        aiChatHistory.push({
            query: query,
            response: data,
            timestamp: new Date()
        });
        
        // Update status
        aiStatus.textContent = 'Ready';
        aiStatus.classList.remove('thinking');
        
    } catch (error) {
        console.error('AI Query error:', error);
        
        // Remove typing indicator
        if (chatMessages.contains(typingIndicator)) {
            chatMessages.removeChild(typingIndicator);
        }
        
        // Show error message with more detail
        let errorMsg = error.message || 'Sorry, I encountered an error. Please try again.';
        if (errorMsg.includes('Could not find weather data')) {
            errorMsg += '\n\nTip: Try asking about major cities like London, Mumbai, New Delhi, Paris, or Tokyo.';
        }
        
        const errorMessage = createErrorMessage(errorMsg);
        chatMessages.appendChild(errorMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        aiStatus.textContent = 'Ready';
        aiStatus.classList.remove('thinking');
    } finally {
        sendBtn.disabled = false;
    }
}

function createUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'user-message';
    messageDiv.innerHTML = `
        <div class="message-icon">
            <i class="fas fa-user"></i>
        </div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    return messageDiv;
}

function createAIMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'ai-message';
    
    let contentHTML = `<p>${formatAIResponse(data.answer)}</p>`;
    
    // Add current conditions summary if available
    if (data.current_conditions) {
        contentHTML += `
            <div class="data-summary">
                <h4>📊 Current Conditions in ${data.location}</h4>
                <div class="data-grid">
                    <div class="data-item">
                        <strong>Temperature</strong>
                        ${data.current_conditions.temperature}
                    </div>
                    <div class="data-item">
                        <strong>Humidity</strong>
                        ${data.current_conditions.humidity}
                    </div>
                    <div class="data-item">
                        <strong>Wind Speed</strong>
                        ${data.current_conditions.wind_speed}
                    </div>
                    <div class="data-item">
                        <strong>PM2.5</strong>
                        ${data.current_conditions.pm2_5}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add predictions if available
    if (data.predictions && data.predictions.temperature) {
        contentHTML += `
            <div class="data-summary">
                <h4>🔮 Next Hour Predictions</h4>
                <div class="data-grid">
                    <div class="data-item">
                        <strong>Temperature</strong>
                        ${data.predictions.temperature}°C (${data.predictions.temperature_trend})
                    </div>
                    <div class="data-item">
                        <strong>Humidity</strong>
                        ${data.predictions.humidity}%
                    </div>
                    <div class="data-item">
                        <strong>PM2.5</strong>
                        ${data.predictions.pm2_5} µg/m³ (${data.predictions.pm25_trend})
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add safety score if available
    if (data.safety_analysis) {
        const safety = data.safety_analysis;
        const scoreColor = safety.safety_color || 'gray';
        contentHTML += `
            <div class="data-summary" style="border-left-color: ${scoreColor};">
                <h4>🎯 Safety Score: ${safety.safety_score}/100</h4>
                <p style="color: ${scoreColor}; font-weight: bold;">${safety.safety_level}</p>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-icon">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            ${contentHTML}
        </div>
    `;
    
    return messageDiv;
}

function createTypingIndicator() {
    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'ai-message';
    indicatorDiv.innerHTML = `
        <div class="message-icon">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    return indicatorDiv;
}

function createErrorMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'ai-message';
    messageDiv.innerHTML = `
        <div class="message-icon">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content warning-box">
            <p><strong>⚠️ Error</strong></p>
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    return messageDiv;
}

function formatAIResponse(text) {
    if (!text) return '';
    
    // Convert markdown-style formatting to HTML
    let formatted = text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')  // Bold
        .replace(/\*(.+?)\*/g, '<em>$1</em>')  // Italic
        .replace(/\n\n/g, '</p><p>')  // Paragraphs
        .replace(/\n•/g, '<br>•')  // Bullet points
        .replace(/\n/g, '<br>');  // Line breaks
    
    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize AI Assistant
function initAIAssistant() {
    const sendBtn = document.getElementById('aiSendBtn');
    const queryInput = document.getElementById('aiQueryInput');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    
    // Send button click
    sendBtn.addEventListener('click', () => {
        const query = queryInput.value.trim();
        if (query) {
            sendAIQuery(query);
        }
    });
    
    // Enter key to send
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = queryInput.value.trim();
            if (query) {
                sendAIQuery(query);
            }
        }
    });
    
    // Suggestion buttons
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const query = btn.getAttribute('data-query');
            queryInput.value = query;
            sendAIQuery(query);
        });
    });
}

// Initialize AI Assistant when page loads
document.addEventListener('DOMContentLoaded', () => {
    initAIAssistant();
});
