#!/usr/bin/env python3
"""
SUMO Data Collection Script
=========================

This script collects data from SUMO simulation and saves it to a CSV file.

Usage:   
    python run_data_collection.py

Requirements:
    - SUMO must be installed
    - Python packages must be installed (requirements.txt)
    - main.sumocfg file must exist
"""

import os
import sys
import time
from datetime import datetime

def check_requirements():
    print("Checking requirements...")
    
    # Check required files
    required_files = [
        "main.sumocfg",
        "vehicles.add.xml",
        "random_routes.rou.xml"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"ERROR: The following files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    # Check Python packages
    try:
        import traci
        import pandas as pd
        import numpy as np
        print("✓ All Python packages are installed")
    except ImportError as e:
        print(f"ERROR: Python package missing: {e}")
        print("Please run 'pip install -r requirements.txt'")
        return False
    
    print("✓ All requirements met")
    return True

def main():
    print("SUMO Data Collection System")
    print("=" * 40)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check requirements
    if not check_requirements():
        print("\nRequirements not met. Please install missing files/packages.")
        return
    
    # Import data collector module
    try:
        from data_collector import SUMODataCollector
    except ImportError as e:
        print(f"Data collector module not found: {e}")
        return
    
    print("\n" + "="*40)
    print("DATA COLLECTION STARTED")
    print("="*40)
    
    # Create data collector
    collector = SUMODataCollector("main.sumocfg")
    
    # Start simulation
    if collector.start_simulation():
        try:
            print("Simulation started, data collection started...")
            
            start_time = time.time()
            df = collector.collect_data("buyukdere_simulation_data_final.csv")
            end_time = time.time()
            
            if df is not None:
                print(f"\n✓ Data collection completed! ({end_time - start_time:.1f} seconds)")
                print(f"✓ Data saved to 'buyukdere_simulation_data_final.csv'")
                print(f"✓ Total records: {len(df):,}")
                print(f"✓ Unique vehicle count: {df['vehicle_id'].nunique()}")
                print(f"✓ Unique vehicle types: {df['vehicle_type'].nunique()}")
                
                # Show file size
                file_size = os.path.getsize("buyukdere_simulation_data_final.csv") / (1024 * 1024)  # MB
                print(f"✓ File size: {file_size:.2f} MB")
                
            else:
                print("✗ Data collection failed!")
                
        finally:
            # Close simulation
            collector.close_simulation()
    else:
        print("✗ Simulation failed to start!")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 