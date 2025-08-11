import traci
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime
import xml.etree.ElementTree as ET

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
            angle = traci.vehicle.getAngle(vehicle_id)  # derece
            edge_id = traci.vehicle.getRoadID(vehicle_id)
            lane_id = traci.vehicle.getLaneID(vehicle_id)
            
            # Vehicle type information
            vehicle_type = traci.vehicle.getTypeID(vehicle_id)
            
            # Road slope information (from edge)
            slope = self.get_edge_slope(edge_id)
            
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
                'position_x': position[0],
                'position_y': position[1],
                'angle': angle,
                'edge_id': edge_id,
                'lane_id': lane_id,
                'slope': slope,
                'mass_kg': mass,
                'battery_level': battery_level
            }
        except Exception as e:
            print(f"Error collecting data for vehicle {vehicle_id}: {e}")
            return None
    
    def get_edge_slope(self, edge_id):
        try:
            # Get edge height information
            shape = traci.edge.getShape(edge_id)
            if len(shape) >= 2:
                # Calculate height difference between start and end points
                start_height = traci.edge.getParameter(edge_id, "height_start")
                end_height = traci.edge.getParameter(edge_id, "height_end")
                
                if start_height and end_height:
                    start_height = float(start_height)
                    end_height = float(end_height)
                    
                    # Get edge length
                    length = traci.edge.getLength(edge_id)
                    
                    # Calculate slope (in degrees)
                    height_diff = end_height - start_height
                    slope_rad = np.arctan2(height_diff, length)
                    slope_deg = np.degrees(slope_rad)
                    
                    return slope_deg
            
            return 0.0  # Default value
        except:
            return 0.0
    
    def get_vehicle_mass(self, vehicle_type):
        try:
            # Read vehicle type information from vehicles.add.xml
            tree = ET.parse("vehicles.add.xml")
            root = tree.getroot()
            
            for vtype in root.findall("vType"):
                if vtype.get("id") == vehicle_type:
                    mass_param = vtype.find("param[@key='mass']")
                    if mass_param is not None:
                        return float(mass_param.get("value"))
            
            return 1500.0  # Default value
        except:
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
            df = collector.collect_data("buyukdere_simulation_data.csv")
            
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