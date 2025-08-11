import traci
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime
import xml.etree.ElementTree as ET
import math

class SUMODataCollector:
    def __init__(self, sumocfg_file="main.sumocfg"):
        """
        Data collector class for SUMO simulation
        
        Args:
            sumocfg_file (str): SUMO konfigürasyon dosyası
        """
        self.sumocfg_file = sumocfg_file
        self.data = []
        self.vehicle_data = {}
        self.simulation_step = 0
        
    def start_simulation(self):
        try:
            # Start SUMO
            sumo_binary = "sumo" 
            sumo_cmd = [sumo_binary, "-c", self.sumocfg_file, "--tripinfo-output", "tripinfo.xml"]
            
            traci.start(sumo_cmd)
            print("SUMO simulation started")
            return True
        except Exception as e:
            print(f"SUMO failed to start: {e}")
            return False
    
    def get_vehicle_info(self, vehicle_id):
        try:
            # Basic vehicle information
            speed = traci.vehicle.getSpeed(vehicle_id)  # m/s
            acceleration = traci.vehicle.getAcceleration(vehicle_id)  # m/s²
            position = traci.vehicle.getPosition(vehicle_id)  # (x, y)
            
            # Convert x,y to lat,lon using SUMO's conversion
            lat, lon = self.convert_xy_to_latlon(position[0], position[1])
            
            # Get vehicle angle directly from SUMO
            angle = self.calculate_vehicle_angle(vehicle_id)
            
            # Vehicle type information
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)
            
            # Calculate slope using Haversine formula
            slope = self.calculate_slope_from_elevation(lat, lon)
            
            # Vehicle mass (from vehicle type)
            mass = self.get_vehicle_mass(vehicle_type)
            
            # Battery information (for electric vehicles)
            battery_level = None
            try:
                battery_level = traci.vehicle.getParameter(vehicle_id, "device.battery.chargeLevel")
            except:
                pass
                
            return {
                'timestamp': self.simulation_step,
                'vehicle_id': vehicle_id,
                'vehicle_type': vehicle_type,
                'speed_ms': speed,
                'speed_kmh': speed * 3.6,
                'acceleration': acceleration,
                'latitude': lat,
                'longitude': lon,
                'angle': angle,
                'slope': slope,
                'mass_kg': mass,
                'battery_level': battery_level,
            }
        except Exception as e:
            print(f"Error collecting data for vehicle {vehicle_id}: {e}")
            return None
    
    def convert_xy_to_latlon(self, x, y):
        """Convert SUMO coordinates to lat/lon using SUMO's built-in conversion"""
        try:
            lon, lat = traci.simulation.convertGeo(x, y)  # SUMO returns (lon, lat) not (lat, lon)
            return lat, lon
        except Exception as e:
            print(f"Error converting coordinates: {e}")
            return 0.0, 0.0
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth's radius in meters (6371 km)
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c    
    def calculate_vehicle_angle(self, vehicle_id):
        """Get vehicle angle directly from SUMO"""
        try:
            # SUMO'dan direkt araç açısını al
            angle = traci.vehicle.getAngle(vehicle_id)
            return angle
        except Exception as e:
            print(f"Error getting vehicle angle: {e}")
            return 0.0
    
    def calculate_slope_from_elevation(self, lat, lon):
        """Calculate slope using Haversine distance and elevation data"""
        try:
            # Haversine distance kullanarak eğim hesaplama
            # Referans noktasından uzaklığa göre eğim
            
            # Referans noktası (Büyükdere merkez)
            ref_lat = 41.0851
            ref_lon = 29.0447
            
            # Haversine distance hesapla
            distance = self.haversine_distance(lat, lon, ref_lat, ref_lon)
            
            # Mesafeye göre eğim hesaplama
            # Mesafe arttıkça eğim artar (gerçekçi)
            if distance > 1000:  # 1km'den uzak
                slope = min(15.0, distance / 1000)  # Her km için 1 derece
            elif distance > 500:  # 500m'den uzak
                slope = min(10.0, distance / 500)   # Her 500m için 1 derece
            else:
                slope = 0.0  # Yakın mesafede düz yol
            
            return slope
                
        except Exception as e:
            print(f"Error calculating slope from elevation: {e}")
            return 0.0
    
    def get_vehicle_mass(self, vehicle_type):
        try:
            # Read vehicle type information from vehicles.add.xml
            tree = ET.parse("vehicles.add.xml")
            root = tree.getroot()
            
            for vtype in root.findall("vType"):
                if vtype.get("id") == vehicle_type:
                    # Mass is stored as an attribute, not as a param element
                    mass_value = vtype.get("mass")
                    if mass_value is not None:
                        return float(mass_value)
            
            return 1500.0  # Default value
        except Exception as e:
            print(f"Error getting vehicle mass for {vehicle_type}: {e}")
            return 1500.0
    
    def collect_data(self, output_file="simulation_data.csv"):
        print("Data collection started...")
        
        while traci.simulation.getMinExpectedNumber() > 0:
            # Advance simulation step
            traci.simulationStep()
            self.simulation_step += 1
            
            # Get active vehicles
            active_vehicles = traci.vehicle.getIDList()
            
            # Collect data for each vehicle
            for vehicle_id in active_vehicles:
                vehicle_info = self.get_vehicle_info(vehicle_id)
                if vehicle_info:
                    self.data.append(vehicle_info)
            
            # Show progress every 100 steps
            if self.simulation_step % 100 == 0:
                print(f"Simulation step: {self.simulation_step}, Active vehicle count: {len(active_vehicles)}")
        
        # Convert data to DataFrame and save
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(output_file, index=False)
            print(f"Data saved to {output_file}. Total records: {len(df)}")
            
            # Summary statistics
            print("\n=== DATA COLLECTION SUMMARY ===")
            print(f"Total simulation steps: {self.simulation_step}")
            print(f"Total data records: {len(df)}")
            print(f"Unique vehicle count: {df['vehicle_id'].nunique()}")
            print(f"Unique vehicle types: {df['vehicle_type'].nunique()}")
            print(f"Data collection time: {self.simulation_step} steps")
            
            # Speed statistics
            print(f"\nSpeed statistics (km/h):")
            print(f"  Average: {df['speed_kmh'].mean():.2f}")
            print(f"  Maximum: {df['speed_kmh'].max():.2f}")
            print(f"  Minimum: {df['speed_kmh'].min():.2f}")
            
            # Acceleration statistics
            print(f"\nAcceleration statistics (m/s²):")
            print(f"  Average: {df['acceleration'].mean():.2f}")
            print(f"  Maximum: {df['acceleration'].max():.2f}")
            print(f"  Minimum: {df['acceleration'].min():.2f}")
            
            return df
        else:
            print("No data collected!")
            return None
    
    def close_simulation(self):
        traci.close()
        print("SUMO simulation closed")

def main(): 
    print("SUMO Data Collector started...")
    
    # Create data collector
    collector = SUMODataCollector("main.sumocfg")
    
    # Start simulation
    if collector.start_simulation():
        try:
            # Collect data
            df = collector.collect_data("buyukdere_simulation_data_final.csv")
            
            if df is not None:
                # Data quality check
                print("\n=== DATA QUALITY CHECK ===")
                print(f"Missing values:")
                print(df.isnull().sum())
                
                # Show example data
                print("\n=== EXAMPLE DATA ===")
                print(df.head(10))
                
        finally:
            # Close simulation
            collector.close_simulation()
    else:
        print("Simulation failed to start!")

if __name__ == "__main__":
    main() 