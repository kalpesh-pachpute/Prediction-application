import sys
import os
from datetime import datetime
from meteostat import Point, Hourly
import pandas as pd

# --- This block adds the root folder to the Python path ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(PROJECT_ROOT)
# --- End of path correction ---

import config  # This will now work

# --- Configuration ---
NYC_LATITUDE = 40.785091  # (Central Park)
NYC_LONGITUDE = -73.968285
START_DATE = datetime(2016, 1, 1) # Jan 1, 2016
END_DATE = datetime(2016, 6, 30, 23, 59, 59) # Jun 30, 2016

# --- Use the new path from config.py ---
OUTPUT_FILE = config.DATA_PATHS['historical_weather']
# Get the directory part (e.g., "data/processed") for os.makedirs
PROCESSED_DIR = os.path.dirname(OUTPUT_FILE)

def fetch_and_save_weather_bulk():
    """
    Fetches all historical weather data for the entire date range
    in a single request and saves it to a CSV.
    """
    print(f"Starting to fetch all weather data from {START_DATE} to {END_DATE}...")
    
    try:
        location = Point(NYC_LATITUDE, NYC_LONGITUDE)
        
        # Get all data in one bulk request
        data = Hourly(location, START_DATE, END_DATE)
        data = data.fetch()
        
        if data.empty:
            print("No data fetched.")
            return

        # --- START OF THE FIX ---

        # 1. Define all columns we WANT and their new names
        desired_rename_map = {
            'temp': 'temp',
            'rhum': 'humidity',
            'wspd': 'wind_speed',
            'visi': 'visibility',  # We want this...
            'coco': 'weather_condition_code'
        }
        
        # 2. Find out which of these columns ACTUALLY exist in the fetched data
        available_cols_map = {
            key: val for key, val in desired_rename_map.items() if key in data.columns
        }
        
        # 3. Inform the user if a column was missing
        if 'visi' not in data.columns:
            print("Note: 'visibility' (visi) data was not found. Skipping this feature.")

        # 4. Select ONLY the available columns
        data_cleaned = data[available_cols_map.keys()].copy()
        
        # 5. Rename ONLY the available columns
        data_cleaned.rename(columns=available_cols_map, inplace=True)

        # --- END OF THE FIX ---
        
        # Handle missing values (fill with 0)
        data_cleaned.fillna(0, inplace=True) 
        data_cleaned.index.name = 'datetime_hourly'
        
        # --- Use the PROCESSED_DIR variable ---
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        
        # Save to CSV
        data_cleaned.to_csv(OUTPUT_FILE)
        
        print(f"Success! Saved {len(data_cleaned)} hourly records to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_and_save_weather_bulk()