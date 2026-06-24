from datetime import datetime
from meteostat import Point, Hourly
import pandas as pd
import sys
import os

# --- This block adds the root folder to the Python path ---
# This allows us to import the 'config.py' file from the root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..')) # Go up two levels (features -> src -> root)
sys.path.append(PROJECT_ROOT)
# --- End of path correction ---

def get_weather_for_trip(latitude: float, longitude: float, timestamp: datetime) -> dict:
    """
    Fetches historical weather data for a specific location and time using Meteostat.
    
    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        timestamp: A datetime object for the time of the trip (assumed UTC).
        
    Returns:
        A dictionary containing key weather features, or an empty dict on failure.
    """
    try:
        # Meteostat needs a start and end time.
        start = timestamp
        end = timestamp
        
        # Create a Meteostat Point
        location = Point(latitude, longitude)
        
        # Fetch the hourly data
        data = Hourly(location, start, end)
        data = data.fetch()
        
        if data.empty:
            print(f"No weather data found for {timestamp} at ({latitude}, {longitude})")
            return {}
            
        # Extract the first (and only) row of data
        weather_row = data.iloc[0]
        
        weather_features = {
            'temp': weather_row.get('temp'),
            'humidity': weather_row.get('rhum'), # 'rhum' is relative humidity
            'wind_speed': weather_row.get('wspd'),
            'visibility': weather_row.get('visi'),
            'weather_condition_code': weather_row.get('coco') # Weather condition code
        }
        
        # Replace any NaN (Not a Number) values with 0.0
        for key, value in weather_features.items():
            if pd.isna(value):
                weather_features[key] = 0.0

        return weather_features

    except Exception as e:
        print(f"Error fetching weather data for {timestamp}: {e}")
        return {}

# --- THIS IS THE PART YOU ARE LIKELY MISSING ---
# This block only runs when you execute the file directly
# (e.g., python src/features/weather_api.py)
if __name__ == "__main__":
    # Test call for a date from the dataset (Jan 1, 2016, 5:00 PM)
    test_lat = 40.767937
    test_lon = -73.982155
    test_time = datetime(2016, 1, 1, 17, 0, 0) 
    
    print(f"Testing Meteostat for {test_time} at ({test_lat}, {test_lon})...")
    weather = get_weather_for_trip(test_lat, test_lon, test_time)
    
    if weather:
        print("Success! Received data:")
        print(weather)
    else:
        print("Test failed.")