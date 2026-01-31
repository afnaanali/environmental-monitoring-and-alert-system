"""
Prediction algorithms for weather forecasting
"""
from datetime import datetime, timedelta
import statistics

def calculate_trend(values):
    """Calculate simple linear trend"""
    if len(values) < 2:
        return 0
    
    n = len(values)
    x = list(range(n))
    
    # Calculate slope using least squares
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(values)
    
    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0
    
    slope = numerator / denominator
    return slope

def predict_next_hour(historical_data):
    """
    Predict weather for next hour based on historical data
    Uses simple moving average + trend analysis
    """
    if not historical_data or len(historical_data) < 3:
        return None
    
    # Extract recent values (last 6 readings minimum)
    recent_data = historical_data[-12:] if len(historical_data) >= 12 else historical_data
    
    # Extract parameters
    temps = [d['temp_c'] for d in recent_data]
    humidity = [d['humidity'] for d in recent_data]
    pm25 = [d['pm2_5'] for d in recent_data if d['pm2_5'] is not None]
    
    # Calculate trends
    temp_trend = calculate_trend(temps)
    humidity_trend = calculate_trend(humidity)
    pm25_trend = calculate_trend(pm25) if pm25 else 0
    
    # Predict next values
    predicted_temp = temps[-1] + temp_trend
    predicted_humidity = max(0, min(100, humidity[-1] + humidity_trend))
    predicted_pm25 = max(0, pm25[-1] + pm25_trend) if pm25 else 0
    
    # Calculate confidence based on data consistency
    temp_variance = statistics.variance(temps) if len(temps) > 1 else 0
    confidence = max(0.5, min(0.95, 1 - (temp_variance / 100)))
    
    prediction_time = datetime.now() + timedelta(hours=1)
    
    return {
        'prediction_for': prediction_time.isoformat(),
        'predicted_temp_c': round(predicted_temp, 1),
        'predicted_humidity': round(predicted_humidity),
        'predicted_pm2_5': round(predicted_pm25, 1),
        'confidence_score': round(confidence, 2),
        'algorithm': 'Linear Trend + Moving Average',
        'data_points_used': len(recent_data),
        'trends': {
            'temperature_trend': round(temp_trend, 2),
            'humidity_trend': round(humidity_trend, 2),
            'pm25_trend': round(pm25_trend, 2)
        }
    }

def predict_multiple_hours(historical_data, hours=6):
    """
    Predict weather for multiple hours ahead
    """
    if not historical_data or len(historical_data) < 3:
        return []
    
    predictions = []
    
    for hour in range(1, hours + 1):
        # Get trend multiplier for each hour ahead
        recent_data = historical_data[-12:] if len(historical_data) >= 12 else historical_data
        
        temps = [d['temp_c'] for d in recent_data]
        humidity = [d['humidity'] for d in recent_data]
        pm25 = [d['pm2_5'] for d in recent_data if d['pm2_5'] is not None]
        
        temp_trend = calculate_trend(temps) * hour
        humidity_trend = calculate_trend(humidity) * hour
        pm25_trend = calculate_trend(pm25) * hour if pm25 else 0
        
        predicted_temp = temps[-1] + temp_trend
        predicted_humidity = max(0, min(100, humidity[-1] + humidity_trend))
        predicted_pm25 = max(0, pm25[-1] + pm25_trend) if pm25 else 0
        
        # Confidence decreases with time
        confidence = max(0.3, 0.85 - (hour * 0.08))
        
        prediction_time = datetime.now() + timedelta(hours=hour)
        
        predictions.append({
            'prediction_for': prediction_time.isoformat(),
            'hours_ahead': hour,
            'predicted_temp_c': round(predicted_temp, 1),
            'predicted_humidity': round(predicted_humidity),
            'predicted_pm2_5': round(predicted_pm25, 1),
            'confidence_score': round(confidence, 2)
        })
    
    return predictions

def analyze_patterns(historical_data):
    """
    Analyze patterns in historical data
    """
    if not historical_data or len(historical_data) < 10:
        return {
            'status': 'insufficient_data',
            'message': 'Need at least 10 data points for pattern analysis'
        }
    
    temps = [d['temp_c'] for d in historical_data]
    humidity = [d['humidity'] for d in historical_data]
    pm25 = [d['pm2_5'] for d in historical_data if d['pm2_5'] is not None]
    
    # Calculate statistics
    temp_stats = {
        'mean': round(statistics.mean(temps), 1),
        'min': round(min(temps), 1),
        'max': round(max(temps), 1),
        'std_dev': round(statistics.stdev(temps), 2) if len(temps) > 1 else 0,
        'trend': 'increasing' if calculate_trend(temps) > 0.1 else 'decreasing' if calculate_trend(temps) < -0.1 else 'stable'
    }
    
    humidity_stats = {
        'mean': round(statistics.mean(humidity)),
        'min': min(humidity),
        'max': max(humidity),
        'trend': 'increasing' if calculate_trend(humidity) > 0.5 else 'decreasing' if calculate_trend(humidity) < -0.5 else 'stable'
    }
    
    pm25_stats = None
    if pm25 and len(pm25) > 1:
        pm25_stats = {
            'mean': round(statistics.mean(pm25), 1),
            'min': round(min(pm25), 1),
            'max': round(max(pm25), 1),
            'trend': 'increasing' if calculate_trend(pm25) > 0.5 else 'decreasing' if calculate_trend(pm25) < -0.5 else 'stable'
        }
    
    # Detect anomalies
    anomalies = []
    if temp_stats['std_dev'] > 5:
        anomalies.append('High temperature variability detected')
    if humidity_stats['max'] - humidity_stats['min'] > 40:
        anomalies.append('Significant humidity fluctuations')
    if pm25_stats and pm25_stats['max'] > 100:
        anomalies.append('Severe air pollution episodes detected')
    
    return {
        'status': 'success',
        'temperature': temp_stats,
        'humidity': humidity_stats,
        'pm2_5': pm25_stats,
        'anomalies': anomalies,
        'data_quality': {
            'readings_count': len(historical_data),
            'time_span_hours': len(historical_data) * 0.083,  # Assuming 5-min intervals
            'completeness': round((len(pm25) / len(historical_data)) * 100) if pm25 else 0
        }
    }
