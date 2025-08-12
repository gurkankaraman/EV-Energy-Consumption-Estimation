import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np

#CSV verisi
df_csv = pd.read_csv("buyukdere_simulation_data_final.csv")

#XML araç tipi bilgisi
tree = ET.parse("vehicles.add.xml")
root = tree.getroot()

vehicle_types = []
all_param_keys = set()

for vtype in root.findall("vType"):
    for param in vtype.findall("param"):
        all_param_keys.add(param.get("key"))

all_param_keys = list(all_param_keys)

for vtype in root.findall("vType"):
    data = {}
    # Temel attribute'lar
    data["vehicle_type"] = vtype.get("id")
    data["max_speed"] = float(vtype.get("maxSpeed", 0))
    data["accel"] = float(vtype.get("accel", 0))
    data["decel"] = float(vtype.get("decel", 0))
    data["length"] = float(vtype.get("length", 0))
    data["sigma"] = float(vtype.get("sigma", 0))
    data["min_gap"] = float(vtype.get("minGap", 0))
    data["mass"] = float(vtype.get("mass", 0))
    data["color"] = vtype.get("color", "")

    # Parametreleri başta None yap
    for key in all_param_keys:
        data[key] = None

    # XML'deki parametreleri doldur
    for param in vtype.findall("param"):
        key = param.get("key")
        value = param.get("value")
        try:
            value = float(value)
        except:
            pass
        data[key] = value

    vehicle_types.append(data)

df_xml = pd.DataFrame(vehicle_types)

df = df_csv.merge(df_xml, on="vehicle_type", how="left")

df['z'] = df['z'].replace(0, np.nan)
df['z'] = pd.to_numeric(df['z'], errors='coerce')

df = df.sort_values(['vehicle_id', 'timestamp']).reset_index(drop=True)

df['z_filled'] = df.groupby('vehicle_id')['z'].transform(
    lambda grp: grp.interpolate(method='linear', limit_direction='both').ffill().bfill()
)
df['z'] = df['z_filled']
df = df.drop(columns=['z_filled'])

columns_to_drop = ['color', 'sigma','has.battery.device','stoppingThreshold','edge_id', 'lane_id',]
df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

df.to_csv("sumo_data_filled.csv", index=False)



