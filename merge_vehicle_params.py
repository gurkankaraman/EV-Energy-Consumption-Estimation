import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path

CSV_IN  = "buyukdere_simulation_data_final.csv"
XML_IN  = "vehicles.add.xml"
CSV_OUT = "buyukdere_simulation_data_with_params.csv"

# 1) XML'den vType parametre tablosu çıkar
def read_vtypes(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows = []
    for vt in root.findall(".//vType"):
        base = vt.attrib.copy()           # accel, decel, mass, maxSpeed, ...
        vid  = base.pop("id", None)
        # <param key="..." value="..."/>
        for p in vt.findall("./param"):
            k = p.attrib.get("key")
            v = p.attrib.get("value")
            base[k] = v
        base["vehicle_type"] = vid       # join için isim sütunu
        rows.append(base)
    df = pd.DataFrame(rows)

    # Tip dönüşümleri (mümkün olanları sayıya çevir)
    numeric_cols = [c for c in df.columns if c != "vehicle_type"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="ignore")
    return df

vtypes_df = read_vtypes(XML_IN)

# 2) CSV'yi oku
# Not: CSV ondalık ayracı '.' ise normal oku. (Türkçe Excel'den geliyorsa delimiter/decimal değişebilir.)
df = pd.read_csv(CSV_IN)

# Eğer vehicle_type sütununda boşluk/format farkı varsa temizleyelim
if "vehicle_type" in df.columns:
    df["vehicle_type"] = df["vehicle_type"].astype(str).str.strip()
else:
    raise ValueError("CSV içinde 'vehicle_type' sütunu bulunamadı.")

# 3) Join: vehicle_type üzerinden parametreleri ekle
merged = df.merge(vtypes_df, on="vehicle_type", how="left")

# 4) Uygun görülen parametreleri yeniden adlandır (opsiyonel, daha okunaklı olsun)
rename_map = {
    "maxSpeed": "vtype_maxSpeed_ms",
    "accel": "vtype_accel_ms2",
    "decel": "vtype_decel_ms2",
    "mass": "vtype_mass_kg",
    "frontSurfaceArea": "vtype_frontalArea_m2",
    "airDragCoefficient": "vtype_Cd",
    "rollDragCoefficient": "vtype_Crr",
    "device.battery.capacity": "vtype_capacity_Wh",
    "maximumPower": "vtype_maxPower_W",
    "constantPowerIntake": "vtype_auxPower_W",
    "propulsionEfficiency": "vtype_propEff",
    "recuperationEfficiency": "vtype_regenEff",
    "device.battery.maximumChargeRate": "vtype_maxChargeRate_W",
}
merged = merged.rename(columns=rename_map)

# 5) Kaydet
merged.to_csv(CSV_OUT, index=False)
print(f"✅ Yazıldı: {Path(CSV_OUT).resolve()}")
print(f"Eklenen kolon sayısı: {merged.shape[1] - df.shape[1]}")
