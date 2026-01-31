"""
Database module for storing historical weather data
"""
import sqlite3
from datetime import datetime
import json
import os

DATABASE_PATH = 'weather_data.db'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create weather readings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            location_lat REAL,
            location_lon REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            temp_c REAL,
            temp_f REAL,
            humidity INTEGER,
            wind_kph REAL,
            wind_dir TEXT,
            wind_degree INTEGER,
            pressure_mb REAL,
            visibility_km REAL,
            uv_index REAL,
            pm2_5 REAL,
            pm10 REAL,
            o3 REAL,
            no2 REAL,
            so2 REAL,
            co REAL,
            risk_score INTEGER,
            condition_text TEXT,
            is_day INTEGER
        )
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_location_timestamp 
        ON weather_readings(location_name, timestamp DESC)
    ''')
    
    # Create predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            prediction_for DATETIME NOT NULL,
            predicted_temp_c REAL,
            predicted_humidity INTEGER,
            predicted_pm2_5 REAL,
            confidence_score REAL,
            algorithm TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def insert_weather_reading(data):
    """Insert weather reading into database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        location = data['location']
        current = data['current']
        air_quality = current.get('air_quality', {})
        
        cursor.execute('''
            INSERT INTO weather_readings (
                location_name, location_lat, location_lon,
                temp_c, temp_f, humidity, wind_kph, wind_dir, wind_degree,
                pressure_mb, visibility_km, uv_index,
                pm2_5, pm10, o3, no2, so2, co,
                condition_text, is_day
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            location['name'],
            location['lat'],
            location['lon'],
            current['temp_c'],
            current['temp_f'],
            current['humidity'],
            current['wind_kph'],
            current['wind_dir'],
            current['wind_degree'],
            current['pressure_mb'],
            current['vis_km'],
            current['uv'],
            air_quality.get('pm2_5', 0),
            air_quality.get('pm10', 0),
            air_quality.get('o3', 0),
            air_quality.get('no2', 0),
            air_quality.get('so2', 0),
            air_quality.get('co', 0),
            current['condition']['text'],
            current['is_day']
        ))
        
        conn.commit()
        reading_id = cursor.lastrowid
        conn.close()
        return reading_id
    except Exception as e:
        print(f"❌ Error inserting weather reading: {e}")
        return None

def get_historical_data(location_name, hours=24):
    """Get historical weather data for a location"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                timestamp,
                temp_c,
                humidity,
                wind_kph,
                pm2_5,
                pm10,
                o3,
                no2,
                uv_index,
                pressure_mb,
                visibility_km,
                condition_text
            FROM weather_readings
            WHERE location_name = ?
            AND datetime(timestamp) >= datetime('now', '-' || ? || ' hours')
            ORDER BY timestamp ASC
        ''', (location_name, hours))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        historical_data = []
        for row in rows:
            historical_data.append({
                'timestamp': row['timestamp'],
                'temp_c': row['temp_c'],
                'humidity': row['humidity'],
                'wind_kph': row['wind_kph'],
                'pm2_5': row['pm2_5'],
                'pm10': row['pm10'],
                'o3': row['o3'],
                'no2': row['no2'],
                'uv_index': row['uv_index'],
                'pressure_mb': row['pressure_mb'],
                'visibility_km': row['visibility_km'],
                'condition_text': row['condition_text']
            })
        
        return historical_data
    except Exception as e:
        print(f"❌ Error fetching historical data: {e}")
        return []

def get_latest_reading(location_name):
    """Get the most recent reading for a location"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM weather_readings
            WHERE location_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (location_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ Error fetching latest reading: {e}")
        return None

def get_database_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total readings
        cursor.execute('SELECT COUNT(*) as total FROM weather_readings')
        total_readings = cursor.fetchone()['total']
        
        # Unique locations
        cursor.execute('SELECT COUNT(DISTINCT location_name) as locations FROM weather_readings')
        unique_locations = cursor.fetchone()['locations']
        
        # Oldest and newest readings
        cursor.execute('SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM weather_readings')
        row = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_readings': total_readings,
            'unique_locations': unique_locations,
            'oldest_reading': row['oldest'],
            'newest_reading': row['newest']
        }
    except Exception as e:
        print(f"❌ Error fetching database stats: {e}")
        return {}

def insert_prediction(location_name, prediction_data):
    """Insert prediction into database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions (
                location_name, prediction_for,
                predicted_temp_c, predicted_humidity, predicted_pm2_5,
                confidence_score, algorithm
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            location_name,
            prediction_data['prediction_for'],
            prediction_data['predicted_temp_c'],
            prediction_data['predicted_humidity'],
            prediction_data['predicted_pm2_5'],
            prediction_data['confidence_score'],
            prediction_data['algorithm']
        ))
        
        conn.commit()
        prediction_id = cursor.lastrowid
        conn.close()
        return prediction_id
    except Exception as e:
        print(f"❌ Error inserting prediction: {e}")
        return None

def cleanup_old_data(days=30):
    """Delete readings older than specified days"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM weather_readings
            WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"🗑️ Cleaned up {deleted} old readings")
        return deleted
    except Exception as e:
        print(f"❌ Error cleaning up old data: {e}")
        return 0

# Initialize database on module import
if not os.path.exists(DATABASE_PATH):
    init_database()
