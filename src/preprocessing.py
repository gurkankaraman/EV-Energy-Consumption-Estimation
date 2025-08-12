import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np

#CSV verisi
df_csv = pd.read_csv("../data/buyukdere_simulation_data_final.csv")

#XML araç tipi bilgisi
tree = ET.parse("../config/vehicles.add.xml")
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

columns_to_drop = ['color', 'sigma','has.battery.device','stoppingThreshold','edge_id', 'lane_id', 'vehicle_type', 'speed_ms', 'lane_position', 'angle', 'lane_speed_limit', 'charge_level', 'capacity', 'battery_level', 'max_speed', 'length', 'min_gap', 'mass']
df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')

# --------------------------
# Haversine ile mesafe, % eğim ve eğim değişimi
# --------------------------
R = 6371000  # Dünya yarıçapı (metre)

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# Bir önceki nokta değerleri
df['lat_prev'] = df.groupby('vehicle_id')['lat'].shift()
df['lon_prev'] = df.groupby('vehicle_id')['lon'].shift()
df['z_prev']   = df.groupby('vehicle_id')['z'].shift()

# Yatay mesafe (m)
df['dist_m'] = haversine(df['lat_prev'], df['lon_prev'], df['lat'], df['lon'])

# % eğim
df['slope_pct'] = (df['z'] - df['z_prev']) / df['dist_m'] * 100 

# Geçersiz verileri temizle
df.loc[df['dist_m'] == 0, ['slope_pct']] = np.nan

# Gereksiz yardımcı sütunları sil
df = df.drop(columns=['lat_prev', 'lon_prev', 'z_prev'])

# Kaydet
df.to_csv("../data/final_training_data.csv", index=False)

# --------------------------
# Mini veri analizi
# --------------------------
print("\nFinal veri başarıyla kaydedildi: ../data/final_training_data.csv")

print("\nVeri boyutu (satır, sütun):", df.shape)

print("\nİlk 5 satır:")
print(df.head())

print("\nSayısal sütunların özet istatistikleri:")
print(df.describe())

print("\nEksik değer sayıları:")
print(df.isnull().sum())




